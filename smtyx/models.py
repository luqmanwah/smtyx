from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Optional
import json
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


@dataclass(frozen=True)
class EvidenceRef:
    ref: str
    digest: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SemanticState:
    protocol: str = "SMTYX"
    protocol_version: str = "0.2"
    state_id: str = field(default_factory=lambda: _id("st"))
    parent_state_id: Optional[str] = None
    trace_id: str = field(default_factory=lambda: _id("tr"))
    timestamp: str = field(default_factory=_now)
    source: Dict[str, Any] = field(default_factory=lambda: {"kind": "unknown", "id": "unknown"})
    destination: Optional[Dict[str, Any]] = None
    intent: str = "UNKNOWN"
    object: str = "UNKNOWN"
    status: str = "PROPOSED"
    confidence: float = 1.0
    payload: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    ack: List[str] = field(default_factory=lambda: ["ACK_RECEIVED"])
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        source: Dict[str, Any],
        intent: str,
        object_type: str,
        destination: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        payload: Optional[Dict[str, Any]] = None,
        permissions: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
        parent_state_id: Optional[str] = None,
    ) -> "SemanticState":
        return cls(
            source=dict(source),
            destination=dict(destination) if destination else None,
            intent=str(intent).upper(),
            object=str(object_type).upper(),
            confidence=float(confidence),
            payload=dict(payload or {}),
            permissions=list(permissions or []),
            trace_id=trace_id or _id("tr"),
            parent_state_id=parent_state_id,
        )

    def child(self, **changes: Any) -> "SemanticState":
        data = self.to_dict()
        data.update(changes)
        data["state_id"] = _id("st")
        data["parent_state_id"] = self.state_id
        data["trace_id"] = self.trace_id
        data["timestamp"] = _now()
        return SemanticState(**data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def digest(self) -> str:
        return "sha256:" + sha256(self.canonical_json().encode("utf-8")).hexdigest()
