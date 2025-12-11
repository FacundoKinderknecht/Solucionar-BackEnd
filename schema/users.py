from __future__ import annotations
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import Mapped
from core.enums import Role

if TYPE_CHECKING:
    from .services import Service
    from .reservations import Reservation

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    phone: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    is_active: bool = Field(default=True)
    role: Role = Field(default=Role.USER)
    created_at: datetime | None = Field(default_factory=datetime.utcnow)

    # Nota: relación inversa con ProviderProfile se gestiona desde ProviderProfile.user_id
    
    # Relationships
    services_provided: Mapped[List["Service"]] = Relationship(back_populates="provider")
    reservations: Mapped[List["Reservation"]] = Relationship(back_populates="client")
