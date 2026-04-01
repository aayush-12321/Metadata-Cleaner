from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    allowed_extensions = sorted(current_app.config["ALLOWED_EXTENSIONS"])
    allowed_extensions_csv = ",".join(f".{ext}" for ext in allowed_extensions)

    return render_template(
        "upload.html",
        page_title=current_app.config["PAGE_TITLE"],
        max_file_size_mb=current_app.config["MAX_FILE_SIZE_MB"],
        max_files=current_app.config["MAX_FILES"],
        support_message=current_app.config["SUPPORT_MESSAGE"],
        allowed_extensions=allowed_extensions,
        allowed_extensions_csv=allowed_extensions_csv,
    )


@main_bp.route("/health")
def health():
    from flask import jsonify
    return jsonify({"status": "ok"})
