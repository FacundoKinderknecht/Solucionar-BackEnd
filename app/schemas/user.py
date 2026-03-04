"""Pydantic request/response schemas for the user profile domain."""
from __future__ import annotations

from sqlmodel import SQLModel

from app.core.enums import Role


class UserProfilePublic(SQLModel):
    """Full public profile of the currently authenticated user."""

    id: int
    full_name: str
    email: str
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    role: Role


class UserProfileUpdate(SQLModel):
    """Partial update schema for the user's own profile.

    All fields are optional; only provided fields are updated.
    """

    full_name: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None
