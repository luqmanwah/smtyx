from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List
import uuid


class MemoryKind(str, Enum):
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"


@dataclass
class MemoryRecord:
    kind: MemoryKind
    content: Dict[str, Any]
    source_state_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    verified: bool = False
    memory_id: str = field(default_factory=lambda: "mem_" + uuid.uuid4().hex[:20])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


class InMemoryStore:
    def __init__(self) -> None:
        self._records: Dict[str, MemoryRecord] = {}

    def add(self, record: MemoryRecord) -> str:
        if not 0.0 <= float(record.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self._records[record.memory_id] = record
        return record.memory_id

    def get(self, memory_id: str) -> MemoryRecord | None:
        return self._records.get(memory_id)

    def query(self, *, kind: MemoryKind | None = None, keyword: str | None = None, verified_only: bool = False) -> List[MemoryRecord]:
        out = []
        needle = (keyword or "").lower()
        for record in self._records.values():
            if kind and record.kind != kind:
                continue
            if verified_only and not record.verified:
                continue
            if needle and needle not in str(record.content).lower():
                continue
            out.append(record)
        return out
