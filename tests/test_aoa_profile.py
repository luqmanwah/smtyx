import unittest

from smtyx import (
    AOA_INTENTS,
    AOA_OBJECTS,
    AOA_PROFILE,
    create_aoa_state,
    validate_aoa_state,
)


class TestAOAProfile(unittest.TestCase):
    def test_create_and_validate(self):
        state = create_aoa_state(
            source={"kind": "human", "id": "luqman"},
            destination={"kind": "orchestrator", "id": "pyxis"},
            intent="route",
            object_type="task",
            project="aoa_lab",
            persona="nara",
            memory_scopes=["NARA_LTM", "PYXIS_LTM"],
        )
        result = validate_aoa_state(state)
        self.assertTrue(result["valid"], result)
        self.assertEqual(state.metadata["aoa_profile"], "AOA/0.1")
        self.assertEqual(state.intent, "ROUTE")
        self.assertEqual(state.object, "TASK")

    def test_profile_is_required(self):
        state = create_aoa_state(
            source={"kind": "human", "id": "u"},
            intent="read",
            object_type="state",
        )
        data = state.to_dict()
        data["metadata"] = {}
        result = validate_aoa_state(data)
        self.assertFalse(result["valid"])
        self.assertIn("AOA_PROFILE_MISMATCH", {e["code"] for e in result["errors"]})

    def test_unknown_intent_rejected(self):
        state = create_aoa_state(
            source={"kind": "human", "id": "u"},
            intent="read",
            object_type="state",
        )
        data = state.to_dict()
        data["intent"] = "INVENTED"
        result = validate_aoa_state(data)
        self.assertFalse(result["valid"])
        self.assertIn("AOA_INTENT", {e["code"] for e in result["errors"]})

    def test_unknown_object_rejected(self):
        state = create_aoa_state(
            source={"kind": "human", "id": "u"},
            intent="read",
            object_type="state",
        )
        data = state.to_dict()
        data["object"] = "INVENTED"
        result = validate_aoa_state(data)
        self.assertFalse(result["valid"])
        self.assertIn("AOA_OBJECT", {e["code"] for e in result["errors"]})

    def test_vocabulary_contains_sync_and_session_control(self):
        self.assertEqual(AOA_PROFILE, "AOA/0.1")
        self.assertIn("HYDRATE", AOA_INTENTS)
        self.assertIn("TUNE", AOA_INTENTS)
        self.assertIn("SESSION", AOA_OBJECTS)
        self.assertIn("PROJECTION", AOA_OBJECTS)


if __name__ == "__main__":
    unittest.main()
