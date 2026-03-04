"""Payment endpoints: create intent, initiate checkout, gateway callback, and history.

The gateway callback endpoint (C3 fix) is secured via the X-Webhook-Secret header.
If WEBHOOK_SECRET is configured in settings, only requests carrying the correct
secret header are accepted. If not configured (development only), a warning is
logged and the check is skipped.
"""
from __future__ import annotations

import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.config import settings
from app.dependencies import SessionDep, get_current_user
from app.models.user import User
from app.schemas.payment import (
    GatewayCallback,
    InitiateResponse,
    PaymentCreate,
    PaymentPublic,
)
from app.services.payment import (
    complete_payment,
    create_payment,
    get_payment_or_404,
    handle_gateway_callback,
    initiate_payment,
    list_my_payments,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def _verify_webhook_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    """Dependency that validates the X-Webhook-Secret header on gateway callbacks.

    If ``WEBHOOK_SECRET`` is configured in settings, the header must be present
    and match exactly. If not configured, the request proceeds with a warning
    (development mode only — always configure this in production).

    Args:
        x_webhook_secret: Value of the ``X-Webhook-Secret`` request header.

    Raises:
        HTTPException 403: If the secret is configured and the header is wrong
            or missing.
    """
    if settings.WEBHOOK_SECRET:
        if x_webhook_secret != settings.WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing webhook secret",
            )
    else:
        logger.warning(
            "WEBHOOK_SECRET is not configured — gateway callback is unprotected. "
            "Set WEBHOOK_SECRET in your environment for production use."
        )


@router.post(
    "/",
    response_model=PaymentPublic,
    status_code=201,
    summary="Create a payment intent for a service booking",
)
def create_payment_endpoint(
    payload: PaymentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> PaymentPublic:
    """Create a payment intent before initiating checkout.

    The reservation is NOT created at this stage.

    Args:
        payload: Payment intent data.
        current_user: Authenticated client user.
        session: Database session.

    Returns:
        The created ``PaymentPublic``.
    """
    payment = create_payment(payload, current_user, session)
    return PaymentPublic.model_validate(payment, from_attributes=True)


@router.post(
    "/{payment_id}/initiate",
    response_model=InitiateResponse,
    summary="Initiate the checkout flow for a payment intent",
)
def initiate_payment_endpoint(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> InitiateResponse:
    """Initiate the gateway checkout and return a redirect URL.

    Transitions the payment from INITIALIZED to PENDING.

    Args:
        payment_id: Payment primary key.
        current_user: Authenticated client user.
        session: Database session.

    Returns:
        An ``InitiateResponse`` containing the checkout URL and reference.
    """
    payment, payment_url, external_reference = initiate_payment(
        payment_id, current_user, session
    )
    return InitiateResponse(
        payment_id=payment.id,
        payment_url=payment_url,
        external_reference=external_reference,
    )


@router.post(
    "/gateway-callback",
    summary="Webhook called by the payment gateway after a transaction (requires X-Webhook-Secret)",
)
def gateway_callback_endpoint(
    payload: GatewayCallback,
    session: SessionDep,
    _: None = Depends(_verify_webhook_secret),
) -> dict:
    """Process a payment gateway webhook notification.

    This endpoint is public-facing (called by the gateway server) but protected
    by the ``X-Webhook-Secret`` header. If payment is approved, the associated
    reservation is automatically created.

    Args:
        payload: Gateway callback data.
        session: Database session.
        _: Webhook secret validation dependency.

    Returns:
        Confirmation dict with payment ID and updated status.
    """
    payment = handle_gateway_callback(payload, session)
    return {"ok": True, "payment_id": payment.id, "status": payment.status}


@router.post(
    "/{payment_id}/complete",
    response_model=PaymentPublic,
    summary="Manually complete a payment (development / simulation only)",
)
def complete_payment_endpoint(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> PaymentPublic:
    """Simulate gateway approval by manually marking a payment as completed.

    Args:
        payment_id: Payment primary key.
        current_user: Authenticated client user.
        session: Database session.

    Returns:
        The updated ``PaymentPublic``.
    """
    payment = complete_payment(payment_id, current_user, session)
    return PaymentPublic.model_validate(payment, from_attributes=True)


@router.get(
    "/my-payments",
    response_model=List[PaymentPublic],
    summary="List the authenticated user's payment records",
)
def list_my_payments_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> List[PaymentPublic]:
    """Return paginated payment records for the authenticated client.

    Args:
        current_user: Authenticated client user.
        session: Database session.
        limit: Page size (max 100).
        offset: Pagination offset.

    Returns:
        Paginated list of ``PaymentPublic`` schemas.
    """
    payments = list_my_payments(current_user, session, limit=limit, offset=offset)
    return [PaymentPublic.model_validate(p, from_attributes=True) for p in payments]


@router.get(
    "/{payment_id}",
    response_model=PaymentPublic,
    summary="Get a specific payment by ID",
)
def get_payment_endpoint(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> PaymentPublic:
    """Fetch a single payment by primary key (payer access only).

    Args:
        payment_id: Payment primary key.
        current_user: Authenticated client user.
        session: Database session.

    Returns:
        The ``PaymentPublic`` schema for the requested payment.
    """
    payment = get_payment_or_404(payment_id, current_user, session)
    return PaymentPublic.model_validate(payment, from_attributes=True)
