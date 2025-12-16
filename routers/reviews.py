from __future__ import annotations

from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlalchemy import func

from database import get_session
from routers.auth import get_current_user
from schema.reservations import Reservation, ReservationStatus
from schema.reviews import (
    ReservationReview,
    ReservationReviewCreate,
    ReservationReviewPublic,
    ReservationReviewSummary,
)
from schema.users import User

router = APIRouter(prefix="/reviews", tags=["reviews"])

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/", response_model=ReservationReviewPublic, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReservationReviewCreate, session: SessionDep, current_user: CurrentUser):
    reservation = session.get(Reservation, payload.reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada")
    if reservation.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el cliente puede dejar una reseña")
    if reservation.status != ReservationStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La reserva debe estar completada")

    existing = session.exec(
        select(ReservationReview).where(ReservationReview.reservation_id == reservation.id)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La reserva ya tiene una reseña")

    review = ReservationReview(
        reservation_id=reservation.id,
        service_id=reservation.service_id,
        client_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment.strip() if payload.comment else None,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


@router.get("/service/{service_id}", response_model=List[ReservationReviewPublic])
def list_service_reviews(service_id: int, session: SessionDep):
    statement = (
        select(ReservationReview)
        .where(ReservationReview.service_id == service_id)
        .order_by(ReservationReview.created_at.desc())
    )
    return session.exec(statement).all()


@router.get("/my", response_model=List[ReservationReviewPublic])
def list_my_reviews(session: SessionDep, current_user: CurrentUser):
    statement = (
        select(ReservationReview)
        .where(ReservationReview.client_id == current_user.id)
        .order_by(ReservationReview.created_at.desc())
    )
    return session.exec(statement).all()


@router.get("/summary", response_model=List[ReservationReviewSummary])
def get_review_summaries(session: SessionDep, service_ids: List[int] = Query(..., alias="service_ids")):
    if not service_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes enviar service_ids")
    stmt = (
        select(
            ReservationReview.service_id,
            func.avg(ReservationReview.rating),
            func.count(ReservationReview.id),
        )
        .where(ReservationReview.service_id.in_(service_ids))
        .group_by(ReservationReview.service_id)
    )
    rows = session.exec(stmt).all()
    return [
        ReservationReviewSummary(
            service_id=row[0],
            average=float(row[1]) if row[1] is not None else 0.0,
            count=int(row[2]) if row[2] is not None else 0,
        )
        for row in rows
    ]
