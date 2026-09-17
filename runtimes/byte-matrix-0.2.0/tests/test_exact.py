from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from smtyx.atomic import new_output
from smtyx.core import Layout, cluster_index, signature
from smtyx.exact import END, MAGIC, decode_exact, encode_exact, is_exact, read_exact, verify_exact
from smtyx.exact_math import decode_micro, decode_signature, encode_micro, encode_signature, read_unsigned, unsigned
from smtyx.registry import add_entry, load_registry, resolve
from smtyx.writer import write_file


ROOT = Path(__file__).resolve().parents[1]


def records(blob):
    position = len(MAGIC)
    result = []
    while position < len(blob) - len(END) - 32:
        kind = blob[position:position + 1]
        size = struct.unpack("<I", blob[position + 1:position + 5])[0]
        result.append((kind, blob[position + 5:position + 5 + size]))
        position += 5 + size
    return result


def container(frames):
    body = MAGIC + b"".join(kind + struct.pack("<I", len(payload)) + payload for kind, payload in frames)
    return body + END + sha256(body).digest()


class ExactMathTests(unittest.TestCase):
    def test_all_256_bytes_and_their_discriminators(self):
        for value in range(256):
            with self.subTest(value=value):
                payload, math_state = encode_micro(bytes([value]))
                data, decoded_math = decode_micro(payload, 1)
                self.assertEqual(data, bytes([value]))
                self.assertEqual(math_state, decoded_math)
                stream = BytesIO(payload)
                for _ in range(5):
                    read_unsigned(stream)
                self.assertEqual(stream.read(1)[0] >> 4, cluster_index(value) - 1)
                trits = [int(f"{value:08b}"[start:start + 2], 2) - 1
                         for start in range(0, 8, 2) if f"{value:08b}"[start:start + 2] != "00"]
                expected = sum(trit * 3 ** (len(trits) - position - 1) for position, trit in enumerate(trits))
                self.assertEqual(int.from_bytes(stream.read(), "big"), expected)

    def test_pair_collision_is_resolved_by_rank(self):
        payload, _ = encode_micro(bytes([1, 2, 3]))
        prefix = encode_signature(signature(bytes([1, 2, 3])))
        self.assertEqual(payload[len(prefix):], bytes([0x11, 0x10, 5]))
        self.assertEqual(decode_micro(payload, 3)[0], bytes([1, 2, 3]))

    def test_varints_are_canonical_and_bounded(self):
        for value in (0, 1, 127, 128, 255, 2 ** 64, 2 ** 447):
            self.assertEqual(read_unsigned(BytesIO(unsigned(value))), value)
        for data in (b"", b"\x80", b"\x80\x00", b"\x80" * 65):
            with self.assertRaises(ValueError):
                read_unsigned(BytesIO(data))
        for value in (-1, True, 2 ** 448):
            with self.assertRaises(ValueError):
                unsigned(value)

    def test_invalid_rank_padding_lengths_and_signature(self):
        payload, _ = encode_micro(bytes([1]))
        bad_cases = [payload[:-1], payload + b"\0", payload[:-1] + b"\x03",
                     payload[:-2] + b"\x11" + payload[-1:], b"\x02" + payload[1:]]
        for broken in bad_cases:
            with self.assertRaises(ValueError):
                decode_micro(broken, 1)
        with self.assertRaises(ValueError):
            encode_micro(b"")
        with self.assertRaises(ValueError):
            encode_micro(bytes(1025))


class ExactRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "source.bin"
        self.packet = self.directory / "input.smtyx"
        self.output = self.directory / "recovered.bin"

    def make_packet(self, data=bytes(range(256))):
        self.source.write_bytes(data)
        return encode_exact(self.source, self.packet)

    def test_round_trip_empty_boundaries_and_arbitrary_binary_without_source(self):
        for length in (0, 1, 31, 32, 33, 127, 128, 129, 4095, 4096, 4097, 8193):
            with self.subTest(length=length):
                data = random.Random(length).randbytes(length)
                self.source.write_bytes(data)
                packet = self.directory / f"{length}.smtyx"
                output = self.directory / f"{length}.bin"
                encoded = encode_exact(self.source, packet)
                self.source.unlink()
                result = decode_exact(packet, output)
                self.assertEqual(output.read_bytes(), data)
                self.assertTrue(result["raw_file_reconstructed"])
                self.assertFalse(result["source_bytes_read"])
                self.assertEqual(result["sha256"], sha256(data).hexdigest())
                self.assertEqual(list(map(int, encoded["root_signature"])), signature(data))
                self.assertEqual(read_exact(packet)["small"], encoded["small"])

    def test_fixture_and_custom_hierarchy(self):
        fixture = ROOT / "tests" / "fixtures" / "SMTYX_Design_Freeze_Chat_2026-09-17.md"
        result = encode_exact(fixture, self.packet, Layout(17, 3, 5))
        self.assertEqual(result["small"]["fingerprint"], ["19794", "236147"])
        self.assertEqual(result["root_signature"], ["19794", "1652792", "16462431679", "220036759485589", "3302292262678241467"])
        self.assertTrue(verify_exact(self.packet, fixture)["verified"])
        decode_exact(self.packet, self.output)
        self.assertEqual(self.output.read_bytes(), fixture.read_bytes())

    def test_repeatable_serialization_and_magic(self):
        self.make_packet()
        repeated = self.directory / "repeated.smtyx"
        encode_exact(self.source, repeated)
        self.assertEqual(self.packet.read_bytes(), repeated.read_bytes())
        self.assertTrue(is_exact(self.packet))
        self.assertFalse(is_exact(self.source))

    def test_corruption_never_publishes_partial_output(self):
        self.make_packet()
        original = self.packet.read_bytes()
        broken_versions = [original[:-1], original[:50], original + b"extra",
                           original[:-1] + bytes([original[-1] ^ 1])]
        for broken in broken_versions:
            self.packet.write_bytes(broken)
            with self.assertRaises(ValueError):
                decode_exact(self.packet, self.output)
            self.assertFalse(self.output.exists())
            self.assertEqual(list(self.directory.glob(".smtyx-*.partial")), [])

    def test_deep_validation_after_attacker_recomputes_container_hash(self):
        self.make_packet(bytes(range(256)) * 20)
        original_frames = records(self.packet.read_bytes())
        for kind in (b"M", b"B", b"P", b"D", b"F"):
            frames = list(original_frames)
            position = next(index for index, frame in enumerate(frames) if frame[0] == kind)
            payload = frames[position][1]
            if kind == b"F":
                footer = json.loads(payload)
                footer["sha256"] = "0" * 64
                replacement = json.dumps(footer).encode()
            elif kind == b"M":
                replacement = payload[:-1] + bytes([payload[-1] ^ 1])
            else:
                values = decode_signature(payload)
                values[1] += 1
                replacement = encode_signature(values)
            frames[position] = (kind, replacement)
            self.packet.write_bytes(container(frames))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                decode_exact(self.packet, self.output)
            self.assertFalse(self.output.exists())

    def test_invalid_header_order_and_record_size(self):
        self.make_packet()
        original_frames = records(self.packet.read_bytes())
        header = json.loads(original_frames[0][1])
        invalid_headers = []
        for key, value in (("version", True), ("profile", "unknown"), ("mode", "SMALL")):
            invalid = dict(header)
            invalid[key] = value
            invalid_headers.append(invalid)
        for invalid in invalid_headers:
            frames = list(original_frames)
            frames[0] = (b"H", json.dumps(invalid).encode())
            self.packet.write_bytes(container(frames))
            with self.assertRaises(ValueError):
                read_exact(self.packet)
        self.packet.write_bytes(container([original_frames[0], *original_frames[2:]]))
        with self.assertRaisesRegex(ValueError, "record order"):
            read_exact(self.packet)
        self.packet.write_bytes(MAGIC + b"H" + struct.pack("<I", 65537))
        with self.assertRaisesRegex(ValueError, "64 KiB"):
            read_exact(self.packet)

    def test_limits_before_publication(self):
        self.make_packet()
        with self.assertRaisesRegex(ValueError, "max-output"):
            decode_exact(self.packet, self.output, 128)
        self.assertFalse(self.output.exists())
        for layout in (Layout(2048, 4, 32), Layout(32, 300, 1)):
            with self.assertRaises(ValueError):
                encode_exact(self.source, self.directory / "bad.smtyx", layout)

    def test_source_and_existing_destination_preserved(self):
        data = bytes(range(256))
        self.make_packet(data)
        with self.assertRaises(FileExistsError):
            encode_exact(self.source, self.source)
        with self.assertRaises(FileExistsError):
            decode_exact(self.packet, self.source)
        alias = self.directory / "alias.bin"
        alias.hardlink_to(self.source)
        with self.assertRaises(FileExistsError):
            decode_exact(self.packet, alias)
        self.assertEqual(self.source.read_bytes(), data)

    def test_exclusive_publication_race(self):
        def competing_writer(temporary, destination):
            Path(destination).write_bytes(b"another writer")
            raise FileExistsError("race")
        with patch("smtyx.atomic.os.link", side_effect=competing_writer):
            with self.assertRaises(FileExistsError):
                with new_output(self.output) as output:
                    output.write(b"candidate")
        self.assertEqual(self.output.read_bytes(), b"another writer")
        self.assertEqual(list(self.directory.glob(".smtyx-*.partial")), [])

    def test_source_mutation_aborts_encoder_publication(self):
        self.source.write_bytes(bytes(range(256)))
        original_encoder = encode_micro
        modified = False

        def modify_during_read(data):
            nonlocal modified
            if not modified:
                with self.source.open("ab") as source:
                    source.write(b"new bytes")
                modified = True
            return original_encoder(data)

        with patch("smtyx.exact.encode_micro", side_effect=modify_during_read):
            with self.assertRaisesRegex(ValueError, "grew|changed"):
                encode_exact(self.source, self.packet)
        self.assertFalse(self.packet.exists())
        self.assertEqual(list(self.directory.glob(".smtyx-*.partial")), [])

    def test_file_route_validated_without_source_lookup_at_decode(self):
        self.source.write_bytes(b"test")
        registry = self.directory / "registry.json"
        add_entry(registry, "tests", "FILE", 1, str(self.source))
        route = resolve(load_registry(registry), "FILE:1")
        encode_exact(self.source, self.packet, route=route)
        self.source.unlink()
        registry.unlink()
        decode_exact(self.packet, self.output)
        self.assertEqual(self.output.read_bytes(), b"test")
        self.source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "FILE route"):
            encode_exact(self.source, self.directory / "stale.smtyx", route=route)
        self.assertFalse((self.directory / "stale.smtyx").exists())

    def test_verify_detects_changed_or_extra_source(self):
        self.make_packet(b"ayam")
        for data in (b"Ayam", b"ayam!", b"aya"):
            self.source.write_bytes(data)
            with self.assertRaises(ValueError):
                verify_exact(self.packet, self.source)

    def cli(self, *args, code=0):
        result = subprocess.run([sys.executable, "-B", "-m", "smtyx", *map(str, args)],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, code, result.stderr)
        if code:
            self.assertNotIn("Traceback", result.stderr)
            return result
        return json.loads(result.stdout)

    def test_cli_exact_write_decode_inspect_and_metadata_summary(self):
        self.source.write_bytes(b"ayam\x00\xff\r\n")
        self.cli("encode", self.source, "--exact", "-o", self.packet)
        self.assertTrue(self.cli("inspect", self.packet)["reconstruction"]["raw_decode_supported"])
        self.assertTrue(self.cli("write", self.packet, "-o", self.output)["raw_file_reconstructed"])
        decoded = self.directory / "second.bin"
        self.cli("decode", self.packet, "-o", decoded)
        self.assertEqual(decoded.read_bytes(), self.source.read_bytes())
        self.assertTrue(self.cli("verify", self.packet, self.source)["verified"])
        metadata = self.directory / "summary.json"
        result = self.cli("write", self.packet, "--metadata", "-o", metadata)
        self.assertFalse(result["raw_file_reconstructed"])
        self.assertEqual(json.loads(metadata.read_text())["format"], "SMTYX-EXACT")
        self.cli("decode", self.packet, code=2)
        self.cli("encode", self.source, "--exact", "--mode", "small", "-o", self.directory / "bad.smtyx", code=2)
        self.cli("write", self.packet, "--metadata", "-o", self.directory / "fake.smtyx", code=2)
        self.cli("inspect", self.packet, "--max-output-bytes", "0", code=2)


if __name__ == "__main__":
    unittest.main()
