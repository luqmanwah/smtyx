import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from smtyx.core import Layout, analyze_file, cluster_index, concatenate, signature
from smtyx.format import encode, load_document, validate_document, verify_source
from smtyx.registry import ROUTE_CLASSES, add_entry, load_registry, resolve
from smtyx.storage import read_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SMTYX_Design_Freeze_Chat_2026-09-17.md"
FIXTURE_SHA = "9fa2af4575cc33ea50218dd76ff5126868b0b9a59ed892fcdebd53f9545f5f45"
FIXTURE_HISTOGRAM = [0, 0, 0, 1495, 2100, 503, 292, 1308, 69, 416, 278, 1140, 1035, 3377, 2607, 5174]
FIXTURE_SIGNATURE = [19794, 1652792, 16462431679, 220036759485589, 3302292262678241467]


class MathematicsTests(unittest.TestCase):
    def test_every_byte_matches_string_pair_definition(self):
        counts = [0] * 16
        for value in range(256):
            binary = f"{value:08b}"
            state = "".join("0" if binary[start:start + 2] == "00" else "1"
                            for start in range(0, 8, 2))
            actual = cluster_index(value)
            self.assertEqual(actual, int(state, 2) + 1)
            counts[actual - 1] += 1
        self.assertEqual(counts, [3 ** state.bit_count() for state in range(16)])

    def test_cluster_golden_and_invalid_values(self):
        self.assertEqual([cluster_index(value) for value in b"ayam"], [14, 16, 14, 16])
        self.assertEqual([cluster_index(value) for value in (0, 1, 4, 16, 64, 255)], [1, 2, 3, 5, 9, 16])
        for invalid in (-1, 256, True, 1.0, "1"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                cluster_index(invalid)

    def test_golden_moments(self):
        self.assertEqual(signature(b"hello"), [5, 532, 1617, 5983, 24615])
        self.assertEqual(signature(b"hello world"), [11, 1116, 6736, 52204, 453382])
        self.assertEqual(signature(b""), [0] * 5)

    def test_concatenation_rebases_positions(self):
        data = bytes(range(256)) * 3
        for split in (1, 31, 32, 127, 128, 255, 512, 768):
            with self.subTest(split=split):
                self.assertEqual(concatenate([signature(data[:split]), signature(data[split:])]), signature(data))

    def test_explicit_information_loss(self):
        self.assertEqual(cluster_index(1), cluster_index(2))
        self.assertNotEqual(bytes([1]), bytes([2]))
        first, second = bytes([10] * 5), bytes([11, 6, 16, 6, 11])
        self.assertNotEqual(first, second)
        self.assertEqual(signature(first), signature(second))


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "arbitrary source.bin"
        self.output = self.directory / "output.smtyx"

    def test_empty_partial_and_multilevel_coverage(self):
        for length in (0, 1, 31, 32, 33, 127, 128, 129, 4095, 4096, 4097, 8209):
            with self.subTest(length=length):
                data = bytes((position * 73 + 17) % 256 for position in range(length))
                self.source.write_bytes(data)
                output = self.directory / f"{length}.smtyx"
                document = encode(self.source, output)
                self.assertEqual(load_document(output), document)
                nodes = document["large"]["nodes"]
                self.assertEqual([int(value) for value in nodes[-1]["signature"]], signature(data))
                for node in nodes:
                    start = int(node["offset"])
                    count = int(node["signature"][0])
                    self.assertEqual([int(value) for value in node["signature"]], signature(data[start:start + count]))
                self.assertEqual(self.source.read_bytes(), data)
                self.assertTrue(verify_source(document, self.source)["verified"])

    def test_custom_layout(self):
        self.source.write_bytes(bytes(range(256)))
        document = encode(self.source, self.output, layout=Layout(7, 3, 2))
        self.assertEqual(document["large"]["layout"], {"micro_bytes": 7, "micros_per_block": 3, "blocks_per_page": 2})
        self.assertTrue(verify_source(document, self.source)["verified"])
        for args in ((0, 4, 32), (32, -1, 32), (65536, 65536, 65536), (True, 4, 32)):
            with self.assertRaises(ValueError):
                Layout(*args)

    def test_small_raw_bytes_include_invalid_utf8(self):
        data = b"\x00\xff\xfe\x80\r\n" + bytes(range(256))
        self.source.write_bytes(data)
        document = encode(self.source, self.output, "SMALL")
        self.assertIsNone(document["large"])
        self.assertEqual(document["source"]["sha256"], sha256(data).hexdigest())
        self.assertTrue(verify_source(document, self.source)["verified"])

    def test_output_refuses_overwrite_and_hardlink(self):
        self.source.write_bytes(b"original")
        with self.assertRaises(FileExistsError):
            encode(self.source, self.source)
        encode(self.source, self.output)
        before = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            encode(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), before)
        alias = self.directory / "alias.smtyx"
        alias.hardlink_to(self.source)
        with self.assertRaises(FileExistsError):
            encode(self.source, alias)
        self.assertEqual(self.source.read_bytes(), b"original")

    def test_resource_bound(self):
        self.source.write_bytes(b"a" * 4097)
        with self.assertRaisesRegex(ValueError, "max_nodes"):
            encode(self.source, self.output, max_nodes=3)
        self.assertFalse(self.output.exists())

    def test_detect_input_changed_during_read(self):
        self.source.write_bytes(b"stable")
        actual = self.source.stat()
        changed = SimpleNamespace(st_size=actual.st_size, st_mtime_ns=actual.st_mtime_ns + 1,
                                  st_ino=actual.st_ino)
        with patch.object(Path, "is_file", return_value=True), patch.object(
            Path, "stat", side_effect=[actual, changed]
        ), self.assertRaisesRegex(ValueError, "changed while"):
            encode(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_repeatable_output_and_json_size_bounds(self):
        self.source.write_bytes(bytes(range(256)))
        encode(self.source, self.output)
        repeated = self.directory / "repeated.smtyx"
        encode(self.source, repeated)
        self.assertEqual(self.output.read_bytes(), repeated.read_bytes())
        with patch("smtyx.storage.MAX_JSON_BYTES", 16):
            with self.assertRaisesRegex(ValueError, "limit"):
                load_document(self.output)
            with self.assertRaisesRegex(ValueError, "limit"):
                encode(self.source, self.directory / "oversize.smtyx")
        self.assertFalse((self.directory / "oversize.smtyx").exists())

    def test_documented_json_examples_parse(self):
        document = (ROOT / "FORMAT.md").read_text(encoding="utf-8")
        examples = [section.split("```", 1)[0] for section in document.split("```json\n")[1:]]
        self.assertGreaterEqual(len(examples), 4)
        for example in examples:
            parsed = json.loads(example)
            if parsed.get("format") == "SMTYX-METADATA":
                validate_document(parsed)

    def test_verify_detects_small_collision_and_stale_file(self):
        self.source.write_bytes(bytes([1]))
        document = encode(self.source, self.output, "SMALL")
        self.source.write_bytes(bytes([2]))
        self.assertEqual(analyze_file(self.source, "SMALL")["small"], document["small"])
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_source(document, self.source)

    def test_tamper_rejection(self):
        self.source.write_bytes(bytes(range(256)) * 20)
        document = encode(self.source, self.output)
        mutations = [
            lambda value: value.update(version=2),
            lambda value: value.update(version=True),
            lambda value: value.update(mode="OTHER"),
            lambda value: value["small"]["fingerprint"].__setitem__(1, "0"),
            lambda value: value["small"]["histogram"].__setitem__(0, "-1"),
            lambda value: value["source"].update(size_bytes=5120),
            lambda value: value["source"].update(size_bytes="05120"),
            lambda value: value["source"].update(sha256="unknown"),
            lambda value: value["large"]["nodes"][0].update(offset="1"),
            lambda value: value["large"]["nodes"][0].update(children=["DOC:1"]),
            lambda value: value["large"]["nodes"][-1]["signature"].__setitem__(2, "1"),
            lambda value: value["large"]["nodes"][-1]["children"].reverse(),
            lambda value: value["large"]["nodes"].append(value["large"]["nodes"][0]),
            lambda value: value["reconstruction"].update(raw_decode_supported=True),
            lambda value: value["reconstruction"].update(metadata_only=1),
            lambda value: value.update(extra="unsupported"),
        ]
        for mutation in mutations:
            altered = copy.deepcopy(document)
            mutation(altered)
            with self.subTest(mutation=mutations.index(mutation)), self.assertRaises(ValueError):
                validate_document(altered)

    def test_malformed_json(self):
        for payload in (b'{"version":1,"version":2}', b'{"value":NaN}', b'\xff', b'{', b'[]'):
            self.output.write_bytes(payload)
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                load_document(self.output)

    def test_fixture_against_conversation(self):
        before = sha256(FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(before, FIXTURE_SHA)
        document = encode(FIXTURE, self.output)
        self.assertEqual(document["small"]["fingerprint"], ["19794", "236147"])
        self.assertEqual(list(map(int, document["small"]["histogram"])), FIXTURE_HISTOGRAM)
        nodes = document["large"]["nodes"]
        self.assertEqual(list(map(int, nodes[-1]["signature"])), FIXTURE_SIGNATURE)
        self.assertEqual([sum(node["kind"] == kind for node in nodes)
                          for kind in ("MICRO", "BLOCK", "PAGE", "DOC")], [619, 155, 5, 1])
        self.assertEqual(list(map(int, nodes[0]["signature"])), [32, 2857, 47898, 1016040, 24275478])
        self.assertEqual(sha256(FIXTURE.read_bytes()).hexdigest(), before)

    def cli(self, *args, code=0):
        result = subprocess.run([sys.executable, "-m", "smtyx", *map(str, args)],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stderr)
        if code:
            self.assertNotIn("Traceback", result.stderr)
            return result
        return json.loads(result.stdout)

    def test_cli_end_to_end(self):
        self.source.write_bytes(b"ayam")
        result = self.cli("encode", self.source, "-o", self.output)
        self.assertEqual(result["small"]["fingerprint"], ["4", "60"])
        inspected = self.cli("inspect", self.output)
        self.assertFalse(inspected["reconstruction"]["raw_decode_supported"])
        decoded = self.directory / "decoded.json"
        self.cli("decode", self.output, "-o", decoded)
        self.assertEqual(read_json(decoded), self.cli("inspect", self.output, "--json"))
        self.assertEqual(self.cli("decode", self.output), read_json(decoded))
        self.assertTrue(self.cli("verify", self.output, self.source)["verified"])
        self.cli("encode", self.source, "-o", self.output, code=2)
        self.cli("decode", self.output, "-o", self.source, code=2)
        self.cli("encode", self.directory, code=2)
        self.cli("encode", self.directory / "missing.bin", code=2)
        self.cli("encode", self.source, "--route", "FILE:1", code=2)
        self.assertEqual(self.source.read_bytes(), b"ayam")

    def test_registry_all_classes_and_snapshot_resolution(self):
        self.source.write_bytes(b"ayam")
        previous = None
        for index, kind in enumerate(ROUTE_CLASSES, 1):
            output = self.directory / f"registry-{index}.json"
            target = str(self.source) if kind == "FILE" else f"core:{kind.lower()}"
            add_entry(output, "tests", kind, index, target, previous)
            registry = load_registry(output)
            self.assertEqual(registry["revision"], index)
            self.assertEqual(resolve(registry, f"{kind}:{index}")["entry"]["target"], target)
            previous = output
        route = resolve(load_registry(previous), "FILE:4")
        document = encode(self.source, self.output, "SMALL", route=route)
        self.assertEqual(document["route"], route)
        self.assertEqual(self.cli("registry", "resolve", previous, "FILE:4"), route)
        with self.assertRaises(ValueError):
            resolve(load_registry(previous), "FILE:999")
        with self.assertRaises(ValueError):
            add_entry(self.directory / "new.json", "tests", "FILE", 4, str(self.source), previous)
        self.source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "does not match"):
            encode(self.source, self.directory / "stale.smtyx", "SMALL", route=route)
        self.assertFalse((self.directory / "stale.smtyx").exists())

    def test_registry_cli_and_invalid_entries(self):
        registry = self.directory / "registry.json"
        self.cli("registry", "add", "--output", registry, "--namespace", "tests",
                 "--kind", "VOCAB", "--index", 21, "--target", "RUN_PROGRAM")
        for route in ("UNKNOWN:1", "FILE:0", "FILE:01", f"FILE:{2 ** 61}"):
            self.cli("registry", "resolve", registry, route, code=2)
        self.cli("registry", "add", "--output", self.directory / "invalid.json", "--namespace", "bad namespace",
                 "--kind", "VOCAB", "--index", 1, "--target", "READ", code=2)
        self.assertFalse((self.directory / "invalid.json").exists())


if __name__ == "__main__":
    unittest.main()
