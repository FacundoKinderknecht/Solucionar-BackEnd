"""Business logic for user profile management."""
from __future__ import annotations

import logging

from sqlmodel import Session

from app.models.user import User
from app.schemas.user import UserProfileUpdate

logger = logging.getLogger(__name__)


def update_user_profile(
    user: User,
    data: UserProfileUpdate,
    session: Session,
) -> User:
    """Apply a partial profile update to the given user.

    Args:
        user: The authenticated user to update.
        data: Partial update payload; only non-None fields are applied.
        session: Active database session.

    Returns:
        The refreshed ``User`` instance with updated fields.
    """
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.province is not None:
        user.province = data.province
    if data.city is not None:
        user.city = data.city

    session.add(user)
    session.commit()
    session.refresh(user)
    logger.info("Profile updated for user id=%s", user.id)
    return user
