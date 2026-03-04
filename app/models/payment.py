"""SQLModel table definition for the Payment entity.

Column names were migrated from Spanish to English in migration f1.
Breaking API change vs. the original schema — see alembic/versions/f1_rename_payment_columns.py.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, JSON
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.reservation import Reservation
    from app.models.user import User


class PaymentGateway(str, Enum):
    """Supported payment gateway identifiers."""

    MERCADOPAGO = "MERCADOPAGO"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    TRANSFER = "TRANSFER"


class PaymentStatus(str, Enum):
    """High-level status of a payment record."""

    INITIALIZED = "initialized"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionStatus(str, Enum):
    """Granular status returned by the payment gateway."""

    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    OTHER = "other"


class Payment(SQLModel, table=True):
    """A payment record linking a client to a service reservation intent.

    A ``Payment`` is created before the ``Reservation`` so the reservation is
    only materialised after the gateway confirms a successful transaction.
    """

    __tablename__ = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Reservation is created after payment confirmation; may be null initially.
    reservation_id: Optional[int] = Field(default=None, foreign_key="reservations.id")

    # Intent fields: which service/time the client wants to book.
    client_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    service_id: Optional[int] = Field(default=None, foreign_key="services.id", index=True)
    reservation_datetime: Optional[datetime] = None
    notes: Optional[str] = None

    gateway: Optional[PaymentGateway] = None
    amount: Optional[float] = None        # renamed from `monto`
    currency: str = "ARS"                 # renamed from `moneda`
    commission: Optional[float] = None    # renamed from `comision`
    net_amount: Optional[float] = None    # renamed from `neto`
    external_reference: Optional[str] = None

    # Gateway state
    status: PaymentStatus = Field(default=PaymentStatus.INITIALIZED, index=True)  # renamed from `estado`
    transaction_id: Optional[str] = Field(default=None, index=True)
    transaction_status: Optional[TransactionStatus] = Field(default=None, index=True)

    # Timestamps (renamed from creado_en / actualizado_en)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Raw gateway response stored as JSON for audit purposes.
    gateway_response: Optional[dict] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    reservation: Optional["Reservation"] = Relationship(
        back_populates="payments",
        sa_relationship=relationship("Reservation", back_populates="payments"),
    )
    payer: Optional["User"] = Relationship(
        back_populates="payments",
        sa_relationship=relationship("User", back_populates="payments"),
    )
