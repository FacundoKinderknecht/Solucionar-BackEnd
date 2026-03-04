"""Security utilities: password hashing and JWT token management.

Combines password (bcrypt via passlib) and token (python-jose) concerns
into a single, importable module used by the services and dependency layers.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plain-text password.

    Args:
        plain: Raw password string provided by the user.

    Returns:
        Bcrypt-hashed password string safe for database storage.
    """
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain: Raw password provided during login.
        hashed: Previously hashed password retrieved from the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    subject: dict[str, Any],
    expires_minutes: int | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: Claims to embed (should include at minimum ``"sub"``
            with the user's ID as a string).
        expires_minutes: Token lifetime in minutes. Defaults to
            ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        Encoded JWT string ready to be sent to the client.
    """
    lifetime = timedelta(
        minutes=(
            expires_minutes
            if expires_minutes is not None
            else settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {"iat": now, "exp": now + lifetime, **subject}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT string received from the client.

    Returns:
        Decoded payload dict if the token is valid and not expired,
        or ``None`` if validation fails.
    """
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        logger.debug("JWT decode failed — token is invalid or expired")
        return None
