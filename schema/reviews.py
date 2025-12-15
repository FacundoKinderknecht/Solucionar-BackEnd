from __future__ import annotations

from datetime import datetime
from sqlmodel import SQLModel, Field, UniqueConstraint
from pydantic import Field as PydanticField, ConfigDict


class ReservationReview(SQLModel, table=True):
    __tablename__ = "reservation_reviews"
    __table_args__ = (UniqueConstraint("reservation_id", name="uq_review_reservation"),)

    id: int | None = Field(default=None, primary_key=True)
    reservation_id: int = Field(foreign_key="reservations.id", index=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)


class ReservationReviewCreate(SQLModel):
    reservation_id: int
    rating: int = PydanticField(ge=1, le=5)
    comment: str | None = PydanticField(default=None, max_length=1000)


class ReservationReviewPublic(SQLModel):
    id: int
    reservation_id: int
    service_id: int
    client_id: int
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReservationReviewSummary(SQLModel):
    service_id: int
    average: float
    count: int
