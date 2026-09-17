import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from smtyx.format import encode, load_document
from smtyx.writer import write_file


ROOT = Path(__file__).resolve().parents[1]


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "original.bin"
        self.source.write_bytes(bytes(range(256)))
        self.packet = self.directory / "input.smtyx"
        self.document = encode(self.source, self.packet)

    def test_metadata_write_without_original_source(self):
        self.source.unlink()
        for extension in (".smtyx", ".json"):
            output = self.directory / f"written{extension}"
            result = write_file(self.packet, output, metadata=True)
            self.assertEqual(load_document(output), self.document)
            self.assertEqual(result["output_kind"], "metadata")
            self.assertFalse(result["raw_file_reconstructed"])
            self.assertFalse(result["source_bytes_read"])

    def test_raw_write_refuses_without_creating_output(self):
        output = self.directory / "original.zip"
        with self.assertRaisesRegex(ValueError, "RAW_RECONSTRUCTION_UNAVAILABLE"):
            write_file(self.packet, output)
        self.assertFalse(output.exists())
        self.assertEqual(self.source.read_bytes(), bytes(range(256)))

    def test_raw_write_also_refuses_small_packet(self):
        packet = self.directory / "small.smtyx"
        encode(self.source, packet, mode="SMALL")
        with self.assertRaisesRegex(ValueError, "RAW_RECONSTRUCTION_UNAVAILABLE"):
            write_file(packet, self.directory / "raw.bin")
        self.assertFalse((self.directory / "raw.bin").exists())

    def test_metadata_cannot_be_disguised_as_original_extension(self):
        for name in ("fake.zip", "fake.pdf", "fake.exe", "fake"):
            output = self.directory / name
            with self.assertRaisesRegex(ValueError, "extension"):
                write_file(self.packet, output, metadata=True)
            self.assertFalse(output.exists())

    def test_no_overwrite_or_input_modification(self):
        original = self.packet.read_bytes()
        with self.assertRaises(FileExistsError):
            write_file(self.packet, self.packet, metadata=True)
        alias = self.directory / "alias.smtyx"
        alias.hardlink_to(self.packet)
        with self.assertRaises(FileExistsError):
            write_file(self.packet, alias, metadata=True)
        self.assertEqual(self.packet.read_bytes(), original)

    def test_invalid_input_writes_nothing(self):
        self.packet.write_text('{"format":"UNKNOWN"}', encoding="utf-8")
        output = self.directory / "output.smtyx"
        with self.assertRaises(ValueError):
            write_file(self.packet, output, metadata=True)
        self.assertFalse(output.exists())

    def test_cli_write_and_failure_semantics(self):
        output = self.directory / "output.smtyx"
        result = subprocess.run(
            [sys.executable, "-B", "-m", "smtyx", "write", str(self.packet), "--metadata", "-o", str(output)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["raw_file_reconstructed"])
        raw = self.directory / "output.bin"
        result = subprocess.run(
            [sys.executable, "-B", "-m", "smtyx", "write", str(self.packet), "-o", str(raw)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("RAW_RECONSTRUCTION_UNAVAILABLE", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(raw.exists())


if __name__ == "__main__":
    unittest.main()
