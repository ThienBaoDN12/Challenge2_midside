import secrets
from datetime import datetime, timedelta, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    # NFR-08: stored in UTC
    return (dt or now()).isoformat(timespec="seconds")


def iso_in(days: int) -> str:
    return iso(now() + timedelta(days=days))


def is_past(ts: str) -> bool:
    return datetime.fromisoformat(ts) <= now()


def today() -> str:
    return now().date().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(6)}"
