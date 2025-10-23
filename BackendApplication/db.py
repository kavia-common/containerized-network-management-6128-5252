from typing import Optional, Tuple
from pymongo import MongoClient, errors
from config import Settings

_client: Optional[MongoClient] = None

def _get_client() -> Optional[MongoClient]:
    global _client
    if _client is not None:
        return _client
    settings = Settings.load_from_env()
    try:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1000)
        # Test connection
        _client.admin.command("ping")
        return _client
    except Exception:
        # Leave client as None; caller handles unavailability
        _client = None
        return None

# PUBLIC_INTERFACE
def get_db():
    """Return MongoDB database handle or None if unavailable."""
    client = _get_client()
    if not client:
        return None
    settings = Settings.load_from_env()
    return client.get_database(settings.MONGODB_DB)

# PUBLIC_INTERFACE
def is_db_available() -> Tuple[bool, Optional[str]]:
    """Check if database is reachable; returns (ok, error_message)."""
    try:
        client = _get_client()
        if not client:
            return False, "MongoDB client unavailable"
        client.admin.command("ping")
        return True, None
    except errors.PyMongoError as e:
        return False, str(e)

# PUBLIC_INTERFACE
def ensure_indexes():
    """Ensure required indexes exist on the devices collection."""
    db = get_db()
    if not db:
        return
    devices = db.get_collection("devices")
    # Unique index on ip_address
    devices.create_index("ip_address", unique=True)
    # Common query helpers
    devices.create_index("type")
    devices.create_index("status")
