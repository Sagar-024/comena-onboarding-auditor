"""Upload persistence helpers: validation, sanitized saves, and cleanup."""

import logging
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.exceptions import FileValidationError

logger = logging.getLogger(__name__)

_UPLOAD_CHUNK_BYTES = 1024 * 1024
_MAX_FILENAME_LENGTH = 100
_UNSAFE_FILENAME_CHARS = re.compile(r"[^\w.\- ]+")


def create_session_dir(base_dir: str) -> Path:
    """Create a unique working directory under the upload root and return it."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    session_dir = Path(tempfile.mkdtemp(prefix="analyze-", dir=base))
    return session_dir


async def save_upload(
    upload: UploadFile,
    destination_dir: Path,
    allowed_extensions: set[str],
    max_bytes: int,
) -> Path:
    """Validate and stream one upload to disk under a sanitized filename."""
    filename = sanitize_filename(upload.filename)
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise FileValidationError(
            f"file '{filename}' must have one of these extensions: {allowed}"
        )

    destination = _unique_destination(destination_dir / filename)
    written = 0
    with destination.open("wb") as buffer:
        while chunk := await upload.read(_UPLOAD_CHUNK_BYTES):
            written += len(chunk)
            if written > max_bytes:
                raise FileValidationError(
                    f"file '{filename}' exceeds the {max_bytes // (1024 * 1024)} MB size limit"
                )
            buffer.write(chunk)
    if written == 0:
        raise FileValidationError(f"file '{filename}' is empty")
    logger.info("saved upload %s (%d bytes)", filename, written)
    return destination


def sanitize_filename(filename: str | None) -> str:
    """Strip path separators and unsafe characters from a client-supplied filename."""
    if not filename:
        raise FileValidationError("upload is missing a filename")
    basename = re.split(r"[\\/]+", filename.strip())[-1]
    cleaned = _UNSAFE_FILENAME_CHARS.sub("", basename).strip(". ")
    if not cleaned:
        raise FileValidationError("upload has an unusable filename after sanitization")
    return _cap_filename_length(cleaned)


def cleanup_dir(path: Path) -> None:
    """Remove a session directory and everything in it."""
    shutil.rmtree(path, ignore_errors=True)


def _unique_destination(destination: Path) -> Path:
    """Return a path that does not overwrite an earlier upload with the same name."""
    if not destination.exists():
        return destination
    return destination.with_name(
        f"{destination.stem}-{uuid.uuid4().hex[:6]}{destination.suffix}"
    )


def _cap_filename_length(name: str) -> str:
    """Keep long client filenames within path-length limits, preserving the suffix."""
    if len(name) <= _MAX_FILENAME_LENGTH:
        return name
    stem, dot, suffix = name.rpartition(".")
    if not dot:
        return name[:_MAX_FILENAME_LENGTH]
    return stem[: _MAX_FILENAME_LENGTH - len(suffix) - 1] + dot + suffix
