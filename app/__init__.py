"""
Metadata Cleaner - Application Factory
"""

import os
import logging
from flask import Flask
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    _configure_logging(app)
    _ensure_directories(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    return app


def _configure_logging(app: Flask) -> None:
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


def _ensure_directories(app: Flask) -> None:
    os.makedirs(app.config["UPLOAD_BASE_DIR"], exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    from .routes.main import main_bp
    from .routes.metadata import metadata_bp
    from .routes.clean import clean_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(metadata_bp)
    app.register_blueprint(clean_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")


def _register_error_handlers(app: Flask) -> None:
    from flask import jsonify, render_template

    @app.errorhandler(413)
    def file_too_large(e):
        if _wants_json():
            return jsonify({"error": "File too large"}), 413
        return render_template("error.html", message="File exceeds the maximum allowed size."), 413

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({"error": "Not found"}), 404
        return render_template("error.html", message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        if _wants_json():
            return jsonify({"error": "Internal server error"}), 500
        return render_template("error.html", message="Something went wrong. Please try again."), 500


def _wants_json() -> bool:
    from flask import request
    return request.path.startswith("/api/")
