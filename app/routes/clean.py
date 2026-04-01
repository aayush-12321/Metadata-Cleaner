"""
/process_files  - clean uploaded files and return download.
/download/<id>  - serve a previously cleaned session's zip.
"""

import os
from flask import Blueprint, request, send_file, jsonify, after_this_request, current_app, url_for, abort

from ..services.cleaner import process_batch, CleaningError
from ..utils.validators import validate_upload, safe_filename
from ..utils.file_utils import new_session_dir, remove_session, session_dir

clean_bp = Blueprint("clean", __name__)


@clean_bp.route("/process_files", methods=["POST"])
def process_files():
    files = request.files.getlist("files")
    max_files = current_app.config["MAX_FILES"]

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files received."}), 400

    if len(files) > max_files:
        return jsonify({"error": f"Maximum {max_files} files per batch."}), 400

    preset = request.form.get("preset", "full")
    custom_raw = request.form.get("custom_fields", "")
    custom_fields = [f.strip() for f in custom_raw.split(",") if f.strip()] or None

    session_id, upload_dir = new_session_dir()
    saved_paths = []

    for file in files:
        if file.filename == "":
            continue

        valid, err = validate_upload(file)
        if not valid:
            remove_session(session_id)
            return jsonify({"error": err}), 400

        filename = safe_filename(file.filename)
        path = os.path.join(upload_dir, filename)
        file.save(path)
        saved_paths.append(path)

    if not saved_paths:
        remove_session(session_id)
        return jsonify({"error": "No valid files to process."}), 400

    try:
        batch = process_batch(saved_paths, session_id, preset, custom_fields)
    except CleaningError as exc:
        remove_session(session_id)
        return jsonify({"error": str(exc)}), 500

    is_json = request.args.get("json") == "1" or request.headers.get("Accept", "").startswith("application/json")
    if is_json:
        return jsonify({
            "session_id": session_id,
            "download_url": url_for("clean.download_session", session_id=session_id, _external=False),
            "batch": batch,
        })

    # Single file: serve directly
    if len(saved_paths) == 1 and batch["success_count"] == 1:
        file_to_send = saved_paths[0]

        @after_this_request
        def cleanup_single(response):
            remove_session(session_id)
            return response

        return send_file(file_to_send, as_attachment=True)

    # Multiple files or partial failures: serve zip
    zip_path = batch.get("zip_path")
    if not zip_path or not os.path.exists(zip_path):
        remove_session(session_id)
        return jsonify({"error": "Failed to create download archive."}), 500

    if request.args.get("json") == "1" or request.headers.get("Accept", "").startswith("application/json"):
        return jsonify({
            "session_id": session_id,
            "download_url": url_for("clean.download_session", session_id=session_id, _external=False),
            "batch": batch,
        })

    @after_this_request
    def cleanup_batch(response):
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as exc:
            current_app.logger.warning("Could not remove zip %s: %s", zip_path, exc)
        remove_session(session_id)
        return response

    return send_file(zip_path, as_attachment=True, download_name="cleaned_files.zip")


@clean_bp.route("/download/<session_id>", methods=["GET"])
def download_session(session_id):
    zip_path = os.path.join(current_app.config["UPLOAD_BASE_DIR"], f"cleaned_{session_id}.zip")
    if not os.path.exists(zip_path):
        abort(404)

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as exc:
            current_app.logger.warning("Could not remove zip %s: %s", zip_path, exc)
        remove_session(session_id)
        return response

    return send_file(zip_path, as_attachment=True, download_name="cleaned_files.zip")
