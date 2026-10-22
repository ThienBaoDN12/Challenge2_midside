import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("TRUSTGATE_DATA_DIR", BASE_DIR / ".data"))


@dataclass
class Settings:
    db_path: str = os.getenv("TRUSTGATE_DB", str(DATA_DIR / "trustgate.db"))
    # Fernet key for confidential files. Dev fallback is generated into .data/ (never commit it).
    file_key: str | None = os.getenv("TRUSTGATE_FILE_KEY")
    # Optional: only used to phrase answers from the already-filtered allowed sources.
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv(
            "TRUSTGATE_CORS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
    )
    max_upload_bytes: int = 1024 * 1024  # FR-08: 1 MB
    invite_ttl_days: int = 7  # FR-04
    request_ttl_days: int = 7  # FR-23
    rate_connections_per_hour: int = 10  # NFR-10
    rate_assistant_per_hour: int = 30  # NFR-10


settings = Settings()
