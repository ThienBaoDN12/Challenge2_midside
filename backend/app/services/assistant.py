"""Per-side room assistant (F4, FR-30 – FR-34).

Allowed sources, and nothing else (FR-31):
  1. public fields of the room's listing, current version
  2. active (not revoked) shared items of this room
  3. the room's latest sent contract summary
The assistant has no tools: it cannot message, create contracts or change room state (FR-34).
Answers are composed by rules from those sources; Gemini, if configured, may only
rephrase the composed facts and never receives anything else (open decision §15.2).
"""
import os

import requests

from .. import db
from ..config import settings
from . import listings as lst

TOPICS = {
    "moq": ["moq", "tối thiểu", "minimum order", "đặt tối thiểu"],
    "payment_terms": ["thanh toán", "payment"],
    "delivery_window": ["lịch giao", "ngày giao", "giao hàng", "delivery", "khi nào giao"],
    "certification": ["chứng nhận", "certific"],
    "incoterm": ["incoterm", "điều kiện giao", "fob", "cif", "dap"],
    "port_of_loading": ["cảng", "port", "nơi giao", "địa điểm giao"],
    "grade": ["chất lượng", "grade", "quality", "phân loại"],
    "total": ["tổng giá", "tổng tiền", "total"],
    "quantity": ["số lượng", "khối lượng", "quantity", "bao nhiêu tấn"],
    "valid_until": ["hiệu lực", "valid", "hết hạn"],
    "indicative_price": ["đơn giá", "giá đề xuất", "giá tham khảo", "giá bán", "price", "giá"],
    "product": ["sản phẩm", "product", "mặt hàng"],
}
# Data that belongs to one party and is never answered unless its owner shared it in this room (FR-33)
PRIVATE = {
    "floor_price": ["giá sàn", "floor price", "floor"],
    "cost_price": ["giá vốn", "cost price"],
    "budget": ["ngân sách", "budget"],
    "supplier_households": ["hộ cung cấp", "hộ nông dân", "farmer", "household"],
}
INJECTION = [
    "bỏ qua luật", "bỏ qua quy tắc", "ignore previous", "ignore the rules", "ignore all",
    "file mật", "confidential file", "snapshot riêng", "system prompt", "jailbreak", "developer mode",
]
EXPLAIN_CONTRACT = ["giải thích", "explain", "hợp đồng", "contract", "điều khoản"]

# shared-item type -> topic, contract term -> topic
SHARED_TOPIC = {"offer_price": "indicative_price", "delivery_schedule": "delivery_window", "payment_terms": "payment_terms", "certification": "certification", "moq": "moq"}
CONTRACT_TOPIC = {"quality": "grade", "unit_price": "indicative_price", "delivery_date": "delivery_window", "delivery_location": "port_of_loading", "payment_terms": "payment_terms", "quantity": "quantity", "incoterm": "incoterm", "product": "product", "total": "total"}

NO_DATA = "Mình chưa có thông tin này trong phòng. Bạn có thể hỏi đối tác trong chat."
DENIED = "Mình chỉ trả lời từ listing công khai, thông tin đã chia sẻ trong phòng và tóm tắt hợp đồng. Bạn có thể hỏi đối tác trong chat."


def _has(q: str, words: list[str]) -> bool:
    return any(w in q for w in words)


def gather(room: dict) -> dict:
    """Collect the three allowed sources for a room. Nothing private is read here."""
    v = lst.current_version(room["listing_id"])
    shared = db.all_("SELECT * FROM shared_items WHERE room_id = ? AND revoked_at IS NULL", (room["id"],))
    contract = db.one(
        "SELECT * FROM contracts WHERE room_id = ? AND status != 'draft' ORDER BY version DESC LIMIT 1",
        (room["id"],),
    )
    return {"listing_id": room["listing_id"], "listing_version": v["version"], "listing": v["public_projection"], "shared": shared, "contract": contract}


def _fmt(value, unit) -> str:
    try:  # shared items store numbers as text ("3850.0")
        num = float(value)
        value = f"{num:,.0f}" if num.is_integer() else f"{num:,}"
    except (TypeError, ValueError):
        pass
    return f"{value} {unit}".strip() if unit else str(value)


