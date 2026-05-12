import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── User ──────────────────────────────────────────────────────────────────

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


# ── Ground ────────────────────────────────────────────────────────────────

class GroundBase(BaseModel):
    name: str = Field(..., max_length=120)
    geofence: Optional[str] = None      # GeoJSON Polygon string
    area_hectares: Optional[float] = None
    user_id: Optional[uuid.UUID] = None


class GroundCreate(GroundBase):
    pass


class GroundRead(GroundBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Animal ─────────────────────────────────────────────────────────────────

class AnimalBase(BaseModel):
    tag: str = Field(..., max_length=50, description="Unique ear-tag or RFID number")
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

