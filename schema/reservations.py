from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from enum import Enum

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import Mapped

if TYPE_CHECKING:
    from .services import Service
    from .users import User

class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_PROVIDER = "cancelled_by_provider"
    COMPLETED = "completed"

class ReservationBase(SQLModel):
    service_id: int = Field(foreign_key="services.id")
    reservation_datetime: datetime
    notes: str | None = None

class Reservation(ReservationBase, table=True):
    __tablename__ = "reservations"

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    status: ReservationStatus = Field(default=ReservationStatus.PENDING, index=True)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)

    # Relationships
    client: Mapped[User] = Relationship(back_populates="reservations")
    service: Mapped[Service] = Relationship(back_populates="reservations")

# --- Schemas for API ---

class ReservationCreate(ReservationBase):
    pass

class ReservationPublic(ReservationBase):
    id: int
    client_id: int
    status: ReservationStatus
    created_at: datetime