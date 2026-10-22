"""F1: templates, confidential file upload, private snapshot, listings (FR-07 – FR-15)."""
import io
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .. import db
from ..auth import Ctx, current
from ..config import settings
from ..errors import ApiError, not_found
from ..services import audit, extractor, vault
from ..services import listings as lst
from ..services import templates as tpl
from ..util import iso, new_id, today

router = APIRouter(prefix="/api", tags=["listings"])


class PublicFieldsIn(BaseModel):
    snapshot_id: str
    public_keys: list[str] = Field(default_factory=list)
    confirm_sensitive: list[str] = Field(default_factory=list)


class ListingIn(PublicFieldsIn):
    publish: bool = True


class ListingUpdateIn(BaseModel):
    snapshot_id: str | None = None  # new confidential upload; defaults to the current snapshot
    public_keys: list[str]
    confirm_sensitive: list[str] = Field(default_factory=list)


# ---------- templates ----------

@router.get("/templates")
def list_templates(ctx: Ctx = Depends(current)):
    return [{k: t[k] for k in ("id", "product_type", "label", "version", "fields")} for t in tpl.TEMPLATES]


@router.get("/templates/{template_id}/download")
def download_template(template_id: str, format: str = "json", ctx: Ctx = Depends(current)):
    t = tpl.by_id(template_id)
    if not t:
        raise not_found("Mẫu")
    if format == "xlsx":
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "fields"
        ws.append(["key", "value", "unit", "label", "required", "unit_options"])
        ws.append(["template", t["id"], None, "Không sửa dòng này", None, None])
        for fd in t["fields"]:
            ws.append([fd["key"], None, None, fd["label"], "yes" if fd["required"] else "", ", ".join(fd["unit_options"])])
        buf = io.BytesIO()
        wb.save(buf)
        return Response(
            buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{t["id"]}.xlsx"'},
        )
    return Response(
        json.dumps(tpl.sample_file(t), ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{t["id"]}.json"'},
    )


SAMPLE_PRODUCTS = {"coffee": "Robusta Coffee Grade 1", "pepper": "Black Pepper 500 g/l", "cashew": "Cashew Kernels W320", "rice": "Jasmine Rice 5% broken"}


@router.get("/templates/{template_id}/sample")
def sample_file(template_id: str, variant: str = "valid", ctx: Ctx = Depends(current)):
    """Demo helper: a filled-in confidential file (valid / missing_moq / extra_column)."""
    from ..seed import coffee

    t = tpl.by_id(template_id)
    if not t:
        raise not_found("Mẫu")
    payload = coffee(SAMPLE_PRODUCTS[t["product_type"]], 20, "2026-12-31")
    payload["template"] = t["id"]
    if variant == "missing_moq":
        payload["fields"].pop("moq")
    elif variant == "extra_column":
        payload["fields"]["internal_warehouse_note"] = {"value": "Bay 4, lot 17"}
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{t["product_type"]}_{variant}.json"'},
    )


# ---------- confidential file -> private snapshot ----------

@router.post("/files")
async def upload_file(template_id: str = Form(...), file: UploadFile = File(...), ctx: Ctx = Depends(current)):
    ctx.require_manager("seller")
    t = tpl.by_id(template_id)
    if not t:
        raise not_found("Mẫu")
    raw = await file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        audit.log(ctx, "file.upload", None, outcome="blocked", detail="too_large")
        raise ApiError("policy_denied", "File vượt quá 1 MB. Hãy dùng đúng file mẫu và bỏ dữ liệu thừa.")
    try:
        result = extractor.extract(file.filename or "", raw, t)
    except extractor.ExtractError as e:
        audit.log(ctx, "file.upload", None, outcome="blocked", detail=f"{len(e.errors)} errors")
        raise ApiError("validation_failed", e.errors[0]["message"], {"errors": e.errors})

    ciphertext, digest = vault.encrypt(raw)
    file_id, snap_id = new_id("file"), new_id("snap")
    with db.transaction():
        db.run(
            "INSERT INTO confidential_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, ctx.org_id, t["id"], file.filename, ciphertext, digest, len(raw), ctx.user_id, iso()),
        )
        db.run(
            "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
            (snap_id, file_id, ctx.org_id, t["id"], db.dumps(result["fields"]), db.dumps(result["dropped_columns"]), iso()),
        )
    audit.log(ctx, "file.upload", file_id)
    return snapshot_view(snap_id, ctx)