def _org_name(side: str, room: dict) -> str:
    org_id = room["seller_org_id"] if side == "seller" else room["buyer_org_id"]
    return db.one("SELECT name FROM organizations WHERE id = ?", (org_id,))["name"]


def answer(room: dict, question: str) -> dict:
    q = question.lower()
    src = gather(room)

    if _has(q, INJECTION):
        return {"answer": DENIED, "sources": [], "refused": True}

    # FR-33: private data only if its owner shared it here
    for key, words in PRIVATE.items():
        if _has(q, words):
            item = next((s for s in src["shared"] if key in (s["from_field"], s["type_key"])), None)
            if not item:
                return {"answer": NO_DATA, "sources": [], "refused": True}
            who = _org_name(item["side"], room)
            return {
                "answer": f"{item['label']}: {_fmt(item['value'], item['unit'])} (do {who} chia sẻ trong phòng).",
                "sources": [{"type": "shared_item", "id": item["id"], "label": item["label"], "shared_by": who}],
                "refused": False,
            }

    c = src["contract"]
    if c and _has(q, EXPLAIN_CONTRACT) and not any(_has(q, w) for k, w in TOPICS.items() if k not in ("product",)):
        lines = [f"- {t['label']}: {_fmt(t['value'], t.get('unit'))}" for t in c["terms"]]
        lines.append(f"- Tổng giá trị: {c['total']} {c['currency']} (hệ thống tính)")
        return {
            "answer": f"Hợp đồng v{c['version']} ({c['status']}) gồm các điều khoản:\n" + "\n".join(lines)
            + "\nĐây là xác nhận trong hệ thống, không phải chữ ký số.",
            "sources": [{"type": "contract", "id": c["id"], "version": c["version"]}],
            "refused": False,
        }

    topic = next((k for k, words in TOPICS.items() if _has(q, words)), None)
    if not topic:
        return {"answer": NO_DATA, "sources": [], "refused": False}

    facts, sources = [], []
    if c:
        for t in c["terms"]:
            if CONTRACT_TOPIC.get(t["key"]) == topic:
                facts.append(f"Hợp đồng v{c['version']}: {t['label']} = {_fmt(t['value'], t.get('unit'))}")
                sources.append({"type": "contract", "id": c["id"], "version": c["version"], "term": t["key"]})
        if topic == "total":
            facts.append(f"Hợp đồng v{c['version']}: Tổng giá trị = {c['total']} {c['currency']} (hệ thống tính)")
            sources.append({"type": "contract", "id": c["id"], "version": c["version"], "term": "total"})
    for s in src["shared"]:
        if topic in (SHARED_TOPIC.get(s["type_key"]), s["from_field"]):
            who = _org_name(s["side"], room)
            facts.append(f"Chia sẻ trong phòng bởi {who}: {s['label']} = {_fmt(s['value'], s['unit'])}")
            sources.append({"type": "shared_item", "id": s["id"], "label": s["label"], "shared_by": who})
    field = src["listing"].get(topic)
    if field:
        facts.append(f"Theo listing {src['listing_id']} v{src['listing_version']} · trường {field['label']}: {_fmt(field['value'], field['unit'])}")
        sources.append({"type": "listing", "id": src["listing_id"], "version": src["listing_version"], "field": topic})

    if not facts:
        return {"answer": NO_DATA, "sources": [], "refused": False}
    text = "\n".join(facts)
    return {"answer": _rephrase(question, text), "sources": sources, "refused": False}


def _rephrase(question: str, facts: str) -> str:
    """Optional LLM wording. The model only ever sees the question and already-allowed facts."""
    if not settings.gemini_api_key:
        return facts
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    prompt = (
        "Trả lời ngắn gọn bằng tiếng Việt chỉ dựa trên các dữ kiện sau, giữ nguyên số liệu và "
        "ghi rõ nguồn trong ngoặc. Không thêm thông tin khác.\n"
        f"Câu hỏi: {question}\nDữ kiện:\n{facts}"
    )
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=10,
        )
        if res.status_code == 200:
            return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return facts
