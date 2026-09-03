import unittest
from smtyx import Capability, CapabilityRegistry, RuntimePolicy, SemanticOrchestrator, SemanticState


class TestRouting(unittest.TestCase):
    def test_ranking(self):
        reg = CapabilityRegistry()
        reg.register(Capability("a", {"ANALYZE"}, {"DOCUMENT"}, reliability=.8, latency_score=.8, cost_score=.8))
        reg.register(Capability("b", {"ANALYZE"}, {"DOCUMENT"}, reliability=.95, latency_score=.8, cost_score=.8))
        ranked = reg.select(intent="ANALYZE", object_type="DOCUMENT")
        self.assertEqual(ranked[0]["agent_id"], "b")

    def test_permission_boundary(self):
        reg = CapabilityRegistry()
        reg.register(Capability("editor", {"EDIT"}, {"DOCUMENT"}, reliability=.9))
        state = SemanticState.create(source={"kind":"human","id":"u"}, intent="EDIT", object_type="DOCUMENT", permissions=["document.write"])
        denied = SemanticOrchestrator(registry=reg, policy=RuntimePolicy()).route(state)
        self.assertFalse(denied["routable"])
        allowed = SemanticOrchestrator(registry=reg, policy=RuntimePolicy(granted_permissions={"document.write"})).route(state)
        self.assertTrue(allowed["routable"])
        self.assertEqual(allowed["selected"], "editor")


if __name__ == "__main__": unittest.main()
