"""Server-side identity and authorization (FR-01, FR-02, FR-06).

The browser only sends a bearer token. User, organization, side and role are
always resolved here from the database; any org_id/role in a request body is ignored.
In production the token comes from TideCloak (OIDC); in dev, /api/auth/demo-login
issues a local session token so the frontend demo works offline.
"""
from dataclasses import dataclass

from fastapi import Header

from . import db
from .errors import ApiError, manager_only


@dataclass
class Ctx:
    user_id: str
    user_name: str
    email: str
    org_id: str | None
    org_name: str | None
    side: str | None  # seller | buyer
    role: str | None  # manager | staff

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"

    @property
    def role_label(self) -> str | None:
        if not self.side:
            return None
        return f"{self.side.title()} {self.role.title()}"

    def require_member(self) -> "Ctx":
        if not self.org_id:
            raise ApiError("forbidden", "Bạn chưa thuộc tổ chức nào. Tạo tổ chức hoặc mở link lời mời.")
        return self

    def require_side(self, side: str) -> "Ctx":
        self.require_member()
        if self.side != side:
            who = "bên bán (Seller)" if side == "seller" else "bên mua (Buyer)"
            raise ApiError("forbidden", f"Chỉ tổ chức {who} mới làm được việc này.")
        return self

    def require_manager(self, side: str | None = None) -> "Ctx":
        if side:
            self.require_side(side)
        self.require_member()
        # Re-read the role at the moment of the action (FR-06, F5 rules).
        m = db.one(
            "SELECT role, status FROM memberships WHERE user_id = ? AND org_id = ?",
            (self.user_id, self.org_id),
        )
        if not m or m["status"] != "active" or m["role"] != "manager":
            raise manager_only(self.org_name)
        return self


def load_ctx(user_id: str) -> Ctx:
    user = db.one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        raise ApiError("unauthenticated", "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.")
    if user["status"] != "active":
        raise ApiError("forbidden", "Tài khoản đang bị đình chỉ. Liên hệ quản trị nền tảng.")
    m = db.one(
        """SELECT m.role, o.id AS org_id, o.name AS org_name, o.side
           FROM memberships m JOIN organizations o ON o.id = m.org_id
           WHERE m.user_id = ? AND m.status = 'active'""",
        (user_id,),
    )
    return Ctx(
        user_id=user["id"],
        user_name=user["name"],
        email=user["email"],
        org_id=m["org_id"] if m else None,
        org_name=m["org_name"] if m else None,
        side=m["side"] if m else None,
        role=m["role"] if m else None,
    )


def current(authorization: str | None = Header(default=None)) -> Ctx:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError("unauthenticated", "Bạn cần đăng nhập để tiếp tục.")
    token = authorization.split(" ", 1)[1].strip()
    session = db.one("SELECT user_id FROM sessions WHERE token = ?", (token,))
    if not session:
        raise ApiError("unauthenticated", "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.")
    return load_ctx(session["user_id"])
