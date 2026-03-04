"""Business logic for provider profile management and dashboard metrics."""
from __future__ import annotations

import logging

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.enums import CATEGORY_CHOICES, Role, SERVICE_AREA_CHOICES
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.payment import Payment, PaymentStatus
from app.models.provider import ProviderProfile
from app.models.reservation import Reservation, ReservationStatus
from app.models.review import ReservationReview
from app.models.service import Service
from app.models.user import User
from app.schemas.provider import OnboardingStatus, ProviderUpsertRequest

logger = logging.getLogger(__name__)


def _validate_cuit(cuit: str) -> bool:
    """Validate an Argentine CUIT/CUIL number using modulo-11 check digit.

    Args:
        cuit: 11-digit string to validate.

    Returns:
        True if the CUIT/CUIL is structurally valid, False otherwise.
    """
    if not cuit or not cuit.isdigit() or len(cuit) != 11:
        return False
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(cuit[:10], weights))
    dv = 11 - (total % 11)
    if dv == 11:
        dv = 0
    if dv == 10:
        dv = 9
    return dv == int(cuit[-1])


def get_provider_profile(user_id: int, session: Session) -> ProviderProfile | None:
    """Fetch the provider profile for the given user, or return None.

    Args:
        user_id: ID of the user whose provider profile is requested.
        session: Active database session.

    Returns:
        The ``ProviderProfile`` instance, or ``None`` if the user has not
        completed provider onboarding.
    """
    return session.exec(
        select(ProviderProfile).where(ProviderProfile.user_id == user_id)
    ).first()


def upsert_provider_profile(
    user: User,
    data: ProviderUpsertRequest,
    session: Session,
) -> ProviderProfile:
    """Create or update the provider profile for the given user.

    Also elevates the user's role to PROVIDER on first successful upsert.

    Args:
        user: The authenticated user requesting the upsert.
        data: Validated provider profile data.
        session: Active database session.

    Returns:
        The created or updated ``ProviderProfile``.

    Raises:
        BusinessRuleError: If CUIT/CUIL is invalid, banking info is missing
            when required, or category/service_areas values are invalid.
    """
    if not _validate_cuit(data.cuit_or_cuil):
        raise BusinessRuleError("Invalid CUIT/CUIL number")

    if data.has_invoice and not (data.bank_alias or data.bank_cbu):
        raise BusinessRuleError("bank_alias or bank_cbu is required when has_invoice is true")

    if data.category and data.category not in CATEGORY_CHOICES:
        raise BusinessRuleError(f"Invalid category. Allowed values: {CATEGORY_CHOICES}")

    if data.service_areas and data.service_areas not in SERVICE_AREA_CHOICES:
        raise BusinessRuleError(f"Invalid service area. Allowed values: {SERVICE_AREA_CHOICES}")

    profile = get_provider_profile(user.id, session)
    if not profile:
        profile = ProviderProfile(user_id=user.id, **data.model_dump())
        session.add(profile)
    else:
        for key, value in data.model_dump().items():
            setattr(profile, key, value)

    user.role = Role.PROVIDER
    session.add(user)
    session.commit()
    session.refresh(profile)
    logger.info("Provider profile upserted for user id=%s", user.id)
    return profile


def get_provider_dashboard(user: User, session: Session) -> dict:
    """Compute basic dashboard metrics for a provider.

    Args:
        user: The authenticated provider user.
        session: Active database session.

    Returns:
        A dict containing totals, ratings, and real revenue (sum of
        ``net_amount`` for all COMPLETED payments linked to the provider's services).

    Raises:
        NotFoundError: If the user has no provider profile.
    """
    profile = get_provider_profile(user.id, session)
    if not profile:
        raise NotFoundError("Provider profile")

    services_published = int(
        session.exec(
            select(func.count())
            .select_from(Service)
            .where(Service.provider_id == user.id, Service.active == True)  # noqa: E712
        ).one()
        or 0
    )

    reservations_total = int(
        session.exec(
            select(func.count())
            .select_from(Reservation)
            .join(Service, Reservation.service_id == Service.id)
            .where(Service.provider_id == user.id)
        ).one()
        or 0
    )

    reservations_completed = int(
        session.exec(
            select(func.count())
            .select_from(Reservation)
            .join(Service, Reservation.service_id == Service.id)
            .where(
                Service.provider_id == user.id,
                Reservation.status == ReservationStatus.COMPLETED.value,
            )
        ).one()
        or 0
    )

    rating_row = session.exec(
        select(func.avg(ReservationReview.rating), func.count(ReservationReview.id))
        .select_from(ReservationReview)
        .join(Service, ReservationReview.service_id == Service.id)
        .where(Service.provider_id == user.id)
    ).one()

    rating_average = float(rating_row[0]) if rating_row[0] is not None else 0.0
    rating_count = int(rating_row[1]) if rating_row[1] is not None else 0

    revenue_row = session.exec(
        select(func.sum(Payment.net_amount))
        .select_from(Payment)
        .join(Service, Payment.service_id == Service.id)
        .where(
            Service.provider_id == user.id,
            Payment.status == PaymentStatus.COMPLETED,
        )
    ).one()
    total_revenue = float(revenue_row) if revenue_row is not None else 0.0

    return {
        "provider_id": profile.id,
        "totals": {
            "services_published": services_published,
            "reservations_total": reservations_total,
            "reservations_completed": reservations_completed,
            "favorites_count": 0,
        },
        "ratings": {
            "average": round(rating_average, 2),
            "count": rating_count,
        },
        "revenue": {
            "total": round(total_revenue, 2),
            "currency": "ARS",
        },
    }


def get_onboarding_status(user_id: int, session: Session) -> OnboardingStatus:
    """Calculate the completion percentage of a provider's onboarding.

    Args:
        user_id: ID of the user to check.
        session: Active database session.

    Returns:
        An ``OnboardingStatus`` with completion flag, percentage, and a list
        of missing field names.
    """
    profile = get_provider_profile(user_id, session)
    if not profile:
        return OnboardingStatus(
            completed=False,
            percent=0,
            missing=[
                "legal_name",
                "cuit_or_cuil",
                "tax_status",
                "has_invoice",
                "bank_alias_or_cbu",
            ],
        )

    missing: list[str] = []

    def _require(field: str, ok: bool) -> None:
        if not ok:
            missing.append(field)

    _require("legal_name", bool(profile.legal_name))
    _require("cuit_or_cuil", bool(profile.cuit_or_cuil))
    _require("tax_status", bool(profile.tax_status))
    _require("category", bool(profile.category))
    _require("service_areas", bool(profile.service_areas))
    _require("has_invoice", profile.has_invoice is True)
    _require("bank_alias_or_cbu", bool(profile.bank_alias or profile.bank_cbu))

    total = 7
    done = total - len(missing)
    percent = max(0, min(100, int((done / total) * 100)))
    return OnboardingStatus(completed=len(missing) == 0, percent=percent, missing=missing)
