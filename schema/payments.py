from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import relationship
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from .reservations import Reservation
    from .users import User


class PaymentGateway(str, Enum):
    MERCADOPAGO = "MERCADOPAGO"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    TRANSFER = "TRANSFER"


class PaymentStatus(str, Enum):
    INITIALIZED = "initialized"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    OTHER = "other"


class PaymentBase(SQLModel):
    # reservation_id is optional: reservation may be created only after payment
    reservation_id: int | None = Field(default=None, foreign_key="reservations.id")
    # store intent: which service/time the client wants when paying
    client_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    service_id: int | None = Field(default=None, foreign_key="services.id", index=True)
    reservation_datetime: datetime | None = None
    notes: str | None = None
    gateway: PaymentGateway | None = None
    monto: float | None = None
    moneda: str = "ARS"
    comision: float | None = None
    neto: float | None = None
    external_reference: str | None = None


class Payment(PaymentBase, table=True):
    __tablename__ = "payments"

    id: int | None = Field(default=None, primary_key=True)
    estado: PaymentStatus = Field(default=PaymentStatus.INITIALIZED, index=True)
    transaction_id: str | None = Field(default=None, index=True)
    transaction_status: TransactionStatus | None = Field(default=None, index=True)
    creado_en: datetime | None = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime | None = Field(default_factory=datetime.utcnow)

    # Relationship to reservation
    reservation: "Reservation" | None = Relationship(
        back_populates="payments",
        sa_relationship=relationship("Reservation", back_populates="payments"),
    )
    # optional relationship to user who initiated the payment
    payer: "User" | None = Relationship(
        back_populates="payments",
        sa_relationship=relationship("User", back_populates="payments"),
    )
    # raw gateway response (JSON) for audit / debugging
    gateway_response: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))


# --- API Schemas ---
class PaymentCreate(PaymentBase):
    pass


class PaymentPublic(PaymentBase):
    id: int
    estado: PaymentStatus
    creado_en: datetime | None
    actualizado_en: datetime | None
