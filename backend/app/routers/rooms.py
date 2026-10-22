"""F4: deal room — direct chat, per-side AI assistant, room-scoped sharing, closing (FR-28 – FR-37)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import db
from ..auth import Ctx, current
from ..config import settings
from ..errors import ApiError, not_found
from ..services import assistant, audit, ratelimit
from ..services import listings as lst
from ..services import templates as tpl
from ..util import iso, new_id

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

# FR-35: structured items only (type + value + unit), no free text
STRUCTURED = {
    "offer_price": {"label": "Giá đề xuất", "type": "number", "units": ["USD/ton", "USD/kg"]},
    "delivery_schedule": {"label": "Lịch giao", "type": "date", "units": []},
    "payment_terms": {"label": "Điều kiện thanh toán", "type": "enum", "units": [],
                      "options": ["L/C at sight", "T/T 30% deposit, 70% before shipment", "T/T 100% before shipment", "CAD"]},
    "certification": {"label": "Chứng nhận", "type": "enum", "units": [],
                      "options": ["Rainforest Alliance", "4C", "Organic (EU)", "Fairtrade", "Phytosanitary certificate"]},
    "moq": {"label": "MOQ", "type": "number", "units": ["ton", "kg"]},
}


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ShareIn(BaseModel):
    mode: str = Field(pattern="^(snapshot|structured)$")
    field_key: str | None = None  # mode=snapshot (seller only)
    confirm_sensitive: bool = False
    type_key: str | None = None  # mode=structured
    value: str | float | None = None
    unit: str | None = None


def room_for(room_id: str, ctx: Ctx) -> dict:
    """FR-28: only members of the two organizations can see the room."""
    ctx.require_member()
    room = db.one("SELECT * FROM rooms WHERE id = ? AND (seller_org_id = ? OR buyer_org_id = ?)", (room_id, ctx.org_id, ctx.org_id))
    if not room:
        raise not_found("Phòng giao dịch")
    return room


def require_active(room: dict) -> None:
    if room["status"] != "active":
        label = "đã chốt" if room["status"] == "finalized" else "đã đóng"
        raise ApiError("conflict", f"Phòng {room['id']} {label}. Không thể thực hiện thêm thao tác.")


def _side(room: dict, ctx: Ctx) -> str:
    return "seller" if ctx.org_id == room["seller_org_id"] else "buyer"


def _org(org_id: str) -> dict:
    return db.one("SELECT id, name, side FROM organizations WHERE id = ?", (org_id,))


@router.get("")
def my_rooms(ctx: Ctx = Depends(current)):
    ctx.require_member()
    rows = db.all_("SELECT * FROM rooms WHERE seller_org_id = ? OR buyer_org_id = ? ORDER BY created_at DESC", (ctx.org_id, ctx.org_id))
    return [{**r, "seller_org": _org(r["seller_org_id"])["name"], "buyer_org": _org(r["buyer_org_id"])["name"]} for r in rows]


@router.get("/{room_id}")
def room_detail(room_id: str, ctx: Ctx = Depends(current)):
    """Info panel: Listing · Shared info · Contract · Members."""
    room = room_for(room_id, ctx)
    listing = lst.public_view(db.one("SELECT * FROM listings WHERE id = ?", (room["listing_id"],)))
    shared = db.all_("SELECT * FROM shared_items WHERE room_id = ? ORDER BY created_at", (room_id,))
    for s in shared:
        s["shared_by_org"] = _org(room[f"{s['side']}_org_id"])["name"]
        s["badge"] = "Đã thu hồi" if s["revoked_at"] else f"Chia sẻ trong phòng · bởi {s['shared_by_org']}"
    members = db.all_(
        """SELECT u.name, o.name AS org, o.side, m.role FROM memberships m JOIN users u ON u.id = m.user_id
           JOIN organizations o ON o.id = m.org_id WHERE m.org_id IN (?, ?) AND m.status = 'active' ORDER BY o.side DESC, m.role""",
        (room["seller_org_id"], room["buyer_org_id"]),
    )
    contract = db.one("SELECT id, version, status, total, currency FROM contracts WHERE room_id = ? ORDER BY version DESC LIMIT 1", (room_id,))
    side = _side(room, ctx)
    active = room["status"] == "active"
    return {
        "id": room["id"], "status": room["status"], "request_id": room["request_id"],
        "seller_org": _org(room["seller_org_id"])["name"], "buyer_org": _org(room["buyer_org_id"])["name"],
        "my_side": side,
        "listing": listing,
        "listing_changed": listing["version"] != room["listing_version_seen"],
        "shared_items": shared,
        "contract": contract,
        "members": [{**m, "role_label": f"{m['side'].title()} {m['role'].title()}"} for m in members],
        "assistant_title": f"Trợ lý AI — chỉ {ctx.org_name} thấy",
        "permissions": {  # what the UI should show (server still enforces each action)
            "chat": active,
            "share": active and ctx.is_manager,
            "share_from_snapshot": active and ctx.is_manager and side == "seller",
            "close": active and ctx.is_manager,
            "create_contract": active and ctx.is_manager and side == "seller",
            "decide_contract": active and ctx.is_manager and side == "buyer",
        },
        "structured_types": STRUCTURED,
    }


@router.post("/{room_id}/ack-listing-version")
def ack_listing_version(room_id: str, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    v = db.one("SELECT current_version FROM listings WHERE id = ?", (room["listing_id"],))["current_version"]
    db.run("UPDATE rooms SET listing_version_seen = ? WHERE id = ?", (v, room_id))
    db.get_conn().commit()
    return {"ok": True}


# ---------- direct chat (AI never reads this) ----------

@router.get("/{room_id}/messages")
def messages(room_id: str, ctx: Ctx = Depends(current)):
    room_for(room_id, ctx)
    rows = db.all_(
        """SELECT msg.id, msg.text, msg.created_at, u.name AS sender_name, o.name AS sender_org, o.side, m.role
           FROM messages msg LEFT JOIN users u ON u.id = msg.sender_id
           LEFT JOIN memberships m ON m.user_id = msg.sender_id LEFT JOIN organizations o ON o.id = m.org_id
           WHERE msg.room_id = ? ORDER BY msg.id""",
        (room_id,),
    )
    for r in rows:
        r["system"] = r["sender_name"] is None
        r["sender_role"] = f"{r['side'].title()} {r['role'].title()}" if r["side"] else None
    return rows


@router.post("/{room_id}/messages")
def send_message(room_id: str, body: MessageIn, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    require_active(room)
    db.run("INSERT INTO messages (room_id, sender_id, text, created_at) VALUES (?, ?, ?, ?)", (room_id, ctx.user_id, body.text.strip(), iso()))
    db.get_conn().commit()
    return {"ok": True}


# ---------- per-side assistant ----------

@router.get("/{room_id}/assistant")
def assistant_history(room_id: str, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    # FR-30: shared within my org, never the other side's turns
    return db.all_(
        """SELECT t.question, t.answer, t.sources, t.created_at, u.name AS asked_by FROM assistant_turns t
           JOIN users u ON u.id = t.user_id WHERE t.room_id = ? AND t.org_side = ? ORDER BY t.id""",
        (room_id, _side(room, ctx)),
    )


@router.post("/{room_id}/assistant")
def ask(room_id: str, body: AskIn, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ratelimit.check("assistant", ctx.user_id, settings.rate_assistant_per_hour)
    result = assistant.answer(room, body.question)
    db.run(
        "INSERT INTO assistant_turns (room_id, org_side, user_id, question, answer, sources, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (room_id, _side(room, ctx), ctx.user_id, body.question, result["answer"], db.dumps(result["sources"]), iso()),
    )
    db.get_conn().commit()
    if result["refused"]:
        audit.log(ctx, "assistant.refuse", room_id, outcome="blocked")  # no prompt stored (FR-48)
    return result


# ---------- room-scoped sharing (managers only) ----------

@router.post("/{room_id}/shared")
def share(room_id: str, body: ShareIn, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager()  # AT-21
    require_active(room)
    side = _side(room, ctx)

    if body.mode == "snapshot":
        if side != "seller":
            raise ApiError("forbidden", "Chỉ Seller Manager mới chia sẻ được trường từ snapshot riêng.")
        listing = db.one("SELECT * FROM listings WHERE id = ?", (room["listing_id"],))
        snap = db.one("SELECT * FROM snapshots WHERE id = ?", (lst.current_version(listing["id"])["snapshot_id"],))
        fd = tpl.field_map(tpl.by_id(listing["template_id"])).get(body.field_key or "")
        item = next((i for i in snap["fields"] if i["key"] == body.field_key), None)
        if not fd or not item:
            raise ApiError("validation_failed", "Trường không có trong snapshot của listing này.")
        if fd["blocked"]:
            audit.log(ctx, "room.share", room_id, outcome="blocked", detail=fd["key"])
            raise ApiError("policy_denied", "Trường này không được công khai theo chính sách của sàn.")
        if fd["sensitive"] and not body.confirm_sensitive:
            raise ApiError("validation_failed", f"{fd['label']} là trường nhạy cảm. Xác nhận thêm một lần để chia sẻ trong phòng này.",
                           {"needs_confirmation": [fd["key"]]})
        type_key, label, value, unit, from_field = fd["key"], fd["label"], item["value"], item["unit"], fd["key"]
    else:
        spec = STRUCTURED.get(body.type_key or "")
        if not spec:
            raise ApiError("validation_failed", f"Loại thông tin không hợp lệ. Chọn: {', '.join(STRUCTURED)}.")
        if body.value in (None, ""):
            raise ApiError("validation_failed", f"Nhập giá trị cho {spec['label']}.")
        if spec["type"] == "number":
            try:
                value = float(body.value)
            except (TypeError, ValueError):
                raise ApiError("validation_failed", f"{spec['label']} phải là số.")
        elif spec["type"] == "enum":
            if body.value not in spec["options"]:
                raise ApiError("validation_failed", f"Chọn {spec['label']} trong danh sách có sẵn.")
            value = body.value
        else:
            value = str(body.value)
        if spec["units"] and body.unit not in spec["units"]:
            raise ApiError("validation_failed", f"Chọn đơn vị cho {spec['label']}: {', '.join(spec['units'])}.")
        type_key, label, unit, from_field = body.type_key, spec["label"], body.unit if spec["units"] else None, None

    item_id = new_id("shr")
    db.run(
        "INSERT INTO shared_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
        (item_id, room_id, side, ctx.user_id, type_key, label, str(value), unit, from_field, iso()),
    )
    db.get_conn().commit()
    audit.log(ctx, "room.share", item_id)  # label only, never the value
    return {"id": item_id, "label": label, "badge": f"Chia sẻ trong phòng · bởi {ctx.org_name}"}


@router.post("/{room_id}/shared/{item_id}/revoke")
def revoke(room_id: str, item_id: str, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager()
    item = db.one("SELECT * FROM shared_items WHERE id = ? AND room_id = ? AND side = ?", (item_id, room_id, _side(room, ctx)))
    if not item:
        raise not_found("Mục chia sẻ")
    if item["revoked_at"]:
        raise ApiError("conflict", "Mục này đã được thu hồi.")
    db.run("UPDATE shared_items SET revoked_at = ? WHERE id = ?", (iso(), item_id))
    db.get_conn().commit()
    audit.log(ctx, "room.revoke", item_id)
    return {"ok": True, "note": "AI sẽ không dùng mục này nữa. Người đã đọc thì không thể \"quên\"."}


@router.post("/{room_id}/close")
def close_room(room_id: str, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager()
    require_active(room)
    with db.transaction():
        db.run("UPDATE rooms SET status = 'closed' WHERE id = ?", (room_id,))
        # FR-37: pending contract is cancelled, history kept
        db.run("UPDATE contracts SET status = 'cancelled' WHERE room_id = ? AND status IN ('pending', 'draft', 'revision_requested')", (room_id,))
        db.run("INSERT INTO messages (room_id, sender_id, text, created_at) VALUES (?, NULL, ?, ?)",
               (room_id, f"{ctx.org_name} đã đóng phòng.", iso()))
    audit.log(ctx, "room.close", room_id)
    return {"ok": True, "status": "closed"}
