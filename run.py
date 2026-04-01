"""
Entry point for development and production (gunicorn/waitress).

Development:
    python run.py

Production (gunicorn):
    gunicorn "run:app" --workers 4 --bind 0.0.0.0:5000

Production (waitress, Windows):
    waitress-serve --port=5000 run:app
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port  = int(os.getenv("PORT", 5000))
    app.run(debug=debug, host="0.0.0.0", port=port)
