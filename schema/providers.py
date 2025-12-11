from __future__ import annotations

from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint
from core.enums import TaxStatus

class ProviderProfile(SQLModel, table=True):
    __tablename__ = "provider_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_provider_user"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    legal_name: str
    cuit_or_cuil: str = Field(index=True)  # validaremos 11 dígitos + dígito verificador si querés
    tax_status: TaxStatus
    fiscal_address: Optional[str] = None
    service_areas: Optional[str] = None
    category: Optional[str] = None
    has_invoice: bool = True
    bank_alias: Optional[str] = None
    bank_cbu: Optional[str] = None

    # Campos opcionales eliminados del modelo público/entrada. Si existen en BD
    # por versiones previas, se ignoran sin impacto.

    # Relación inversa no es necesaria para las consultas actuales; usar FK user_id
