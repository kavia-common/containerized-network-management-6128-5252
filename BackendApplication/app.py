import os
from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix
from utils.logging_conf import configure_logging
from utils.errors import register_error_handlers, ApiError
from config import Settings
from db import get_db, ensure_indexes, is_db_available
from routes.devices import devices_bp
from routes.status import status_bp

# PUBLIC_INTERFACE
def create_app() -> Flask:
    """Create and configure the Flask app with routes, error handling, and DB integration."""
    settings = Settings.load_from_env()
    configure_logging(level=settings.LOG_LEVEL)
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore

    # Health endpoint that works even when DB is down
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint.
        Returns basic reachability and DB availability info.
        """
        ok, err = is_db_available()
        return jsonify({
            "success": True,
            "service": "backend",
            "db_available": ok,
            "error": err
        }), 200

    # Initialize DB and ensure indexes if available
    ok, _ = is_db_available()
    if ok:
        ensure_indexes()

    # API Blueprint mounting
    api_prefix = settings.API_PREFIX
    app.register_blueprint(devices_bp, url_prefix=api_prefix)
    app.register_blueprint(status_bp, url_prefix=api_prefix)

    # OpenAPI spec and docs endpoints
    @app.get(f"{api_prefix}/openapi.json")
    def openapi_json():
        """Serve the OpenAPI spec as JSON."""
        from flask import Response
        from pathlib import Path
        spec_path = Path(__file__).parent / "openapi.yaml"
        try:
            import yaml
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = yaml.safe_load(f)
            return jsonify(spec)
        except Exception as e:
            return jsonify({"success": False, "error": f"Unable to load OpenAPI: {e}"}), 500

    @app.get(f"{api_prefix}/docs")
    def docs():
        """Simple Swagger UI redirection using unpkg CDN."""
        html = f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8"/>
          <title>API Docs</title>
          <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
        </head>
        <body>
          <div id="swagger-ui"></div>
          <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
          <script>
            window.onload = () => {{
              SwaggerUIBundle({{
                url: "{api_prefix}/openapi.json",
                dom_id: '#swagger-ui',
              }});
            }};
          </script>
        </body>
        </html>
        """
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}

    register_error_handlers(app)
    return app


if __name__ == "__main__":
    app = create_app()
    settings = Settings.load_from_env()
    app.run(host=settings.SERVER_HOST, port=settings.SERVER_PORT)
