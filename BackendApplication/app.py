import os
import re
import json
import platform
import subprocess
from datetime import datetime
from typing import Optional, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from pymongo import MongoClient, ASCENDING, errors
except Exception:  # pragma: no cover - if not installed in some envs
    MongoClient = None
    errors = None

# PUBLIC_INTERFACE
def create_app():
    """Create and configure the Flask application.

    Returns:
        Flask: Configured Flask app with routes registered.
    """
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": cors_origins}})

    # Database setup
    db, db_available, db_error = init_db()

    # Ensure indexes if DB available
    if db_available:
        try:
            db.devices.create_index([("ip_address", ASCENDING)], name="unique_ip", unique=True)
        except Exception:
            pass

    # PUBLIC_INTERFACE
    @app.get("/health")
    def health():
        """Health check endpoint.

        Returns:
            JSON with application health and DB availability status.
        """
        return jsonify({
            "success": True,
            "service": "BackendApplication",
            "db_available": db_available and (db is not None),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    # PUBLIC_INTERFACE
    @app.get("/api/v1/devices")
    def list_devices():
        """List all devices.

        Returns:
            200: JSON object { success, data: [Device] }
            503: if database is unavailable.
        """
        if not db_available or db is None:
            return error_response("Database unavailable", 503)
        try:
            docs = list(db.devices.find({}))
            data = [serialize_device(d) for d in docs]
            return jsonify({"success": True, "data": data}), 200
        except Exception as e:
            return error_response(f"Failed to fetch devices: {e}", 500)

    # PUBLIC_INTERFACE
    @app.post("/api/v1/devices")
    def create_device():
        """Create a new device.

        Body:
            JSON with name, ip_address, type, location, status (optional default offline)

        Returns:
            201: { success, data: Device }
            400: Validation error
            409: Duplicate IP
            503: DB unavailable
        """
        if not db_available or db is None:
            return error_response("Database unavailable", 503)
        payload = request.get_json(silent=True) or {}
        ok, msg = validate_device_payload(payload, require_status=False)
        if not ok:
            return error_response(msg, 400)
        if "status" not in payload:
            payload["status"] = "offline"
        try:
            res = db.devices.insert_one({
                "name": payload["name"],
                "ip_address": payload["ip_address"],
                "type": payload["type"],
                "location": payload["location"],
                "status": payload["status"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            doc = db.devices.find_one({"_id": res.inserted_id})
            return jsonify({"success": True, "data": serialize_device(doc)}), 201
        except Exception as e:
            if "duplicate key" in str(e).lower():
                return error_response("Device with this IP already exists", 409)
            return error_response(f"Failed to create device: {e}", 500)

    # PUBLIC_INTERFACE
    @app.get("/api/v1/devices/<id>")
    def get_device(id):
        """Get device details by id.

        Path:
            id: string ObjectId or custom id

        Returns:
            200: { success, data: Device }
            404: Not found
            503: DB unavailable
        """
        if not db_available or db is None:
            return error_response("Database unavailable", 503)
        doc = find_device_by_any_id(db, id)
        if not doc:
            return error_response("Device not found", 404)
        return jsonify({"success": True, "data": serialize_device(doc)}), 200

    # PUBLIC_INTERFACE
    @app.put("/api/v1/devices/<id>")
    def update_device(id):
        """Update a device.

        Body:
            JSON with required fields: name, ip_address, type, location, status

        Returns:
            200: { success, data: Device }
            400: Validation error
            404: Not found
            409: Duplicate IP
            503: DB unavailable
        """
        if not db_available or db is None:
            return error_response("Database unavailable", 503)
        payload = request.get_json(silent=True) or {}
        ok, msg = validate_device_payload(payload, require_status=True)
        if not ok:
            return error_response(msg, 400)
        doc = find_device_by_any_id(db, id)
        if not doc:
            return error_response("Device not found", 404)
        try:
            # ensure unique IP not conflicting with other devices
            other = db.devices.find_one({"ip_address": payload["ip_address"], "_id": {"$ne": doc["_id"]}})
            if other:
                return error_response("Device with this IP already exists", 409)
            db.devices.update_one({"_id": doc["_id"]}, {"$set": {
                "name": payload["name"],
                "ip_address": payload["ip_address"],
                "type": payload["type"],
                "location": payload["location"],
                "status": payload["status"],
                "updated_at": datetime.utcnow(),
            }})
            doc = db.devices.find_one({"_id": doc["_id"]})
            return jsonify({"success": True, "data": serialize_device(doc)}), 200
        except Exception as e:
            return error_response(f"Failed to update device: {e}", 500)

    # PUBLIC_INTERFACE
    @app.delete("/api/v1/devices/<id>")
    def delete_device(id):
        """Delete a device.

        Returns:
            204: No Content on success
            404: Not found
            503: DB unavailable
        """
        if not db_available or db is None:
            return error_response("Database unavailable", 503)
        doc = find_device_by_any_id(db, id)
        if not doc:
            return error_response("Device not found", 404)
        try:
            db.devices.delete_one({"_id": doc["_id"]})
            return ("", 204)
        except Exception as e:
            return error_response(f"Failed to delete device: {e}", 500)

    # PUBLIC_INTERFACE
    @app.get("/api/v1/devices/<id>/status")
    def device_status(id):
        """Check device online/offline status by attempting a platform ping with short timeout.

        Returns:
            200: { success, data: { status: 'online'|'offline' } }
            404: Device not found
            200: If DB unavailable, tries to parse IP from id (if it's IP), otherwise returns unknown offline.
        """
        ip = None
        device = None
        if db_available and db is not None:
            device = find_device_by_any_id(db, id)
            if not device:
                return error_response("Device not found", 404)
            ip = device.get("ip_address")
        else:
            # degrade gracefully if DB is down
            if is_ipv4(id):
                ip = id

        status = "offline"
        if ip:
            ok = ping_host(ip, timeout=2.5)
            status = "online" if ok else "offline"

        # optionally log status if DB available
        if db_available and db is not None and device:
            try:
                db.devices.update_one({"_id": device["_id"]}, {"$set": {"status": status, "updated_at": datetime.utcnow()}})
            except Exception:
                pass

        return jsonify({"success": True, "data": {"status": status}}), 200

    # PUBLIC_INTERFACE
    @app.get("/api/v1")
    def api_root():
        """API root provides basic info."""
        return jsonify({
            "success": True,
            "message": "Backend API Root",
            "endpoints": ["/api/v1/devices", "/api/v1/devices/{id}", "/api/v1/devices/{id}/status", "/health", "/openapi.json", "/docs"],
        })

    # Serve OpenAPI spec generated inline from this implementation (minimal)
    # PUBLIC_INTERFACE
    @app.get("/openapi.json")
    def openapi():
        """Return OpenAPI spec for the API."""
        spec = get_openapi_spec()
        return jsonify(spec)

    # PUBLIC_INTERFACE
    @app.get("/docs")
    def docs():
        """Very small docs pointer."""
        return jsonify({"success": True, "docs": "/openapi.json"})

    return app


def is_ipv4(val: str) -> bool:
    return re.match(r"^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$", val or "") is not None


def ping_host(host: str, timeout: float = 2.0) -> bool:
    """Attempt to ping a host using system ping with a short timeout."""
    try:
        count_flag = "-n" if platform.system().lower().startswith("win") else "-c"
        timeout_flag = "-w" if platform.system().lower().startswith("win") else "-W"
        cmd = ["ping", count_flag, "1", timeout_flag, str(int(timeout)), host]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False


def validate_device_payload(payload: dict, require_status: bool) -> Tuple[bool, str]:
    """Validate device payload fields."""
    required = ["name", "ip_address", "type", "location"]
    if require_status:
        required.append("status")
    for k in required:
        if k not in payload or payload.get(k) in (None, ""):
            return False, f"{k} is required"
    if not is_ipv4(payload.get("ip_address", "")):
        return False, "ip_address must be valid IPv4"
    if payload.get("type") not in ["router", "switch", "server"]:
        return False, "type must be one of router, switch, server"
    if require_status and payload.get("status") not in ["online", "offline"]:
        return False, "status must be one of online, offline"
    return True, ""


def serialize_device(doc: dict) -> dict:
    """Serialize Mongo document to API Device."""
    if not doc:
        return {}
    _id = str(doc.get("_id"))
    return {
        "id": _id,
        "name": doc.get("name"),
        "ip_address": doc.get("ip_address"),
        "type": doc.get("type"),
        "location": doc.get("location"),
        "status": doc.get("status") or "offline",
    }


def init_db():
    """Initialize MongoDB connection from environment variables.

    Returns:
        (db, db_available, db_error)
    """
    uri = os.getenv("MONGODB_URI")
    if not uri:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "27017")
        dbname = os.getenv("DB_NAME", "devicesdb")
        user = os.getenv("DB_USER")
        pwd = os.getenv("DB_PASS")
        if user and pwd:
            uri = f"mongodb://{user}:{pwd}@{host}:{port}/{dbname}"
        else:
            uri = f"mongodb://{host}:{port}/{dbname}"
    try:
        if MongoClient is None:
            return None, False, "pymongo not installed"
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        # attempt to connect
        client.admin.command("ping")
        return client.get_database(), True, None
    except Exception as e:
        return None, False, str(e)


def get_openapi_spec():
    """Build a minimal OpenAPI spec matching endpoints implemented."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Backend REST API",
            "version": "1.0.0",
            "description": "RESTful API for device management and status checks.",
        },
        "servers": [{"url": "/api/v1"}],
        "paths": {
            "/devices": {
                "get": {"summary": "List all devices", "responses": {"200": {"description": "OK"}}},
                "post": {"summary": "Create device", "responses": {"201": {"description": "Created"}}},
            },
            "/devices/{id}": {
                "get": {"summary": "Get device", "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}, "404": {"description": "Not Found"}}},
                "put": {"summary": "Update device", "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
                "delete": {"summary": "Delete device", "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"204": {"description": "No Content"}}},
            },
            "/devices/{id}/status": {
                "get": {"summary": "Device status", "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
            },
        },
        "components": {},
        "tags": [{"name": "Devices"}],
    }


def error_response(message: str, status: int = 400):
    """Standard error payload."""
    return jsonify({"success": False, "error": message}), status


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "3001"))
    app.run(host="0.0.0.0", port=port)
