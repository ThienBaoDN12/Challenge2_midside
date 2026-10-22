"""F2 + F3: discovery, staff proposals, connection requests and room creation (FR-16 – FR-27)."""
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from .. import db
from ..auth import Ctx, current
from ..config import settings
from ..errors import ApiError, not_found
from ..services import audit, discovery, ratelimit
from ..services import listings as lst
from ..util import is_past, iso, iso_in, new_id, today

router = APIRouter(prefix="/api", tags=["discovery & connections"])


class DiscoveryIn(BaseModel):
    query: str = Field(default="", max_length=500)
    criteria: dict | None = None  # answers from quick-reply buttons
    accept_relaxation: dict | None = None  # only set after the user clicked "agree"


class ProposalIn(BaseModel):
    listing_id: str
    note: str | None = Field(default=None, max_length=500)


class ConnectIn(BaseModel):
    listing_id: str
    message: str | None = Field(default=None, max_length=1000)
    acknowledge_not_contract: bool = False


class SendProposalIn(BaseModel):
    message: str | None = Field(default=None, max_length=1000)
    acknowledge_not_contract: bool = False


class AcceptIn(BaseModel):
    confirm_version: int | None = None  # seller saw the diff for this listing version


class DeclineIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


# ---------- discovery ----------

@router.post("/discovery/ai")
def ai_search(body: DiscoveryIn, ctx: Ctx = Depends(current)):
    ctx.require_side("buyer")
    return discovery.search(body.query, body.criteria, body.accept_relaxation)


@router.get("/discovery/search")
def standard_search(product_type: str | None = None, min_quantity: float | None = None, unit: str | None = None,
                    available_before: str | None = None, ctx: Ctx = Depends(current)):
    ctx.require_side("buyer")
    return {"results": discovery.standard(product_type, min_quantity, unit, available_before),
            "notice": "Gợi ý của AI chưa phải là kết nối."}


# ---------- proposals (Buyer Staff -> Buyer Manager) ----------

@router.post("/proposals")
def create_proposal(body: ProposalIn, ctx: Ctx = Depends(current)):
    ctx.require_side("buyer")
    if ctx.is_manager:
        raise ApiError("conflict", "Manager gửi yêu cầu kết nối trực tiếp, không cần đề xuất.")
    _published(body.listing_id)
    pid = new_id("prop")
    db.run("INSERT INTO proposals VALUES (?, ?, ?, ?, ?, 'pending', ?)", (pid, body.listing_id, ctx.org_id, ctx.user_id, body.note, iso()))
    db.get_conn().commit()
    audit.log(ctx, "proposal.create", pid)
    audit.notify(ctx.org_id, "proposal", f"{ctx.user_name} đề xuất listing {body.listing_id}.", pid)
    db.get_conn().commit()
    return {"id": pid, "status": "pending", "label": "Chờ manager xác nhận"}


@router.get("/proposals")
def list_proposals(ctx: Ctx = Depends(current)):
    ctx.require_side("buyer")
    sql = """SELECT p.*, u.name AS by_name FROM proposals p JOIN users u ON u.id = p.by_user WHERE p.buyer_org_id = ?"""
    params: tuple = (ctx.org_id,)
    if not ctx.is_manager:  # staff sees the status of their own proposals
        sql += " AND p.by_user = ?"
        params += (ctx.user_id,)
    rows = db.all_(sql + " ORDER BY p.created_at DESC", params)
    for r in rows:
        listing = db.one("SELECT * FROM listings WHERE id = ?", (r["listing_id"],))
        r["listing"] = lst.public_view(listing) if listing else None
    return rows


@router.post("/proposals/{proposal_id}/send")
def send_proposal(proposal_id: str, body: SendProposalIn, ctx: Ctx = Depends(current),
                  idempotency_key: str | None = Header(default=None)):
    ctx.require_manager("buyer")
    p = db.one("SELECT * FROM proposals WHERE id = ? AND buyer_org_id = ?", (proposal_id, ctx.org_id))
    if not p:
        raise not_found("Đề xuất")
    if p["status"] != "pending":
        raise ApiError("conflict", "Đề xuất này đã được xử lý.")
    req = _create_request(ctx, ConnectIn(listing_id=p["listing_id"], message=body.message,
                                         acknowledge_not_contract=body.acknowledge_not_contract), idempotency_key)
    db.run("UPDATE proposals SET status = 'sent' WHERE id = ?", (proposal_id,))
    db.get_conn().commit()
    return req


