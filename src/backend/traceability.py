"""Hash-chain traceability endpoints."""

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel

from src.backend import database as db
from src.backend.auth import require_user
from src.hashchain.chain import HashChain, verify_block_dicts

router = APIRouter()


class TracePayload(BaseModel):
    """Payload for creating a trace block."""

    trace_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


def _load_blocks(trace_id: str) -> list:
    return db.get_blocks_by_trace_id(trace_id)


def _save_block(**kwargs) -> int:
    return db.insert_block(**kwargs)


def add_trace_block(trace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Add a block to the per-trace hash chain and return block metadata."""
    chain = HashChain(
        trace_id=trace_id,
        load_blocks_callback=_load_blocks,
        save_block_callback=_save_block,
    )
    block = chain.add_block(payload)
    return {
        "block_index": block.index,
        "hash": block.hash,
        "prev_hash": block.prev_hash,
        "timestamp": block.timestamp,
    }


def _resp(data: Any, message: str = "ok", code: int = 0) -> Dict[str, Any]:
    return {"code": code, "message": message, "data": data}


@router.post("/trace")
async def trace_endpoint(
    body: TracePayload,
    current_user: Dict[str, Any] = Depends(require_user),
):
    """
    Append a复核 payload to a per-trace hash chain.

    Only the owner of the detection or an admin may append blocks.
    Returns block metadata including index, hash, prev_hash and timestamp.
    """
    trace_id = body.trace_id
    if not trace_id:
        raise HTTPException(status_code=400, detail="trace_id is required")

    detection = db.get_detection(trace_id)
    if detection is None:
        raise HTTPException(status_code=404, detail=f"trace_id {trace_id} not found")

    if detection.get("user_id") != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner or an admin can append to this trace",
        )

    payload = body.payload or {}
    block_info = add_trace_block(trace_id, payload)
    block_info["trace_id"] = trace_id
    return _resp(block_info)


@router.get("/trace/{trace_id}")
async def get_trace(
    trace_id: str = Path(..., description="Trace id (detection id)"),
    current_user: Dict[str, Any] = Depends(require_user),
):
    """
    Get the hash chain for a trace_id and verify its integrity.

    Only the owner of the detection, an admin, or any authenticated user for
    anonymous (user_id is None) traces may read the chain.
    Returns chain blocks and a tamper flag.
    """
    detection = db.get_detection(trace_id)
    if detection is None:
        raise HTTPException(status_code=404, detail=f"trace_id {trace_id} not found")

    owner_id = detection.get("user_id")
    if owner_id is not None and owner_id != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner or an admin can view this trace",
        )

    blocks = db.get_blocks_by_trace_id(trace_id)
    if not blocks:
        raise HTTPException(status_code=404, detail=f"trace_id {trace_id} not found")

    chain_data = [
        {
            "index": b["index"],
            "timestamp": b["timestamp"],
            "prev_hash": b["prev_hash"],
            "data_hash": b["data_hash"],
            "hash": b["hash"],
            "payload": b["payload"],
        }
        for b in blocks
    ]

    is_valid = verify_block_dicts(chain_data)
    return _resp({"trace_id": trace_id, "valid": is_valid, "chain": chain_data})
