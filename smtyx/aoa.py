from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .models import SemanticState
from .protocol import validate_state

AOA_PROFILE = "AOA/0.1"

AOA_INTENTS = frozenset({
    "READ", "WRITE", "ANALYZE", "VERIFY", "ROUTE", "EXECUTE", "REPORT",
    "SYNC", "OBSERVE", "CONTROL", "PROPOSE", "TUNE", "HYDRATE", "RESOLVE",
})

AOA_OBJECTS = frozenset({
    "STATE", "DELTA", "TASK", "SESSION", "PROJECTION", "TOOL", "DOCUMENT",
    "FILE", "PROJECT", "MEMORY", "CAPABILITY", "SOURCE", "REPORT", "TUNING",
    "RESULT", "CONTEXT", "POLICY", "CHECKPOINT",
})


def create_aoa_state(
    *,
    source: Dict[str, Any],
    intent: str,
    object_type: str,
    destination: Optional[Dict[str, Any]] = None,
    confidence: float = 1.0,
    payload: Optional[Dict[str, Any]] = None,
    permissions: Optional[Iterable[str]] = None,
    trace_id: Optional[str] = None,
    parent_state_id: Optional[str] = None,
    domain: Optional[str] = None,
    project: Optional[str] = None,
    persona: Optional[str] = None,
    projection_id: Optional[str] = None,
    authority: Optional[str] = None,
    memory_scopes: Optional[Iterable[str]] = None,
    source_priority: Optional[Iterable[str]] = None,
    client_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> SemanticState:
    """Create a SMTYX 0.2 state carrying the stable AOA/0.1 profile metadata."""

    state = SemanticState.create(
        source=source,
        intent=str(intent).upper(),
        object_type=str(object_type).upper(),
        destination=destination,
        confidence=confidence,
        payload=payload,
        permissions=list(permissions or ()),
        trace_id=trace_id,
        parent_state_id=parent_state_id,
    )

    aoa_metadata: Dict[str, Any] = dict(metadata or {})
    aoa_metadata["aoa_profile"] = AOA_PROFILE

    optional = {
        "domain": domain,
        "project": project,
        "persona": persona,
        "projection_id": projection_id,
        "authority": authority,
        "client_key": client_key,
    }
    for key, value in optional.items():
        if value is not None:
            aoa_metadata[key] = str(value)

    if memory_scopes is not None:
        aoa_metadata["memory_scopes"] = [str(v) for v in memory_scopes]
    if source_priority is not None:
        aoa_metadata["source_priority"] = [str(v) for v in source_priority]

    state.metadata = aoa_metadata
    return state


def validate_aoa_state(state: SemanticState | Dict[str, Any]) -> Dict[str, Any]:
    """Validate the stable AOA/0.1 profile on top of SMTYX 0.2."""

    data = state.to_dict() if isinstance(state, SemanticState) else dict(state)
    result = validate_state(data)
    errors = list(result["errors"])

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        errors.append({"code": "AOA_METADATA_TYPE", "value": type(metadata).__name__})
        metadata = {}

    if metadata.get("aoa_profile") != AOA_PROFILE:
        errors.append({
            "code": "AOA_PROFILE_MISMATCH",
            "value": metadata.get("aoa_profile"),
            "expected": AOA_PROFILE,
        })

    intent = str(data.get("intent", "")).upper()
    if intent not in AOA_INTENTS:
        errors.append({"code": "AOA_INTENT", "value": data.get("intent")})

    object_type = str(data.get("object", "")).upper()
    if object_type not in AOA_OBJECTS:
        errors.append({"code": "AOA_OBJECT", "value": data.get("object")})

    for key in ("domain", "project", "persona", "projection_id", "authority", "client_key"):
        value = metadata.get(key)
        if value is not None and (not isinstance(value, str) or not value):
            errors.append({"code": "AOA_METADATA_FIELD", "field": key, "value": value})

    for key in ("memory_scopes", "source_priority"):
        value = metadata.get(key)
        if value is not None:
            if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
                errors.append({"code": "AOA_METADATA_LIST", "field": key, "value": value})

    return {"valid": not errors, "errors": errors}
