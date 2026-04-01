"""
Filesystem helpers: session directory management and temp file cleanup.
"""

import os
import shutil
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)


def new_session_dir() -> tuple[str, str]:
    """
    Create a unique temporary directory for one upload session.

    Returns:
        (session_id, absolute_path)
    """
    session_id = str(uuid.uuid4())
    path = os.path.join(current_app.config["UPLOAD_BASE_DIR"], session_id)
    os.makedirs(path, exist_ok=True)
    return session_id, path


def session_dir(session_id: str) -> str:
    """Return the absolute path for a given session ID."""
    return os.path.join(current_app.config["UPLOAD_BASE_DIR"], session_id)


def remove_session(session_id: str) -> None:
    """Silently remove a session directory and all its contents."""
    path = session_dir(session_id)
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except Exception as exc:
        logger.warning("Failed to remove session %s: %s", session_id, exc)


def make_zip(session_id: str, source_dir: str) -> str:
    """
    Zip all files in source_dir and save the archive next to it.

    Returns:
        Absolute path to the created .zip file.
    """
    zip_name = f"cleaned_{session_id}"
    zip_base = os.path.join(current_app.config["UPLOAD_BASE_DIR"], zip_name)
    shutil.make_archive(zip_base, "zip", source_dir)
    return zip_base + ".zip"


def cleanup_old_sessions(ttl_minutes: int | None = None) -> int:
    """
    Delete session directories older than ttl_minutes.
    Intended to be called by a background scheduler.

    Returns:
        Number of sessions removed.
    """
    ttl = ttl_minutes or current_app.config.get("SESSION_TTL_MINUTES", 30)
    base = current_app.config["UPLOAD_BASE_DIR"]
    cutoff = datetime.utcnow() - timedelta(minutes=ttl)
    removed = 0

    for entry in Path(base).iterdir():
        if not entry.is_dir():
            continue
        try:
            mtime = datetime.utcfromtimestamp(entry.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(entry)
                removed += 1
        except Exception as exc:
            logger.warning("Could not clean up %s: %s", entry, exc)

    return removed
