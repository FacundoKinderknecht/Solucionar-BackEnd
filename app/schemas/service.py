"""Pydantic request/response schemas for the service catalog domain."""
from __future__ import annotations

from datetime import date, time
from typing import Optional

from sqlmodel import SQLModel

from app.core.enums import TipoArea


class CategoryCreate(SQLModel):
    """Input schema for creating a service category."""

    name: str
    slug: str
    parent_id: Optional[int] = None


class ServiceCreate(SQLModel):
    """Input schema for publishing a new service listing."""

    category_id: int
    title: str
    description: str
    price: Optional[float] = None
    currency: str = "ARS"
    duration_min: int = 0
    area_type: TipoArea = TipoArea.PRESENCIAL
    location_note: Optional[str] = None
    price_to_agree: bool = False
    radius_km: Optional[float] = None
    availability_start_date: Optional[date] = None
    availability_end_date: Optional[date] = None


class ServiceUpdate(SQLModel):
    """Partial update schema for an existing service listing.

    All fields are optional; only provided fields are modified.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    duration_min: Optional[int] = None
    area_type: Optional[TipoArea] = None
    location_note: Optional[str] = None
    price_to_agree: Optional[bool] = None
    category_id: Optional[int] = None
    radius_km: Optional[float] = None
    availability_start_date: Optional[date] = None
    availability_end_date: Optional[date] = None


class ServiceImageCreate(SQLModel):
    """Input schema for a single image in the upsert-images operation."""

    url: str
    is_cover: bool = False
    sort_order: int = 0


class ServiceScheduleCreate(SQLModel):
    """Input schema for a single weekly time slot in the upsert-schedule operation.

    ``time_from`` and ``time_to`` accept ISO-format time strings (e.g. ``"09:00"``).
    """

    weekday: int
    time_from: time
    time_to: time
    timezone: str = "America/Argentina/Buenos_Aires"
