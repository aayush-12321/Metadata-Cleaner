"""
Cleaning service: orchestrates metadata extraction, preset application,
and result packaging.
"""

import os
import logging
from pathlib import Path
from flask import current_app

from .exiftool import extract_metadata, clean_metadata, ExifToolError
from .metadata import (
    filter_metadata,
    categorize_metadata,
    compute_risk,
    build_diff,
    compare_metadata,
)
from ..utils.file_utils import make_zip

logger = logging.getLogger(__name__)


class CleaningError(RuntimeError):
    """Raised when a cleaning job fails."""


def get_preset_flags(preset: str, custom_fields: list[str] | None = None) -> list[str]:
    """
    Resolve a preset name to ExifTool flag list.

    Args:
        preset: 'full', 'safe', 'privacy', or 'custom'.
        custom_fields: Required when preset == 'custom'. List of tag names to strip.

    Returns:
        List of ExifTool flag strings.

    Raises:
        ValueError: for unknown preset or missing custom fields.
    """
    presets = current_app.config["CLEANING_PRESETS"]

    if preset == "custom":
        if not custom_fields:
            raise ValueError("Custom preset requires at least one field.")
        return [f"-{f}=" for f in custom_fields]

    if preset not in presets:
        available = ", ".join(presets.keys()) + ", custom"
        raise ValueError(f"Unknown preset '{preset}'. Available: {available}.")

    return presets[preset]


def process_file(file_path: str, preset: str, custom_fields: list[str] | None = None) -> dict:
    """
    Extract metadata, clean the file, and return a full result payload.

    Args:
        file_path: Absolute path to the saved upload.
        preset: Cleaning preset name.
        custom_fields: Optional list for 'custom' preset.

    Returns:
        Dict with keys: filename, before, after, diff, risk, categories_before, categories_after.

    Raises:
        CleaningError: wraps ExifToolError or other failures.
    """
    filename = Path(file_path).name

    try:
        raw_before = extract_metadata(file_path)
        before = filter_metadata(raw_before)
        before_size = os.path.getsize(file_path)

        flags = get_preset_flags(preset, custom_fields)
        clean_metadata(file_path, flags)

        raw_after = extract_metadata(file_path)
        after = filter_metadata(raw_after)
        after_size = os.path.getsize(file_path)

    except ExifToolError as exc:
        raise CleaningError(str(exc)) from exc
    except ValueError as exc:
        raise CleaningError(str(exc)) from exc

    metadata_comparison = compare_metadata(before, after)
    diff = build_diff(before, after)
    removed_count = sum(1 for d in diff if d["status"] == "removed")

    size_diff_kb = round((before_size - after_size) / 1024, 2)
    size_diff_pct = round((size_diff_kb / (before_size / 1024)) * 100, 2) if before_size > 0 else 0

    return {
        "filename": filename,
        "before": before,
        "after": after,
        "diff": diff,
        "risk": compute_risk(before),
        "categories_before": categorize_metadata(before),
        "categories_after": categorize_metadata(after),
        "fields_removed": removed_count,
        "metadata_comparison": metadata_comparison,
        "original_size": before_size,
        "cleaned_size": after_size,
        "size_reduction_kb": size_diff_kb,
        "size_reduction_pct": size_diff_pct,
    }


def process_batch(
    file_paths: list[str],
    session_id: str,
    preset: str,
    custom_fields: list[str] | None = None,
) -> dict:
    """
    Process multiple files and zip the results.

    Returns:
        Dict with keys: results (per-file), zip_path, total_removed.
    """
    results = []
    total_removed = 0

    for path in file_paths:
        try:
            result = process_file(path, preset, custom_fields)
            results.append({"success": True, **result})
            total_removed += result["fields_removed"]
        except CleaningError as exc:
            results.append({
                "success": False,
                "filename": Path(path).name,
                "error": str(exc),
            })
            logger.warning("Failed to clean '%s': %s", path, exc)

    cleaned_dir = os.path.dirname(file_paths[0]) if file_paths else ""
    zip_path = make_zip(session_id, cleaned_dir) if cleaned_dir else None

    return {
        "results": results,
        "zip_path": zip_path,
        "total_removed": total_removed,
        "file_count": len(file_paths),
        "success_count": sum(1 for r in results if r["success"]),
    }
