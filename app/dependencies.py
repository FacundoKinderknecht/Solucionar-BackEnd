"""Shared FastAPI dependencies used across multiple routers.

Centralising ``get_current_user``, ``SessionDep``, ``CurrentUser``, and
role-based access control here eliminates the duplication that previously
existed across every router file.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.enums import Role
from app.core.security import decode_token
from app.database import get_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session dependency
# ---------------------------------------------------------------------------

SessionDep = Annotated[Session, Depends(get_session)]

# ---------------------------------------------------------------------------
# Authentication dependencies
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
):
    """Extract and validate the current authenticated user from a Bearer JWT.

    Args:
        token: Bearer token extracted from the ``Authorization`` header.
        session: Active database session for the current request.

    Returns:
        The authenticated ``User`` model instance.

    Raises:
        HTTPException 401: If the token is missing, invalid, expired, or the
            associated user no longer exists or is inactive.
    """
    # Import here to avoid circular imports at module load time.
    from app.models.user import User

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user: User | None = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated",
        )

    return user


CurrentUser = Annotated[object, Depends(get_current_user)]

# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


def require_roles(*allowed_roles: Role):
    """Return a dependency that enforces role-based access control.

    Usage::

        @router.get("/admin-only")
        def admin_endpoint(
            user: Annotated[User, Depends(require_roles(Role.ADMIN))]
        ):
            ...

    Args:
        *allowed_roles: One or more ``Role`` values that are permitted to
            access the endpoint.

    Returns:
        A FastAPI dependency callable that returns the current user if their
        role is in *allowed_roles*, or raises HTTP 403 otherwise.
    """

    def _checker(current_user=Depends(get_current_user)):
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user

    return _checker
