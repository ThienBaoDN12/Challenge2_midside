"""SQLite storage. Schema follows SRS v2 §9 (logical data model).

Versioned objects (listing, contract) are never overwritten: every change
inserts a new version row.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    identity_subject TEXT UNIQUE,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email_verified INTEGER DEFAULT 1,
    is_platform_admin INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active'            -- active | suspended
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    side TEXT NOT NULL,                     -- seller | buyer
    product_group TEXT,
    description TEXT,
    verification_status TEXT DEFAULT 'unverified'
);
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    role TEXT NOT NULL,                     -- manager | staff
    status TEXT DEFAULT 'active',
    invited_by TEXT,
    PRIMARY KEY (user_id, org_id)
);
CREATE TABLE IF NOT EXISTS invites (
    id TEXT PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    org_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT DEFAULT 'pending',          -- pending | accepted | expired | revoked
    invited_by TEXT,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    product_type TEXT NOT NULL,
    label TEXT NOT NULL,
    version INTEGER NOT NULL,
    fields TEXT NOT NULL                    -- json
);
CREATE TABLE IF NOT EXISTS confidential_files (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    template_id TEXT NOT NULL,
    filename TEXT,
    ciphertext BLOB NOT NULL,
    hash TEXT NOT NULL,
    size INTEGER NOT NULL,
    uploaded_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    template_id TEXT NOT NULL,
    fields TEXT NOT NULL,                   -- json [{key,value,unit}]
    dropped_columns TEXT NOT NULL,          -- json
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,                    -- LST-VN-xxxx
    org_id TEXT NOT NULL,
    template_id TEXT NOT NULL,
    product_type TEXT NOT NULL,
    status TEXT NOT NULL,                   -- draft | published | paused | expired
    current_version INTEGER NOT NULL,
    valid_until TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listing_versions (
    listing_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    snapshot_id TEXT NOT NULL,
    public_keys TEXT NOT NULL,              -- json
    public_projection TEXT NOT NULL,        -- json: the ONLY listing data AI/search may read
    created_at TEXT NOT NULL,
    PRIMARY KEY (listing_id, version)
);
CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    buyer_org_id TEXT NOT NULL,
    by_user TEXT NOT NULL,
    note TEXT,
    status TEXT DEFAULT 'pending',          -- pending | sent | dismissed
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS connection_requests (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    listing_version INTEGER NOT NULL,
    listing_snapshot TEXT NOT NULL,         -- json public projection at send time
    seller_org_id TEXT NOT NULL,
    buyer_org_id TEXT NOT NULL,
    by_user TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending',          -- pending | accepted | declined | withdrawn | expired
    reason TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    room_id TEXT
);
CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY,                    -- DR-xxxx
    request_id TEXT UNIQUE NOT NULL,
    listing_id TEXT NOT NULL,
    seller_org_id TEXT NOT NULL,
    buyer_org_id TEXT NOT NULL,
    status TEXT DEFAULT 'active',           -- active | finalized | closed
    listing_version_seen INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    sender_id TEXT,                         -- NULL for system notices
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shared_items (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    side TEXT NOT NULL,
    by_user TEXT NOT NULL,
    type_key TEXT NOT NULL,
    label TEXT NOT NULL,
    value TEXT NOT NULL,
    unit TEXT,
    from_field TEXT,
    created_at TEXT NOT NULL,
    revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS assistant_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    org_side TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT NOT NULL,                  -- json
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,                   -- draft | pending | confirmed | revision_requested | declined | cancelled
    terms TEXT NOT NULL,                    -- json [{key,label,value,unit}]
    total TEXT,
    currency TEXT,
    pdf_name TEXT,
    pdf_blob BLOB,
    sent_by TEXT,
    decided_by TEXT,
    note TEXT,
    term_notes TEXT,                        -- json {term_key: note} for revision requests
    created_at TEXT NOT NULL,
    decided_at TEXT,
    UNIQUE (room_id, version)
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    ref TEXT,
    created_at TEXT NOT NULL,
    read INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    org_id TEXT,
    action TEXT NOT NULL,
    resource_ref TEXT,
    outcome TEXT NOT NULL,
    detail TEXT,
    timestamp TEXT NOT NULL,
    correlation_id TEXT
);
"""

JSON_COLUMNS = {
    "fields", "dropped_columns", "public_keys", "public_projection",
    "listing_snapshot", "sources", "terms", "term_notes",
}

_local = threading.local()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_conn() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = connect()
        _local.conn = conn
    return conn


def reset_connection() -> None:
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None


def init_schema(conn: sqlite3.Connection | None = None) -> None:
    (conn or get_conn()).executescript(SCHEMA)


def _decode(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    out = dict(row)
    for k in JSON_COLUMNS & out.keys():
        if isinstance(out[k], str):
            out[k] = json.loads(out[k])
    return out


def one(sql: str, params: tuple = ()) -> dict | None:
    return _decode(get_conn().execute(sql, params).fetchone())


def all_(sql: str, params: tuple = ()) -> list[dict]:
    return [_decode(r) for r in get_conn().execute(sql, params).fetchall()]


def run(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    return get_conn().execute(sql, params)


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
