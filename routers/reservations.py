from __future__ import annotations
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from schema.reservations import Reservation, ReservationCreate, ReservationPublic
from schema.services import Service
from schema.users import User
from core.enums import Role
from routers.auth import get_current_user

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/", response_model=ReservationPublic, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Crea una nueva reserva para un servicio.
    El usuario actual (cliente) realiza la reserva.
    """
    service = session.get(Service, payload.service_id)
    if not service or not service.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o inactivo",
        )

    if service.provider_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes reservar tu propio servicio.",
        )

    # Validar que la fecha de reserva esté dentro de la disponibilidad del servicio
    if service.availability_start_date and payload.reservation_datetime.date() < service.availability_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de reserva es anterior a la disponibilidad del servicio.",
        )
    if service.availability_end_date and payload.reservation_datetime.date() > service.availability_end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de reserva es posterior a la disponibilidad del servicio.",
        )

    # TODO: Añadir validación más compleja, ej:
    # - No superponer con otras reservas confirmadas para el mismo servicio/proveedor.
    # - Validar contra los `ServiceSchedule` (horarios por día de semana).

    # New flow: reservations must be created only after successful payment.
    # Direct reservation creation is disabled; instruct the client to create a payment intent instead.
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Las reservas ahora se crean solo después del pago. Crea un intent de pago en /payments/ con los datos de la reserva.",
    )


@router.get("/my-reservations", response_model=List[ReservationPublic])
def get_my_reservations(session: SessionDep, current_user: CurrentUser):
    """
    Obtiene todas las reservas hechas por el usuario actual (como cliente).
    """
    statement = select(Reservation).where(Reservation.client_id == current_user.id)
    reservations = session.exec(statement.order_by(Reservation.reservation_datetime.desc())).all()
    # build response objects (do not assign Pydantic models to ORM relationship attributes)
    from schema.reservations import ServicePublic, ReservationPublic
    out: list[ReservationPublic] = []
    for r in reservations:
        svc = session.get(Service, r.service_id)
        svc_data = ServicePublic.model_validate(svc).model_dump() if svc is not None else None
        res_data = r.model_dump() if hasattr(r, 'model_dump') else r.__dict__
        res_data['service'] = svc_data
        out.append(ReservationPublic.model_validate(res_data))
    return out


@router.get("/provider-reservations", response_model=List[ReservationPublic])
def get_provider_reservations(session: SessionDep, current_user: CurrentUser):
    """
    Obtiene todas las reservas para los servicios ofrecidos por el usuario actual (como proveedor).
    """
    if current_user.role != Role.PROVIDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No eres un proveedor.",
        )

    # Obtener los IDs de todos los servicios del proveedor actual
    provider_services_ids_stmt = select(Service.id).where(Service.provider_id == current_user.id)
    provider_services_ids = session.exec(provider_services_ids_stmt).all()

    if not provider_services_ids:
        return []

    statement = select(Reservation).where(Reservation.service_id.in_(provider_services_ids))
    reservations = session.exec(statement.order_by(Reservation.reservation_datetime.desc())).all()
    from schema.reservations import ServicePublic, ReservationPublic
    out: list[ReservationPublic] = []
    for r in reservations:
        svc = session.get(Service, r.service_id)
        svc_data = ServicePublic.model_validate(svc).model_dump() if svc is not None else None
        res_data = r.model_dump() if hasattr(r, 'model_dump') else r.__dict__
        res_data['service'] = svc_data
        out.append(ReservationPublic.model_validate(res_data))
    return out