from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import parser

VERSION = parser.VERSION
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VOCAB_PATH = ROOT_DIR / "vocab" / "core_vocab.json"


def _load_maps(vocab_path: Optional[Path | str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    by_name, by_id = parser.load_vocab(vocab_path)
    by_name_l = {key.upper(): value for key, value in by_name.items()}
    return by_name_l, by_id


def _as_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        raise TypeError("actions must be a list")
    return [str(item).upper() for item in value]


def encode_symbolic(
    canonical: Dict[str, Any],
    *,
    vocab_path: Optional[Path | str] = None,
    include_end: bool = True,
) -> str:
    by_name, _ = _load_maps(vocab_path)
    actions = _as_list(canonical.get("actions", []))
    if not actions:
        raise ValueError("actions is required")

    object_name = canonical.get("object")
    target = canonical.get("target")
    state = canonical.get("state")
    priority = canonical.get("priority")
    destination = canonical.get("destination")
    confidence = canonical.get("confidence")

    tokens: List[str] = []

    for action in actions:
        if action not in by_name:
            raise ValueError(f"UNKNOWN_ACTION:{action}")
        tokens.append(action)

    if object_name:
        if str(object_name).upper() not in by_name:
            raise ValueError(f"UNKNOWN_OBJECT:{object_name}")
        tokens.append(str(object_name).upper())

    if target and str(target).upper() in by_name:
        tokens.append(str(target).upper())

    if state and str(state).upper() in by_name:
        tokens.append(str(state).upper())

    if priority and str(priority).upper() in by_name:
        tokens.append(str(priority).upper())

    if destination and str(destination).upper() in by_name:
        tokens.append(str(destination).upper())

    if confidence is not None:
        tokens.append("CONFIDENCE")
        tokens.append(str(confidence))

    if include_end:
        tokens.append("END")

    return " ".join(tokens)


def encode_numeric(
    canonical: Dict[str, Any],
    *,
    vocab_path: Optional[Path | str] = None,
    include_end: bool = True,
) -> str:
    by_name, by_id = _load_maps(vocab_path)
    symbolic = encode_symbolic(canonical, vocab_path=vocab_path, include_end=include_end)
    symbolic_tokens = [token for token in symbolic.split(" ") if token]

    numeric_tokens: List[str] = []
    for token in symbolic_tokens:
        if token == "CONFIDENCE":
            numeric_tokens.append("095")
            continue
        if token.replace(".", "").replace("-", "").isdigit():
            continue
        by_name_token = parser._resolve_token(token, by_name, by_id)[1]
        if by_name_token is None:
            raise ValueError(f"UNKNOWN_TOKEN:{token}")
        numeric_tokens.append(by_name_token["id"])

    return " ".join(numeric_tokens)

