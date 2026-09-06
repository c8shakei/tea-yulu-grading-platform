"""M3 milestone integration tests."""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from src.backend.db import get_conn, init_db
from src.backend.main import app
from src.hashchain.chain import verify_block_dicts


def setup():
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM blocks")
        conn.execute("DELETE FROM detections")
        conn.commit()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["code"] == 0
    print("health PASS")


def test_detect(client):
    img = io.BytesIO(b"fake-image-data")
    r = client.post("/api/detect", files={"image": ("test.jpg", img, "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert "trace_id" in data
    assert "class_id" in data
    assert "class_name" in data
    assert "confidence" in data
    assert "bbox" in data
    print("detect PASS trace_id:", data["trace_id"])
    return data["trace_id"]


def test_trace(client, trace_id: str):
    r = client.post(
        "/api/trace",
        json={
            "trace_id": trace_id,
            "details": {"operator": "W3-M3", "action": "graded", "grade": "特级"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["block_index"] >= 1
    assert len(data["hash"]) == 64
    assert len(data["prev_hash"]) == 64
    print("trace POST PASS block_index:", data["block_index"])


def test_get_trace(client, trace_id: str):
    r = client.get(f"/api/trace/{trace_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    chain = body["data"]["chain"]
    assert len(chain) >= 2
    assert chain[0]["index"] == 0
    assert chain[0]["prev_hash"] == "0" * 64
    assert verify_block_dicts(chain)
    print("trace GET PASS chain length:", len(chain))
    return chain


def test_tamper(chain):
    tampered = [dict(b) for b in chain]
    tampered[1]["data_hash"] = "x" * 64
    assert not verify_block_dicts(tampered)
    print("tamper detection PASS")


def test_openapi(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "/api/detect" in spec["paths"]
    assert "/api/trace" in spec["paths"]
    assert "/api/trace/{trace_id}" in spec["paths"]
    print("openapi PASS")


if __name__ == "__main__":
    setup()
    with TestClient(app) as client:
        test_health(client)
        test_openapi(client)
        tid = test_detect(client)
        test_trace(client, tid)
        chain = test_get_trace(client, tid)
        test_tamper(chain)
    print("\nALL M3 TESTS PASSED")
