import os
from pydantic import BaseModel

class Settings(BaseModel):
    """Configuration loaded from environment variables."""
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "3001"))
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "devicesdb")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # PUBLIC_INTERFACE
    @staticmethod
    def load_from_env() -> "Settings":
        """Load settings from environment variables with defaults."""
        return Settings()
