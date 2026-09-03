from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Set


@dataclass
class TaskNode:
    node_id: str
    intent: str
    object: str
    depends_on: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, TaskNode] = {}

    def add(self, node: TaskNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node_id: {node.node_id}")
        self.nodes[node.node_id] = node

    def validate(self) -> Dict[str, Any]:
        errors = []
        for node in self.nodes.values():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    errors.append({"code": "MISSING_DEPENDENCY", "node": node.node_id, "dependency": dep})

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(node_id: str) -> None:
            if node_id in visiting:
                errors.append({"code": "CYCLE", "node": node_id})
                return
            if node_id in visited or node_id not in self.nodes:
                return
            visiting.add(node_id)
            for dep in self.nodes[node_id].depends_on:
                dfs(dep)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in self.nodes:
            dfs(node_id)
        return {"valid": not errors, "errors": errors}

    def ready(self, completed: Iterable[str] = ()) -> List[TaskNode]:
        completed_set = set(completed)
        return [
            node for node in self.nodes.values()
            if node.node_id not in completed_set and set(node.depends_on).issubset(completed_set)
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {"nodes": [node.to_dict() for node in self.nodes.values()]}
