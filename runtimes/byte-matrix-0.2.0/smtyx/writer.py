"""Explicit output writer for validated SMTYX documents."""

from pathlib import Path

from .exact import DEFAULT_MAX_OUTPUT, decode_exact, is_exact, read_exact
from .format import load_document
from .storage import write_new_json


def write_file(input_path, output_path, metadata=False, max_output_bytes=DEFAULT_MAX_OUTPUT):
    if is_exact(input_path):
        if not metadata:
            return decode_exact(input_path, output_path, max_output_bytes)
        if Path(output_path).suffix.lower() != ".json":
            raise ValueError("exact metadata summary requires .json; it is not a reconstructable .smtyx")
        document = read_exact(input_path, max_output_bytes=max_output_bytes)
        write_new_json(output_path, document)
        return {"output": str(output_path), "output_kind": "metadata-summary",
                "raw_file_reconstructed": False, "source_bytes_read": False}
    document = load_document(input_path)
    if not metadata:
        raise ValueError(
            "RAW_RECONSTRUCTION_UNAVAILABLE: SMTYX-METADATA v1 contains signatures "
            "and hierarchy, not a reconstructable raw payload. No output was written. "
            "Use --metadata only to write an explicitly labelled .smtyx or .json document."
        )
    output = Path(output_path)
    if output.suffix.lower() not in (".smtyx", ".json"):
        raise ValueError("metadata output requires .smtyx or .json extension; cannot impersonate a raw file")
    write_new_json(output, document)
    return {
        "output": str(output),
        "output_kind": "metadata",
        "size_bytes": str(output.stat().st_size),
        "raw_file_reconstructed": False,
        "source_bytes_read": False,
    }
