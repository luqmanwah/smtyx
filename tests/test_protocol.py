import unittest

from smtyx import SemanticState, advance_state, validate_state


class TestProtocol(unittest.TestCase):
    def test_state_is_valid(self):
        state = SemanticState.create(source={"kind":"human","id":"u"}, intent="ANALYZE", object_type="DOCUMENT")
        result = validate_state(state)
        self.assertTrue(result["valid"], result)
        self.assertEqual(state.protocol, "SMTYX")
        self.assertEqual(state.protocol_version, "0.2")

    def test_lineage_and_transition(self):
        root = SemanticState.create(source={"kind":"human","id":"u"}, intent="VERIFY", object_type="CLAIM")
        parsed = advance_state(root, "PARSED")
        verified = advance_state(parsed, "VERIFIED", confidence=0.9)
        final = advance_state(verified, "FINAL")
        self.assertEqual(parsed.parent_state_id, root.state_id)
        self.assertEqual(final.trace_id, root.trace_id)
        self.assertIn("ACK_FINAL", final.ack)

    def test_illegal_transition(self):
        state = SemanticState.create(source={"kind":"human","id":"u"}, intent="ANALYZE", object_type="DOCUMENT")
        with self.assertRaises(ValueError):
            advance_state(state, "FINAL")

    def test_digest_stable_for_same_state(self):
        state = SemanticState.create(source={"kind":"human","id":"u"}, intent="ANALYZE", object_type="DOCUMENT")
        self.assertEqual(state.digest(), state.digest())


if __name__ == "__main__":
    unittest.main()
