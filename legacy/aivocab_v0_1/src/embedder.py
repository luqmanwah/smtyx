from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import parser


def canonical_to_vector(
    canonical: Dict[str, Any],
    *,
    vocab_path: Optional[str | None] = None,
    max_vector_size: int = 64,
) -> List[float]:
    if max_vector_size <= 0:
        return []

    vector = [0.0 for _ in range(max_vector_size)]
    tokens = []

    version = str(canonical.get("version", parser.VERSION))
    tokens.append(f"VERSION:{version}")

    for action in canonical.get("actions", []) or []:
        if action:
            tokens.append(f"ACTION:{str(action).upper()}")

    if canonical.get("object") is not None:
        tokens.append(f"OBJECT:{str(canonical['object']).upper()}")
    if canonical.get("target") is not None:
        tokens.append(f"TARGET:{str(canonical['target']).upper()}")
    if canonical.get("state") is not None:
        tokens.append(f"STATE:{str(canonical['state']).upper()}")
    if canonical.get("priority") is not None:
        tokens.append(f"PRIORITY:{str(canonical['priority']).upper()}")
    if canonical.get("destination") is not None:
        tokens.append(f"DESTINATION:{str(canonical['destination']).upper()}")

    if bool(canonical.get("end", False)):
        tokens.append("END:TRUE")
    else:
        tokens.append("END:FALSE")

    if canonical.get("confidence") is not None:
        try:
            value = float(canonical["confidence"])
            if 0.0 <= value <= 1.0:
                scaled = int(round(value * (max_vector_size - 1)))
                vector[min(max_vector_size - 1, max(0, scaled))] += 1.0
        except (TypeError, ValueError):
            pass

    for token in tokens:
        index = 0
        for char in token:
            index = (index * 31 + ord(char)) % max_vector_size
        vector[index] += 1.0

    # optional density metadata (helps distinguish near-empty vectors in simple rerouting)
    density_slot = max_vector_size - 2
    if density_slot >= 0:
        vector[density_slot] = float(len(tokens)) / max(1, max_vector_size)

    return vector


__all__ = ["canonical_to_vector"]
