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

# ================= MODELOS =================


# ================ OPERADOR ================

class Operator(Base):
    # Granjero o responsable del grupo de animales.

    __tablename__ = "operators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="operator"
    )  # "admin" | "operator" | "vet"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relaciones
    livestock: Mapped[list["Livestock"]] = relationship(
        back_populates="operator", lazy="selectin"
    )
    grazing_lots: Mapped[list["GrazingLot"]] = relationship(
        back_populates="operator", lazy="selectin"
    )

# ================ LOTE ================
class GrazingLot(Base):
    """ Un sección de campo limitada (lote).
    """

    __tablename__ = "grazing_lots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # relaciones
    operator: Mapped[Optional["Operator"]] = relationship(back_populates="grazing_lots")
    
    
# ================ GANADO ================
class Livestock(Base):
    # Un animal perteneciente al rebaño.

    __tablename__ = "livestock"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # relaciones
    operator: Mapped[Optional["Operator"]] = relationship(back_populates="livestock")