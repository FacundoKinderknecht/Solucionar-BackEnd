"""Business logic for payment management and the post-payment reservation flow."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from sqlmodel import Session, select

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError

from app.models.payment import Payment, PaymentStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.service import Service
from app.models.user import User
from app.schemas.payment import GatewayCallback, PaymentCreate
from app.services.gateway import get_gateway_adapter

logger = logging.getLogger(__name__)

# Platform commission rate applied when not explicitly provided.
DEFAULT_COMMISSION_RATE: float = 0.10


def create_payment(data: PaymentCreate, user: User, session: Session) -> Payment:
    """Create a payment intent for a service booking.

    The reservation is NOT created at this stage — it is created only after
    the gateway confirms a successful transaction.

    Args:
        data: Validated payment creation data.
        user: The authenticated client initiating the payment.
        session: Active database session.

    Returns:
        The newly created ``Payment`` record.

    Raises:
        NotFoundError: If the service does not exist or is inactive.
        BusinessRuleError: If the client attempts to book their own service.
    """
    service = session.get(Service, data.service_id) if data.service_id else None
    if not service or not service.active:
        raise NotFoundError("Service", data.service_id)

    if service.provider_id == user.id:
        raise BusinessRuleError("You cannot book your own service")

    # Compute commission and net amount if not explicitly provided.
    amount = data.amount or 0.0
    commission = (
        data.commission
        if data.commission is not None
        else round(amount * DEFAULT_COMMISSION_RATE, 2)
    )
    net_amount = (
        data.net_amount
        if data.net_amount is not None
        else round(amount - commission, 2)
        if data.amount is not None
        else None
    )

    payment = Payment.model_validate(
        data,
        update={
            "client_id": user.id,
            "status": PaymentStatus.INITIALIZED,
            "external_reference": str(uuid4()),
            "commission": commission,
            "net_amount": net_amount,
        },
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    logger.info("Payment intent created: id=%s for user=%s", payment.id, user.id)
    return payment


def initiate_payment(
    payment_id: int,
    user: User,
    session: Session,
) -> tuple[Payment, str, str]:
    """Initiate the gateway checkout flow for an existing payment.

    Transitions the payment from INITIALIZED to PENDING and returns the
    gateway redirect URL.

    Args:
        payment_id: Primary key of the payment to initiate.
        user: The authenticated client who owns this payment.
        session: Active database session.

    Returns:
        Tuple of (updated Payment, payment_url, external_reference).

    Raises:
        NotFoundError: If the payment does not exist.
        ForbiddenError: If the caller is not the payer.
    """
    payment = session.get(Payment, payment_id)
    if not payment:
        raise NotFoundError("Payment", payment_id)

    if payment.client_id != user.id:
        raise ForbiddenError()

    adapter = get_gateway_adapter(payment.gateway)
    initiation = adapter.initiate(payment)

    payment.status = PaymentStatus.PENDING
    payment.updated_at = datetime.now(timezone.utc)
    session.add(payment)
    session.commit()
    session.refresh(payment)

    return payment, initiation.payment_url, initiation.external_reference


def handle_gateway_callback(data: GatewayCallback, session: Session) -> Payment:
    """Process a gateway webhook callback and update the payment accordingly.

    If the payment is approved and no reservation exists yet, one is created
    automatically from the intent data stored on the payment record.

    Args:
        data: Validated callback payload from the gateway.
        session: Active database session.

    Returns:
        The updated ``Payment`` record.

    Raises:
        NotFoundError: If no matching payment is found.
    """
    payment: Payment | None = None

    if data.payment_id is not None:
        payment = session.get(Payment, data.payment_id)
    elif data.external_reference:
        payment = session.exec(
            select(Payment).where(Payment.external_reference == data.external_reference)
        ).first()

    if not payment:
        raise NotFoundError("Payment")

    adapter = get_gateway_adapter(payment.gateway)
    normalized = adapter.normalize_status(data.status)

    payment.transaction_id = data.transaction_id
    payment.transaction_status = normalized.transaction_status
    payment.status = normalized.payment_status
    payment.updated_at = datetime.now(timezone.utc)
    payment.gateway_response = data.raw or {
        "status": data.status,
        "transaction_id": data.transaction_id,
    }

    # Auto-create the reservation after a successful payment.
    if payment.status == PaymentStatus.COMPLETED and not payment.reservation_id:
        if not all([payment.service_id, payment.reservation_datetime, payment.client_id]):
            logger.warning(
                "Payment %s is COMPLETED but lacks intent data to create a reservation",
                payment.id,
            )
            payment.status = PaymentStatus.FAILED
        else:
            new_res = Reservation(
                service_id=payment.service_id,
                reservation_datetime=payment.reservation_datetime,
                notes=payment.notes,
                client_id=payment.client_id,
                status=ReservationStatus.PENDING,
            )
            session.add(new_res)
            session.commit()
            session.refresh(new_res)
            payment.reservation_id = new_res.id
            logger.info(
                "Reservation %s auto-created after payment %s approved",
                new_res.id,
                payment.id,
            )

    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def complete_payment(payment_id: int, user: User, session: Session) -> Payment:
    """Manually mark a payment as completed (development / simulation endpoint).

    Args:
        payment_id: Primary key of the payment to complete.
        user: The authenticated client who owns this payment.
        session: Active database session.

    Returns:
        The updated ``Payment`` record.

    Raises:
        NotFoundError: If the payment does not exist.
        ForbiddenError: If the caller is not the payer.
        BusinessRuleError: If reservation intent data is insufficient.
    """
    payment = session.get(Payment, payment_id)
    if not payment:
        raise NotFoundError("Payment", payment_id)

    if payment.client_id != user.id:
        raise ForbiddenError()

    payment.status = PaymentStatus.COMPLETED
    payment.updated_at = datetime.now(timezone.utc)

    if not payment.reservation_id:
        if not payment.service_id or not payment.reservation_datetime:
            raise BusinessRuleError("Insufficient reservation intent data on this payment")
        new_res = Reservation(
            service_id=payment.service_id,
            reservation_datetime=payment.reservation_datetime,
            notes=payment.notes,
            client_id=payment.client_id,
            status=ReservationStatus.PENDING,
        )
        session.add(new_res)
        session.commit()
        session.refresh(new_res)
        payment.reservation_id = new_res.id

    session.add(payment)
    session.commit()
    session.refresh(payment)
    logger.info("Payment %s manually completed by user %s", payment_id, user.id)
    return payment


def list_my_payments(
    user: User,
    session: Session,
    limit: int = 20,
    offset: int = 0,
) -> List[Payment]:
    """Return paginated payments for the authenticated client.

    Args:
        user: The authenticated client user.
        session: Active database session.
        limit: Maximum records to return.
        offset: Pagination offset.

    Returns:
        Paginated list of ``Payment`` records.
    """
    limit = min(limit, 100)
    return session.exec(
        select(Payment)
        .where(Payment.client_id == user.id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()


def get_payment_or_404(payment_id: int, user: User, session: Session) -> Payment:
    """Fetch a payment by ID, verifying the caller is the payer.

    Args:
        payment_id: Primary key of the payment.
        user: The authenticated client user.
        session: Active database session.

    Returns:
        The ``Payment`` instance.

    Raises:
        NotFoundError: If the payment does not exist.
        ForbiddenError: If the caller is not the payer.
    """
    payment = session.get(Payment, payment_id)
    if not payment:
        raise NotFoundError("Payment", payment_id)
    if payment.client_id != user.id:
        raise ForbiddenError()
    return payment
