from smtyx import (
    SemanticState,
    Capability,
    CapabilityRegistry,
    RuntimePolicy,
    SemanticOrchestrator,
    advance_state,
)

registry = CapabilityRegistry()
registry.register(Capability(
    agent_id="cloud-reviewer",
    intents={"ANALYZE", "VERIFY"},
    objects={"DOCUMENT"},
    locality="cloud",
    reliability=0.95,
    latency_score=0.7,
    cost_score=0.6,
))
registry.register(Capability(
    agent_id="local-executor",
    intents={"EDIT"},
    objects={"DOCUMENT"},
    locality="local",
    reliability=0.9,
    latency_score=0.9,
    cost_score=0.9,
))

policy = RuntimePolicy(granted_permissions={"document.read"})
orchestrator = SemanticOrchestrator(registry=registry, policy=policy)

state = SemanticState.create(
    source={"kind": "human", "id": "user"},
    intent="ANALYZE",
    object_type="DOCUMENT",
    permissions=["document.read"],
    payload={"goal": "find inconsistent table numbering"},
)

print(orchestrator.route(state, locality="cloud"))
parsed = advance_state(state, "PARSED")
verified = advance_state(parsed, "VERIFIED", confidence=0.93)
print(verified.to_dict())
