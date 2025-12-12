# ------------------------------------------------------------
# Esquemas Pydantic para autenticación (entrada/salida).
# NO contienen endpoints ni lógica.
# ------------------------------------------------------------
from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel
from typing import Optional
from core.enums import Role, TaxStatus


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    phone: str | None = None
    # role está controlado por el backend; no confiar en el input del cliente
    role: str = "USER"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool


class RegisterRequest(SQLModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None


class UserPublic(SQLModel):
    id: int
    full_name: str
    email: str
    role: Role

class UserProfilePublic(SQLModel):
    id: int
    full_name: str
    email: str
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    role: Role

class UserProfileUpdate(SQLModel):
    full_name: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None


class ProviderUpsertRequest(SQLModel):
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
    # Campos eliminados de la API pública