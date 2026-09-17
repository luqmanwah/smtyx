"""Bounded JSON input and exclusive output creation."""

import json
from pathlib import Path


MAX_JSON_BYTES = 64 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    with Path(path).open("rb") as source:
        data = source.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("JSON exceeds the 64 MiB metadata limit")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=lambda value: invalid_constant(value))
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid UTF-8 JSON") from error


def invalid_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_new_json(path, value):
    data = json_bytes(value)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("output exceeds the 64 MiB metadata limit; increase micro size")
    path = Path(path)
    with path.open("xb") as output:
        try:
            output.write(data)
        except BaseException:
            output.close()
            path.unlink(missing_ok=True)
            raise
