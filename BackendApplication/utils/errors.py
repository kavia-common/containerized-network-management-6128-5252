from flask import jsonify
from typing import Optional

class ApiError(Exception):
    """Custom API error with status and message."""
    def __init__(self, status: int, message: str, details: Optional[str] = None):
        self.status = status
        self.message = message
        self.details = details
        super().__init__(message)

def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        resp = {"success": False, "error": err.message}
        if err.details:
            resp["details"] = err.details
        return jsonify(resp), err.status

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"success": False, "error": "Not found"}), 404

    @app.errorhandler(400)
    def handle_400(_):
        return jsonify({"success": False, "error": "Bad request"}), 400

    @app.errorhandler(Exception)
    def handle_generic(err: Exception):
        return jsonify({"success": False, "error": str(err)}), 500
