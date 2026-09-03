from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SEMANTIC_PROTOCOL_VERSION = "TS/0.1"
VOCAB_PROTOCOL_VERSION = "VA/0.1"

ACK_RECEIVED = "ACK_RECEIVED"
ACK_PARSED = "ACK_PARSED"
ACK_SEMANTIC = "ACK_SEMANTIC"
ACK_VERIFIED = "ACK_VERIFIED"
ACK_FINAL = "ACK_FINAL"

PROTOCOL_STATUSES = {
    "PROPOSED",
    "PARSED",
    "AMBIGUOUS",
    "VERIFIED",
    "FINAL",
    "CONFLICT",
    "DENIED",
    "FAILED",
    "STALE",
}

DEFAULT_CONFIRMATION_THRESHOLD = 0.35
DEFAULT_SEMANTIC_STATE_MAX_TOKENS = 4096


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stable_id(*parts: str) -> str:
    raw = "|".join(part for part in parts if part is not None).encode("utf-8")
    return "st_" + hashlib.sha1(raw).hexdigest()[:20]


def _normalize_status(status: str) -> str:
    value = str(status or "").upper()
    return value if value in PROTOCOL_STATUSES else "PROPOSED"


def compute_status(
    canonical: Dict[str, Any],
    validation: Dict[str, Any],
    *,
    needs_confirmation: bool = False,
    route_mode: str = "assistant",
    ambiguous_confidence_threshold: float = 0.55,
) -> str:
    if not validation.get("valid", True):
        return "DENIED"

    status_field = str(canonical.get("status") or "").upper()
    if status_field in {"CONFLICT", "DENIED", "FAILED", "AMBIGUOUS", "STALE"}:
        return _normalize_status(status_field)

    confidence = _coerce_float(canonical.get("confidence"))
    state = str(canonical.get("state", "")).upper()
    target = str(canonical.get("target", "")).upper()
    object_name = str(canonical.get("object", "")).upper()

    if confidence is not None and confidence < ambiguous_confidence_threshold:
        return "AMBIGUOUS"
    if state == "UNKNOWN" and not target:
        return "AMBIGUOUS"
    if state == "FALSE" and object_name and confidence is not None and confidence < 0.9:
        return "AMBIGUOUS"
    if route_mode == "assistant" and not needs_confirmation:
        return "FINAL"
    if needs_confirmation:
        return "PARSED"
    if route_mode == "tool":
        return "VERIFIED"
    return "PROPOSED"


def build_ack_chain(canonical: Dict[str, Any], validation: Dict[str, Any], status: str) -> List[str]:
    ack_chain: List[str] = [ACK_RECEIVED]

    if canonical.get("errors"):
        return ack_chain

    ack_chain.append(ACK_PARSED)
    if not validation.get("valid", True):
        return ack_chain

    ack_chain.append(ACK_SEMANTIC)
    status_upper = str(status).upper()
    if status_upper in {"FINAL", "VERIFIED"}:
        ack_chain.append(ACK_VERIFIED)
        ack_chain.append(ACK_FINAL)
    return ack_chain


def make_source_payload(
    *,
    kind: str = "human",
    id: str = "user",
    adapter: str = "ux",
) -> Dict[str, str]:
    return {"kind": kind, "id": id, "adapter": adapter}


def enrich_canonical_state(
    canonical: Dict[str, Any],
    *,
    source_kind: str,
    source_id: str = "user",
    source_adapter: str = "ux",
    identity_id: str = "default",
    protocol_version: str = SEMANTIC_PROTOCOL_VERSION,
    vocab_version: str = VOCAB_PROTOCOL_VERSION,
    parent_state_id: Optional[str] = None,
    route_mode: str = "assistant",
    needs_confirmation: bool = False,
    validation: Optional[Dict[str, Any]] = None,
    raw_input: str = "",
    max_tokens: int = DEFAULT_SEMANTIC_STATE_MAX_TOKENS,
) -> Dict[str, Any]:
    state_id = _stable_id(
        identity_id,
        source_id,
        str(canonical.get("version", "")),
        _now_utc(),
        raw_input[:64],
    )
    validation = validation or {"valid": True, "errors": [], "warnings": []}
    status = compute_status(
        canonical,
        validation,
        needs_confirmation=needs_confirmation,
        route_mode=route_mode,
    )

    confidence = _coerce_float(canonical.get("confidence"))
    provenance = [{
        "ts": _now_utc(),
        "source": make_source_payload(kind=source_kind, id=source_id, adapter=source_adapter),
        "canonical_version": str(canonical.get("version", "")),
        "input_digest": hashlib.sha1(raw_input[:max_tokens].encode("utf-8")).hexdigest(),
    }]

    evidence = list(canonical.get("evidence") or [])
    if validation.get("errors"):
        evidence.extend(validation["errors"])
    if validation.get("warnings"):
        evidence.extend(validation["warnings"])

    required_actions = list(canonical.get("actions") or [])

    risk = str(canonical.get("priority") or canonical.get("risk") or "LOW").upper()
    if risk not in {"LOW", "MEDIUM", "HIGH", "URGENT"}:
        risk = "LOW"

    permissions = ["workspace.read"]
    if route_mode == "tool":
        permissions.append("tool.execute")
    if risk in {"HIGH", "URGENT"}:
        permissions.append("review.required")

    output = dict(canonical)
    output.update({
        "protocol_version": protocol_version,
        "vocab_version": vocab_version,
        "state_id": state_id,
        "parent_state_id": parent_state_id,
        "timestamp": _now_utc(),
        "identity_id": identity_id,
        "source": make_source_payload(kind=source_kind, id=source_id, adapter=source_adapter),
        "status": status,
        "confidence": confidence if confidence is not None else canonical.get("confidence"),
        "evidence": evidence,
        "required_actions": required_actions,
        "risk": risk,
        "permissions": permissions,
        "provenance": provenance,
    })

    # keep compatibility if external callers pass their own policy/routing traces
    output["ack"] = build_ack_chain(output, validation, status)
    if "errors" not in output:
        output["errors"] = validation.get("errors", [])

    return output


def dump_state(state: Dict[str, Any], *, indent: Optional[int] = 2) -> str:
    return json.dumps(state, ensure_ascii=False, indent=indent)


def state_log_path(root: Optional[Path | str] = None, *, filename: str = "semantic_state.log") -> Path:
    if root is None:
        root = Path.cwd()
    return Path(root) / filename


__all__ = [
    "SEMANTIC_PROTOCOL_VERSION",
    "VOCAB_PROTOCOL_VERSION",
    "ACK_RECEIVED",
    "ACK_PARSED",
    "ACK_SEMANTIC",
    "ACK_VERIFIED",
    "ACK_FINAL",
    "PROTOCOL_STATUSES",
    "DEFAULT_CONFIRMATION_THRESHOLD",
    "compute_status",
    "build_ack_chain",
    "make_source_payload",
    "enrich_canonical_state",
    "dump_state",
    "state_log_path",
]
