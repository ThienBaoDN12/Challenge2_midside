"""F0: sign-in, organizations, members and invitations (FR-01 – FR-06)."""
import secrets

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from .. import db
from ..auth import Ctx, current, load_ctx
from ..config import settings
from ..errors import ApiError, manager_only, not_found
from ..services import audit
from ..util import is_past, iso, iso_in, new_id

router = APIRouter(prefix="/api", tags=["accounts"])

COUNTRY = {"seller": "Việt Nam", "buyer": "Campuchia"}


class DemoLogin(BaseModel):
    email: EmailStr


class Signup(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)


class OrgIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    side: str = Field(pattern="^(seller|buyer)$")
    product_group: str | None = None
    description: str | None = Field(default=None, max_length=1000)


class InviteIn(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(manager|staff)$")


class RoleIn(BaseModel):
    role: str = Field(pattern="^(manager|staff)$")


def _session_for(user_id: str) -> dict:
    token = secrets.token_urlsafe(32)
    db.run("INSERT INTO sessions VALUES (?, ?, ?)", (token, user_id, iso()))
    db.get_conn().commit()
    return {"token": token, "me": me_payload(load_ctx(user_id))}


def me_payload(ctx: Ctx) -> dict:
    user = db.one("SELECT email_verified FROM users WHERE id = ?", (ctx.user_id,))
    org = db.one("SELECT * FROM organizations WHERE id = ?", (ctx.org_id,)) if ctx.org_id else None
    return {
        "user": {"id": ctx.user_id, "name": ctx.user_name, "email": ctx.email, "email_verified": bool(user["email_verified"])},
        "organization": None if not org else {
            "id": org["id"], "name": org["name"], "country": org["country"], "side": org["side"],
            "product_group": org["product_group"],
            # FR-05: email verification and business verification are separate labels
            "business_verified": org["verification_status"] == "verified",
        },
        "role": ctx.role,
        "role_label": ctx.role_label,  # e.g. "Seller Manager" — matches the frontend's UserRole
    }


# ---------- auth (TideCloak stand-in for local dev) ----------

@router.post("/auth/demo-login")
def demo_login(body: DemoLogin):
    user = db.one("SELECT id FROM users WHERE email = ?", (body.email.lower(),))
    if not user:
        raise ApiError("unauthenticated", "Không tìm thấy tài khoản với email này. Hãy tạo tài khoản mới.")
    return _session_for(user["id"])


@router.get("/auth/demo-accounts")
def demo_accounts():
    """Seeded accounts for the login screen's 4 role buttons."""
    rows = db.all_(
        """SELECT u.email, u.name, m.role, o.side, o.name AS org FROM users u
           JOIN memberships m ON m.user_id = u.id AND m.status = 'active'
           JOIN organizations o ON o.id = m.org_id
           WHERE o.id IN ('org_mekong', 'org_ppi') ORDER BY o.side DESC, m.role"""
    )
    return [{**r, "role_label": f"{r['side'].title()} {r['role'].title()}"} for r in rows]


@router.post("/auth/signup")
def signup(body: Signup):
    email = body.email.lower()
    if db.one("SELECT 1 FROM users WHERE email = ?", (email,)):
        raise ApiError("conflict", "Email này đã có tài khoản. Hãy đăng nhập.")
    uid = new_id("usr")
    db.run("INSERT INTO users (id, identity_subject, email, name) VALUES (?, ?, ?, ?)", (uid, f"tide|{uid}", email, body.name))
    return _session_for(uid)


@router.post("/auth/logout")
def logout(ctx: Ctx = Depends(current)):
    db.run("DELETE FROM sessions WHERE user_id = ?", (ctx.user_id,))
    db.get_conn().commit()
    return {"ok": True}


@router.get("/me")
def me(ctx: Ctx = Depends(current)):
    return me_payload(ctx)


# ---------- organizations ----------

@router.post("/orgs")
def create_org(body: OrgIn, ctx: Ctx = Depends(current)):
    if ctx.org_id:
        raise ApiError("conflict", f"Bạn đã thuộc tổ chức {ctx.org_name}. Mỗi tài khoản chỉ thuộc một tổ chức.")
    oid = new_id("org")
    with db.transaction():
        db.run(
            "INSERT INTO organizations (id, name, country, side, product_group, description) VALUES (?, ?, ?, ?, ?, ?)",
            (oid, body.name.strip(), COUNTRY[body.side], body.side, body.product_group, body.description),
        )
        # FR-03: the creator is automatically the manager
        db.run("INSERT INTO memberships (user_id, org_id, role) VALUES (?, ?, 'manager')", (ctx.user_id, oid))
    new_ctx = load_ctx(ctx.user_id)
    audit.log(new_ctx, "org.create", oid)
    return me_payload(new_ctx)


def _expire_invites(org_id: str) -> None:
    for inv in db.all_("SELECT id, expires_at FROM invites WHERE org_id = ? AND status = 'pending'", (org_id,)):
        if is_past(inv["expires_at"]):
            db.run("UPDATE invites SET status = 'expired' WHERE id = ?", (inv["id"],))
    db.get_conn().commit()


@router.get("/orgs/me/members")
def members(ctx: Ctx = Depends(current)):
    ctx.require_member()
    _expire_invites(ctx.org_id)
    people = db.all_(
        """SELECT u.id AS user_id, u.name, u.email, u.email_verified, m.role, m.status FROM memberships m
           JOIN users u ON u.id = m.user_id WHERE m.org_id = ? ORDER BY m.role, u.name""",
        (ctx.org_id,),
    )
    out = {"members": people}
    if ctx.is_manager:  # pending/expired invites are a manager concern (C3)
        out["invites"] = db.all_(
            "SELECT id, email, role, status, expires_at FROM invites WHERE org_id = ? AND status != 'accepted' ORDER BY expires_at DESC",
            (ctx.org_id,),
        )
    return out


@router.post("/orgs/me/invites")
def invite(body: InviteIn, ctx: Ctx = Depends(current)):
    ctx.require_manager()
    email = body.email.lower()
    if db.one(
        "SELECT 1 FROM memberships m JOIN users u ON u.id = m.user_id WHERE u.email = ? AND m.org_id = ?",
        (email, ctx.org_id),
    ):
        raise ApiError("conflict", "Người này đã là thành viên của tổ chức.")
    db.run("UPDATE invites SET status = 'revoked' WHERE org_id = ? AND email = ? AND status = 'pending'", (ctx.org_id, email))
    inv_id, token = new_id("inv"), secrets.token_urlsafe(24)
    db.run(
        "INSERT INTO invites (id, token, org_id, email, role, invited_by, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (inv_id, token, ctx.org_id, email, body.role, ctx.user_id, iso_in(settings.invite_ttl_days)),
    )
    db.get_conn().commit()
    audit.log(ctx, "invite.create", inv_id)
    # In production the link is emailed; returned here so the demo can open it.
    return {"id": inv_id, "email": email, "role": body.role, "status": "pending", "invite_link": f"/invite/{token}"}


@router.delete("/orgs/me/invites/{invite_id}")
def revoke_invite(invite_id: str, ctx: Ctx = Depends(current)):
    ctx.require_manager()
    if not db.one("SELECT 1 FROM invites WHERE id = ? AND org_id = ?", (invite_id, ctx.org_id)):
        raise not_found("Lời mời")
    db.run("UPDATE invites SET status = 'revoked' WHERE id = ?", (invite_id,))
    db.get_conn().commit()
    audit.log(ctx, "invite.revoke", invite_id)
    return {"ok": True}


@router.get("/invites/{token}")
def view_invite(token: str, ctx: Ctx = Depends(current)):
    inv = db.one(
        "SELECT i.*, o.name AS org_name, o.side FROM invites i JOIN organizations o ON o.id = i.org_id WHERE token = ?",
        (token,),
    )
    if not inv or inv["email"] != ctx.email:
        raise not_found("Lời mời")
    status = "expired" if inv["status"] == "pending" and is_past(inv["expires_at"]) else inv["status"]
    return {"org_name": inv["org_name"], "side": inv["side"], "role": inv["role"], "status": status, "expires_at": inv["expires_at"]}


@router.post("/invites/{token}/accept")
def accept_invite(token: str, ctx: Ctx = Depends(current)):
    inv = db.one("SELECT * FROM invites WHERE token = ?", (token,))
    # FR-04: only a valid invite addressed to this account joins an org — never by name or id
    if not inv or inv["email"] != ctx.email:
        raise not_found("Lời mời")
    if inv["status"] != "pending" or is_past(inv["expires_at"]):
        db.run("UPDATE invites SET status = 'expired' WHERE id = ? AND status = 'pending'", (inv["id"],))
        db.get_conn().commit()
        raise ApiError("expired", "Lời mời đã hết hạn. Hãy nhờ manager gửi lời mời mới.")
    if ctx.org_id:
        raise ApiError("conflict", f"Bạn đã thuộc tổ chức {ctx.org_name}.")
    with db.transaction():
        db.run(
            "INSERT INTO memberships (user_id, org_id, role, invited_by) VALUES (?, ?, ?, ?)",
            (ctx.user_id, inv["org_id"], inv["role"], inv["invited_by"]),
        )
        db.run("UPDATE invites SET status = 'accepted' WHERE id = ?", (inv["id"],))
    new_ctx = load_ctx(ctx.user_id)
    audit.log(new_ctx, "invite.accept", inv["id"])
    return me_payload(new_ctx)


def _managers(org_id: str) -> int:
    return db.one("SELECT COUNT(*) AS n FROM memberships WHERE org_id = ? AND role = 'manager' AND status = 'active'", (org_id,))["n"]


@router.patch("/orgs/me/members/{user_id}")
def change_role(user_id: str, body: RoleIn, ctx: Ctx = Depends(current)):
    ctx.require_manager()
    m = db.one("SELECT role FROM memberships WHERE user_id = ? AND org_id = ?", (user_id, ctx.org_id))
    if not m:
        raise not_found("Thành viên")
    if m["role"] == "manager" and body.role == "staff" and _managers(ctx.org_id) <= 1:
        raise ApiError("conflict", "Không thể hạ vai trò manager cuối cùng. Hãy chỉ định một manager khác trước.")
    db.run("UPDATE memberships SET role = ? WHERE user_id = ? AND org_id = ?", (body.role, user_id, ctx.org_id))
    db.get_conn().commit()
    audit.log(ctx, "member.role_change", user_id, detail=body.role)
    return {"ok": True}


@router.delete("/orgs/me/members/{user_id}")
def remove_member(user_id: str, ctx: Ctx = Depends(current)):
    ctx.require_manager()
    m = db.one("SELECT role FROM memberships WHERE user_id = ? AND org_id = ?", (user_id, ctx.org_id))
    if not m:
        raise not_found("Thành viên")
    if m["role"] == "manager" and _managers(ctx.org_id) <= 1:
        raise ApiError("conflict", "Không thể xóa manager cuối cùng của tổ chức.")  # FR-03
    db.run("DELETE FROM memberships WHERE user_id = ? AND org_id = ?", (user_id, ctx.org_id))
    db.get_conn().commit()
    audit.log(ctx, "member.remove", user_id)
    return {"ok": True}


# ---------- notifications & activity ----------

@router.get("/notifications")
def notifications(ctx: Ctx = Depends(current)):
    ctx.require_member()
    return db.all_("SELECT * FROM notifications WHERE org_id = ? ORDER BY id DESC LIMIT 50", (ctx.org_id,))


@router.get("/audit")
def activity(ctx: Ctx = Depends(current)):
    """FR-49: activity history for managers of this org (metadata only)."""
    ctx.require_manager()
    return db.all_(
        "SELECT actor, action, resource_ref, outcome, detail, timestamp FROM audit_events WHERE org_id = ? ORDER BY id DESC LIMIT 200",
        (ctx.org_id,),
    )


# ---------- platform admin: metadata only (§3.2, AT-28) ----------

def _require_admin(ctx: Ctx) -> None:
    if not db.one("SELECT is_platform_admin FROM users WHERE id = ?", (ctx.user_id,))["is_platform_admin"]:
        raise ApiError("forbidden", "Chỉ quản trị nền tảng mới làm được việc này.")


@router.get("/admin/files/{file_id}")
def admin_open_file(file_id: str, ctx: Ctx = Depends(current)):
    audit.log(ctx, "admin.open_confidential_file", file_id, outcome="denied")
    raise ApiError("forbidden", "Quản trị nền tảng không được mở file mật của doanh nghiệp.")


@router.post("/admin/memberships")
def admin_assign_role(ctx: Ctx = Depends(current)):
    audit.log(ctx, "admin.assign_manager", None, outcome="denied")
    raise ApiError("forbidden", "Quản trị nền tảng không được tự gán vai trò manager.")


@router.get("/admin/metrics")
def admin_metrics(ctx: Ctx = Depends(current)):
    _require_admin(ctx)
    count = lambda t: db.one(f"SELECT COUNT(*) AS n FROM {t}")["n"]  # noqa: E731
    return {t: count(t) for t in ("organizations", "users", "listings", "connection_requests", "rooms", "contracts")}
