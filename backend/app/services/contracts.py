"""Contract prefill, validation and diff marking (F5, FR-39 – FR-43)."""
from decimal import Decimal

from ..errors import ApiError
from . import assistant
from .units import fmt_money, total_value

TERMS = [
    ("product", "Sản phẩm"),
    ("quality", "Chất lượng"),
    ("quantity", "Số lượng"),
    ("unit_price", "Đơn giá"),
    ("incoterm", "Điều kiện giao"),
    ("delivery_location", "Địa điểm giao"),
    ("delivery_date", "Ngày giao"),
    ("payment_terms", "Điều kiện thanh toán"),
]
LABELS = dict(TERMS)
REQUIRED = ["quantity", "unit_price", "delivery_date", "payment_terms"]  # FR-40
QTY_UNITS = ["ton", "kg"]
PRICE_UNITS = ["USD/ton", "USD/kg", "VND/ton", "VND/kg"]

# contract term <- listing field
FROM_LISTING = {"product": "product", "quality": "grade", "quantity": "quantity", "unit_price": "indicative_price",
                "incoterm": "incoterm", "delivery_location": "port_of_loading", "delivery_date": "delivery_window",
                "payment_terms": "payment_terms"}
# contract term <- structured shared item type
FROM_SHARED = {"unit_price": "offer_price", "delivery_date": "delivery_schedule", "payment_terms": "payment_terms"}


def prefill(room: dict) -> list[dict]:
    src = assistant.gather(room)
    terms = []
    for key, label in TERMS:
        value, unit, origin = None, None, None
        lf = src["listing"].get(FROM_LISTING[key])
        if lf:
            value, unit, origin = lf["value"], lf["unit"], "listing"
        shared = next((s for s in src["shared"] if s["type_key"] == FROM_SHARED.get(key) or s["from_field"] == FROM_LISTING[key]), None)
        if shared:  # room info is more specific than the public listing
            value, unit, origin = shared["value"], shared["unit"], "shared"
        terms.append({"key": key, "label": label, "value": value, "unit": unit, "origin": origin})
    return terms


def validate(terms: list[dict], claimed_total: str | None = None) -> tuple[Decimal, str]:
    """Policy check §8 for send/confirm: units, currency, required terms, deterministic total."""
    by = {t["key"]: t for t in terms}
    problems = []
    for key in REQUIRED:
        t = by.get(key)
        if not t or t.get("value") in (None, ""):
            problems.append(f"Thiếu điều khoản {LABELS[key]}.")
    q, p = by.get("quantity") or {}, by.get("unit_price") or {}
    if q.get("value") not in (None, "") and q.get("unit") not in QTY_UNITS:
        problems.append("Số lượng phải chọn đơn vị (ton hoặc kg).")
    if p.get("value") not in (None, "") and p.get("unit") not in PRICE_UNITS:
        problems.append("Đơn giá phải chọn tiền tệ và đơn vị (ví dụ USD/ton).")
    if problems:
        raise ApiError("policy_denied", " ".join(problems), {"problems": problems})
    try:
        total, currency = total_value(q["value"], q["unit"], p["value"], p["unit"])
    except Exception:
        raise ApiError("validation_failed", "Số lượng và đơn giá phải là số.")
    if claimed_total not in (None, ""):
        if Decimal(str(claimed_total)).quantize(Decimal("0.01")) != total:
            raise ApiError(
                "policy_denied",
                f"Tổng giá trị không khớp. Hệ thống đã tính lại: {fmt_money(total, currency)}.",
                {"recalculated_total": str(total), "currency": currency},
            )
    return total, currency


def mark_differences(room: dict, terms: list[dict]) -> list[dict]:
    """FR-43: flag terms that differ from the public listing or come from room-shared info."""
    src = assistant.gather(room)
    out = []
    for t in terms:
        t = dict(t)
        lf = src["listing"].get(FROM_LISTING.get(t["key"], ""))
        shared = next((s for s in src["shared"] if s["type_key"] == FROM_SHARED.get(t["key"]) or s["from_field"] == FROM_LISTING.get(t["key"])), None)
        t["from_shared"] = bool(shared and str(shared["value"]) == str(t["value"]))
        t["differs_from_listing"] = bool(lf) and (str(lf["value"]) != str(t["value"]) or (lf["unit"] or None) != (t.get("unit") or None))
        out.append(t)
    return out
