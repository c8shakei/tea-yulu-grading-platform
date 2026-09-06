"""Hash chain module for traceability data integrity (contract④)."""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Block:
    """Block structure for a trace-specific hash chain."""

    index: int
    timestamp: float
    prev_hash: str
    data_hash: str
    hash: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


GENESIS_PREV_HASH = "0" * 64


def compute_data_hash(payload: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of the payload with sorted keys (contract④)."""
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_block_hash(
    index: int, timestamp: float, prev_hash: str, data_hash: str
) -> str:
    """Compute block hash per contract④: sha256(index + timestamp + prev_hash + data_hash)."""
    raw = f"{index}{timestamp}{prev_hash}{data_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class HashChain:
    """Per-trace append-only hash chain backed by external storage callbacks."""

    def __init__(
        self,
        trace_id: str,
        load_blocks_callback: Callable[[str], List[Dict[str, Any]]],
        save_block_callback: Callable[..., int],
    ):
        self.trace_id = trace_id
        self._load = load_blocks_callback
        self._save = save_block_callback
        self._blocks: List[Block] = []
        self._reload()

    def _reload(self) -> None:
        rows = self._load(self.trace_id)
        self._blocks = [
            Block(
                index=row["index"],
                timestamp=row["timestamp"],
                prev_hash=row["prev_hash"],
                data_hash=row["data_hash"],
                hash=row["hash"],
                payload=row.get("payload", {}),
            )
            for row in rows
        ]

    @property
    def chain(self) -> List[Block]:
        return list(self._blocks)

    def last_block(self) -> Optional[Block]:
        return self._blocks[-1] if self._blocks else None

    def _create_genesis(self) -> Block:
        timestamp = time.time()
        payload = {"message": "genesis", "trace_id": self.trace_id}
        data_hash = compute_data_hash(payload)
        block_hash = compute_block_hash(0, timestamp, GENESIS_PREV_HASH, data_hash)
        return Block(
            index=0,
            timestamp=timestamp,
            prev_hash=GENESIS_PREV_HASH,
            data_hash=data_hash,
            hash=block_hash,
            payload=payload,
        )

    def add_block(self, payload: Dict[str, Any]) -> Block:
        """Append a new block with the given payload for this trace_id."""
        # Reload to pick up blocks written by other processes/requests.
        self._reload()

        if not self._blocks:
            # Per-trace genesis block at index 0.
            genesis = self._create_genesis()
            self._save(
                trace_id=self.trace_id,
                timestamp=genesis.timestamp,
                prev_hash=genesis.prev_hash,
                data_hash=genesis.data_hash,
                hash_value=genesis.hash,
                payload=genesis.payload,
                index=genesis.index,
            )
            self._blocks.append(genesis)

        last = self._blocks[-1]
        index = last.index + 1
        timestamp = time.time()
        # Attach trace_id inside payload for auditability.
        payload = dict(payload)
        payload.setdefault("trace_id", self.trace_id)
        data_hash = compute_data_hash(payload)
        block_hash = compute_block_hash(index, timestamp, last.hash, data_hash)
        block = Block(
            index=index,
            timestamp=timestamp,
            prev_hash=last.hash,
            data_hash=data_hash,
            hash=block_hash,
            payload=payload,
        )
        self._save(
            trace_id=self.trace_id,
            timestamp=block.timestamp,
            prev_hash=block.prev_hash,
            data_hash=block.data_hash,
            hash_value=block.hash,
            payload=block.payload,
            index=block.index,
        )
        self._blocks.append(block)
        return block

    def verify_chain(self) -> bool:
        """Verify the trace-specific chain integrity."""
        return verify_block_dicts([b.to_dict() for b in self._blocks])


def verify_block_dicts(blocks: List[Dict[str, Any]]) -> bool:
    """
    Verify integrity of a list of block dicts.

    Checks:
    - index continuity starting at 0
    - prev_hash link matches previous block hash (genesis uses "0" * 64)
    - data_hash matches recomputed payload hash
    - hash matches recomputed block hash
    """
    for i, block in enumerate(blocks):
        if i == 0:
            expected_prev_hash = GENESIS_PREV_HASH
        else:
            prev = blocks[i - 1]
            expected_prev_hash = prev["hash"]

        expected_data_hash = compute_data_hash(block.get("payload", {}))
        if block["prev_hash"] != expected_prev_hash:
            return False
        if block["data_hash"] != expected_data_hash:
            return False

        expected_hash = compute_block_hash(
            block["index"], block["timestamp"], block["prev_hash"], block["data_hash"]
        )
        if block["hash"] != expected_hash:
            return False
        if block["index"] != i:
            return False
    return True
