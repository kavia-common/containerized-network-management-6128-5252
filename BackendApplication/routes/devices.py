from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from utils.errors import ApiError
from db import get_db, is_db_available
from models.device_schema import DeviceCreate, DeviceUpdate, DeviceOut

devices_bp = Blueprint("devices", __name__)

def _require_db():
    ok, err = is_db_available()
    if not ok:
        raise ApiError(status=503, message="Database unavailable", details=err)

def _to_out(doc) -> DeviceOut:
    return DeviceOut(
        id=str(doc["_id"]),
        name=doc["name"],
        ip_address=str(doc["ip_address"]),
        type=doc["type"],
        location=doc["location"],
        status=doc.get("status", "offline"),
    )

@devices_bp.get("/devices")
def list_devices():
    """List all devices."""
    _require_db()
    db = get_db()
    coll = db.get_collection("devices")
    items = [_to_out(d).model_dump() for d in coll.find({}).sort("name", 1)]
    return jsonify({"success": True, "data": items}), 200

@devices_bp.post("/devices")
def create_device():
    """Create a device."""
    _require_db()
    data = request.get_json(silent=True) or {}
    try:
        payload = DeviceCreate(**data)
    except Exception as e:
        raise ApiError(400, "Invalid input", str(e))
    db = get_db()
    coll = db.get_collection("devices")
    doc = {
        "name": payload.name,
        "ip_address": str(payload.ip_address),
        "type": payload.type,
        "location": payload.location,
        "status": payload.status or "offline",
    }
    try:
        res = coll.insert_one(doc)
    except DuplicateKeyError:
        raise ApiError(400, "Device with this IP already exists")
    doc["_id"] = res.inserted_id
    return jsonify({"success": True, "data": _to_out(doc).model_dump()}), 201

@devices_bp.get("/devices/<id>")
def get_device(id: str):
    """Get a single device."""
    _require_db()
    db = get_db()
    coll = db.get_collection("devices")
    try:
        doc = coll.find_one({"_id": ObjectId(id)})
    except Exception:
        doc = None
    if not doc:
        raise ApiError(404, "Device not found")
    return jsonify({"success": True, "data": _to_out(doc).model_dump()}), 200

@devices_bp.put("/devices/<id>")
def update_device(id: str):
    """Update a device."""
    _require_db()
    data = request.get_json(silent=True) or {}
    try:
        payload = DeviceUpdate(**data)
    except Exception as e:
        raise ApiError(400, "Invalid input", str(e))
    db = get_db()
    coll = db.get_collection("devices")
    try:
        res = coll.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": payload.name,
                "ip_address": str(payload.ip_address),
                "type": payload.type,
                "location": payload.location,
                "status": payload.status
            }},
            return_document=True
        )
    except DuplicateKeyError:
        raise ApiError(400, "Device with this IP already exists")
    if not res:
        raise ApiError(404, "Device not found")
    # fetch updated doc
    doc = coll.find_one({"_id": ObjectId(id)})
    return jsonify({"success": True, "data": _to_out(doc).model_dump()}), 200

@devices_bp.delete("/devices/<id>")
def delete_device(id: str):
    """Delete a device."""
    _require_db()
    db = get_db()
    coll = db.get_collection("devices")
    try:
        res = coll.delete_one({"_id": ObjectId(id)})
    except Exception:
        res = None
    if not res or res.deleted_count == 0:
        raise ApiError(404, "Device not found")
    return "", 204
