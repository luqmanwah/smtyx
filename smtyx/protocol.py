from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple
from .models import SemanticState

PROTOCOL_NAME = "SMTYX"
PROTOCOL_VERSION = "0.2"

STATUSES = {
    "PROPOSED", "PARSED", "AMBIGUOUS", "VERIFIED", "FINAL",
    "CONFLICT", "DENIED", "FAILED", "STALE",
}
ACKS = {
    "ACK_RECEIVED", "ACK_PARSED", "ACK_SEMANTIC", "ACK_VERIFIED", "ACK_FINAL",
}

_TRANSITIONS = {
    "PROPOSED": {"PARSED", "AMBIGUOUS", "DENIED", "FAILED"},
    "PARSED": {"VERIFIED", "AMBIGUOUS", "CONFLICT", "DENIED", "FAILED", "STALE"},
    "AMBIGUOUS": {"PARSED", "VERIFIED", "DENIED", "FAILED", "STALE"},
    "VERIFIED": {"FINAL", "CONFLICT", "DENIED", "FAILED", "STALE"},
    "CONFLICT": {"VERIFIED", "DENIED", "FAILED", "STALE"},
    "STALE": {"PARSED", "VERIFIED", "DENIED", "FAILED"},
    "FINAL": set(),
    "DENIED": set(),
    "FAILED": set(),
}

_STATUS_ACK = {
    "PROPOSED": "ACK_RECEIVED",
    "PARSED": "ACK_PARSED",
    "AMBIGUOUS": "ACK_SEMANTIC",
    "VERIFIED": "ACK_VERIFIED",
    "FINAL": "ACK_FINAL",
    "CONFLICT": "ACK_SEMANTIC",
    "DENIED": "ACK_SEMANTIC",
    "FAILED": "ACK_SEMANTIC",
    "STALE": "ACK_SEMANTIC",
}


def validate_state(state: SemanticState | Dict[str, Any]) -> Dict[str, Any]:
    data = state.to_dict() if isinstance(state, SemanticState) else dict(state)
    errors = []
    required = [
        "protocol", "protocol_version", "state_id", "trace_id", "source",
        "intent", "object", "status", "confidence", "payload", "evidence",
        "permissions", "ack",
    ]
    for key in required:
        if key not in data:
            errors.append({"code": "MISSING_FIELD", "field": key})
    if data.get("protocol") != PROTOCOL_NAME:
        errors.append({"code": "PROTOCOL_MISMATCH", "value": data.get("protocol")})
    if str(data.get("protocol_version")) != PROTOCOL_VERSION:
        errors.append({"code": "VERSION_MISMATCH", "value": data.get("protocol_version")})
    if str(data.get("status", "")).upper() not in STATUSES:
        errors.append({"code": "INVALID_STATUS", "value": data.get("status")})
    try:
        confidence = float(data.get("confidence"))
        if not 0.0 <= confidence <= 1.0:
            errors.append({"code": "CONFIDENCE_RANGE", "value": confidence})
    except (TypeError, ValueError):
        errors.append({"code": "CONFIDENCE_TYPE", "value": data.get("confidence")})
    for ack in data.get("ack", []) if isinstance(data.get("ack", []), list) else []:
        if ack not in ACKS:
            errors.append({"code": "INVALID_ACK", "value": ack})
    if not isinstance(data.get("source"), dict):
        errors.append({"code": "SOURCE_TYPE", "value": type(data.get("source")).__name__})
    return {"valid": not errors, "errors": errors}


def can_transition(current: str, target: str) -> bool:
    return str(target).upper() in _TRANSITIONS.get(str(current).upper(), set())


def advance_state(state: SemanticState, target_status: str, **changes: Any) -> SemanticState:
    target = str(target_status).upper()
    if target not in STATUSES:
        raise ValueError(f"Unknown status: {target}")
    if not can_transition(state.status, target):
        raise ValueError(f"Illegal status transition: {state.status} -> {target}")
    ack = list(state.ack)
    milestone = _STATUS_ACK[target]
    if milestone not in ack:
        ack.append(milestone)
    changes.update({"status": target, "ack": ack})
    return state.child(**changes)


def legal_transitions() -> Dict[str, Tuple[str, ...]]:
    return {k: tuple(sorted(v)) for k, v in _TRANSITIONS.items()}
