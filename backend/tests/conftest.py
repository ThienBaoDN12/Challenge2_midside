import pytest
from fastapi.testclient import TestClient

from app import db
from app.config import settings
from app.main import app
from app.services import ratelimit


@pytest.fixture()
def client(tmp_path):
    settings.db_path = str(tmp_path / "test.db")
    db.reset_connection()
    ratelimit.reset()
    with TestClient(app) as c:
        yield c
    db.reset_connection()


EMAILS = {
    "SM": "lan@mekongagro.vn",
    "SS": "minh@mekongagro.vn",
    "BM": "dara@ppimports.com.kh",
    "BS": "sokha@ppimports.com.kh",
}


@pytest.fixture()
def as_(client):
    """as_("BM") -> headers for that seeded role."""
    cache = {}

    def headers(role: str) -> dict:
        if role not in cache:
            r = client.post("/api/auth/demo-login", json={"email": EMAILS.get(role, role)})
            assert r.status_code == 200, r.text
            cache[role] = {"Authorization": f"Bearer {r.json()['token']}"}
        return cache[role]

    return headers
