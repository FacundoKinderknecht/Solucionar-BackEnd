"""SQLModel table definitions for the service catalog domain.

Includes Category, Service, ServiceImage, and ServiceSchedule.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import TYPE_CHECKING, Annotated, List, Optional

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import TipoArea

if TYPE_CHECKING:
    from app.models.reservation import Reservation
    from app.models.user import User


class Category(SQLModel, table=True):
    """Service category (supports hierarchical nesting via parent_id)."""

    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    slug: str = Field(index=True, unique=True)


class Service(SQLModel, table=True):
    """A service offering published by a provider."""

    __tablename__ = "services"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="users.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    title: str
    description: str
    price: float
    currency: str = Field(default="ARS")
    # 0 means unspecified / on-demand duration.
    duration_min: int
    area_type: TipoArea = Field(default=TipoArea.CUSTOMER_LOCATION)
    radius_km: Optional[float] = None
    # Free-text location note; required when area_type == PERSONALIZADO.
    location_note: Optional[str] = None
    price_to_agree: bool = Field(default=False)
    active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    availability_start_date: Optional[date] = Field(default=None)
    availability_end_date: Optional[date] = Field(default=None)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    provider: Optional[Annotated["User", Relationship(back_populates="services_provided")]] = Relationship(
        back_populates="services_provided",
        sa_relationship=relationship("User", back_populates="services_provided"),
    )
    reservations: Annotated[
        List["Reservation"], Relationship(back_populates="service")
    ] = Relationship(
        back_populates="service",
        sa_relationship=relationship("Reservation", back_populates="service"),
    )


class ServiceImage(SQLModel, table=True):
    """An image associated with a service listing."""

    __tablename__ = "service_images"

    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    url: str
    is_cover: bool = Field(default=False)
    sort_order: int = Field(default=0)


class ServiceSchedule(SQLModel, table=True):
    """A recurring weekly time slot during which a service is available."""

    __tablename__ = "service_schedules"

    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    # ISO weekday: 0 = Monday … 6 = Sunday.
    weekday: int
    time_from: time
    time_to: time
    timezone: str = Field(default="America/Argentina/Buenos_Aires")
