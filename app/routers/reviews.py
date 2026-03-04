"""Review endpoints: submit, list by service, and retrieve the caller's reviews."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewPublic, ReviewSummary
from app.services.review import (
    create_review,
    get_review_summaries,
    list_my_reviews,
    list_service_reviews,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post(
    "/",
    response_model=ReviewPublic,
    status_code=201,
    summary="Submit a review for a completed reservation",
)
def create_review_endpoint(
    payload: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> ReviewPublic:
    """Create a new review for a completed reservation.

    Args:
        payload: Review data (reservation_id, rating, optional comment).
        current_user: Authenticated client user.
        session: Database session.

    Returns:
        The created ``ReviewPublic``.
    """
    review = create_review(payload, current_user, session)
    return ReviewPublic.model_validate(review, from_attributes=True)


@router.get(
    "/service/{service_id}",
    response_model=List[ReviewPublic],
    summary="List reviews for a specific service",
)
def list_service_reviews_endpoint(
    service_id: int,
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[ReviewPublic]:
    """Return paginated reviews for a given service, newest first.

    Args:
        service_id: Service primary key.
        session: Database session.
        limit: Page size.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReviewPublic`` schemas.
    """
    reviews = list_service_reviews(service_id, session, limit=limit, offset=offset)
    return [ReviewPublic.model_validate(r, from_attributes=True) for r in reviews]


@router.get(
    "/my",
    response_model=List[ReviewPublic],
    summary="List reviews written by the authenticated user",
)
def list_my_reviews_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[ReviewPublic]:
    """Return paginated reviews written by the authenticated user.

    Args:
        current_user: Authenticated user.
        session: Database session.
        limit: Page size.
        offset: Pagination offset.

    Returns:
        Paginated list of ``ReviewPublic`` schemas.
    """
    reviews = list_my_reviews(current_user, session, limit=limit, offset=offset)
    return [ReviewPublic.model_validate(r, from_attributes=True) for r in reviews]


@router.get(
    "/summary",
    response_model=List[ReviewSummary],
    summary="Get aggregated rating statistics for multiple services",
)
def get_review_summaries_endpoint(
    session: SessionDep,
    service_ids: List[int] = Query(..., alias="service_ids"),
) -> List[ReviewSummary]:
    """Return aggregated rating statistics for a batch of services.

    Args:
        session: Database session.
        service_ids: List of service IDs to aggregate (pass as repeated query params).

    Returns:
        List of ``ReviewSummary`` objects, one per service with reviews.
    """
    return get_review_summaries(service_ids, session)
