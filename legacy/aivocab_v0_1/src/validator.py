from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from . import parser
from . import policy

VERSION = parser.VERSION


def _error(code: str, value: Any) -> Dict[str, Any]:
    return {"code": code, "value": str(value)}


def validate_canonical(
    canonical: Dict[str, Any],
    *,
    vocab_path: Optional[Path | str] = None,
    policy_path: Optional[Path | str] = None,
    policy_config: Optional[Dict[str, Any]] = None,
    require_end: bool = False,
    version: str = VERSION,
) -> Dict[str, Any]:
    by_name, _ = parser.load_vocab(vocab_path)
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    effective_policy = policy_config or policy.get_policy(policy_path)

    v = str(canonical.get("version", version))
    if v != version:
        errors.append(_error("VERSION_MISMATCH", v))

    actions = canonical.get("actions")
    if not isinstance(actions, list) or not actions:
        errors.append(_error("ACTION_MISSING", "actions"))
    else:
        norm_actions = []
        for action in actions:
            token = str(action).upper()
            if token not in by_name:
                errors.append(_error("UNKNOWN_OPCODE", token))
            elif by_name[token]["primary_class"] not in {"ACTION", "CONTROL"} and by_name[token].get("secondary_class") != "ACTION":
                errors.append(_error("NON_ACTION_IN_ACTIONS", token))
            elif not policy.is_action_allowed(token, effective_policy):
                errors.append(_error("ACTION_NOT_ALLOWED", token))
            elif policy.is_action_blocked(token, effective_policy):
                errors.append(_error("ACTION_FORBIDDEN", token))
            elif policy.is_confirmation_required(token, effective_policy):
                warnings.append(_error("CONFIRMATION_REQUIRED", token))
            norm_actions.append(token)

        max_actions = int(effective_policy.get("max_actions_per_instruction", 6))
        if len(norm_actions) > max_actions:
            errors.append(_error("TOO_MANY_ACTIONS", f"{len(norm_actions)}>{max_actions}"))

        # duplicate consecutive action opcodes usually indicate accidental repetition
        for idx in range(1, len(norm_actions)):
            if norm_actions[idx] == norm_actions[idx - 1] and norm_actions[idx] not in {"WAIT", "PAUSE", "RESUME"}:
                errors.append(_error("DUPLICATE_ACTION", norm_actions[idx]))

        if not actions:
            pass

    if canonical.get("object") is None:
        errors.append(_error("OBJECT_MISSING", "object"))
    elif str(canonical["object"]).upper() not in by_name:
        errors.append(_error("UNKNOWN_OPCODE", canonical["object"]))

    target = canonical.get("target")
    if target is not None and str(target).upper() not in by_name:
        errors.append(_error("UNKNOWN_OPCODE", target))

    state = canonical.get("state")
    if state is not None and str(state).upper() not in by_name:
        errors.append(_error("UNKNOWN_OPCODE", state))

    destination = canonical.get("destination")
    if destination is not None and str(destination).upper() not in by_name:
        errors.append(_error("UNKNOWN_OPCODE", destination))

    priority = canonical.get("priority")
    if priority is not None and str(priority).upper() not in {"HIGH", "MEDIUM", "LOW", "URGENT"}:
        errors.append(_error("INVALID_PRIORITY", priority))

    confidence = canonical.get("confidence")
    if confidence is not None:
        try:
            conf = float(confidence)
            if not (0.0 <= conf <= 1.0):
                errors.append(_error("INVALID_CONFIDENCE", confidence))
        except (TypeError, ValueError):
            errors.append(_error("INVALID_CONFIDENCE", confidence))

    if require_end and not canonical.get("end", False):
        errors.append(_error("END_MISSING", "END"))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_symbolic(
    symbolic: str,
    *,
    vocab_path: Optional[Path | str] = None,
    policy_path: Optional[Path | str] = None,
    policy_config: Optional[Dict[str, Any]] = None,
    require_end: bool = False,
    version: str = VERSION,
) -> Dict[str, Any]:
    parsed = parser.parse_symbolic(
        symbolic,
        vocab_path=vocab_path,
        require_end=require_end,
        version=version,
    )
    return validate_canonical(
        parsed,
        vocab_path=vocab_path,
        policy_path=policy_path,
        policy_config=policy_config,
        require_end=require_end,
        version=version,
    )


def validate_numeric(
    numeric: str,
    *,
    vocab_path: Optional[Path | str] = None,
    policy_path: Optional[Path | str] = None,
    policy_config: Optional[Dict[str, Any]] = None,
    require_end: bool = False,
    version: str = VERSION,
) -> Dict[str, Any]:
    parsed = parser.parse_numeric(
        numeric,
        vocab_path=vocab_path,
        require_end=require_end,
        version=version,
    )
    return validate_canonical(
        parsed,
        vocab_path=vocab_path,
        policy_path=policy_path,
        policy_config=policy_config,
        require_end=require_end,
        version=version,
    )
