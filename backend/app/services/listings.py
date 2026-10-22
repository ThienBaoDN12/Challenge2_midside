"""Listing projection, visibility rules and versioning (FR-12 – FR-15)."""
from .. import db
from ..errors import ApiError
from ..util import iso, today
from . import audit
from . import templates as tpl


def check_public_keys(template: dict, public_keys: list[str], confirmed_sensitive: list[str]) -> list[str]:
    """Apply FR-13 to a requested set of public fields; returns the effective list."""
    fields = tpl.field_map(template)
    unknown = [k for k in public_keys if k not in fields]
    if unknown:
        raise ApiError("validation_failed", f"Trường không có trong mẫu: {', '.join(unknown)}.")
    blocked = [fields[k]["label"] for k in public_keys if fields[k]["blocked"]]
    if blocked:
        raise ApiError(
            "policy_denied",
            f"Trường {', '.join(blocked)} không được công khai theo chính sách của sàn.",
        )
    unconfirmed = [
        fields[k]["label"] for k in public_keys if fields[k]["sensitive"] and k not in confirmed_sensitive
    ]
    if unconfirmed:
        raise ApiError(
            "validation_failed",
            f"Trường nhạy cảm {', '.join(unconfirmed)} cần được xác nhận trước khi công khai.",
            {"needs_confirmation": [k for k in public_keys if fields[k]["sensitive"] and k not in confirmed_sensitive]},
        )
    locked = [k for k, fd in fields.items() if fd["locked_public"]]
    return list(dict.fromkeys(locked + public_keys))  # locked fields always public, keep order


def projection(template: dict, snapshot_fields: list[dict], public_keys: list[str]) -> dict:
    fields = tpl.field_map(template)
    out = {}
    for item in snapshot_fields:
        if item["key"] in public_keys:
            out[item["key"]] = {"label": fields[item["key"]]["label"], "value": item["value"], "unit": item["unit"]}
    return out


def next_listing_id() -> str:
    row = db.one("SELECT id FROM listings ORDER BY id DESC LIMIT 1")
    n = int(row["id"].rsplit("-", 1)[1]) + 1 if row else 161
    return f"LST-VN-{n:04d}"


def refresh_expired() -> None:
    """Published listings past valid_until become expired (lifecycle §6)."""
    db.run(
        "UPDATE listings SET status = 'expired' WHERE status = 'published' AND valid_until < ?",
        (today(),),
    )
    db.get_conn().commit()


def current_version(listing_id: str) -> dict:
    return db.one(
        """SELECT v.* FROM listing_versions v JOIN listings l
           ON l.id = v.listing_id AND l.current_version = v.version WHERE l.id = ?""",
        (listing_id,),
    )


def public_view(listing: dict) -> dict:
    """What any signed-in member (and the AI) may see. Never includes the snapshot."""
    v = current_version(listing["id"])
    org = db.one("SELECT id, name, country, verification_status FROM organizations WHERE id = ?", (listing["org_id"],))
    return {
        "id": listing["id"],
        "version": listing["current_version"],
        "version_label": f"v{listing['current_version']}",
        "status": listing["status"],
        "product_type": listing["product_type"],
        "valid_until": listing["valid_until"],
        "updated_at": listing["updated_at"],
        "seller": {
            "org_id": org["id"],
            "name": org["name"],
            "country": org["country"],
            "business_verified": org["verification_status"] == "verified",
        },
        "public_fields": v["public_projection"],
    }


def diff(old: dict, new: dict) -> list[dict]:
    changes = []
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        if a != b:
            changes.append({
                "key": key,
                "label": (b or a)["label"],
                "before": None if a is None else {"value": a["value"], "unit": a["unit"]},
                "after": None if b is None else {"value": b["value"], "unit": b["unit"]},
            })
    return changes


def add_version(ctx, listing: dict, snapshot_id: str, template: dict, snapshot_fields: list[dict], public_keys: list[str]) -> dict:
    """Never overwrite: insert version N+1 and notify open rooms (FR-15, AT-27)."""
    old = current_version(listing["id"])
    new_no = listing["current_version"] + 1
    proj = projection(template, snapshot_fields, public_keys)
    valid_until = next(i["value"] for i in snapshot_fields if i["key"] == "valid_until")
    db.run(
        "INSERT INTO listing_versions VALUES (?, ?, ?, ?, ?, ?)",
        (listing["id"], new_no, snapshot_id, db.dumps(public_keys), db.dumps(proj), iso()),
    )
    db.run(
        "UPDATE listings SET current_version = ?, valid_until = ?, updated_at = ? WHERE id = ?",
        (new_no, valid_until, iso(), listing["id"]),
    )
    changes = diff(old["public_projection"], proj)
    for room in db.all_("SELECT * FROM rooms WHERE listing_id = ? AND status = 'active'", (listing["id"],)):
        text = f"Listing {listing['id']} đã thay đổi: v{new_no - 1} → v{new_no}."
        db.run(
            "INSERT INTO messages (room_id, sender_id, text, created_at) VALUES (?, NULL, ?, ?)",
            (room["id"], text, iso()),
        )
        for org in (room["seller_org_id"], room["buyer_org_id"]):
            audit.notify(org, "listing_changed", text, room["id"])
    db.get_conn().commit()
    audit.log(ctx, "listing.new_version", f"{listing['id']}@v{new_no}")
    return {"version": new_no, "changes": changes}
