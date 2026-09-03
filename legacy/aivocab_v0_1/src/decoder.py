from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from . import parser

VERSION = parser.VERSION


def decode_to_canonical(
    payload: str,
    *,
    vocab_path: Optional[Path | str] = None,
    require_end: bool = False,
    version: str = VERSION,
) -> Dict[str, Any]:
    text = str(payload).strip()
    if not text:
        return {
            "version": version,
            "actions": [],
            "object": None,
            "target": None,
            "state": None,
            "priority": None,
            "confidence": None,
            "destination": None,
            "end": False,
            "errors": [{"code": "EMPTY_PAYLOAD", "value": ""}],
        }

    if re.search(r"\b\d{3}\b", text):
        return parser.parse_numeric(
            text,
            vocab_path=vocab_path,
            require_end=require_end,
            version=version,
        )

    return parser.parse_symbolic(
        text,
        vocab_path=vocab_path,
        require_end=require_end,
        version=version,
    )


def decode_to_symbolic(canonical: Dict[str, Any], *, include_end: bool = True) -> str:
    # Keep small utility for interoperability tests.
    from .encoder import encode_symbolic

    return encode_symbolic(canonical, include_end=include_end)
