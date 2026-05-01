"""Artifact file helpers shared by CLI and bundle generation."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from asimov_sim_lab.errors import LabError


def sha256_file(path: Path) -> str:
    """Compute a SHA-256 digest for a local artifact."""
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError as exc:
        raise LabError(
            "CHECKSUM_COMPUTE_FAILED",
            f"Could not compute checksum for {path}: {exc}",
            "Check file permissions and rerun the command.",
            exit_code=3,
        ) from exc
    return hasher.hexdigest()


def write_text_atomic(path: Path, content: str) -> None:
    """Write UTF-8 text through a temp file and atomic replace."""
    write_bytes_atomic(path, content.encode("utf-8"))


def write_bytes_atomic(path: Path, content: bytes) -> None:
    """Write bytes through a temp file and atomic replace."""
    if path.exists() and path.is_dir():
        raise LabError(
            "OUTPUT_PATH_IS_DIRECTORY",
            f"Output path is a directory: {path}",
            "Pass a file path for the output artifact.",
            exit_code=2,
        )
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise LabError(
            "OUTPUT_WRITE_FAILED",
            f"Could not write output path: {path}: {exc}",
            "Check directory permissions and available disk space.",
            exit_code=2,
        ) from exc
