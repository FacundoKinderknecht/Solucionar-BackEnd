"""Provider profile endpoints: onboarding, profile management, and dashboard."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import SessionDep, get_current_user
from app.models.user import User
from app.schemas.provider import OnboardingStatus, ProviderPublic, ProviderUpsertRequest
from app.services.provider import (
    get_onboarding_status,
    get_provider_dashboard,
    get_provider_profile,
    upsert_provider_profile,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get(
    "/me",
    response_model=ProviderPublic | None,
    summary="Return the provider profile of the authenticated user",
)
def get_my_provider(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> ProviderPublic | None:
    """Return the provider profile for the authenticated user, or null if none exists.

    Args:
        current_user: Authenticated user extracted from the Bearer token.
        session: Database session injected by FastAPI.

    Returns:
        The ``ProviderPublic`` profile, or ``None`` if onboarding is incomplete.
    """
    profile = get_provider_profile(current_user.id, session)
    if not profile:
        return None
    return ProviderPublic(
        id=profile.id,
        user_id=profile.user_id,
        legal_name=profile.legal_name,
        cuit_or_cuil=profile.cuit_or_cuil,
        tax_status=profile.tax_status,
        category=profile.category,
        fiscal_address=profile.fiscal_address,
        service_areas=profile.service_areas,
        has_invoice=profile.has_invoice,
        bank_alias=profile.bank_alias,
        bank_cbu=profile.bank_cbu,
    )


@router.put(
    "/me",
    response_model=ProviderPublic,
    summary="Create or update the authenticated user's provider profile",
)
def upsert_my_provider(
    payload: ProviderUpsertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> ProviderPublic:
    """Create or update the provider profile and elevate the user's role to PROVIDER.

    Args:
        payload: Provider profile data to upsert.
        current_user: Authenticated user extracted from the Bearer token.
        session: Database session injected by FastAPI.

    Returns:
        The created or updated ``ProviderPublic`` profile.
    """
    profile = upsert_provider_profile(current_user, payload, session)
    return ProviderPublic(
        id=profile.id,
        user_id=profile.user_id,
        legal_name=profile.legal_name,
        cuit_or_cuil=profile.cuit_or_cuil,
        tax_status=profile.tax_status,
        category=profile.category,
        fiscal_address=profile.fiscal_address,
        service_areas=profile.service_areas,
        has_invoice=profile.has_invoice,
        bank_alias=profile.bank_alias,
        bank_cbu=profile.bank_cbu,
    )


@router.get(
    "/me/status",
    response_model=OnboardingStatus,
    summary="Return the onboarding completion status for the provider",
)
def provider_onboarding_status(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> OnboardingStatus:
    """Calculate and return the provider onboarding completion percentage.

    Args:
        current_user: Authenticated user extracted from the Bearer token.
        session: Database session injected by FastAPI.

    Returns:
        An ``OnboardingStatus`` with completion flag, percentage, and missing fields.
    """
    return get_onboarding_status(current_user.id, session)


@router.get(
    "/me/dashboard",
    summary="Return aggregated metrics for the authenticated provider",
)
def provider_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> dict:
    """Return basic dashboard metrics for the authenticated provider.

    Args:
        current_user: Authenticated user extracted from the Bearer token.
        session: Database session injected by FastAPI.

    Returns:
        A dict with totals, ratings, and revenue summaries.
    """
    return get_provider_dashboard(current_user, session)
