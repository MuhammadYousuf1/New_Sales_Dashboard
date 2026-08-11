import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Render injects the port via the $PORT environment variable.
    # Default to a sane local value when not running on Render.
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    app.run(host=host, port=port, debug=debug)