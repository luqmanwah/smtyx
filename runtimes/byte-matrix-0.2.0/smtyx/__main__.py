"""Command line entry point: python -m smtyx."""

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .core import Layout
from .exact import DEFAULT_MAX_OUTPUT, decode_exact, encode_exact, is_exact, read_exact, verify_exact
from .format import encode, load_document, summary, verify_source
from .registry import ROUTE_CLASSES, add_entry, load_registry, resolve
from .storage import write_new_json
from .writer import write_file


def parser():
    root = argparse.ArgumentParser(description="SMTYX raw-byte matrix metadata and exact reconstruction runtime")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    encoder = commands.add_parser("encode", help="read raw file bytes and create .smtyx metadata")
    encoder.add_argument("source", type=Path)
    encoder.add_argument("-o", "--output", type=Path)
    encoder.add_argument("--mode", choices=("small", "large"), default="large")
    encoder.add_argument("--exact", action="store_true", help="encode reversible cluster masks and ternary discriminators (LARGE only)")
    encoder.add_argument("--micro-bytes", type=int, default=32)
    encoder.add_argument("--micros-per-block", type=int, default=4)
    encoder.add_argument("--blocks-per-page", type=int, default=32)
    encoder.add_argument("--max-nodes", type=int, default=100000)
    encoder.add_argument("--registry", type=Path)
    encoder.add_argument("--route")
    inspector = commands.add_parser("inspect", help="validate metadata and print a summary")
    inspector.add_argument("input", type=Path)
    inspector.add_argument("--json", action="store_true", help="print the complete metadata document")
    decoder = commands.add_parser("decode", help="decode v1 metadata or reconstruct v2 exact raw bytes")
    decoder.add_argument("input", type=Path)
    decoder.add_argument("-o", "--output", type=Path)
    writer = commands.add_parser("write", help="write verified raw bytes from exact v2, or export metadata explicitly")
    writer.add_argument("input", type=Path)
    writer.add_argument("-o", "--output", type=Path, required=True)
    writer.add_argument("--metadata", action="store_true", help="write metadata to .smtyx or .json, not the original raw file")
    verifier = commands.add_parser("verify", help="recompute metadata against an external file")
    verifier.add_argument("input", type=Path)
    verifier.add_argument("source", type=Path)
    for reader_command in (inspector, decoder, writer, verifier):
        reader_command.add_argument("--max-output-bytes", type=int, default=DEFAULT_MAX_OUTPUT,
                                    help="maximum decoded size for exact v2 (default 8 GiB)")
    registry = commands.add_parser("registry", help="create or resolve immutable route snapshots")
    registry_commands = registry.add_subparsers(dest="registry_command", required=True)
    add = registry_commands.add_parser("add")
    add.add_argument("--output", required=True, type=Path)
    add.add_argument("--base", type=Path)
    add.add_argument("--namespace", required=True)
    add.add_argument("--kind", required=True, choices=ROUTE_CLASSES)
    add.add_argument("--index", required=True, type=int)
    add.add_argument("--target", required=True)
    resolver = registry_commands.add_parser("resolve")
    resolver.add_argument("registry", type=Path)
    resolver.add_argument("route")
    return root


def run(args):
    if args.command == "encode":
        if bool(args.registry) != bool(args.route):
            raise ValueError("--registry and --route must be supplied together")
        route = resolve(load_registry(args.registry), args.route) if args.registry else None
        output = args.output or Path(str(args.source) + ".smtyx")
        if output.suffix.lower() != ".smtyx":
            raise ValueError("encoded output must have .smtyx extension")
        if output.exists():
            raise FileExistsError(f"output already exists: {output}")
        layout = Layout(args.micro_bytes, args.micros_per_block, args.blocks_per_page)
        if args.exact:
            if args.mode != "large":
                raise ValueError("--exact requires LARGE mode")
            if args.max_nodes != 100000:
                raise ValueError("--max-nodes applies to v1 metadata; exact v2 streams its hierarchy")
            return {"output": str(output), **encode_exact(args.source, output, layout, route)}
        document = encode(args.source, output, args.mode.upper(), layout, route, args.max_nodes)
        return {"output": str(output), **summary(document)}
    if args.command == "inspect":
        if is_exact(args.input):
            return read_exact(args.input, max_output_bytes=args.max_output_bytes)
        document = load_document(args.input)
        return document if args.json else summary(document)
    if args.command == "decode":
        if is_exact(args.input):
            if not args.output:
                raise ValueError("exact decode requires -o/--output; raw bytes are never written to stdout")
            return decode_exact(args.input, args.output, args.max_output_bytes)
        document = load_document(args.input)
        if args.output:
            write_new_json(args.output, document)
            return {"metadata_output": str(args.output), "raw_decode_supported": False}
        return document
    if args.command == "verify":
        if is_exact(args.input):
            return verify_exact(args.input, args.source, args.max_output_bytes)
        return verify_source(load_document(args.input), args.source)
    if args.command == "write":
        return write_file(args.input, args.output, args.metadata, args.max_output_bytes)
    if args.registry_command == "resolve":
        return resolve(load_registry(args.registry), args.route)
    return add_entry(args.output, args.namespace, args.kind, args.index, args.target, args.base)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, RecursionError) as error:
        print(f"smtyx: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
