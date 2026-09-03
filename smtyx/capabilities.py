from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set


@dataclass
class Capability:
    agent_id: str
    intents: Set[str] = field(default_factory=set)
    objects: Set[str] = field(default_factory=set)
    tools: Set[str] = field(default_factory=set)
    locality: str = "any"
    reliability: float = 0.5
    latency_score: float = 0.5
    cost_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.intents = {str(x).upper() for x in self.intents}
        self.objects = {str(x).upper() for x in self.objects}
        self.tools = {str(x) for x in self.tools}
        for name in ("reliability", "latency_score", "cost_score"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
            setattr(self, name, value)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key in ("intents", "objects", "tools"):
            data[key] = sorted(data[key])
        return data


class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._items[capability.agent_id] = capability

    def get(self, agent_id: str) -> Optional[Capability]:
        return self._items.get(agent_id)

    def select(self, *, intent: str, object_type: str, locality: Optional[str] = None) -> List[Dict[str, Any]]:
        intent = str(intent).upper()
        object_type = str(object_type).upper()
        ranked = []
        for cap in self._items.values():
            if cap.intents and intent not in cap.intents:
                continue
            if cap.objects and object_type not in cap.objects:
                continue
            if locality and cap.locality not in {"any", locality}:
                continue
            score = (0.60 * cap.reliability) + (0.20 * cap.latency_score) + (0.20 * cap.cost_score)
            ranked.append({"agent_id": cap.agent_id, "score": round(score, 6), "capability": cap.to_dict()})
        return sorted(ranked, key=lambda x: (-x["score"], x["agent_id"]))

    def list(self) -> List[Capability]:
        return list(self._items.values())
