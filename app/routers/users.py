"""User profile endpoints: view and update the authenticated user's profile."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import SessionDep, get_current_user
from app.models.user import User
from app.schemas.user import UserProfilePublic, UserProfileUpdate
from app.services.user import update_user_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me/profile",
    response_model=UserProfilePublic,
    summary="Return the full profile of the authenticated user",
)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserProfilePublic:
    """Return the full profile of the currently authenticated user.

    Args:
        current_user: Authenticated user extracted from the Bearer token.

    Returns:
        The full ``UserProfilePublic`` for the caller.
    """
    return UserProfilePublic(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        province=current_user.province,
        city=current_user.city,
        role=current_user.role,
    )


@router.put(
    "/me/profile",
    response_model=UserProfilePublic,
    summary="Update the authenticated user's profile",
)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> UserProfilePublic:
    """Partially update the profile of the currently authenticated user.

    Args:
        payload: Partial update data; only non-null fields are applied.
        current_user: Authenticated user extracted from the Bearer token.
        session: Database session injected by FastAPI.

    Returns:
        The updated ``UserProfilePublic``.
    """
    user = update_user_profile(current_user, payload, session)
    return UserProfilePublic(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        province=user.province,
        city=user.city,
        role=user.role,
    )


@router.get(
    "/me/history",
    summary="Return the authenticated user's activity history (stub)",
)
def get_my_history(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Placeholder for the user's service/reservation history.

    Args:
        current_user: Authenticated user extracted from the Bearer token.

    Returns:
        A placeholder response — implement with real Reservation data.

    Todo:
        Implement with paginated Reservation history from the database.
    """
    return {"last_services": []}
