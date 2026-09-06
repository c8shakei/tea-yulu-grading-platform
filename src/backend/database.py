"""SQLite single-file database module for W3 backend."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.config import DB_PATH


def get_conn() -> sqlite3.Connection:
    """Create a connection with row factory and foreign keys enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_INIT_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hashchain (
    trace_id TEXT NOT NULL,
    "index" INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    prev_hash TEXT NOT NULL,
    data_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (trace_id, "index")
);

CREATE TABLE IF NOT EXISTS detections (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    image_hash TEXT,
    class_id INTEGER,
    class_name TEXT,
    confidence REAL,
    bbox TEXT,
    trace_block_index INTEGER,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_hashchain_trace_id ON hashchain(trace_id);
CREATE INDEX IF NOT EXISTS idx_detections_user_id ON detections(user_id);
CREATE INDEX IF NOT EXISTS idx_detections_created_at ON detections(created_at);
"""


def init_db() -> None:
    """Initialize database schema."""
    with get_conn() as conn:
        conn.executescript(_INIT_SQL)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def create_user(username: str, password_hash: str, role: str = "user") -> int:
    """Insert a new user and return its id."""
    from datetime import datetime, timezone

    created_at = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, created_at),
        )
        conn.commit()
        return cur.lastrowid


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetch a user by username."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a user by id."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Detections
# ---------------------------------------------------------------------------


def insert_detection(
    detection_id: str,
    user_id: Optional[int],
    image_hash: Optional[str],
    class_id: int,
    class_name: str,
    confidence: float,
    bbox: List[float],
    trace_block_index: Optional[int] = None,
) -> None:
    """Insert a detection record."""
    from datetime import datetime, timezone

    created_at = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO detections (id, user_id, image_hash, class_id, class_name, confidence, bbox, trace_block_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                detection_id,
                user_id,
                image_hash,
                class_id,
                class_name,
                confidence,
                json.dumps(bbox),
                trace_block_index,
                created_at,
            ),
        )
        conn.commit()


def update_detection_trace_block_index(detection_id: str, trace_block_index: int) -> None:
    """Update the hashchain block index for a detection."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE detections SET trace_block_index = ? WHERE id = ?",
            (trace_block_index, detection_id),
        )
        conn.commit()


def get_detection(detection_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a detection by id."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM detections WHERE id = ?", (detection_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["bbox"] = json.loads(record["bbox"])
        return record


def list_detections(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch detections, optionally filtered by user_id."""
    sql = "SELECT * FROM detections"
    params: tuple = ()
    if user_id is not None:
        sql += " WHERE user_id = ?"
        params = (user_id,)
    sql += " ORDER BY created_at DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        result = []
        for row in rows:
            record = dict(row)
            record["bbox"] = json.loads(record["bbox"])
            result.append(record)
        return result


# ---------------------------------------------------------------------------
# Hashchain
# ---------------------------------------------------------------------------


def insert_block(
    trace_id: Optional[str],
    timestamp: float,
    prev_hash: str,
    data_hash: str,
    hash_value: str,
    payload: Dict[str, Any],
    index: int,
) -> int:
    """Insert a block into the per-trace hash chain and return its index."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO hashchain (trace_id, "index", timestamp, prev_hash, data_hash, hash, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                index,
                timestamp,
                prev_hash,
                data_hash,
                hash_value,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
            ),
        )
        conn.commit()
        return index


def get_latest_block() -> Optional[Dict[str, Any]]:
    """Fetch the latest block in the global chain."""
    with get_conn() as conn:
        row = conn.execute(
            'SELECT * FROM hashchain ORDER BY "index" DESC LIMIT 1'
        ).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["payload"] = json.loads(record["payload"])
        return record


def get_blocks_by_trace_id(trace_id: str) -> List[Dict[str, Any]]:
    """Fetch all blocks for a trace_id ordered by index."""
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT * FROM hashchain WHERE trace_id = ? ORDER BY "index" ASC',
            (trace_id,),
        ).fetchall()
        result = []
        for row in rows:
            record = dict(row)
            record["payload"] = json.loads(record["payload"])
            result.append(record)
        return result


def get_all_blocks() -> List[Dict[str, Any]]:
    """Fetch all blocks in the global chain ordered by index."""
    with get_conn() as conn:
        rows = conn.execute('SELECT * FROM hashchain ORDER BY "index" ASC').fetchall()
        result = []
        for row in rows:
            record = dict(row)
            record["payload"] = json.loads(record["payload"])
            result.append(record)
        return result


def get_block_by_index(index: int) -> Optional[Dict[str, Any]]:
    """Fetch a block by its index."""
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM hashchain WHERE "index" = ?', (index,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["payload"] = json.loads(record["payload"])
        return record
