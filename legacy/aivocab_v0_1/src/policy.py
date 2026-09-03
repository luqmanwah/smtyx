from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_POLICY_PATH = ROOT_DIR / "bridge_config.json"


def _fallback_policy() -> Dict[str, Any]:
    return {
        "policy": {
            "policy_version": "0.1",
            "allowed_actions": [
                "READ",
                "WRITE",
                "SEARCH",
                "FIND",
                "OPEN",
                "CLOSE",
                "CREATE",
                "DELETE",
                "UPDATE",
                "EDIT",
                "FIX",
                "CHECK",
                "VERIFY",
                "VALIDATE",
                "CALCULATE",
                "COMPARE",
                "ANALYZE",
                "EXTRACT",
                "CONVERT",
                "MERGE",
                "SPLIT",
                "COPY",
                "MOVE",
                "SAVE",
                "LOAD",
                "RUN",
                "STOP",
                "PAUSE",
                "RESUME",
                "RETRY",
                "START",
                "FINISH",
                "WAIT",
                "SEND",
                "RECEIVE",
                "RETURN",
                "CALL",
                "ROUTE",
                "SELECT",
                "REJECT",
                "ACCEPT",
                "ENABLE",
                "DISABLE",
                "LOCK",
                "UNLOCK",
                "CONNECT",
                "DISCONNECT",
                "SYNC",
                "MONITOR",
                "REPORT",
            ],
            "blocked_actions": [],
            "confirm_required_actions": [
                "DELETE",
                "MOVE",
                "COPY",
                "SAVE",
                "WRITE",
                "UPDATE",
                "CREATE",
            ],
            "max_actions_per_instruction": 6,
            "allow_structural_input": True,
            "require_end_by_default": False,
        },
        "language_objects": [
            "PYTHON",
            "JAVASCRIPT",
            "TYPESCRIPT",
            "JAVA",
            "CSHARP",
            "CPP",
            "GO",
            "RUST",
            "PHP",
            "SQL",
            "R",
            "KOTLIN",
            "SWIFT",
            "RUBY",
        ],
        "tool_rules": [],
    }


def load_bridge_config(path: Optional[Path | str] = None) -> Dict[str, Any]:
    cfg_path = Path(path) if path else DEFAULT_POLICY_PATH
    if not cfg_path.exists():
        return _fallback_policy()

    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_policy(path: Optional[Path | str] = None) -> Dict[str, Any]:
    return load_bridge_config(path).get("policy", {})


def get_tool_rules(path: Optional[Path | str] = None) -> list[Dict[str, Any]]:
    return load_bridge_config(path).get("tool_rules", [])


def get_language_objects(path: Optional[Path | str] = None) -> set[str]:
    return set(load_bridge_config(path).get("language_objects", []))


def is_action_allowed(action: str, config: Dict[str, Any]) -> bool:
    allowed = set(config.get("allowed_actions", []))
    if not allowed:
        return True
    return action.upper() in allowed


def is_action_blocked(action: str, config: Dict[str, Any]) -> bool:
    return action.upper() in set(config.get("blocked_actions", []))


def is_confirmation_required(action: str, config: Dict[str, Any]) -> bool:
    return action.upper() in set(config.get("confirm_required_actions", []))

