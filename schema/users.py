from __future__ import annotations

# models/user.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from core.enums import Role

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
