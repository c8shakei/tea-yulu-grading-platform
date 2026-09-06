"""W3 backend self-test script covering all M3 API contracts.

This script uses a temporary database so it never touches production data.
Run with pytest or directly: python tests/test_backend.py
"""

import io
import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is on path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use a temporary database for tests to avoid wiping production data.
_temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_temp_db.close()
os.environ["TEA_DB_PATH"] = _temp_db.name

from fastapi.testclient import TestClient

from src.backend import database as db
from src.backend.config import DB_PATH
from src.backend.main import app


def cleanup_db():
    """Remove temporary SQLite file after tests."""
    try:
        if DB_PATH.exists():
            DB_PATH.unlink()
    except OSError:
        pass


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["code"] == 0
    print("[OK] /health")


def test_register_login(client):
    # Register
    r = client.post("/api/auth/register", json={"username": "tester", "password": "123456"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert "token" in body["data"]
    print("[OK] /api/auth/register")

    # Login (OAuth2 form)
    r = client.post("/api/auth/login", data={"username": "tester", "password": "123456"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    token = body["data"]["token"]
    print("[OK] /api/auth/login")

    # Me
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["username"] == "tester"
    print("[OK] /api/auth/me")

    # Logout
    r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    print("[OK] /api/auth/logout")

    return token


def test_detect_anonymous(client):
    img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    img.name = "tea.png"
    r = client.post("/api/detect", files={"image": ("tea.png", img, "image/png")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert "class_name" in body["data"]
    assert "trace_id" in body["data"]
    print("[OK] /api/detect anonymous")
    return body["data"]["trace_id"]


def test_detect_authenticated(client, token: str):
    img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    r = client.post(
        "/api/detect",
        files={"image": ("tea2.png", img, "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["user_id"] is not None
    print("[OK] /api/detect authenticated")
    return body["data"]["trace_id"]


def test_trace_and_verify(client, trace_id: str, token: str):
    # Add another block to the same trace (must be authenticated and owner).
    r = client.post(
        "/api/trace",
        json={"trace_id": trace_id, "payload": {"note": "人工复核通过"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    print("[OK] /api/trace")

    # Verify chain.
    r = client.get(f"/api/trace/{trace_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["valid"] is True
    assert len(body["data"]["chain"]) >= 1
    print("[OK] /api/trace/{id} verify")

    # Tamper simulation: mutate a payload in memory and verify local helper fails.
    chain = body["data"]["chain"].copy()
    chain[0]["payload"]["tampered"] = True
    from src.hashchain.chain import verify_block_dicts

    assert verify_block_dicts(chain) is False
    print("[OK] hashchain tamper detection")


def test_detections(client, token: str):
    r = client.get("/api/detections", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    print(f"[OK] /api/detections ({len(body['data'])} records)")


def test_ui_schema(client):
    r = client.get("/api/ui/schema")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert "appName" in body["data"]
    assert "nav" in body["data"]
    assert "pages" in body["data"]
    print("[OK] /api/ui/schema")


def test_stats(client, token: str):
    r = client.get("/api/stats/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert "total_detections" in body["data"]
    assert "grade_distribution" in body["data"]
    assert "weekly_trend" in body["data"]
    print("[OK] /api/stats/overview")

    user = db.get_user_by_username("tester")
    r = client.get(f"/api/stats/user/{user['id']}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert "total_detections" in body["data"]
    print("[OK] /api/stats/user/{user_id}")


def main():
    print("=== W3 Backend Self Test ===")
    print(f"Using temp DB: {DB_PATH}")
    with TestClient(app) as client:
        test_health(client)
        token = test_register_login(client)
        anon_trace = test_detect_anonymous(client)
        auth_trace = test_detect_authenticated(client, token)
        test_trace_and_verify(client, auth_trace, token)
        test_detections(client, token)
        test_ui_schema(client)
        test_stats(client, token)
    print("=== All tests passed ===")
    cleanup_db()


if __name__ == "__main__":
    main()
