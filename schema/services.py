from __future__ import annotations

from typing import Optional
from datetime import datetime, time
from sqlmodel import SQLModel, Field
from core.enums import TipoArea


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    parent_id: int | None = Field(default=None, foreign_key="categories.id")
    slug: str = Field(index=True, unique=True)


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: int | None = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="users.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    title: str
    description: str
    price: float
    currency: str = Field(default="ARS")  # 3-letter code
    duration_min: int  # 0 = indefinido
    area_type: TipoArea = Field(default=TipoArea.CUSTOMER_LOCATION)
    radius_km: float | None = None
    # Nuevos campos
    location_note: str | None = None  # texto libre: "Rosario zona sur", etc.
    price_to_agree: bool = Field(default=False)  # "Precio a convenir"
    active: bool = Field(default=True)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)


class ServiceImage(SQLModel, table=True):
    __tablename__ = "service_images"

    id: int | None = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    url: str
    is_cover: bool = Field(default=False)
    sort_order: int = Field(default=0)


class ServiceSchedule(SQLModel, table=True):
    __tablename__ = "service_schedules"

    id: int | None = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    weekday: int  # 0..6
    time_from: time
    time_to: time
    timezone: str = Field(default="America/Argentina/Buenos_Aires")
# ------------------------------------------------------------
# Modelos de Servicios (SQLModel).
# ------------------------------------------------------------
from sqlmodel import SQLModel, Field
from typing import Union

class ServicioBase(SQLModel):
    name: str = Field(index=True)
    description: Union[str, None] = None

class Servicio(ServicioBase, table=True):
    id: int = Field(default=None, primary_key=True)
