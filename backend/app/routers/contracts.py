"""F5: contracts — Seller Manager creates, Buyer Manager decides (FR-38 – FR-44).

This is an in-system confirmation, not a digital signature and not a legal contract.
"""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .. import db
from ..auth import Ctx, current
from ..config import settings
from ..errors import ApiError, not_found
from ..services import audit
from ..services import contracts as svc
from ..util import iso, new_id
from .rooms import require_active, room_for

router = APIRouter(prefix="/api/rooms/{room_id}/contracts", tags=["contracts"])

DISCLAIMER = "Xác nhận trong hệ thống, không phải chữ ký số và không thay thế hợp đồng pháp lý."
OPEN_STATUSES = ("draft", "pending")


class TermIn(BaseModel):
    key: str
    label: str | None = None
    value: str | float | None = None
    unit: str | None = None


class ContractIn(BaseModel):
    terms: list[TermIn]
    total: str | None = None  # optional client-side total; must match the system's
    send: bool = False  # false = save draft


class ConfirmIn(BaseModel):
    acknowledge_in_system: bool = False


class RevisionIn(BaseModel):
    term_notes: dict[str, str] = Field(default_factory=dict)
    note: str | None = None


class DeclineIn(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


def _view(c: dict, room: dict, ctx: Ctx) -> dict:
    out = {k: c[k] for k in ("id", "version", "status", "total", "currency", "pdf_name", "note", "term_notes", "created_at", "decided_at")}
    out["version_label"] = f"v{c['version']}"
    out["terms"] = svc.mark_differences(room, c["terms"])
    out["disclaimer"] = DISCLAIMER
    side = "seller" if ctx.org_id == room["seller_org_id"] else "buyer"
    active = room["status"] == "active"
    out["actions"] = {  # staff never gets actions (FR-42, AT-23)
        "edit": active and ctx.is_manager and side == "seller" and c["status"] == "draft",
        "send": active and ctx.is_manager and side == "seller" and c["status"] == "draft",
        "decide": active and ctx.is_manager and side == "buyer" and c["status"] == "pending",
    }
    return out


def _contract(room_id: str, contract_id: str) -> dict:
    c = db.one("SELECT * FROM contracts WHERE id = ? AND room_id = ?", (contract_id, room_id))
    if not c:
        raise not_found("Hợp đồng")
    return c


def _normalize(terms: list[TermIn]) -> list[dict]:
    out = []
    for t in terms:
        if t.key not in svc.LABELS:
            raise ApiError("validation_failed", f"Điều khoản không hợp lệ: {t.key}.")
        out.append({"key": t.key, "label": svc.LABELS[t.key], "value": t.value, "unit": t.unit})
    return out


@router.get("")
def history(room_id: str, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    rows = db.all_("SELECT * FROM contracts WHERE room_id = ? ORDER BY version DESC", (room_id,))
    return {"disclaimer": DISCLAIMER, "versions": [_view(c, room, ctx) for c in rows]}


@router.get("/prefill")
def prefill(room_id: str, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager("seller")
    terms = svc.prefill(room)
    return {"terms": terms, "quantity_units": svc.QTY_UNITS, "price_units": svc.PRICE_UNITS, "disclaimer": DISCLAIMER}


@router.post("")
def create(room_id: str, body: ContractIn, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager("seller")  # FR-38
    require_active(room)
    if db.one("SELECT 1 FROM contracts WHERE room_id = ? AND status IN ('pending', 'draft')", (room_id,)):
        raise ApiError("conflict", "Phòng đã có một hợp đồng đang chờ xác nhận hoặc bản nháp. Hoàn tất bản đó trước.")
    terms = _normalize(body.terms)
    total, currency = svc.validate(terms, body.total) if body.send else (None, None)
    version = db.one("SELECT COALESCE(MAX(version), 0) + 1 AS v FROM contracts WHERE room_id = ?", (room_id,))["v"]
    cid = new_id("ctr")
    db.run(
        "INSERT INTO contracts (id, room_id, version, status, terms, total, currency, sent_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (cid, room_id, version, "pending" if body.send else "draft", db.dumps(terms),
         None if total is None else str(total), currency, ctx.user_id if body.send else None, iso()),
    )
    db.get_conn().commit()
    if body.send:
        _announce_sent(room, version, ctx)
    audit.log(ctx, "contract.send" if body.send else "contract.draft", f"{cid}@v{version}")
    return _view(_contract(room_id, cid), room, ctx)


@router.put("/{contract_id}")
def edit_draft(room_id: str, contract_id: str, body: ContractIn, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager("seller")
    require_active(room)
    c = _contract(room_id, contract_id)
    if c["status"] != "draft":
        # FR-41: sent contracts are never edited in place
        raise ApiError("conflict", "Hợp đồng đã gửi không sửa tại chỗ. Tạo phiên bản mới sau khi buyer yêu cầu sửa.")
    terms = _normalize(body.terms)
    db.run("UPDATE contracts SET terms = ? WHERE id = ?", (db.dumps(terms), contract_id))
    db.get_conn().commit()
    if body.send:
        return send(room_id, contract_id, ContractIn(terms=body.terms, total=body.total), ctx)
    return _view(_contract(room_id, contract_id), room, ctx)


@router.post("/{contract_id}/send")
def send(room_id: str, contract_id: str, body: ContractIn | None = None, ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager("seller")
    require_active(room)
    c = _contract(room_id, contract_id)
    if c["status"] != "draft":
        raise ApiError("conflict", "Chỉ gửi được bản nháp.")
    if db.one("SELECT 1 FROM contracts WHERE room_id = ? AND status = 'pending'", (room_id,)):
        raise ApiError("conflict", "Đã có một hợp đồng khác đang chờ xác nhận.")
    total, currency = svc.validate(c["terms"], body.total if body else None)
    db.run("UPDATE contracts SET status = 'pending', total = ?, currency = ?, sent_by = ? WHERE id = ?", (str(total), currency, ctx.user_id, contract_id))
    db.get_conn().commit()
    _announce_sent(room, c["version"], ctx)
    audit.log(ctx, "contract.send", f"{contract_id}@v{c['version']}")
    return _view(_contract(room_id, contract_id), room, ctx)


def _announce_sent(room: dict, version: int, ctx: Ctx) -> None:
    audit.notify(room["buyer_org_id"], "contract_sent", f"Hợp đồng v{version} trong phòng {room['id']} chờ buyer xác nhận.", room["id"])
    db.run("INSERT INTO messages (room_id, sender_id, text, created_at) VALUES (?, NULL, ?, ?)",
           (room["id"], f"{ctx.org_name} đã gửi hợp đồng v{version}. Chờ buyer xác nhận.", iso()))
    db.get_conn().commit()


@router.post("/{contract_id}/pdf")
async def attach_pdf(room_id: str, contract_id: str, file: UploadFile = File(...), ctx: Ctx = Depends(current)):
    room = room_for(room_id, ctx)
    ctx.require_manager("seller")
    c = _contract(room_id, contract_id)
    if c["status"] != "draft":
        raise ApiError("conflict", "Chỉ đính kèm PDF vào bản nháp.")
    raw = await file.read(5 * settings.max_upload_bytes + 1)
    if not raw.startswith(b"%PDF") or len(raw) > 5 * settings.max_upload_bytes:
        raise ApiError("validation_failed", "Chỉ nhận file PDF tối đa 5 MB.")
    db.run("UPDATE contracts SET pdf_name = ?, pdf_blob = ? WHERE id = ?", (file.filename, raw, contract_id))
    db.get_conn().commit()
    return _view(_contract(room_id, contract_id), room, ctx)


@router.get("/{contract_id}/pdf")
def download_pdf(room_id: str, contract_id: str, ctx: Ctx = Depends(current)):
    room_for(room_id, ctx)
    c = db.one("SELECT pdf_name, pdf_blob FROM contracts WHERE id = ? AND room_id = ?", (contract_id, room_id))
    if not c or not c["pdf_blob"]:
        raise not_found("PDF")
    return Response(c["pdf_blob"], media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{c["pdf_name"]}"'})


def _pending_for_buyer(room_id: str, contract_id: str, ctx: Ctx) -> tuple[dict, dict]:
    room = room_for(room_id, ctx)
    ctx.require_manager("buyer")  # role re-checked at click time (F5 rules)
    require_active(room)
    c = _contract(room_id, contract_id)
    if c["status"] != "pending":
        raise ApiError("conflict", f"Hợp đồng đang ở trạng thái {c['status']}, không thể xử lý.")
    return room, c


@router.post("/{contract_id}/confirm")
def confirm(room_id: str, contract_id: str, body: ConfirmIn, ctx: Ctx = Depends(current)):
    room, c = _pending_for_buyer(room_id, contract_id, ctx)
    if not body.acknowledge_in_system:
        raise ApiError("validation_failed", "Hãy tick \"Tôi hiểu đây là xác nhận trong hệ thống\" trước khi xác nhận.")
    svc.validate(c["terms"], c["total"])  # policy check also at confirm time (§8)
    with db.transaction():
        db.run("UPDATE contracts SET status = 'confirmed', decided_by = ?, decided_at = ? WHERE id = ?", (ctx.user_id, iso(), contract_id))
        db.run("UPDATE rooms SET status = 'finalized' WHERE id = ?", (room_id,))  # FR-44
        db.run("INSERT INTO messages (room_id, sender_id, text, created_at) VALUES (?, NULL, ?, ?)",
               (room_id, f"{ctx.org_name} đã xác nhận hợp đồng v{c['version']}. Phòng chuyển sang Đã chốt.", iso()))
        audit.notify(room["seller_org_id"], "contract_confirmed", f"Hợp đồng v{c['version']} đã được xác nhận.", room_id)
    audit.log(ctx, "contract.confirm", f"{contract_id}@v{c['version']}")
    return _view(_contract(room_id, contract_id), db.one("SELECT * FROM rooms WHERE id = ?", (room_id,)), ctx)


@router.post("/{contract_id}/request-revision")
def request_revision(room_id: str, contract_id: str, body: RevisionIn, ctx: Ctx = Depends(current)):
    room, c = _pending_for_buyer(room_id, contract_id, ctx)
    notes = {k: v.strip() for k, v in body.term_notes.items() if v and v.strip()}
    if not notes and not (body.note or "").strip():
        raise ApiError("validation_failed", "Ghi rõ điều khoản cần sửa.")  # FR-42: note required
    db.run("UPDATE contracts SET status = 'revision_requested', term_notes = ?, note = ?, decided_by = ?, decided_at = ? WHERE id = ?",
           (db.dumps(notes), body.note, ctx.user_id, iso(), contract_id))
    audit.notify(room["seller_org_id"], "contract_revision", f"Buyer yêu cầu sửa hợp đồng v{c['version']}.", room_id)
    db.get_conn().commit()
    audit.log(ctx, "contract.request_revision", f"{contract_id}@v{c['version']}")
    return _view(_contract(room_id, contract_id), room, ctx)


@router.post("/{contract_id}/decline")
def decline(room_id: str, contract_id: str, body: DeclineIn, ctx: Ctx = Depends(current)):
    room, c = _pending_for_buyer(room_id, contract_id, ctx)
    db.run("UPDATE contracts SET status = 'declined', note = ?, decided_by = ?, decided_at = ? WHERE id = ?",
           (body.reason, ctx.user_id, iso(), contract_id))
    audit.notify(room["seller_org_id"], "contract_declined", f"Buyer đã từ chối hợp đồng v{c['version']}. Phòng vẫn mở.", room_id)
    db.get_conn().commit()
    audit.log(ctx, "contract.decline", f"{contract_id}@v{c['version']}")
    return _view(_contract(room_id, contract_id), room, ctx)
