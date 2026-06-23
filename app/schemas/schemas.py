import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

# USER
class UserBase(BaseModel):
    name: str = Field(..., max_length=120)
    email: EmailStr
    role: str = Field("user", pattern="^(admin|user|vet)$")
    country: str = Field(..., max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# GROUND
class GroundBase(BaseModel):
    name: str = Field(..., max_length=120)
    geofence: Optional[str] = None      # GeoJSON Polygon string
    area_hectares: Optional[float] = None
    users_id: Optional[uuid.UUID] = None


class GroundCreate(GroundBase):
    pass


class GroundRead(GroundBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ANIMAL
class AnimalBase(BaseModel):
    species: str = Field(..., max_length=80)
    birth_date: Optional[datetime] = None
    sex: str = Field(..., pattern="^(M|F)$")
    weight_kg: Optional[float] = None
    user_id: Optional[uuid.UUID] = None


class AnimalCreate(AnimalBase):
    pass


class AnimalRead(AnimalBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
    

# HEALTH ALERT 
class HealthAlertBase(BaseModel):
    animal_id: uuid.UUID
    alert_type: str = Field(..., max_length=50)
    pattern_label: Optional[str] = Field(None, max_length=100)
    similarity_score: Optional[float] = Field(None, ge=0, le=1)
    message: str


class HealthAlertCreate(HealthAlertBase):
    pass


class HealthAlertRead(HealthAlertBase):
    id: uuid.UUID
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# DEVICE
class DeviceBase(BaseModel):
    hardware_id: str = Field(..., max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=30)
    animal_id: Optional[uuid.UUID] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceRead(DeviceBase):
    id: uuid.UUID
    battery_pct: Optional[float] = None
    last_seen: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceTelemetryUpdate(BaseModel):
    """Payload sent by the ESP32 on each telemetry ping."""
    battery_pct: Optional[float] = Field(None, ge=0, le=100)


# TELEMETRÍA (MongoDB) 

class AccelerometerReading(BaseModel):
    x: float
    y: float
    z: float


class TelemetryIngest(BaseModel):
    device_hardware_id: str
    timestamp: datetime
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    altitude_m: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    accel: AccelerometerReading
    battery_pct: Optional[float] = Field(None, ge=0, le=100)


class TelemetryRead(TelemetryIngest):
    id: str               
    animal_id: Optional[str] = None
