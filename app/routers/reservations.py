"""Reservation management endpoints."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, get_current_user
from app.models.user import User
from app.schemas.reservation import ReservationPublic, ReservationStatusUpdate
from app.services.reservation import (
    get_my_reservations,
    get_provider_reservations,
    update_reservation_status,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get(
    "/my-reservations",
    response_model=List[ReservationPublic],
    summary="List the authenticated client's reservations",
)
def get_my_reservations_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[ReservationPublic]:
    """Return paginated reservations made by the caller as a client.

    Args:
        current_user: Authenticated user.
        session: Database session.
        limit: Page size.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReservationPublic`` schemas including review data.
    """
    return get_my_reservations(current_user, session, limit=limit, offset=offset)


@router.get(
    "/provider-reservations",
    response_model=List[ReservationPublic],
    summary="List reservations for the authenticated provider's services",
)
def get_provider_reservations_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[ReservationPublic]:
    """Return paginated reservations across all services offered by the caller.

    Args:
        current_user: Authenticated provider user.
        session: Database session.
        limit: Page size.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReservationPublic`` schemas.
    """
    return get_provider_reservations(current_user, session, limit=limit, offset=offset)


@router.patch(
    "/{reservation_id}/status",
    response_model=ReservationPublic,
    summary="Update the status of a reservation",
)
def update_reservation_status_endpoint(
    reservation_id: int,
    payload: ReservationStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> ReservationPublic:
    """Advance or cancel a reservation's lifecycle status.

    Allowed transitions:
    - ``CANCELLED_BY_CLIENT``: only by the client.
    - ``CANCELLED_BY_PROVIDER`` / ``COMPLETED``: only by the owning provider.

    Args:
        reservation_id: Reservation primary key.
        payload: New status to apply.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        The updated ``ReservationPublic`` schema.
    """
    reservation = update_reservation_status(
        reservation_id, payload.status, current_user, session
    )
    return ReservationPublic.model_validate(reservation, from_attributes=True)
