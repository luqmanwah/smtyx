from __future__ import annotations

from typing import Any, Dict, Optional
from .models import SemanticState
from .capabilities import CapabilityRegistry
from .memory import InMemoryStore
from .learning import LearningLedger
from .policy import RuntimePolicy
from .protocol import validate_state


class SemanticOrchestrator:
    """Small reference orchestrator. Protocol semantics are not coupled to this implementation."""

    def __init__(
        self,
        *,
        registry: Optional[CapabilityRegistry] = None,
        memory: Optional[InMemoryStore] = None,
        learning: Optional[LearningLedger] = None,
        policy: Optional[RuntimePolicy] = None,
    ) -> None:
        self.registry = registry or CapabilityRegistry()
        self.memory = memory or InMemoryStore()
        self.learning = learning or LearningLedger()
        self.policy = policy or RuntimePolicy()

    def route(self, state: SemanticState, *, locality: str | None = None) -> Dict[str, Any]:
        validity = validate_state(state)
        if not validity["valid"]:
            return {"routable": False, "errors": validity["errors"], "candidates": []}
        policy_decision = self.policy.evaluate(state.permissions)
        candidates = self.registry.select(intent=state.intent, object_type=state.object, locality=locality)
        return {
            "routable": bool(candidates) and policy_decision.allowed,
            "state_id": state.state_id,
            "trace_id": state.trace_id,
            "policy": policy_decision.to_dict(),
            "candidates": candidates,
            "selected": candidates[0]["agent_id"] if candidates and policy_decision.allowed else None,
        }
