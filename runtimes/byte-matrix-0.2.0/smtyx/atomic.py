"""Publish a new verified output without replacing any existing path."""

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile


@contextmanager
def new_output(path):
    path = Path(path)
    if os.path.lexists(path):
        raise FileExistsError(f"output already exists: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".smtyx-", suffix=".partial", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
