"""Encryption for confidential files (FR-09).

Fernet (AES-128-CBC + HMAC). Only the listing owner's Seller Manager endpoints
call decrypt(); admins have no endpoint that reads ciphertext.
NOTE: SRS §15.2 leaves the TideCloak key-management mechanism open. Replace the
local key with TideCloak-held keys before claiming real data protection.
"""
import hashlib

from cryptography.fernet import Fernet

from ..config import DATA_DIR, settings

_fernet: Fernet | None = None


def _key() -> bytes:
    if settings.file_key:
        return settings.file_key.encode()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "dev_file.key"
    if not path.exists():
        path.write_bytes(Fernet.generate_key())
    return path.read_bytes()


def _f() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_key())
    return _fernet


def encrypt(raw: bytes) -> tuple[bytes, str]:
    return _f().encrypt(raw), hashlib.sha256(raw).hexdigest()


def decrypt(blob: bytes) -> bytes:
    return _f().decrypt(blob)
