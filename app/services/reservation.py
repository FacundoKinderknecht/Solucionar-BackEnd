"""Business logic for reservation management."""
from __future__ import annotations

import logging
from typing import List

from sqlmodel import Session, select

from app.core.enums import Role
from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.models.reservation import Reservation, ReservationStatus
from app.models.review import ReservationReview
from app.models.service import Service
from app.models.user import User
from app.schemas.reservation import ReservationPublic
from app.schemas.review import ReviewPublic

logger = logging.getLogger(__name__)

FINAL_STATUSES: frozenset[ReservationStatus] = frozenset({
    ReservationStatus.CANCELLED_BY_CLIENT,
    ReservationStatus.CANCELLED_BY_PROVIDER,
    ReservationStatus.COMPLETED,
})


def _hydrate_reviews(
    reservations: List[Reservation],
    session: Session,
) -> List[ReservationPublic]:
    """Attach review data to each reservation in a single batch query.

    Fetches all reviews for the given reservations in one query (avoiding N+1)
    and returns the fully hydrated public schema list.

    Args:
        reservations: List of ``Reservation`` instances to hydrate.
        session: Active database session.

    Returns:
        List of ``ReservationPublic`` schemas with review data attached.
    """
    if not reservations:
        return []

    reservation_ids = [r.id for r in reservations]
    reviews = session.exec(
        select(ReservationReview).where(
            ReservationReview.reservation_id.in_(reservation_ids)
        )
    ).all()
    review_map = {rev.reservation_id: rev for rev in reviews}

    result: List[ReservationPublic] = []
    for reservation in reservations:
        public = ReservationPublic.model_validate(reservation, from_attributes=True)
        rev = review_map.get(reservation.id)
        if rev:
            public.review = ReviewPublic.model_validate(rev, from_attributes=True)
        result.append(public)
    return result


def get_my_reservations(
    user: User,
    session: Session,
    limit: int = 20,
    offset: int = 0,
) -> List[ReservationPublic]:
    """Return paginated reservations made by the caller as a client.

    Args:
        user: The authenticated client user.
        session: Active database session.
        limit: Maximum records to return.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReservationPublic`` schemas.
    """
    limit = min(limit, 100)
    reservations = session.exec(
        select(Reservation)
        .where(Reservation.client_id == user.id)
        .order_by(Reservation.reservation_datetime.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return _hydrate_reviews(reservations, session)


def get_provider_reservations(
    user: User,
    session: Session,
    limit: int = 20,
    offset: int = 0,
) -> List[ReservationPublic]:
    """Return paginated reservations for all services offered by the caller.

    Args:
        user: The authenticated provider user.
        session: Active database session.
        limit: Maximum records to return.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReservationPublic`` schemas.

    Raises:
        ForbiddenError: If the caller is not a provider.
    """
    if user.role != Role.PROVIDER:
        raise ForbiddenError("Only providers can access provider reservations")

    limit = min(limit, 100)
    provider_service_ids = list(
        session.exec(select(Service.id).where(Service.provider_id == user.id))
    )
    if not provider_service_ids:
        return []

    reservations = session.exec(
        select(Reservation)
        .where(Reservation.service_id.in_(provider_service_ids))
        .order_by(Reservation.reservation_datetime.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return _hydrate_reviews(reservations, session)


def update_reservation_status(
    reservation_id: int,
    new_status: ReservationStatus,
    user: User,
    session: Session,
) -> Reservation:
    """Advance or cancel a reservation's status with role-based access checks.

    Args:
        reservation_id: Primary key of the reservation to update.
        new_status: The desired new status value.
        user: The authenticated user requesting the status change.
        session: Active database session.

    Returns:
        The updated ``Reservation`` instance.

    Raises:
        NotFoundError: If the reservation does not exist.
        BusinessRuleError: If the reservation is already in a final state or
            the requested status is not supported.
        ForbiddenError: If the caller lacks permission to perform the transition.
    """
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise NotFoundError("Reservation", reservation_id)

    if reservation.status in FINAL_STATUSES:
        raise BusinessRuleError("This reservation has already reached a final state and cannot be modified")

    if new_status == ReservationStatus.CANCELLED_BY_CLIENT:
        if reservation.client_id != user.id:
            raise ForbiddenError("Only the client who made this reservation can cancel it")

    elif new_status in (ReservationStatus.CANCELLED_BY_PROVIDER, ReservationStatus.COMPLETED):
        if user.role != Role.PROVIDER:
            raise ForbiddenError("Only a provider can perform this status transition")
        service = session.get(Service, reservation.service_id)
        if not service or service.provider_id != user.id:
            raise ForbiddenError("You are not the provider for this reservation")

    else:
        raise BusinessRuleError("Requested status transition is not supported")

    reservation.status = new_status
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    logger.info(
        "Reservation %s status updated to %s by user %s",
        reservation_id,
        new_status,
        user.id,
    )
    return reservation
