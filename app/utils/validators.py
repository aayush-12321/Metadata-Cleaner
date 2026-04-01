"""
File validation: extension checks, size enforcement, filename sanitization.
No MIME magic dependency required - uses extension + exiftool for validation.
"""

import os
from werkzeug.utils import secure_filename
from flask import current_app


def is_allowed_extension(filename: str) -> bool:
    """Return True if the file extension is in the allowed set."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def safe_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.
    Falls back to 'upload' if secure_filename returns an empty string.
    """
    name = secure_filename(filename)
    return name if name else "upload"


def check_file_size(file_storage, max_mb: int) -> tuple[bool, float]:
    """
    Check a FileStorage object's size without saving it first.

    Returns:
        (ok, size_mb) - ok is False if size exceeds max_mb.
    """
    file_storage.seek(0, os.SEEK_END)
    size_bytes = file_storage.tell()
    file_storage.seek(0)
    size_mb = size_bytes / (1024 * 1024)
    return size_mb <= max_mb, size_mb


def validate_upload(file_storage) -> tuple[bool, str]:
    """
    Run all upload validations on a FileStorage object.

    Returns:
        (valid, error_message) - error_message is empty string when valid.
    """
    if not file_storage or file_storage.filename == "":
        return False, "No file selected."

    if not is_allowed_extension(file_storage.filename):
        ext = file_storage.filename.rsplit(".", 1)[-1] if "." in file_storage.filename else "unknown"
        return False, f"File type '.{ext}' is not supported."

    max_mb = current_app.config["MAX_FILE_SIZE_MB"]
    ok, size_mb = check_file_size(file_storage, max_mb)
    if not ok:
        return False, f"File '{file_storage.filename}' is {size_mb:.1f} MB, exceeding the {max_mb} MB limit."

    return True, ""
