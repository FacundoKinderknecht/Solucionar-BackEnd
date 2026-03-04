"""Pydantic request/response schemas for the reservations domain."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.models.reservation import ReservationStatus
from app.schemas.review import ReviewPublic


class ReservationCreate(SQLModel):
    """Input schema for creating a reservation intent (used by the payment flow)."""

    service_id: int
    reservation_datetime: datetime
    notes: Optional[str] = None


class ReservationPublic(SQLModel):
    """Public representation of a reservation, optionally including its review."""

    id: int
    service_id: int
    client_id: int
    reservation_datetime: datetime
    notes: Optional[str] = None
    status: ReservationStatus
    created_at: datetime
    review: Optional[ReviewPublic] = None

    model_config = ConfigDict(from_attributes=True)


class ReservationStatusUpdate(SQLModel):
    """Input schema for advancing or cancelling a reservation's status."""

    status: ReservationStatus
