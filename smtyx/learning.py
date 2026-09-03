from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class LearningStage(str, Enum):
    OBSERVATION = "OBSERVATION"
    CANDIDATE = "CANDIDATE"
    VERIFIED = "VERIFIED"
    ADOPTED = "ADOPTED"
    REJECTED = "REJECTED"


@dataclass
class LearningCandidate:
    statement: str
    scope: str
    source_state_ids: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    stage: LearningStage = LearningStage.OBSERVATION
    confidence: float = 0.5
    candidate_id: str = field(default_factory=lambda: "learn_" + uuid.uuid4().hex[:20])
    verification_note: Optional[str] = None
    adoption_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


class LearningLedger:
    def __init__(self, *, allow_auto_adopt: bool = False) -> None:
        self.allow_auto_adopt = allow_auto_adopt
        self._items: Dict[str, LearningCandidate] = {}

    def observe(self, statement: str, *, scope: str, source_state_ids: List[str] | None = None, confidence: float = 0.5) -> LearningCandidate:
        item = LearningCandidate(statement=statement, scope=scope, source_state_ids=list(source_state_ids or []), confidence=float(confidence))
        self._items[item.candidate_id] = item
        return item

    def promote_candidate(self, candidate_id: str) -> LearningCandidate:
        item = self._items[candidate_id]
        if item.stage != LearningStage.OBSERVATION:
            raise ValueError("Only observations can become candidates")
        item.stage = LearningStage.CANDIDATE
        return item

    def verify(self, candidate_id: str, *, note: str, confidence: float | None = None) -> LearningCandidate:
        item = self._items[candidate_id]
        if item.stage != LearningStage.CANDIDATE:
            raise ValueError("Only candidates can be verified")
        item.stage = LearningStage.VERIFIED
        item.verification_note = note
        if confidence is not None:
            item.confidence = float(confidence)
        return item

    def adopt(self, candidate_id: str, *, human_approved: bool = False, note: str = "") -> LearningCandidate:
        item = self._items[candidate_id]
        if item.stage != LearningStage.VERIFIED:
            raise ValueError("Only verified candidates can be adopted")
        if not human_approved and not self.allow_auto_adopt:
            raise PermissionError("Adoption requires explicit approval under the default policy")
        item.stage = LearningStage.ADOPTED
        item.adoption_note = note
        return item

    def reject(self, candidate_id: str, *, note: str = "") -> LearningCandidate:
        item = self._items[candidate_id]
        if item.stage in {LearningStage.ADOPTED, LearningStage.REJECTED}:
            raise ValueError("Learning item is already terminal")
        item.stage = LearningStage.REJECTED
        item.adoption_note = note
        return item
