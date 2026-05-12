import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.postgres import Base


# ================ USUARIOS ================

class User(Base):
    # Granjero o responsable del grupo de animales.

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="users"
    )  # "admin" | "granjero" | "veterinario"
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relaciones
    animal: Mapped[list["Animal"]] = relationship(
        back_populates="users", lazy="selectin"
    )
    ground: Mapped[list["Ground"]] = relationship(
        back_populates="users", lazy="selectin"
    )



# ================ LOTES DE PASTOREO ================

class Ground(Base):
    # Terreno de la granja, donde pastorean los animales
    
    __tablename__ = "ground"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    geofence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    area_hectares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    users_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relaciones
    users: Mapped[Optional["User"]] = relationship(back_populates="ground")


# ================ ANIMALES / GANADO ================

class Animal(Base):
    # Animal individual con sus datos

    __tablename__ = "animal"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    species: Mapped[str] = mapped_column(String(80), nullable=False) # 'vaca', 'oveja', 'cabra'
    birth_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sex: Mapped[str] = mapped_column(String(10), nullable=False)  # "M" | "F"
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    users_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relaciones
    users: Mapped[Optional["User"]] = relationship(back_populates="animal")
