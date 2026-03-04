"""Pydantic request/response schemas for the authentication domain.

These are pure data-transfer objects — they do not map to database tables.
"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import SQLModel

from app.core.enums import Role


class RegisterRequest(SQLModel):
    """Input schema for user registration."""

    full_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    province: str | None = None
    city: str | None = None

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        """Reject blank full_name values."""
        if not v.strip():
            raise ValueError("full_name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """Enforce a minimum password length of 8 characters."""
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserPublic(SQLModel):
    """Public representation of a user returned after register / GET /auth/me."""

    id: int
    full_name: str
    email: str
    role: Role


class TokenResponse(BaseModel):
    """Response body returned by POST /auth/login."""

    id: int
    full_name: str
    email: str
    phone: str | None = None
    role: str
    is_active: bool
    access_token: str
    token_type: str = "bearer"


class RefreshTokenResponse(BaseModel):
    """Response body returned by POST /auth/refresh."""

    access_token: str
    token_type: str = "bearer"
