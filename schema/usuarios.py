# ------------------------------------------------------------
# Modelo de usuario como tabla SQLModel.
# ------------------------------------------------------------
from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=320)
    password_hash: str = Field(max_length=255)
    phone: Optional[str] = Field(default=None, max_length=32)
    role: str = Field(default="CLIENTE", max_length=16)  # ADMIN | CLIENTE | PROVEEDOR
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
