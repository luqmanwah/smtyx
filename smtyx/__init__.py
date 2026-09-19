"""SMTYX reference SDK."""

from .models import SemanticState, EvidenceRef
from .protocol import (
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
    STATUSES,
    ACKS,
    advance_state,
    validate_state,
)
from .task_graph import TaskNode, TaskGraph
from .capabilities import Capability, CapabilityRegistry
from .memory import MemoryKind, MemoryRecord, InMemoryStore
from .learning import LearningStage, LearningCandidate, LearningLedger
from .policy import PolicyDecision, RuntimePolicy
from .orchestrator import SemanticOrchestrator
from .aoa import (
    AOA_PROFILE,
    AOA_INTENTS,
    AOA_OBJECTS,
    create_aoa_state,
    validate_aoa_state,
)

__version__ = "0.2.0"

__all__ = [
    "SemanticState", "EvidenceRef", "PROTOCOL_NAME", "PROTOCOL_VERSION",
    "STATUSES", "ACKS", "advance_state", "validate_state", "TaskNode",
    "TaskGraph", "Capability", "CapabilityRegistry", "MemoryKind",
    "MemoryRecord", "InMemoryStore", "LearningStage", "LearningCandidate",
    "LearningLedger", "PolicyDecision", "RuntimePolicy", "SemanticOrchestrator",
    "AOA_PROFILE", "AOA_INTENTS", "AOA_OBJECTS", "create_aoa_state",
    "validate_aoa_state",
]
