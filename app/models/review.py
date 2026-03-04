"""SQLModel table definition for the ReservationReview entity."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class ReservationReview(SQLModel, table=True):
    """A rating and optional comment left by a client after a completed reservation.

    Enforces one review per reservation via a unique constraint.
    """

    __tablename__ = "reservation_reviews"
    __table_args__ = (UniqueConstraint("reservation_id", name="uq_review_reservation"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    reservation_id: int = Field(foreign_key="reservations.id", index=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    # Rating from 1 (lowest) to 5 (highest).
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
