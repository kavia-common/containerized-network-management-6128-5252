from typing import Optional, Literal
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator

DeviceType = Literal["router", "switch", "server"]
DeviceStatus = Literal["online", "offline"]

class DeviceCreate(BaseModel):
    """Schema for creating a device."""
    name: str = Field(..., description="Device name")
    ip_address: IPvAnyAddress = Field(..., description="IPv4 address")
    type: DeviceType = Field(..., description="Device type")
    location: str = Field(..., description="Device location")
    status: Optional[DeviceStatus] = Field(default="offline", description="Initial status")

class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    name: str = Field(..., description="Device name")
    ip_address: IPvAnyAddress = Field(..., description="IPv4 address")
    type: DeviceType = Field(..., description="Device type")
    location: str = Field(..., description="Device location")
    status: DeviceStatus = Field(..., description="Status")

class DeviceOut(BaseModel):
    """Schema returned to clients."""
    id: str = Field(..., description="String ID")
    name: str
    ip_address: str
    type: DeviceType
    location: str
    status: Optional[DeviceStatus] = "offline"
