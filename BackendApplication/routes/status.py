from datetime import datetime
from flask import Blueprint, jsonify
from bson.objectid import ObjectId
from db import get_db, is_db_available
from utils.errors import ApiError

status_bp = Blueprint("status", __name__)

@status_bp.get("/devices/<id>/status")
def get_status(id: str):
    """Get device status (simulated)."""
    ok, err = is_db_available()
    if not ok:
        raise ApiError(503, "Database unavailable", err)
    db = get_db()
    coll = db.get_collection("devices")
    try:
        doc = coll.find_one({"_id": ObjectId(id)})
    except Exception:
        doc = None
    if not doc:
        raise ApiError(404, "Device not found")
    # Simulate by returning stored status
    status = doc.get("status", "offline")
    return jsonify({
        "success": True,
        "data": {
            "status": status,
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    }), 200
