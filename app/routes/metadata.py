"""
/get_metadata  - single-file metadata preview (AJAX, returns JSON).
"""

import os
from flask import Blueprint, request, jsonify, current_app

from ..services.exiftool import extract_metadata, ExifToolError
from ..services.metadata import filter_metadata, categorize_metadata, compute_risk
from ..utils.validators import validate_upload, safe_filename
from ..utils.file_utils import new_session_dir, remove_session

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route("/get_metadata", methods=["POST"])
def get_metadata():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "No file received."}), 400

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
        categories = categorize_metadata(filtered)
        risk = compute_risk(filtered)

        return jsonify({
            "filename": filename,
            "metadata": filtered,
            "categories": categories,
            "risk": risk,
            "field_count": len(filtered),
        })

    except ExifToolError as exc:
        current_app.logger.error("ExifTool error for '%s': %s", filename, exc)
        return jsonify({"error": str(exc)}), 500

    finally:
        remove_session(session_id)
