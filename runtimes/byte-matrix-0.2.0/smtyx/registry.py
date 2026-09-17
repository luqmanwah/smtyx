"""Versioned, immutable route snapshots; resolution never executes targets."""

import re

from .core import analyze_file
from .storage import read_json, write_new_json


ROUTE_CLASSES = ("VOCAB", "PATH", "LINK", "FILE", "SOP", "TOOL", "MODEL", "STATE")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
NAMESPACE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


def parse_route(route):
    if not isinstance(route, str) or not re.fullmatch(
        r"(?:VOCAB|PATH|LINK|FILE|SOP|TOOL|MODEL|STATE):[1-9][0-9]{0,18}", route
    ):
        raise ValueError("route must be CLASS:positive-index, e.g. FILE:37")
    kind, index = route.split(":")
    if int(index) >= 2 ** 61:
        raise ValueError("route index must fit 61 bits")
    return kind, int(index)


def validate_entry(entry):
    if not isinstance(entry, dict) or set(entry) != {"class", "index", "target", "sha256"}:
        raise ValueError("invalid route entry fields")
    kind, index = parse_route(f"{entry['class']}:{entry['index']}")
    if not isinstance(entry["index"], str) or str(index) != entry["index"]:
        raise ValueError("route index must be a canonical decimal string")
    if not isinstance(entry["target"], str) or not entry["target"].strip():
        raise ValueError("route target must be nonempty text")
    digest = entry["sha256"]
    if kind == "FILE":
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
            raise ValueError("FILE entries require SHA-256")
    elif digest is not None:
        raise ValueError("only FILE entries carry content SHA-256")
    return entry


def validate_registry(registry):
    if not isinstance(registry, dict) or set(registry) != {
        "format", "version", "namespace", "revision", "entries"
    }:
        raise ValueError("invalid registry fields")
    if registry["format"] != "SMTYX-REGISTRY" or type(registry["version"]) is not int or registry["version"] != 1:
        raise ValueError("unsupported registry format/version")
    if not isinstance(registry["namespace"], str) or not NAMESPACE_PATTERN.fullmatch(registry["namespace"]):
        raise ValueError("invalid registry namespace")
    if type(registry["revision"]) is not int or not 1 <= registry["revision"] <= 2147483647:
        raise ValueError("invalid registry revision")
    if not isinstance(registry["entries"], dict):
        raise ValueError("registry entries must be an object")
    for route, entry in registry["entries"].items():
        parse_route(route)
        validate_entry(entry)
        if route != f"{entry['class']}:{entry['index']}":
            raise ValueError("route key does not match entry")
    return registry


def load_registry(path):
    return validate_registry(read_json(path))


def resolve(registry, route):
    validate_registry(registry)
    parse_route(route)
    if route not in registry["entries"]:
        raise ValueError(f"route not found: {route}")
    return {
        "namespace": registry["namespace"],
        "revision": registry["revision"],
        "entry": dict(registry["entries"][route]),
    }


def add_entry(output, namespace, kind, index, target, base=None):
    registry = load_registry(base) if base else {
        "format": "SMTYX-REGISTRY", "version": 1,
        "namespace": namespace, "revision": 0, "entries": {},
    }
    if base and namespace != registry["namespace"]:
        raise ValueError("namespace must match the base registry")
    route = f"{kind}:{index}"
    parse_route(route)
    if route in registry["entries"]:
        raise ValueError("route already exists; allocate a new index for a new object/version")
    digest = analyze_file(target, "SMALL")["source"]["sha256"] if kind == "FILE" else None
    registry["entries"][route] = {
        "class": kind, "index": str(index), "target": target, "sha256": digest,
    }
    registry["revision"] += 1
    validate_registry(registry)
    write_new_json(output, registry)
    return resolve(registry, route)
