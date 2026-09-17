"""Streaming SMTYX-EXACT v2 container and verified reconstruction."""

from hashlib import sha256
import json
from pathlib import Path
import struct

from .atomic import new_output
from .core import CLUSTER_TABLE, Layout, concatenate
from .exact_math import decode_micro, decode_signature, encode_micro, encode_signature
from .format import PROVENANCE, fields, natural, validate_route
from .storage import invalid_constant, unique_object


MAGIC = b"SMTYXEX2\r\n\x1a\n"
END = b"END!"
MAX_RECORD = 65536
DEFAULT_MAX_OUTPUT = 8 * 1024 ** 3
EXACT_PROVENANCE = {**PROVENANCE, "implementation": "smtyx-python/0.2.0"}


def json_payload(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def parse_json(payload):
    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid exact JSON record") from error


def exact_layout(layout):
    if layout.micro_bytes > 1024:
        raise ValueError("exact MICRO must be at most 1024 bytes")
    if layout.micros_per_block > 256 or layout.blocks_per_page > 256:
        raise ValueError("exact hierarchy fanout must be at most 256")
    if layout.micro_bytes * layout.micros_per_block * layout.blocks_per_page > 1048576:
        raise ValueError("exact PAGE capacity must be at most 1 MiB")
    return layout


def is_exact(path):
    with Path(path).open("rb") as stream:
        return stream.read(len(MAGIC)) == MAGIC


def validate_header(header):
    fields(header, "format version profile mode layout source route provenance", "exact header")
    if (header["format"] != "SMTYX-EXACT" or type(header["version"]) is not int
            or header["version"] != 2 or header["profile"] != "cluster-ternary-msb-v1"
            or header["mode"] != "LARGE" or header["provenance"] != EXACT_PROVENANCE):
        raise ValueError("unsupported exact format/profile/version/provenance")
    fields(header["layout"], "micro_bytes micros_per_block blocks_per_page", "exact layout")
    layout = exact_layout(Layout(**header["layout"]))
    fields(header["source"], "name size_bytes", "exact source")
    if not isinstance(header["source"]["name"], str) or not header["source"]["name"]:
        raise ValueError("invalid source name")
    if natural(header["source"]["size_bytes"]) >= 2 ** 63:
        raise ValueError("exact source size must fit 63 bits")
    if header["route"] is not None:
        validate_route(header["route"])
    return layout


class RecordWriter:
    def __init__(self, stream):
        self.stream = stream
        self.digest = sha256()
        self.write(MAGIC)

    def write(self, data):
        self.stream.write(data)
        self.digest.update(data)

    def record(self, kind, payload):
        if len(payload) > MAX_RECORD:
            raise ValueError("exact record exceeds 64 KiB")
        self.write(kind + struct.pack("<I", len(payload)) + payload)

    def finish(self):
        self.stream.write(END + self.digest.digest())


class RecordReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = sha256()
        if self.read(len(MAGIC)) != MAGIC:
            raise ValueError("invalid exact container magic")

    def read(self, size):
        data = self.stream.read(size)
        if len(data) != size:
            raise ValueError("truncated exact container")
        self.digest.update(data)
        return data

    def record(self, expected):
        if self.read(1) != expected:
            raise ValueError(f"invalid record order; expected {expected.decode('ascii')}")
        size = struct.unpack("<I", self.read(4))[0]
        if size > MAX_RECORD:
            raise ValueError("exact record exceeds 64 KiB")
        return self.read(size)

    def finish(self):
        trailer = self.stream.read(len(END) + 32)
        if trailer != END + self.digest.digest():
            raise ValueError("exact container checksum mismatch or truncated trailer")
        if self.stream.read(1):
            raise ValueError("trailing data after exact container")


class Statistics:
    def __init__(self):
        self.digest = sha256()
        self.histogram = [0] * 16
        self.counts = {"MICRO": 0, "BLOCK": 0, "PAGE": 0, "DOC": 1}
        self.root = [0] * 5

    def update(self, data):
        self.digest.update(data)
        clusters = data.translate(CLUSTER_TABLE)
        for index in range(16):
            self.histogram[index] += clusters.count(index + 1)
        self.counts["MICRO"] += 1

    def footer(self):
        return {
            "sha256": self.digest.hexdigest(),
            "small": {
                "fingerprint": [str(sum(self.histogram)), str(sum(
                    (index + 1) * count for index, count in enumerate(self.histogram)
                ))],
                "histogram": list(map(str, self.histogram)),
            },
            "node_counts": dict(self.counts),
            "root_signature": list(map(str, self.root)),
        }


def check_file_route(header, content_hash):
    if header["route"] is not None:
        entry = header["route"]["entry"]
        if entry["class"] == "FILE" and entry["sha256"] != content_hash:
            raise ValueError("FILE route content does not match reconstructed SHA-256")


def result_summary(header, footer, validation):
    return {
        "format": "SMTYX-EXACT", "version": 2, "profile": header["profile"], "mode": "LARGE",
        "source": {**header["source"], "sha256": footer["sha256"]},
        "small": footer["small"], "layout": header["layout"],
        "node_counts": footer["node_counts"], "root_signature": footer["root_signature"],
        "route": header["route"], "provenance": header["provenance"],
        "reconstruction": {"metadata_only": False, "raw_decode_supported": True,
                           "scheme": "ordered-cluster-masks-and-ternary-discriminator"},
        "validation": validation,
    }


def encode_exact(source, output, layout=None, route=None):
    source = Path(source)
    if not source.is_file():
        raise ValueError("input must be a regular file")
    before = source.stat()
    layout = exact_layout(layout or Layout())
    header = {
        "format": "SMTYX-EXACT", "version": 2, "profile": "cluster-ternary-msb-v1", "mode": "LARGE",
        "layout": layout.as_dict(), "source": {"name": source.name, "size_bytes": str(before.st_size)},
        "route": route, "provenance": dict(EXACT_PROVENANCE),
    }
    validate_header(header)
    stats = Statistics()
    block_size = layout.micro_bytes * layout.micros_per_block
    page_size = block_size * layout.blocks_per_page
    with new_output(output) as encoded, source.open("rb") as original:
        writer = RecordWriter(encoded)
        writer.record(b"H", json_payload(header))
        for page_start in range(0, before.st_size, page_size):
            page_end = min(page_start + page_size, before.st_size)
            page_math = [0] * 5
            for block_start in range(page_start, page_end, block_size):
                block_end = min(block_start + block_size, page_end)
                block_math = [0] * 5
                for micro_start in range(block_start, block_end, layout.micro_bytes):
                    length = min(layout.micro_bytes, block_end - micro_start)
                    data = original.read(length)
                    if len(data) != length:
                        raise ValueError("input truncated during encoding")
                    payload, math_state = encode_micro(data)
                    writer.record(b"M", payload)
                    stats.update(data)
                    block_math = concatenate([block_math, math_state])
                writer.record(b"B", encode_signature(block_math))
                stats.counts["BLOCK"] += 1
                page_math = concatenate([page_math, block_math])
            writer.record(b"P", encode_signature(page_math))
            stats.counts["PAGE"] += 1
            stats.root = concatenate([stats.root, page_math])
        if original.read(1):
            raise ValueError("input grew during encoding")
        after = source.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("input changed during encoding")
        writer.record(b"D", encode_signature(stats.root))
        footer = stats.footer()
        check_file_route(header, footer["sha256"])
        writer.record(b"F", json_payload(footer))
        writer.finish()
    return result_summary(header, footer, "encoded-from-raw-bytes")


def read_exact(path, sink=None, max_output_bytes=DEFAULT_MAX_OUTPUT):
    if type(max_output_bytes) is not int or max_output_bytes < 0:
        raise ValueError("max_output_bytes must be nonnegative")
    with Path(path).open("rb") as stream:
        reader = RecordReader(stream)
        header = parse_json(reader.record(b"H"))
        layout = validate_header(header)
        source_size = natural(header["source"]["size_bytes"])
        if source_size > max_output_bytes:
            raise ValueError("declared source exceeds --max-output-bytes")
        block_size = layout.micro_bytes * layout.micros_per_block
        page_size = block_size * layout.blocks_per_page
        stats = Statistics()
        for page_start in range(0, source_size, page_size):
            page_end = min(page_start + page_size, source_size)
            page_math = [0] * 5
            for block_start in range(page_start, page_end, block_size):
                block_end = min(block_start + block_size, page_end)
                block_math = [0] * 5
                for micro_start in range(block_start, block_end, layout.micro_bytes):
                    length = min(layout.micro_bytes, block_end - micro_start)
                    data, math_state = decode_micro(reader.record(b"M"), length)
                    stats.update(data)
                    block_math = concatenate([block_math, math_state])
                    if sink is not None:
                        sink.write(data)
                if decode_signature(reader.record(b"B")) != block_math:
                    raise ValueError("BLOCK signature mismatch")
                stats.counts["BLOCK"] += 1
                page_math = concatenate([page_math, block_math])
            if decode_signature(reader.record(b"P")) != page_math:
                raise ValueError("PAGE signature mismatch")
            stats.counts["PAGE"] += 1
            stats.root = concatenate([stats.root, page_math])
        if decode_signature(reader.record(b"D")) != stats.root:
            raise ValueError("DOC signature mismatch")
        footer = parse_json(reader.record(b"F"))
        if json_payload(footer) != json_payload(stats.footer()):
            raise ValueError("footer SHA-256, SMALL, counts, or root mismatch")
        check_file_route(header, footer["sha256"])
        reader.finish()
    return result_summary(header, footer, "all-records-moments-and-sha256-verified")


def decode_exact(path, output, max_output_bytes=DEFAULT_MAX_OUTPUT):
    with new_output(output) as reconstructed:
        result = read_exact(path, reconstructed, max_output_bytes)
    return {
        "output": str(output), "output_kind": "raw", "raw_file_reconstructed": True,
        "source_bytes_read": False, "size_bytes": result["source"]["size_bytes"],
        "sha256": result["source"]["sha256"], "validation": result["validation"],
    }


class CompareSink:
    def __init__(self, original):
        self.original = original

    def write(self, data):
        if self.original.read(len(data)) != data:
            raise ValueError("source does not match reconstructed bytes")


def verify_exact(path, source, max_output_bytes=DEFAULT_MAX_OUTPUT):
    with Path(source).open("rb") as original:
        result = read_exact(path, CompareSink(original), max_output_bytes)
        if original.read(1):
            raise ValueError("source contains extra bytes")
    return {"verified": True, "sha256": result["source"]["sha256"],
            "scope": "byte-for-byte-reconstruction-and-all-metadata"}
