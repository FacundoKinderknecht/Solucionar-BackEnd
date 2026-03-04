"""Pydantic request/response schemas for the reviews domain."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class ReviewCreate(SQLModel):
    """Input schema for submitting a review for a completed reservation."""

    reservation_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewPublic(SQLModel):
    """Public representation of a single review."""

    id: int
    reservation_id: int
    service_id: int
    client_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewSummary(SQLModel):
    """Aggregated rating statistics for a service."""

    service_id: int
    average: float
    count: int
