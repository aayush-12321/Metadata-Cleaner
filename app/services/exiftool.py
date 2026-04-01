"""
ExifTool service: locate the binary, extract metadata, and strip metadata.
All subprocess calls are isolated here so the rest of the app stays clean.
"""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from flask import current_app

logger = logging.getLogger(__name__)


class ExifToolError(RuntimeError):
    """Raised when ExifTool is missing or returns an unexpected error."""


def _get_exiftool_path() -> str:
    """
    Resolve the ExifTool binary path from config or system PATH.

    Raises:
        ExifToolError: if ExifTool cannot be found.
    """
    configured = current_app.config.get("EXIFTOOL_PATH")
    if configured and Path(configured).is_file():
        return configured

    found = shutil.which("exiftool")
    if found:
        return found

    raise ExifToolError(
        "exiftool not found. Install it and ensure it is on PATH. "
        "Ubuntu/Debian: sudo apt install libimage-exiftool-perl  "
        "macOS: brew install exiftool  "
        "Windows: https://exiftool.org/"
    )


def extract_metadata(file_path: str) -> dict:
    """
    Extract all metadata from a file using ExifTool.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Raw metadata dict from ExifTool (unfiltered).

    Raises:
        ExifToolError: on binary missing or parse failure.
    """
    exiftool = _get_exiftool_path()

    try:
        result = subprocess.run(
            [exiftool, "-j", "-a", "-G1", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise ExifToolError(f"ExifTool timed out reading '{file_path}'.")
    except OSError as exc:
        raise ExifToolError(f"Failed to launch ExifTool: {exc}") from exc

    if result.returncode not in (0, 1):
        raise ExifToolError(f"ExifTool error: {result.stderr.strip()}")

    if not result.stdout.strip():
        return {}

    try:
        data = json.loads(result.stdout)
        return data[0] if data else {}
    except (json.JSONDecodeError, IndexError) as exc:
        raise ExifToolError(f"Failed to parse ExifTool output: {exc}") from exc


def clean_metadata(file_path: str, preset_flags: list[str]) -> None:
    """
    Remove metadata from a file in-place using the provided ExifTool flags.

    Args:
        file_path: Absolute path to the file.
        preset_flags: List of ExifTool flag strings, e.g. ['-all=', '-GPS:all='].

    Raises:
        ExifToolError: on binary missing or clean failure.
    """
    exiftool = _get_exiftool_path()
    cmd = [exiftool] + preset_flags + ["-overwrite_original", file_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise ExifToolError(f"ExifTool timed out cleaning '{file_path}'.")
    except OSError as exc:
        raise ExifToolError(f"Failed to launch ExifTool: {exc}") from exc

    if result.returncode not in (0, 1):
        raise ExifToolError(
            f"ExifTool failed on '{Path(file_path).name}': {result.stderr.strip()}"
        )

    logger.info("Cleaned metadata from '%s'", Path(file_path).name)
