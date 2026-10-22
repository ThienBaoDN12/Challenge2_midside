"""Discovery AI (F2, FR-16 – FR-20).

Input surface is ONLY listings.public_view() of published, unexpired listings
(FR-17). Criteria parsing and ranking are rule based, so results are explainable
and never invent sellers (FR-19). Hard criteria are filtered before ranking and
are never silently dropped; relaxing one requires explicit user consent (FR-18).
"""
import re
from datetime import date

from .. import db
from ..util import today
from . import listings as lst
from .units import to_kg

PRODUCTS = {
    "coffee": ["cà phê", "ca phe", "coffee", "robusta", "arabica"],
    "pepper": ["hồ tiêu", "ho tieu", "tiêu", "pepper"],
    "cashew": ["hạt điều", "hat dieu", "điều", "cashew"],
    "rice": ["gạo", "gao", "rice"],
    # Known products the platform has no template for -> valid query, zero results (AT-08)
    "durian": ["sầu riêng", "sau rieng", "durian"],
}
VARIETIES = ["robusta", "arabica"]
UNIT_ALIASES = {"tấn": "ton", "tan": "ton", "tons": "ton", "ton": "ton", "t": "ton", "kg": "kg", "kilograms": "kg", "kilogram": "kg"}
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse(text: str, given: dict | None = None) -> dict:
    """Free text (+ answers from quick-reply buttons) -> normalized criteria."""
    t = (text or "").lower()
    c = {"product_type": None, "variety": None, "quantity": None, "unit": None, "destination": None, "before": None}
    for ptype, words in PRODUCTS.items():
        if any(w in t for w in words):
            c["product_type"] = ptype
            break
    c["variety"] = next((v for v in VARIETIES if v in t), None)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(tấn|tan|tons?|kg|kilograms?|t)\b", t)
    if m:
        c["quantity"] = float(m.group(1).replace(",", "."))
        c["unit"] = UNIT_ALIASES[m.group(2)]
    else:
        m = re.search(r"\b(\d+(?:[.,]\d+)?)\b", t)
        if m and not re.search(r"\d+/\d+", t[m.start():m.end() + 3]):
            c["quantity"] = float(m.group(1).replace(",", "."))
    for dest in ["phnom penh", "siem reap", "sihanoukville", "battambang"]:
        if dest in t:
            c["destination"] = dest.title()
    m = re.search(r"(?:trước|before)\s+(\d{1,2})/(\d{1,2})", t) or None
    if m:
        c["before"] = date(date.fromisoformat(today()).year, int(m.group(2)), int(m.group(1))).isoformat()
    else:
        m = re.search(r"before\s+([a-z]{3})[a-z]*\s+(\d{1,2})", t)
        if m and m.group(1) in MONTHS:
            c["before"] = date(date.fromisoformat(today()).year, MONTHS[m.group(1)], int(m.group(2))).isoformat()
    for k, v in (given or {}).items():
        if v not in (None, ""):
            c[k] = v
    return c


def missing(c: dict) -> list[str]:
    return [k for k in ("product_type", "quantity", "unit") if not c.get(k)]


QUICK_REPLIES = {
    "product_type": [{"label": "Cà phê", "value": {"product_type": "coffee"}}, {"label": "Hồ tiêu", "value": {"product_type": "pepper"}}, {"label": "Hạt điều", "value": {"product_type": "cashew"}}, {"label": "Gạo", "value": {"product_type": "rice"}}],
    "quantity": [{"label": "10 tấn", "value": {"quantity": 10, "unit": "ton"}}, {"label": "20 tấn", "value": {"quantity": 20, "unit": "ton"}}, {"label": "50 tấn", "value": {"quantity": 50, "unit": "ton"}}],
    "unit": [{"label": "Tấn", "value": {"unit": "ton"}}, {"label": "Kg", "value": {"unit": "kg"}}],
}
QUESTIONS = {
    "product_type": "Bạn cần mua sản phẩm gì?",
    "quantity": "Bạn cần khối lượng bao nhiêu?",
    "unit": "Khối lượng đó tính theo đơn vị nào?",
}


