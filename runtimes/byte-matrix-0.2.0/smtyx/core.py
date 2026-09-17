"""Deterministic byte mathematics, with no text interpretation."""

from dataclasses import dataclass
from hashlib import sha256
from math import comb
from pathlib import Path


def cluster_index(value: int) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError("byte must be an integer in 0..255")
    state = 0
    for shift in (6, 4, 2, 0):
        state = (state << 1) | int(bool((value >> shift) & 3))
    return state + 1


CLUSTER_TABLE = bytes(cluster_index(value) for value in range(256))


def signature(data: bytes) -> list[int]:
    moments = [0, 0, 0, 0]
    for position, value in enumerate(data, 1):
        term = value
        for degree in range(4):
            moments[degree] += term
            term *= position
    return [len(data), *moments]


def concatenate(signatures: list[list[int]]) -> list[int]:
    length = 0
    moments = [0, 0, 0, 0]
    for child in signatures:
        for degree in range(4):
            moments[degree] += sum(
                comb(degree, lower) * length ** (degree - lower) * child[lower + 1]
                for lower in range(degree + 1)
            )
        length += child[0]
    return [length, *moments]


@dataclass(frozen=True)
class Layout:
    micro_bytes: int = 32
    micros_per_block: int = 4
    blocks_per_page: int = 32

    def __post_init__(self):
        for value in (self.micro_bytes, self.micros_per_block, self.blocks_per_page):
            if type(value) is not int or not 1 <= value <= 65536:
                raise ValueError("layout values must be integers in 1..65536")
        if self.micro_bytes * self.micros_per_block * self.blocks_per_page > 16777216:
            raise ValueError("page capacity must be at most 16 MiB")

    def as_dict(self):
        return {
            "micro_bytes": self.micro_bytes,
            "micros_per_block": self.micros_per_block,
            "blocks_per_page": self.blocks_per_page,
        }


def make_node(kind, number, offset, math_state, children):
    return {
        "id": f"{kind}:{number}",
        "kind": kind,
        "offset": str(offset),
        "signature": [str(value) for value in math_state],
        "children": children,
    }


def group_nodes(children, kind, fanout):
    parents = []
    for start in range(0, len(children), fanout):
        group = children[start:start + fanout]
        math_state = concatenate([
            [int(value) for value in child["signature"]] for child in group
        ])
        parents.append(make_node(
            kind, len(parents) + 1, int(group[0]["offset"]), math_state,
            [child["id"] for child in group],
        ))
    return parents


def analyze_file(path, mode="LARGE", layout=None, max_nodes=100000):
    if mode not in ("SMALL", "LARGE"):
        raise ValueError("mode must be SMALL or LARGE")
    if type(max_nodes) is not int or max_nodes < 1:
        raise ValueError("max_nodes must be positive")
    layout = layout or Layout()
    path = Path(path)
    if not path.is_file():
        raise ValueError("input must be a regular file")
    before = path.stat()
    if mode == "LARGE":
        micro_count = (before.st_size + layout.micro_bytes - 1) // layout.micro_bytes
        block_count = (micro_count + layout.micros_per_block - 1) // layout.micros_per_block
        page_count = (block_count + layout.blocks_per_page - 1) // layout.blocks_per_page
        if micro_count + block_count + page_count + 1 > max_nodes:
            raise ValueError("hierarchy exceeds max_nodes; increase micro size or --max-nodes")
    histogram = [0] * 16
    length = 0
    digest = sha256()
    micros = []
    read_size = layout.micro_bytes if mode == "LARGE" else 65536
    with path.open("rb") as source:
        while data := source.read(read_size):
            digest.update(data)
            clusters = data.translate(CLUSTER_TABLE)
            for cluster in range(1, 17):
                histogram[cluster - 1] += clusters.count(cluster)
            if mode == "LARGE":
                if len(micros) >= max_nodes - 1:
                    raise ValueError("growing input exceeds max_nodes")
                micros.append(make_node("MICRO", len(micros) + 1, length, signature(data), []))
            length += len(data)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
        after.st_size, after.st_mtime_ns, after.st_ino
    ) or length != before.st_size:
        raise ValueError("input changed while being read; retry on a stable file")
    hierarchy = None
    if mode == "LARGE":
        blocks = group_nodes(micros, "BLOCK", layout.micros_per_block)
        pages = group_nodes(blocks, "PAGE", layout.blocks_per_page)
        root = make_node("DOC", 1, 0, concatenate([
            [int(value) for value in page["signature"]] for page in pages
        ]), [page["id"] for page in pages])
        nodes = micros + blocks + pages + [root]
        if len(nodes) > max_nodes:
            raise ValueError("hierarchy exceeds max_nodes")
        hierarchy = {"layout": layout.as_dict(), "root": "DOC:1", "nodes": nodes}
    return {
        "source": {"name": path.name, "size_bytes": str(length), "sha256": digest.hexdigest()},
        "small": {
            "fingerprint": [str(length), str(sum(
                cluster * count for cluster, count in enumerate(histogram, 1)
            ))],
            "histogram": [str(count) for count in histogram],
        },
        "large": hierarchy,
    }
