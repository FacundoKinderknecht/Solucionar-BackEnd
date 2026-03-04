"""SQLModel table definition for the Reservation entity."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Annotated, List, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.service import Service
    from app.models.user import User


class ReservationStatus(str, Enum):
    """Lifecycle states of a reservation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_PROVIDER = "cancelled_by_provider"
    COMPLETED = "completed"


class Reservation(SQLModel, table=True):
    """A booking made by a client for a specific service at a specific time."""

    __tablename__ = "reservations"

    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    reservation_datetime: datetime
    notes: Optional[str] = None
    status: ReservationStatus = Field(
        default=ReservationStatus.PENDING,
        sa_column=Column(
            SAEnum(
                ReservationStatus,
                name="reservationstatus",
                native_enum=True,
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            index=True,
            server_default=ReservationStatus.PENDING.value,
        ),
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    client: Optional[Annotated["User", Relationship(back_populates="reservations")]] = Relationship(
        back_populates="reservations",
        sa_relationship=relationship("User", back_populates="reservations"),
    )
    service: Optional[Annotated["Service", Relationship(back_populates="reservations")]] = Relationship(
        back_populates="reservations",
        sa_relationship=relationship("Service", back_populates="reservations"),
    )
    payments: Optional[List["Payment"]] = Relationship(
        back_populates="reservation",
        sa_relationship=relationship("Payment", back_populates="reservation"),
    )
