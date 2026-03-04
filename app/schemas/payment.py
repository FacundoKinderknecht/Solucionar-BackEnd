"""Pydantic request/response schemas for the payments domain.

Field names use English identifiers matching the renamed database columns
introduced in Alembic migration f1_rename_payment_columns.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel

from app.models.payment import PaymentGateway, PaymentStatus, TransactionStatus


class PaymentCreate(SQLModel):
    """Input schema for creating a payment intent before checkout."""

    service_id: Optional[int] = None
    reservation_datetime: Optional[datetime] = None
    notes: Optional[str] = None
    gateway: Optional[PaymentGateway] = None
    amount: Optional[float] = None
    currency: str = "ARS"
    commission: Optional[float] = None
    net_amount: Optional[float] = None


class PaymentPublic(SQLModel):
    """Public representation of a payment record.

    Intentionally omits ``gateway_response`` to avoid leaking internal data.
    """

    id: int
    reservation_id: Optional[int] = None
    client_id: Optional[int] = None
    service_id: Optional[int] = None
    reservation_datetime: Optional[datetime] = None
    notes: Optional[str] = None
    gateway: Optional[PaymentGateway] = None
    amount: Optional[float] = None
    currency: str = "ARS"
    commission: Optional[float] = None
    net_amount: Optional[float] = None
    external_reference: Optional[str] = None
    status: PaymentStatus
    transaction_id: Optional[str] = None
    transaction_status: Optional[TransactionStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InitiateResponse(BaseModel):
    """Response returned when initiating the payment checkout flow."""

    payment_id: int
    payment_url: str
    external_reference: str


class GatewayCallback(BaseModel):
    """Payload sent by the payment gateway webhook after a transaction completes."""

    external_reference: Optional[str] = None
    payment_id: Optional[int] = None
    transaction_id: str
    status: str  # raw gateway status string, e.g. "approved", "rejected"
    raw: Optional[dict] = None