def _own_snapshot(snapshot_id: str, ctx: Ctx) -> dict:
    ctx.require_manager("seller")  # FR-12: only the Seller Manager sees the snapshot
    snap = db.one("SELECT * FROM snapshots WHERE id = ? AND org_id = ?", (snapshot_id, ctx.org_id))
    if not snap:
        raise not_found("Snapshot")
    return snap


@router.get("/snapshots/{snapshot_id}")
def snapshot_view(snapshot_id: str, ctx: Ctx = Depends(current)):
    snap = _own_snapshot(snapshot_id, ctx)
    t = tpl.by_id(snap["template_id"])
    fields = tpl.field_map(t)
    rows = []
    for item in snap["fields"]:
        fd = fields[item["key"]]
        tag = "blocked" if fd["blocked"] else "sensitive" if fd["sensitive"] else "required" if fd["required"] else "standard"
        rows.append({
            **item, "label": fd["label"], "tag": tag,
            "locked_public": fd["locked_public"], "sensitive": fd["sensitive"], "blocked": fd["blocked"],
            "default_public": fd["locked_public"] or not (fd["sensitive"] or fd["blocked"]),
        })
    return {"id": snap["id"], "template_id": t["id"], "template_label": f"{t['label']} v{t['version']}",
            "fields": rows, "dropped_columns": snap["dropped_columns"], "classification": "Riêng tư"}


@router.post("/listings/preview")
def preview(body: PublicFieldsIn, ctx: Ctx = Depends(current)):
    """FR-14: the two columns 'Người mua và AI sẽ thấy' / 'Giữ riêng'."""
    snap = _own_snapshot(body.snapshot_id, ctx)
    t = tpl.by_id(snap["template_id"])
    keys = lst.check_public_keys(t, body.public_keys, body.confirm_sensitive)
    labels = tpl.field_map(t)
    visible = [{**i, "label": labels[i["key"]]["label"]} for i in snap["fields"] if i["key"] in keys]
    private = [{"key": i["key"], "label": labels[i["key"]]["label"]} for i in snap["fields"] if i["key"] not in keys]
    return {"public": visible, "private": private}


@router.post("/listings")
def create_listing(body: ListingIn, ctx: Ctx = Depends(current)):
    snap = _own_snapshot(body.snapshot_id, ctx)
    t = tpl.by_id(snap["template_id"])
    keys = lst.check_public_keys(t, body.public_keys, body.confirm_sensitive)
    listing_id = lst.next_listing_id()
    valid_until = next(i["value"] for i in snap["fields"] if i["key"] == "valid_until")
    status = "published" if body.publish else "draft"
    if status == "published" and valid_until < today():
        raise ApiError("validation_failed", "Hạn hiệu lực đã qua. Cập nhật Validity Date trong file mật rồi upload lại.")
    with db.transaction():
        db.run(
            "INSERT INTO listings VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
            (listing_id, ctx.org_id, t["id"], t["product_type"], status, valid_until, iso()),
        )
        db.run(
            "INSERT INTO listing_versions VALUES (?, 1, ?, ?, ?, ?)",
            (listing_id, snap["id"], db.dumps(keys), db.dumps(lst.projection(t, snap["fields"], keys)), iso()),
        )
    audit.log(ctx, "listing.publish" if body.publish else "listing.draft", f"{listing_id}@v1")
    return get_listing(listing_id, ctx)


def _visible_listing(listing_id: str, ctx: Ctx) -> dict:
    ctx.require_member()
    lst.refresh_expired()
    listing = db.one("SELECT * FROM listings WHERE id = ?", (listing_id,))
    if not listing:
        raise not_found("Listing")
    own = listing["org_id"] == ctx.org_id
    if not own and listing["status"] != "published":
        raise not_found("Listing")  # drafts/paused/expired are invisible to other orgs (FR-15)
    return listing