def _searchable() -> list[dict]:
    lst.refresh_expired()
    rows = db.all_("SELECT * FROM listings WHERE status = 'published' AND valid_until >= ?", (today(),))
    return [lst.public_view(r) for r in rows]


def _qty_kg(view: dict) -> float | None:
    q = view["public_fields"].get("quantity")
    return float(to_kg(q["value"], q["unit"])) if q else None


def _hard_match(view: dict, c: dict, min_kg: float | None) -> bool:
    if view["product_type"] != c["product_type"]:
        return False
    if c.get("variety"):
        product = str(view["public_fields"].get("product", {}).get("value", "")).lower()
        if c["variety"] not in product:
            return False
    if min_kg is not None:
        have = _qty_kg(view)
        if have is None or have < min_kg:
            return False
    return True


def _explain(view: dict, c: dict) -> tuple[list[str], list[str]]:
    pf = view["public_fields"]
    matched = ["Sản phẩm"]
    if c.get("quantity"):
        matched.append("Khối lượng")
    unmet = []
    if c.get("before"):
        if view["valid_until"] >= c["before"] and "delivery_window" in pf:
            matched.append("Thời gian giao")
        else:
            unmet.append("Ngày giao cần xác nhận với seller")
    if c.get("destination"):
        inc = pf.get("incoterm", {}).get("value")
        if inc in ("DAP", "CIF"):
            matched.append(f"Điều kiện giao {inc}")
        else:
            unmet.append(f"Vận chuyển tới {c['destination']} chưa được xác nhận")
    if "moq" in pf and c.get("quantity"):
        moq_kg = float(to_kg(pf["moq"]["value"], pf["moq"]["unit"]))
        if moq_kg > float(to_kg(c["quantity"], c["unit"])):
            unmet.append("MOQ cao hơn khối lượng bạn cần")
    return matched, unmet


def search(text: str, given: dict | None = None, accept_relaxation: dict | None = None) -> dict:
    c = parse(text, given)
    miss = missing(c)
    if miss:
        k = miss[0]
        return {"status": "needs_clarification", "criteria": c, "missing": miss, "question": QUESTIONS[k], "quick_replies": QUICK_REPLIES[k]}

    if accept_relaxation:  # user clicked "agree" on a proposed relaxation
        c.update(accept_relaxation)
    min_kg = float(to_kg(c["quantity"], c["unit"]))
    pool = _searchable()
    hits = [v for v in pool if _hard_match(v, c, min_kg)]

    results = []
    for v in hits:
        matched, unmet = _explain(v, c)
        score = round(100 * len(matched) / (len(matched) + len(unmet)))
        results.append({"listing": v, "matched": matched, "unmet": unmet, "score": score, "updated_at": v["updated_at"]})
    results.sort(key=lambda r: (-r["score"], r["listing"]["id"]))

    out = {"status": "ok" if results else "no_results", "criteria": c, "results": results,
           "notice": "Gợi ý của AI chưa phải là kết nối."}
    if not results:
        out["message"] = "Hiện không có listing công khai nào đáp ứng tiêu chí của bạn."
        same_product = [v for v in pool if _hard_match(v, c, None)]
        if same_product:
            best = max(same_product, key=lambda v: _qty_kg(v) or 0)
            q = best["public_fields"]["quantity"]
            out["relaxation"] = {
                "description": f"Giảm khối lượng xuống {q['value']:g} {q['unit']}?",
                "apply": {"quantity": q["value"], "unit": q["unit"]},
            }
    return out


def standard(product_type: str | None, min_quantity: float | None, unit: str | None, available_before: str | None) -> list[dict]:
    """FR-20: plain filter search, works without the AI."""
    out = []
    for v in _searchable():
        if product_type and v["product_type"] != product_type:
            continue
        if min_quantity and unit:
            have = _qty_kg(v)
            if have is None or have < float(to_kg(min_quantity, unit)):
                continue
        if available_before and v["valid_until"] < available_before:
            continue
        out.append(v)
    return out
