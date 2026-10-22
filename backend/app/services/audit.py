"""Audit log (FR-47, FR-48). Never pass private field values, file content, full prompts or tokens."""
from .. import db
from ..util import iso


def log(ctx, action: str, resource_ref: str | None, outcome: str = "ok", detail: str | None = None) -> None:
    db.run(
        """INSERT INTO audit_events (actor, org_id, action, resource_ref, outcome, detail, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            getattr(ctx, "user_id", None),
            getattr(ctx, "org_id", None),
            action,
            resource_ref,
            outcome,
            detail,
            iso(),
        ),
    )
    db.get_conn().commit()


def notify(org_id: str, kind: str, text: str, ref: str | None = None) -> None:
    db.run(
        "INSERT INTO notifications (org_id, kind, text, ref, created_at) VALUES (?, ?, ?, ?, ?)",
        (org_id, kind, text, ref, iso()),
    )