@router.get("/listings/mine")
def my_listings(ctx: Ctx = Depends(current)):
    ctx.require_side("seller")
    lst.refresh_expired()
    rows = db.all_("SELECT * FROM listings WHERE org_id = ? ORDER BY updated_at DESC", (ctx.org_id,))
    out = []
    for r in rows:
        view = lst.public_view(r)
        view["open_rooms"] = db.one("SELECT COUNT(*) AS n FROM rooms WHERE listing_id = ? AND status = 'active'", (r["id"],))["n"]
        out.append(view)
    # Seller Staff gets the same public-only view and no action flags (S1 · SS)
    return {"listings": out, "can_manage": ctx.is_manager}


@router.get("/listings/{listing_id}")
def get_listing(listing_id: str, ctx: Ctx = Depends(current)):
    listing = _visible_listing(listing_id, ctx)
    view = lst.public_view(listing)
    if listing["org_id"] == ctx.org_id and ctx.is_manager:
        v = lst.current_version(listing_id)
        view["snapshot_id"] = v["snapshot_id"]  # owner manager only, to edit
        view["public_keys"] = v["public_keys"]
    return view


@router.get("/listings/{listing_id}/versions")
def listing_versions(listing_id: str, ctx: Ctx = Depends(current)):
    _visible_listing(listing_id, ctx)
    rows = db.all_("SELECT version, public_projection, created_at FROM listing_versions WHERE listing_id = ? ORDER BY version", (listing_id,))
    return rows


def _own_listing(listing_id: str, ctx: Ctx) -> dict:
    ctx.require_manager("seller")
    listing = db.one("SELECT * FROM listings WHERE id = ? AND org_id = ?", (listing_id, ctx.org_id))
    if not listing:
        raise not_found("Listing")
    return listing


@router.put("/listings/{listing_id}")
def update_listing(listing_id: str, body: ListingUpdateIn, ctx: Ctx = Depends(current)):
    """Change public fields or upload a new confidential file -> new version (FR-15)."""
    listing = _own_listing(listing_id, ctx)
    snap_id = body.snapshot_id or lst.current_version(listing_id)["snapshot_id"]
    snap = _own_snapshot(snap_id, ctx)
    t = tpl.by_id(snap["template_id"])
    if t["id"] != listing["template_id"]:
        raise ApiError("validation_failed", "File mới phải dùng cùng mẫu sản phẩm với listing.")
    keys = lst.check_public_keys(t, body.public_keys, body.confirm_sensitive)
    result = lst.add_version(ctx, listing, snap["id"], t, snap["fields"], keys)
    if listing["status"] == "expired":
        db.run("UPDATE listings SET status = 'published' WHERE id = ? AND valid_until >= ?", (listing_id, today()))
        db.get_conn().commit()
    return {**get_listing(listing_id, ctx), "changes": result["changes"]}


def _set_status(listing_id: str, ctx: Ctx, allowed_from: tuple, to: str, action: str) -> dict:
    listing = _own_listing(listing_id, ctx)
    lst.refresh_expired()
    listing = db.one("SELECT * FROM listings WHERE id = ?", (listing_id,))
    if listing["status"] not in allowed_from:
        raise ApiError("conflict", f"Không thể chuyển listing từ trạng thái {listing['status']} sang {to}.")
    if to == "published" and listing["valid_until"] < today():
        raise ApiError("validation_failed", "Listing đã quá hạn hiệu lực. Upload file mật mới để gia hạn.")
    db.run("UPDATE listings SET status = ?, updated_at = ? WHERE id = ?", (to, iso(), listing_id))
    db.get_conn().commit()
    audit.log(ctx, action, listing_id)
    return get_listing(listing_id, ctx)


@router.post("/listings/{listing_id}/publish")
def publish(listing_id: str, ctx: Ctx = Depends(current)):
    return _set_status(listing_id, ctx, ("draft",), "published", "listing.publish")


@router.post("/listings/{listing_id}/pause")
def pause(listing_id: str, ctx: Ctx = Depends(current)):
    return _set_status(listing_id, ctx, ("published",), "paused", "listing.pause")


@router.post("/listings/{listing_id}/resume")
def resume(listing_id: str, ctx: Ctx = Depends(current)):
    return _set_status(listing_id, ctx, ("paused",), "published", "listing.resume")