@router.post("/proposals/{proposal_id}/dismiss")
def dismiss_proposal(proposal_id: str, ctx: Ctx = Depends(current)):
    ctx.require_manager("buyer")
    if not db.one("SELECT 1 FROM proposals WHERE id = ? AND buyer_org_id = ? AND status = 'pending'", (proposal_id, ctx.org_id)):
        raise not_found("Đề xuất")
    db.run("UPDATE proposals SET status = 'dismissed' WHERE id = ?", (proposal_id,))
    db.get_conn().commit()
    audit.log(ctx, "proposal.dismiss", proposal_id)
    return {"ok": True}


# ---------- connection requests ----------

def _published(listing_id: str) -> dict:
    lst.refresh_expired()
    listing = db.one("SELECT * FROM listings WHERE id = ? AND status = 'published' AND valid_until >= ?", (listing_id, today()))
    if not listing:
        raise not_found("Listing")
    return listing


def _expire_requests() -> None:
    for r in db.all_("SELECT id, expires_at FROM connection_requests WHERE status = 'pending'"):
        if is_past(r["expires_at"]):
            db.run("UPDATE connection_requests SET status = 'expired' WHERE id = ?", (r["id"],))
    db.get_conn().commit()


def _next_seq(table: str, prefix: str, start: int) -> str:
    n = db.one(f"SELECT COUNT(*) AS n FROM {table}")["n"]
    return f"{prefix}-{start + n:04d}"


