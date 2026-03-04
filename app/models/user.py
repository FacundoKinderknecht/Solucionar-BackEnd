"""SQLModel table definition for the User entity."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated, List, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import Role

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.reservation import Reservation
    from app.models.service import Service


class User(SQLModel, table=True):
    """Platform user — can hold USER, PROVIDER, or ADMIN roles."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    phone: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    is_active: bool = Field(default=True)
    role: str = Field(
        default=Role.USER.value,
        sa_column=Column(SQLEnum(Role, name="role_enum")),
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    services_provided: Annotated[
        List["Service"], Relationship(back_populates="provider")
    ] = Relationship(
        back_populates="provider",
        sa_relationship=relationship("Service", back_populates="provider"),
    )
    reservations: Annotated[
        List["Reservation"], Relationship(back_populates="client")
    ] = Relationship(
        back_populates="client",
        sa_relationship=relationship("Reservation", back_populates="client"),
    )
    payments: Annotated[
        List["Payment"], Relationship(back_populates="payer")
    ] = Relationship(
        back_populates="payer",
        sa_relationship=relationship("Payment", back_populates="payer"),
    )
