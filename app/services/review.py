"""Business logic for the reviews domain."""
from __future__ import annotations

import logging
from typing import List

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError

from app.models.reservation import Reservation, ReservationStatus
from app.models.review import ReservationReview
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewSummary

logger = logging.getLogger(__name__)


def create_review(data: ReviewCreate, user: User, session: Session) -> ReservationReview:
    """Submit a review for a completed reservation.

    Args:
        data: Validated review creation data.
        user: The authenticated client user submitting the review.
        session: Active database session.

    Returns:
        The newly created ``ReservationReview``.

    Raises:
        NotFoundError: If the reservation does not exist.
        ForbiddenError: If the caller is not the client on the reservation.
        BusinessRuleError: If the reservation is not completed.
        ConflictError: If a review has already been submitted for this reservation.
    """
    reservation = session.get(Reservation, data.reservation_id)
    if not reservation:
        raise NotFoundError("Reservation", data.reservation_id)

    if reservation.client_id != user.id:
        raise ForbiddenError("Only the client on this reservation can leave a review")

    if reservation.status != ReservationStatus.COMPLETED:
        raise BusinessRuleError("Reviews can only be submitted for completed reservations")

    existing = session.exec(
        select(ReservationReview).where(
            ReservationReview.reservation_id == reservation.id
        )
    ).first()
    if existing:
        raise ConflictError("A review has already been submitted for this reservation")

    review = ReservationReview(
        reservation_id=reservation.id,
        service_id=reservation.service_id,
        client_id=user.id,
        rating=data.rating,
        comment=data.comment.strip() if data.comment else None,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    logger.info("Review created for reservation %s by user %s", reservation.id, user.id)
    return review


def list_service_reviews(
    service_id: int,
    session: Session,
    limit: int = 20,
    offset: int = 0,
) -> List[ReservationReview]:
    """Return paginated reviews for a given service, newest first.

    Args:
        service_id: Primary key of the service.
        session: Active database session.
        limit: Maximum records to return.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReservationReview`` records.
    """
    limit = min(limit, 100)
    return session.exec(
        select(ReservationReview)
        .where(ReservationReview.service_id == service_id)
        .order_by(ReservationReview.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()


def list_my_reviews(
    user: User,
    session: Session,
    limit: int = 20,
    offset: int = 0,
) -> List[ReservationReview]:
    """Return paginated reviews written by the authenticated user.

    Args:
        user: The authenticated user.
        session: Active database session.
        limit: Maximum records to return.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReservationReview`` records.
    """
    limit = min(limit, 100)
    return session.exec(
        select(ReservationReview)
        .where(ReservationReview.client_id == user.id)
        .order_by(ReservationReview.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()


def get_review_summaries(
    service_ids: List[int],
    session: Session,
) -> List[ReviewSummary]:
    """Compute aggregated rating statistics for a list of services.

    Uses a single GROUP BY query to avoid N+1 problems.

    Args:
        service_ids: List of service IDs to aggregate.
        session: Active database session.

    Returns:
        List of ``ReviewSummary`` objects, one per service that has reviews.

    Raises:
        BusinessRuleError: If no service_ids are provided.
    """
    if not service_ids:
        raise BusinessRuleError("At least one service_id must be provided")

    rows = session.exec(
        select(
            ReservationReview.service_id,
            func.avg(ReservationReview.rating),
            func.count(ReservationReview.id),
        )
        .where(ReservationReview.service_id.in_(service_ids))
        .group_by(ReservationReview.service_id)
    ).all()

    return [
        ReviewSummary(
            service_id=row[0],
            average=float(row[1]) if row[1] is not None else 0.0,
            count=int(row[2]) if row[2] is not None else 0,
        )
        for row in rows
    ]
