"""Detection, history and statistics endpoints."""

import hashlib
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.backend import database as db
from src.backend.auth import get_current_user, require_user
from src.backend.config import CLASS_MAP, MAX_UPLOAD_SIZE, UPLOAD_DIR
from src.backend.traceability import add_trace_block
from src.inference.detector import TeaGradeDetector

router = APIRouter()

# Lazy singleton detector instance (initialized by main.py lifespan).
_detector: Optional[TeaGradeDetector] = None


def set_detector(detector: TeaGradeDetector) -> None:
    """Set the global detector instance."""
    global _detector
    _detector = detector


def get_detector() -> TeaGradeDetector:
    """Return the detector instance or raise if not initialized."""
    if _detector is None:
        raise RuntimeError("Detector not initialized")
    return _detector


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class DetectResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]
    trace_id: str
    user_id: Optional[int] = None


class DetectionHistoryItem(BaseModel):
    id: str
    user_id: Optional[int]
    image_hash: Optional[str]
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]
    trace_block_index: Optional[int]
    created_at: Optional[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resp(data: Any, message: str = "ok", code: int = 0) -> Dict[str, Any]:
    return {"code": code, "message": message, "data": data}


def _compute_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def _save_upload(image: UploadFile) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(image.filename or "image.jpg").suffix
    if not ext or ext not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        ext = ".jpg"

    # Read bytes with size cap to prevent unbounded growth of uploads/.
    image_bytes = image.file.read()
    if len(image_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large: {len(image_bytes)} bytes exceeds limit {MAX_UPLOAD_SIZE} bytes",
        )

    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = UPLOAD_DIR / saved_name
    try:
        with saved_path.open("wb") as buf:
            buf.write(image_bytes)
    finally:
        image.file.close()
    return saved_path


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _seven_days_ago() -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=6)).isoformat()


# ---------------------------------------------------------------------------
# Detection endpoints
# ---------------------------------------------------------------------------


@router.post("/detect")
async def detect_endpoint(
    image: UploadFile = File(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Detect tea leaf quality from an uploaded image.

    Supports anonymous uploads; user_id is recorded when a valid token is provided.
    """
    # Save uploaded image to disk and compute its hash.
    saved_path = _save_upload(image)
    image_bytes = saved_path.read_bytes()
    image_hash = _compute_image_hash(image_bytes)

    # Run inference via W2 detector.
    detector = get_detector()
    result = detector.detect(str(saved_path))

    detection_id = uuid.uuid4().hex
    user_id = current_user["id"] if current_user else None

    # Insert detection record first (without trace_block_index).
    db.insert_detection(
        detection_id=detection_id,
        user_id=user_id,
        image_hash=image_hash,
        class_id=result["class_id"],
        class_name=result["class_name"],
        confidence=result["confidence"],
        bbox=result["bbox"],
    )

    # Append to hash chain with detection payload.
    trace_payload = {
        "detection_id": detection_id,
        "image_hash": image_hash,
        "class_id": result["class_id"],
        "class_name": result["class_name"],
        "confidence": result["confidence"],
        "bbox": result["bbox"],
        "user_id": user_id,
    }
    block_info = add_trace_block(detection_id, trace_payload)
    db.update_detection_trace_block_index(detection_id, block_info["block_index"])

    data = DetectResult(
        class_id=result["class_id"],
        class_name=result["class_name"],
        confidence=result["confidence"],
        bbox=result["bbox"],
        trace_id=detection_id,
        user_id=user_id,
    )
    return _resp(data.model_dump())


@router.get("/detections")
async def list_detections_endpoint(current_user: Dict[str, Any] = Depends(require_user)):
    """Return detection history for the currently logged-in user."""
    rows = db.list_detections(user_id=current_user["id"])
    return _resp([DetectionHistoryItem(**row).model_dump() for row in rows])


# ---------------------------------------------------------------------------
# Statistics endpoints
# ---------------------------------------------------------------------------


@router.get("/stats/overview")
async def stats_overview():
    """Return global statistics for the dashboard."""
    all_rows = db.list_detections()
    total = len(all_rows)

    today = _today_iso()
    today_count = sum(1 for r in all_rows if r["created_at"] and r["created_at"].startswith(today))

    # Grade distribution for pie chart.
    grade_distribution = []
    for name in ["特级", "一级", "二级", "等外"]:
        value = sum(1 for r in all_rows if r["class_name"] == name)
        grade_distribution.append({"name": name, "value": value})

    # Weekly trend: last 7 days including today.
    start_date = datetime.now(timezone.utc).date() - timedelta(days=6)
    weekly_trend = []
    for i in range(7):
        d = (start_date + timedelta(days=i)).isoformat()
        count = sum(1 for r in all_rows if r["created_at"] and r["created_at"].startswith(d))
        weekly_trend.append({"date": d, "count": count})

    return _resp(
        {
            "total_detections": total,
            "today_detections": today_count,
            "grade_distribution": grade_distribution,
            "weekly_trend": weekly_trend,
        }
    )


@router.get("/stats/user/{user_id}")
async def stats_user(user_id: int, current_user: Dict[str, Any] = Depends(require_user)):
    """Return user-level statistics."""
    # Users can only view their own stats unless admin (simplified for project).
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    rows = db.list_detections(user_id=user_id)
    total = len(rows)

    grade_distribution = []
    for name in ["特级", "一级", "二级", "等外"]:
        value = sum(1 for r in rows if r["class_name"] == name)
        grade_distribution.append({"name": name, "value": value})

    # Confidence trend grouped by date.
    by_date: Dict[str, List[float]] = {}
    for r in rows:
        if not r["created_at"]:
            continue
        d = r["created_at"][:10]
        by_date.setdefault(d, []).append(r["confidence"])

    confidence_trend = [
        {"date": d, "avg_confidence": round(sum(v) / len(v), 4)}
        for d, v in sorted(by_date.items())
    ]

    return _resp(
        {
            "total_detections": total,
            "grade_distribution": grade_distribution,
            "confidence_trend": confidence_trend,
        }
    )
