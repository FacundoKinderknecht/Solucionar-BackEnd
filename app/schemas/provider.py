"""Pydantic request/response schemas for the provider profile domain."""
from __future__ import annotations

from typing import Optional

from sqlmodel import SQLModel

from app.core.enums import TaxStatus


class ProviderUpsertRequest(SQLModel):
    """Input schema for creating or updating a provider profile."""

    legal_name: str
    cuit_or_cuil: str
    tax_status: TaxStatus
    fiscal_address: Optional[str] = None
    service_areas: Optional[str] = None
    category: Optional[str] = None
    has_invoice: bool = True
    bank_alias: Optional[str] = None
    bank_cbu: Optional[str] = None


class ProviderPublic(SQLModel):
    """Public representation of a provider profile."""

    id: int
    user_id: int
    legal_name: str
    cuit_or_cuil: str
    tax_status: TaxStatus
    category: Optional[str] = None
    fiscal_address: Optional[str] = None
    service_areas: Optional[str] = None
    has_invoice: bool = True
    bank_alias: Optional[str] = None
    bank_cbu: Optional[str] = None


class OnboardingStatus(SQLModel):
    """Progress report for a provider's onboarding completion."""

    completed: bool
    percent: int
    missing: list[str]
