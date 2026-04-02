from datetime import date

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
        current_page="home",
    )


@main_bp.route("/how-it-works")
def how_it_works():
    return render_template("how-it-works.html", page_title="How It Works", current_page="how-it-works")


@main_bp.route("/help")
def help():
    return render_template("help.html", page_title="Help", current_page="help")


@main_bp.route("/health")
def health():
    from flask import jsonify
    return jsonify({"status": "ok"})


@main_bp.route("/sitemap.xml")
def sitemap():
    from flask import Response

    lastmod = current_app.config.get('SITEMAP_LAST_MODIFIED', date.today().isoformat())
    domain_url = current_app.config.get('DOMAIN_URL', 'https://yoursite.com').rstrip('/')

    sitemap_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{domain_url}/</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{domain_url}/how-it-works</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{domain_url}/help</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>'''
    
    return Response(sitemap_content, mimetype="text/xml")


@main_bp.route('/robots.txt')
def robots_txt():
    from flask import send_from_directory
    # prefer direct static file if available
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')