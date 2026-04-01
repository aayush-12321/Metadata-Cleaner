"""
REST API v1 - programmatic access for developers.
All routes are prefixed /api/v1/ via the blueprint url_prefix.
"""

from flask import Blueprint, request, jsonify, current_app

from ..services.exiftool import extract_metadata, ExifToolError
from ..services.metadata import filter_metadata, categorize_metadata, compute_risk
from ..services.cleaner import get_preset_flags

api_bp = Blueprint("api", __name__)


@api_bp.route("/supported-types", methods=["GET"])
def supported_types():
    """Return sorted list of supported file extensions."""
    return jsonify({
        "extensions": sorted(current_app.config["ALLOWED_EXTENSIONS"]),
        "count": len(current_app.config["ALLOWED_EXTENSIONS"]),
    })


@api_bp.route("/presets", methods=["GET"])
def list_presets():
    """Return available cleaning presets and their ExifTool flags."""
    presets = current_app.config["CLEANING_PRESETS"]
    return jsonify({
        "presets": {name: flags for name, flags in presets.items()},
        "note": "Use 'custom' preset with a 'fields' array to target specific tags.",
    })


@api_bp.route("/metadata", methods=["POST"])
def api_get_metadata():
    """
    Extract metadata from an uploaded file.

    Form fields:
        file (required): the file to inspect.
    """
    import os
    from ..utils.validators import validate_upload, safe_filename
    from ..utils.file_utils import new_session_dir, remove_session

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided."}), 400

    valid, err = validate_upload(file)
    if not valid:
        return jsonify({"error": err}), 400

    session_id, upload_dir = new_session_dir()
    filename = safe_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    try:
        raw = extract_metadata(file_path)
        filtered = filter_metadata(raw)
        return jsonify({
            "filename": filename,
            "metadata": filtered,
            "categories": categorize_metadata(filtered),
            "risk": compute_risk(filtered),
            "field_count": len(filtered),
        })
    except ExifToolError as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        remove_session(session_id)


@api_bp.route("/validate-preset", methods=["POST"])
def validate_preset():
    """Validate a preset name and return the resolved ExifTool flags."""
    data = request.get_json(silent=True) or {}
    preset = data.get("preset", "full")
    custom_fields = data.get("fields", [])

    try:
        flags = get_preset_flags(preset, custom_fields or None)
        return jsonify({"preset": preset, "flags": flags})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
