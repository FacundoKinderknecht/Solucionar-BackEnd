"""SQLModel table definition for the ProviderProfile entity."""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint

from app.core.enums import TaxStatus


class ProviderProfile(SQLModel, table=True):
    """Extended profile for users registered as service providers.

    One-to-one with ``User`` (enforced by the unique constraint on user_id).
    """

    __tablename__ = "provider_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_provider_user"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    legal_name: str
    # 11-digit Argentine tax identifier (CUIT / CUIL), validated by the service layer.
    cuit_or_cuil: str = Field(index=True)
    tax_status: TaxStatus
    fiscal_address: Optional[str] = None
    # Comma-separated service areas or a single area value.
    service_areas: Optional[str] = None
    category: Optional[str] = None
    has_invoice: bool = True
    bank_alias: Optional[str] = None
    bank_cbu: Optional[str] = None
