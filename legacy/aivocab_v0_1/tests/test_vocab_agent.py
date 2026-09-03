import json
from pathlib import Path
import unittest

from src import parser, encoder, decoder, executor, semantic_protocol, validator
from src.bridge import VocabOrchestrator
from src.orchestrator import VocabOrchestrator as LegacyVocabOrchestrator


ROOT_DIR = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT_DIR / "vocab" / "core_vocab.json"
INTEROP_PATH = ROOT_DIR / "examples" / "interoperability_cases.jsonl"


class TestVocabAgent(unittest.TestCase):
    def _assert_subset(self, canonical, expected):
        for key, value in expected.items():
            self.assertIn(key, canonical)
            self.assertEqual(canonical[key], value)

    def test_vocab_has_at_least_114_entries(self):
        entries = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(entries), 114)
        ids = [item["id"] for item in entries]
        names = [item["name"] for item in entries]
        self.assertIn("PYTHON", names)
        self.assertIn("JAVASCRIPT", names)
        self.assertIn("CSHARP", names)
        self.assertIn("RUBY", names)
        self.assertEqual(len(set(ids)), len(entries))
        self.assertEqual(len(set(names)), len(entries))
        for item in entries:
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("primary_class", item)
            self.assertIn("description", item)

    def test_parse_human_instruction_with_language(self):
        canonical = parser.parse_human_instruction(
            "Jalankan Python lalu verifikasi error.",
            vocab_path=VOCAB_PATH,
            require_end=True,
        )
        self._assert_subset(
            canonical,
            {
                "actions": ["RUN", "VERIFY"],
                "object": "PYTHON",
                "target": "ERROR",
                "end": True,
            },
        )

    def test_parse_encoder_decoder_roundtrip_symbolic(self):
        canonical = {
            "version": "0.1",
            "actions": ["READ", "SEARCH", "FIX", "VERIFY"],
            "object": "PDF",
            "target": "ERROR",
            "end": True,
        }
        symbolic = encoder.encode_symbolic(canonical, vocab_path=VOCAB_PATH)
        numeric = encoder.encode_numeric(canonical, vocab_path=VOCAB_PATH)
        recovered_symbolic = decoder.decode_to_canonical(symbolic, vocab_path=VOCAB_PATH)
        recovered_numeric = decoder.decode_to_canonical(numeric, vocab_path=VOCAB_PATH)

        self.assertEqual(recovered_symbolic["actions"], canonical["actions"])
        self.assertEqual(recovered_numeric["actions"], canonical["actions"])
        self.assertEqual(recovered_symbolic["object"], canonical["object"])
        self.assertEqual(recovered_numeric["object"], canonical["object"])

    def test_validation_detects_unknown_and_duplicate(self):
        valid = validator.validate_symbolic(
            "READ PDF SEARCH ERROR FIX VERIFY END",
            vocab_path=VOCAB_PATH,
            require_end=True,
        )
        self.assertTrue(valid["valid"])

        invalid = validator.validate_symbolic(
            "READ READ PDF END",
            vocab_path=VOCAB_PATH,
            require_end=True,
        )
        self.assertFalse(invalid["valid"])
        error_codes = {err["code"] for err in invalid["errors"]}
        self.assertIn("DUPLICATE_ACTION", error_codes)

    def test_interoperability_cases_roundtrip(self):
        lines = [
            json.loads(line)
            for line in INTEROP_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertGreaterEqual(len(lines), 35)

        for case in lines:
            symbolic = case["symbolic_vocab"]
            numeric = case["numeric_vocab"]
            expected = case["expected_canonical_state"]

            symbolic_canon = decoder.decode_to_canonical(symbolic, vocab_path=VOCAB_PATH, require_end=True)
            numeric_canon = decoder.decode_to_canonical(numeric, vocab_path=VOCAB_PATH, require_end=True)

            self._assert_subset(symbolic_canon, expected)
            self._assert_subset(numeric_canon, expected)

            # roundtrip check for deterministic order in symbolic path
            symbols = encoder.encode_symbolic(symbolic_canon, vocab_path=VOCAB_PATH)
            recovered = parser.parse_symbolic(symbols, vocab_path=VOCAB_PATH, require_end=True)
            self._assert_subset(recovered, expected)

    def test_final_bridge_orchestrator(self):
        bridge = VocabOrchestrator()

        tool_case = bridge.route("Tolong buka Windows Notepad")
        self.assertEqual(tool_case["mode"], "tool")
        self.assertEqual(tool_case["tool_calls"][0]["tool"], "powershell")
        self.assertEqual(tool_case["tool_calls"][0]["action"], "open_notepad")
        self.assertEqual(tool_case["tool_calls"][0]["arguments"]["execution_mode"], "deferred")
        self.assertTrue(tool_case["tool_calls"][0]["arguments"]["requires_confirmation"])

        math_case = bridge.route("hitung satu tambah satu")
        self.assertEqual(math_case["mode"], "assistant")
        self.assertEqual(math_case["answer"], "2")

        file_case = bridge.route(r"Baca file F:\\AI")
        self.assertEqual(file_case["mode"], "tool")
        self.assertEqual(file_case["tool_calls"][0]["tool"], "analysis_agent")
        self.assertEqual(file_case["tool_calls"][0]["action"], "list_path_or_file")
        self.assertEqual(file_case["tool_calls"][0]["command"], "list_path")
        self.assertFalse(file_case["tool_calls"][0]["arguments"]["requires_confirmation"])

        folder_case = bridge.route(r"Buka folder F:\\AI")
        self.assertEqual(folder_case["mode"], "tool")
        self.assertEqual(folder_case["tool_calls"][0]["tool"], "analysis_agent")
        self.assertEqual(folder_case["tool_calls"][0]["action"], "list_path_or_file")
        self.assertEqual(folder_case["tool_calls"][0]["command"], "list_path")
        self.assertFalse(folder_case["tool_calls"][0]["arguments"]["requires_confirmation"])

        english_case = bridge.route("Run Python then verify error")
        self.assertEqual(english_case["mode"], "tool")
        self.assertEqual(english_case["canonical"]["actions"], ["RUN", "VERIFY"])
        self.assertEqual(english_case["canonical"]["object"], "PYTHON")

    def test_bridge_symbolic_numeric_and_route(self):
        bridge = VocabOrchestrator()
        self.assertIs(type(bridge), LegacyVocabOrchestrator)
        symbolic = bridge.route("RUN PYTHON ERROR END")
        self.assertEqual(symbolic["mode"], "tool")
        self.assertEqual(symbolic["input_mode"], "symbolic_or_numeric")
        self.assertEqual(symbolic["tool_calls"][0]["tool"], "runtime_sandbox")
        symbolic_2 = bridge.route("026 013 101 079 100")
        self.assertEqual(symbolic_2["mode"], "tool")
        self.assertEqual(symbolic_2["input_mode"], "symbolic_or_numeric")
        self.assertEqual(symbolic_2["tool_calls"][0]["tool"], "runtime_sandbox")
        self.assertEqual(symbolic_2["canonical"]["object"], "PYTHON")
        self.assertEqual(symbolic_2["canonical"]["target"], "ERROR")
        self.assertEqual(symbolic_2["canonical"]["actions"], ["RUN", "VERIFY"])

    def test_bridge_accepts_canonical_inputs_and_vectors(self):
        bridge = VocabOrchestrator()
        payload = {
            "version": "0.1",
            "actions": ["RUN", "VERIFY"],
            "object": "PYTHON",
            "target": "ERROR",
            "end": True,
        }
        route_from_dict = bridge.route(payload)
        self.assertEqual(route_from_dict["mode"], "tool")
        self.assertEqual(route_from_dict["input_mode"], "canonical_dict")
        self.assertIsInstance(route_from_dict["embedding"], list)
        self.assertTrue(len(route_from_dict["embedding"]) > 0)
        self._assert_subset(route_from_dict["canonical"], payload)
        self.assertEqual(route_from_dict["protocol_version"], semantic_protocol.SEMANTIC_PROTOCOL_VERSION)
        self.assertIn("semantic_state", route_from_dict)
        self.assertEqual(route_from_dict["semantic_state"]["status"], "VERIFIED")
        self.assertEqual(route_from_dict["semantic_state"]["source"]["kind"], "canonical")
        self.assertEqual(route_from_dict["semantic_state"]["source"]["adapter"], "bridge")

        route_from_json = bridge.route(json.dumps(payload))
        self.assertEqual(route_from_json["mode"], "tool")
        self.assertEqual(route_from_json["input_mode"], "canonical_json")
        self._assert_subset(route_from_json["canonical"], payload)
        self.assertIn("semantic_state", route_from_json)
        self.assertEqual(route_from_json["semantic_state"]["source"]["kind"], "canonical_json")
        self.assertEqual(route_from_json["semantic_state"]["status"], "VERIFIED")

        math_route = bridge.route("hitung satu tambah satu")
        self.assertEqual(math_route["input_mode"], "math")
        self.assertTrue(len(math_route["embedding"]) > 0)
        self.assertEqual(math_route["semantic_state"]["status"], "FINAL")
        self.assertIn(semantic_protocol.ACK_VERIFIED, math_route["ack"])

    def test_bridge_semantic_protocol_enrichment(self):
        bridge = VocabOrchestrator()
        tool_route = bridge.route("Tolong buka Windows Notepad")
        self.assertEqual(tool_route["mode"], "tool")
        semantic_state = tool_route["semantic_state"]
        self.assertIn("status", semantic_state)
        self.assertEqual(semantic_state["status"], "PARSED")
        self.assertEqual(semantic_state["protocol_version"], semantic_protocol.SEMANTIC_PROTOCOL_VERSION)
        self.assertEqual(semantic_state["ack"][-1], semantic_protocol.ACK_SEMANTIC)
        self.assertIn("tool.execute", semantic_state["permissions"])
        self.assertIn(semantic_protocol.ACK_PARSED, semantic_state["ack"])
        self.assertNotIn(semantic_protocol.ACK_FINAL, semantic_state["ack"])

        tool_execute = bridge.execute(tool_route, confirm=False)
        self.assertEqual(tool_execute["mode"], "tool")
        self.assertTrue(tool_execute["results"][0]["status"] in {"deferred", "blocked"})

    def test_tool_executor_dry_run_and_confirmation(self):
        bridge = VocabOrchestrator()
        route = bridge.route("Tolong buka Windows Notepad")
        self.assertEqual(route["mode"], "tool")
        self.assertEqual(route["tool_calls"][0]["tool"], "powershell")
        self.assertTrue(route["tool_calls"][0]["arguments"]["requires_confirmation"])

        deferred = bridge.execute(route, dry_run=True, confirm=False)
        self.assertEqual(deferred["mode"], "tool")
        self.assertEqual(deferred["results"][0]["status"], "deferred")
        self.assertTrue(deferred["results"][0]["requires_confirmation"])
        self.assertFalse(deferred["results"][0]["confirmation_used"])

        confirmed = bridge.execute(route, dry_run=True, confirm=True)
        self.assertEqual(confirmed["mode"], "tool")
        self.assertEqual(confirmed["results"][0]["status"], "deferred")
        self.assertEqual(confirmed["results"][0]["confirmation_used"], True)

    def test_executor_blocks_disallowed_command(self):
        engine = executor.ToolExecutor(dry_run_default=False)
        blocked = engine.execute_tool_call(
            {
                "tool": "powershell",
                "action": "danger",
                "command": "Get-ChildItem C:\\Windows\\System32\\*; Remove-Item *.tmp",
                "rationale": "manual",
                "arguments": {"requires_confirmation": False},
            },
            dry_run=False,
        )
        self.assertEqual(blocked.status, "blocked")
        self.assertIn("blocked", blocked.stderr.lower())


if __name__ == "__main__":
    unittest.main()
