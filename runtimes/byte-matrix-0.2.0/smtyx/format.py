"""SMTYX-METADATA version 1 construction and structural validation."""

import re

from .core import Layout, analyze_file, concatenate, group_nodes, make_node
from .registry import NAMESPACE_PATTERN, SHA256_PATTERN, validate_entry
from .storage import read_json, write_new_json


PROFILE = "raw-byte-pair-or-msb-v1"
PROVENANCE = {
    "originator": "@luqmanwah",
    "design_reference": "chatgpt:6a99b94e-9758-83ec-8246-c2290888ad53",
    "freeze_date": "2026-09-17",
    "implementation": "smtyx-python/0.1.0",
}


def natural(value):
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]{0,127}", value):
        raise ValueError("expected canonical nonnegative decimal string (max 128 digits)")
    return int(value)


def fields(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected.split()):
        raise ValueError(f"invalid {label} fields")


def validate_route(route):
    fields(route, "namespace revision entry", "route")
    if not isinstance(route["namespace"], str) or not NAMESPACE_PATTERN.fullmatch(route["namespace"]):
        raise ValueError("invalid route namespace")
    if type(route["revision"]) is not int or not 1 <= route["revision"] <= 2147483647:
        raise ValueError("invalid route revision")
    validate_entry(route["entry"])


def validate_signature(values):
    if not isinstance(values, list) or len(values) != 5:
        raise ValueError("signature must be [N,P0,P1,P2,P3]")
    length, *moments = [natural(value) for value in values]
    power_sums = [length, length * (length + 1) // 2,
                  length * (length + 1) * (2 * length + 1) // 6,
                  (length * (length + 1) // 2) ** 2]
    if any(moment > 255 * bound for moment, bound in zip(moments, power_sums)):
        raise ValueError("signature exceeds byte moment bounds")
    if moments != sorted(moments):
        raise ValueError("nonnegative byte moments must be nondecreasing")
    return [length, *moments]


def validate_hierarchy(hierarchy, size):
    fields(hierarchy, "layout root nodes", "hierarchy")
    fields(hierarchy["layout"], "micro_bytes micros_per_block blocks_per_page", "layout")
    layout = Layout(**hierarchy["layout"])
    nodes = hierarchy["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("hierarchy requires a root node")
    micros = []
    for node in nodes:
        fields(node, "id kind offset signature children", "node")
        validate_signature(node["signature"])
        natural(node["offset"])
        if node["kind"] == "MICRO":
            offset = len(micros) * layout.micro_bytes
            length = min(layout.micro_bytes, size - offset)
            if length <= 0 or node != make_node(
                "MICRO", len(micros) + 1, offset,
                [length, *[natural(value) for value in node["signature"][1:]]], [],
            ):
                raise ValueError("invalid MICRO coverage, signature length, or ordering")
            micros.append(node)
    expected_count = (size + layout.micro_bytes - 1) // layout.micro_bytes
    if len(micros) != expected_count:
        raise ValueError("MICRO nodes do not cover source bytes")
    blocks = group_nodes(micros, "BLOCK", layout.micros_per_block)
    pages = group_nodes(blocks, "PAGE", layout.blocks_per_page)
    root = make_node("DOC", 1, 0, concatenate([
        [natural(value) for value in page["signature"]] for page in pages
    ]), [page["id"] for page in pages])
    if hierarchy["root"] != "DOC:1" or nodes != micros + blocks + pages + [root]:
        raise ValueError("hierarchy IDs, edges, offsets, or parent signatures are inconsistent")


def validate_document(document):
    fields(document, "format version profile mode source small large route reconstruction provenance", "document")
    if document["format"] != "SMTYX-METADATA" or type(document["version"]) is not int or document["version"] != 1:
        raise ValueError("unsupported SMTYX format/version")
    if document["profile"] != PROFILE or document["mode"] not in ("SMALL", "LARGE"):
        raise ValueError("unsupported profile/mode")
    if document["reconstruction"] != {"metadata_only": True, "raw_decode_supported": False}:
        raise ValueError("invalid reconstruction capability declaration")
    if any(type(value) is not bool for value in document["reconstruction"].values()):
        raise ValueError("reconstruction flags must be boolean")
    if document["provenance"] != PROVENANCE:
        raise ValueError("unsupported provenance profile")
    fields(document["source"], "name size_bytes sha256", "source")
    source = document["source"]
    if not isinstance(source["name"], str) or not source["name"]:
        raise ValueError("invalid source name")
    if not isinstance(source["sha256"], str) or not SHA256_PATTERN.fullmatch(source["sha256"]):
        raise ValueError("invalid source SHA-256")
    size = natural(source["size_bytes"])
    fields(document["small"], "fingerprint histogram", "small")
    small = document["small"]
    if not isinstance(small["fingerprint"], list) or len(small["fingerprint"]) != 2:
        raise ValueError("fingerprint must be [N,W]")
    length, weight = map(natural, small["fingerprint"])
    if not isinstance(small["histogram"], list) or len(small["histogram"]) != 16:
        raise ValueError("histogram must contain C01..C16")
    histogram = [natural(value) for value in small["histogram"]]
    if length != size or sum(histogram) != size or weight != sum(
        cluster * count for cluster, count in enumerate(histogram, 1)
    ):
        raise ValueError("inconsistent size, fingerprint, or histogram")
    if document["mode"] == "LARGE":
        validate_hierarchy(document["large"], size)
    elif document["large"] is not None:
        raise ValueError("SMALL mode must not contain a LARGE hierarchy")
    if document["route"] is not None:
        validate_route(document["route"])
        entry = document["route"]["entry"]
        if entry["class"] == "FILE" and entry["sha256"] != source["sha256"]:
            raise ValueError("FILE route content does not match source SHA-256")
    return document


def encode(source, output, mode="LARGE", layout=None, route=None, max_nodes=100000):
    document = {
        "format": "SMTYX-METADATA", "version": 1, "profile": PROFILE,
        "mode": mode, **analyze_file(source, mode, layout, max_nodes),
        "route": route,
        "reconstruction": {"metadata_only": True, "raw_decode_supported": False},
        "provenance": dict(PROVENANCE),
    }
    validate_document(document)
    write_new_json(output, document)
    return document


def load_document(path):
    return validate_document(read_json(path))


def verify_source(document, source):
    validate_document(document)
    layout = Layout(**document["large"]["layout"]) if document["large"] else None
    max_nodes = len(document["large"]["nodes"]) if document["large"] else 1
    actual = analyze_file(source, document["mode"], layout, max_nodes)
    if (actual["source"]["sha256"] != document["source"]["sha256"]
            or actual["source"]["size_bytes"] != document["source"]["size_bytes"]
            or actual["small"] != document["small"] or actual["large"] != document["large"]):
        raise ValueError("source content does not match SMTYX metadata")
    return {"verified": True, "sha256": actual["source"]["sha256"], "scope": "external-source-and-all-metadata"}


def summary(document):
    counts = {}
    root_signature = None
    if document["large"]:
        for node in document["large"]["nodes"]:
            counts[node["kind"]] = counts.get(node["kind"], 0) + 1
        root_signature = document["large"]["nodes"][-1]["signature"]
    return {
        "mode": document["mode"], "source": document["source"],
        "small": document["small"], "node_counts": counts,
        "root_signature": root_signature, "route": document["route"],
        "reconstruction": document["reconstruction"],
        "validation": "metadata-structure-only; use verify with an external source",
    }
