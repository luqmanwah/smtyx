from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List, Set


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_confirmation: bool
    missing_permissions: List[str]
    rationale: str

    def to_dict(self):
        return asdict(self)


class RuntimePolicy:
    def __init__(self, *, granted_permissions: Iterable[str] = (), confirm_permissions: Iterable[str] = ()) -> None:
        self.granted_permissions: Set[str] = set(granted_permissions)
        self.confirm_permissions: Set[str] = set(confirm_permissions)

    def evaluate(self, required_permissions: Iterable[str]) -> PolicyDecision:
        required = set(required_permissions)
        missing = sorted(required - self.granted_permissions)
        if missing:
            return PolicyDecision(False, False, missing, "Required runtime permissions are not granted")
        confirm = bool(required & self.confirm_permissions)
        return PolicyDecision(True, confirm, [], "Permission scopes satisfied")
