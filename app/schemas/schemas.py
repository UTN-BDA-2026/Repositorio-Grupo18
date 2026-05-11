import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Operator ──────────────────────────────────────────────────────────────────

class OperatorBase(BaseModel):
    name: str = Field(..., max_length=120)
    email: EmailStr
    role: str = Field("operator", pattern="^(admin|operator|vet)$")


class OperatorCreate(OperatorBase):
    password: str = Field(..., min_length=8)


class OperatorRead(OperatorBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
