"""Authentication endpoints: register, login, token refresh, and current user.

All business logic is delegated to ``app.services.auth``.
Rate limiting is applied to register and login to prevent brute-force attacks.
"""
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import create_access_token
from app.dependencies import CurrentUser, SessionDep, get_current_user
from app.models.user import User
from app.schemas.auth import RefreshTokenResponse, RegisterRequest, TokenResponse, UserPublic
from app.services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=201,
    summary="Register a new user account",
)
@limiter.limit("10/minute")
def register(request: Request, data: Annotated[RegisterRequest, Body()], session: SessionDep) -> UserPublic:
    """Create a new user account.

    Args:
        request: Incoming HTTP request (required by slowapi for rate limiting).
        data: Registration payload validated by ``RegisterRequest``.
        session: Database session injected by FastAPI.

    Returns:
        The public representation of the newly created user.
    """
    user = register_user(data, session)
    return UserPublic(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain a Bearer token",
)
@limiter.limit("20/minute")
def login(
    request: Request,
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """Authenticate using email/password and return a signed JWT.

    The ``username`` form field must contain the user's email address.

    Args:
        request: Incoming HTTP request (required by slowapi).
        session: Database session injected by FastAPI.
        form_data: Standard OAuth2 password form (username = email).

    Returns:
        A ``TokenResponse`` containing the access token and user details.
    """
    user = authenticate_user(form_data.username, form_data.password, session)
    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )
    return TokenResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=user.is_active,
        access_token=token,
    )


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Return the currently authenticated user",
)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    """Return public profile data for the caller's account.

    Args:
        current_user: Authenticated user extracted from the Bearer token.

    Returns:
        The public user representation.
    """
    return UserPublic(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh the caller's access token",
)
def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
) -> RefreshTokenResponse:
    """Issue a new access token preserving the existing claims.

    Args:
        current_user: Authenticated user extracted from the existing token.

    Returns:
        A new ``RefreshTokenResponse`` with an updated expiry.
    """
    new_token = create_access_token(
        {"sub": str(current_user.id), "email": current_user.email, "role": current_user.role}
    )
    return RefreshTokenResponse(access_token=new_token)
