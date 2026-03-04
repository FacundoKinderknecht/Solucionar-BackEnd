"""Business logic for authentication: registration and credential validation."""
from __future__ import annotations

import logging

from sqlmodel import Session, select

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest

logger = logging.getLogger(__name__)


def register_user(data: RegisterRequest, session: Session) -> User:
    """Create a new user account after verifying the email is not already taken.

    Args:
        data: Validated registration request.
        session: Active database session.

    Returns:
        The newly created and persisted ``User`` instance.

    Raises:
        ConflictError: If a user with the given email already exists.
    """
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("A user with this email address is already registered")

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        phone=data.phone,
        province=data.province,
        city=data.city,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    logger.info("New user registered: id=%s email=%s", user.id, user.email)
    return user


def authenticate_user(email: str, password: str, session: Session) -> User:
    """Validate credentials and return the matching user.

    Args:
        email: Email address provided in the login form.
        password: Plain-text password provided in the login form.
        session: Active database session.

    Returns:
        The authenticated ``User`` instance.

    Raises:
        UnauthorizedError: If credentials are invalid or the account is inactive.
    """
    user = session.exec(select(User).where(User.email == email)).first()

    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated")

    logger.info("User authenticated: id=%s", user.id)
    return user