def _create_request(ctx: Ctx, body: ConnectIn, idem: str | None) -> dict:
    if idem:  # FR-24: double clicks return the same request
        prior = db.one("SELECT * FROM connection_requests WHERE idempotency_key = ? AND buyer_org_id = ?", (idem, ctx.org_id))
        if prior:
            return _request_view(prior, ctx)
    if not body.acknowledge_not_contract:
        raise ApiError("validation_failed", "Hãy tick xác nhận \"Kết nối không phải hợp đồng\" trước khi gửi.")
    listing = _published(body.listing_id)
    _expire_requests()
    dup = db.one(
        "SELECT id, status FROM connection_requests WHERE listing_id = ? AND buyer_org_id = ? AND status IN ('pending', 'accepted')",
        (body.listing_id, ctx.org_id),
    )
    if dup:
        raise ApiError("conflict", f"Tổ chức của bạn đã có yêu cầu {dup['id']} ({dup['status']}) cho listing này.")
    ratelimit.check("connect", ctx.user_id, settings.rate_connections_per_hour)
    v = lst.current_version(listing["id"])
    rid = _next_seq("connection_requests", "REQ", 761)
    db.run(
        """INSERT INTO connection_requests (id, listing_id, listing_version, listing_snapshot, seller_org_id, buyer_org_id,
           by_user, message, idempotency_key, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (rid, listing["id"], v["version"], db.dumps(v["public_projection"]), listing["org_id"], ctx.org_id,
         ctx.user_id, body.message, idem, iso(), iso_in(settings.request_ttl_days)),
    )
    audit.notify(listing["org_id"], "connection_request", f"Yêu cầu kết nối mới {rid} cho {listing['id']}.", rid)
    db.get_conn().commit()
    audit.log(ctx, "connection.send", rid)
    return _request_view(db.one("SELECT * FROM connection_requests WHERE id = ?", (rid,)), ctx)


@router.post("/connections")
def send_request(body: ConnectIn, ctx: Ctx = Depends(current), idempotency_key: str | None = Header(default=None)):
    ctx.require_manager("buyer")  # FR-23: Buyer Staff gets forbidden (AT-10)
    return _create_request(ctx, body, idempotency_key)


def _request_view(r: dict, ctx: Ctx) -> dict:
    buyer = db.one("SELECT name FROM organizations WHERE id = ?", (r["buyer_org_id"],))
    seller = db.one("SELECT name FROM organizations WHERE id = ?", (r["seller_org_id"],))
    listing = db.one("SELECT current_version FROM listings WHERE id = ?", (r["listing_id"],))
    out = {k: r[k] for k in ("id", "listing_id", "listing_version", "listing_snapshot", "message", "status", "reason", "created_at", "expires_at", "room_id")}
    out.update(buyer_org=buyer["name"], seller_org=seller["name"],
               listing_changed=listing["current_version"] != r["listing_version"],
               current_listing_version=listing["current_version"])
    # Actions are only offered to the role that may perform them (UI hides, server enforces)
    received = ctx.org_id == r["seller_org_id"]
    out["can_accept"] = received and ctx.is_manager and r["status"] == "pending"
    out["can_withdraw"] = not received and ctx.is_manager and r["status"] == "pending"
    return out


@router.get("/connections")
def list_requests(box: str = "received", status: str | None = None, ctx: Ctx = Depends(current)):
    ctx.require_member()
    _expire_requests()
    col = "seller_org_id" if box == "received" else "buyer_org_id"
    sql, params = f"SELECT * FROM connection_requests WHERE {col} = ?", (ctx.org_id,)
    if status:
        sql, params = sql + " AND status = ?", params + (status,)
    return [_request_view(r, ctx) for r in db.all_(sql + " ORDER BY created_at DESC", params)]


def _request_for(request_id: str, ctx: Ctx, side_col: str) -> dict:
    _expire_requests()
    r = db.one(f"SELECT * FROM connection_requests WHERE id = ? AND {side_col} = ?", (request_id, ctx.org_id))
    if not r:
        raise not_found("Yêu cầu kết nối")
    if r["status"] != "pending":
        code = "expired" if r["status"] == "expired" else "conflict"
        raise ApiError(code, f"Yêu cầu đang ở trạng thái {r['status']}, không thể xử lý tiếp.")
    return r


@router.get("/connections/{request_id}")
def get_request(request_id: str, ctx: Ctx = Depends(current)):
    r = db.one("SELECT * FROM connection_requests WHERE id = ? AND (seller_org_id = ? OR buyer_org_id = ?)", (request_id, ctx.org_id, ctx.org_id))
    if not r:
        raise not_found("Yêu cầu kết nối")
    view = _request_view(r, ctx)
    if view["listing_changed"]:
        view["changes"] = lst.diff(r["listing_snapshot"], lst.current_version(r["listing_id"])["public_projection"])
    return view


@router.post("/connections/{request_id}/withdraw")
def withdraw(request_id: str, ctx: Ctx = Depends(current)):
    ctx.require_manager("buyer")
    _request_for(request_id, ctx, "buyer_org_id")
    db.run("UPDATE connection_requests SET status = 'withdrawn' WHERE id = ?", (request_id,))
    db.get_conn().commit()
    audit.log(ctx, "connection.withdraw", request_id)
    return {"ok": True, "status": "withdrawn"}


@router.post("/connections/{request_id}/decline")
def decline(request_id: str, body: DeclineIn, ctx: Ctx = Depends(current)):
    ctx.require_manager("seller")
    r = _request_for(request_id, ctx, "seller_org_id")
    db.run("UPDATE connection_requests SET status = 'declined', reason = ? WHERE id = ?", (body.reason, request_id))
    audit.notify(r["buyer_org_id"], "connection_declined", f"Yêu cầu {request_id} đã bị từ chối.", request_id)
    db.get_conn().commit()
    audit.log(ctx, "connection.decline", request_id)
    return {"ok": True, "status": "declined"}


@router.post("/connections/{request_id}/accept")
def accept(request_id: str, body: AcceptIn, ctx: Ctx = Depends(current)):
    ctx.require_manager("seller")  # AT-12
    r = _request_for(request_id, ctx, "seller_org_id")
    # FR-26: re-check the listing at accept time
    lst.refresh_expired()
    listing = db.one("SELECT * FROM listings WHERE id = ?", (r["listing_id"],))
    if listing["status"] != "published" or listing["valid_until"] < today():
        audit.log(ctx, "connection.accept", request_id, outcome="blocked", detail=listing["status"])
        raise ApiError("conflict", f"Listing {listing['id']} đang {listing['status']}. Kích hoạt lại listing trước khi chấp nhận.")
    if listing["current_version"] != r["listing_version"] and body.confirm_version != listing["current_version"]:
        changes = lst.diff(r["listing_snapshot"], lst.current_version(listing["id"])["public_projection"])
        raise ApiError("conflict", f"Listing đã đổi từ v{r['listing_version']} sang v{listing['current_version']} kể từ lúc buyer gửi. Xem khác biệt rồi xác nhận lại.",
                       {"changes": changes, "confirm_version": listing["current_version"]})
    room_id = _next_seq("rooms", "DR", 402)
    with db.transaction():
        # Conditional update = exactly one room per request even on double click (FR-27)
        cur = db.run("UPDATE connection_requests SET status = 'accepted', room_id = ? WHERE id = ? AND status = 'pending'", (room_id, request_id))
        if cur.rowcount != 1:
            raise ApiError("conflict", "Yêu cầu đã được xử lý.")
        db.run(
            "INSERT INTO rooms (id, request_id, listing_id, seller_org_id, buyer_org_id, listing_version_seen, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (room_id, request_id, listing["id"], r["seller_org_id"], r["buyer_org_id"], listing["current_version"], iso()),
        )
        db.run("INSERT INTO messages (room_id, sender_id, text, created_at) VALUES (?, NULL, ?, ?)",
               (room_id, f"Đã tạo phòng {room_id} cho listing {listing['id']} v{listing['current_version']}.", iso()))
        for org in (r["seller_org_id"], r["buyer_org_id"]):
            audit.notify(org, "room_created", f"Đã tạo phòng {room_id}.", room_id)
    audit.log(ctx, "connection.accept", request_id)
    return {"ok": True, "status": "accepted", "room_id": room_id}
