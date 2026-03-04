"""Service catalog endpoints: categories, listings, images, and schedules."""
from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, get_current_user
from app.models.service import Category, Service, ServiceImage, ServiceSchedule
from app.models.user import User
from app.schemas.service import (
    CategoryCreate,
    ServiceCreate,
    ServiceImageCreate,
    ServiceScheduleCreate,
    ServiceUpdate,
)
from app.services.service import (
    create_category,
    create_service,
    deactivate_service,
    delete_category,
    get_category_or_404,
    get_service_or_404,
    list_categories,
    list_images,
    list_my_services,
    list_schedule,
    list_services,
    update_service,
    upsert_images,
    upsert_schedule,
)

router = APIRouter(prefix="/services", tags=["services"])


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.post(
    "/categories",
    response_model=Category,
    status_code=201,
    summary="Create a new service category (admin only)",
)
def create_category_endpoint(
    payload: CategoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> Category:
    """Create a new service category.

    Args:
        payload: Category creation data.
        current_user: Authenticated admin user.
        session: Database session.

    Returns:
        The newly created ``Category``.
    """
    return create_category(payload, current_user, session)


@router.get(
    "/categories",
    response_model=List[Category],
    summary="List all service categories",
)
def list_categories_endpoint(session: SessionDep) -> List[Category]:
    """Return all service categories ordered alphabetically.

    Args:
        session: Database session.

    Returns:
        Full list of ``Category`` records.
    """
    return list_categories(session)


@router.get(
    "/categories/{cat_id}",
    response_model=Category,
    summary="Get a single service category by ID",
)
def get_category_endpoint(cat_id: int, session: SessionDep) -> Category:
    """Fetch a service category by its primary key.

    Args:
        cat_id: Category primary key.
        session: Database session.

    Returns:
        The matching ``Category``.
    """
    return get_category_or_404(cat_id, session)


@router.delete(
    "/categories/{cat_id}",
    status_code=204,
    summary="Delete a service category (admin only)",
)
def delete_category_endpoint(
    cat_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> None:
    """Delete a service category.

    Args:
        cat_id: Category primary key.
        current_user: Authenticated admin user.
        session: Database session.
    """
    delete_category(cat_id, current_user, session)


# ---------------------------------------------------------------------------
# Service listings
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=Service,
    status_code=201,
    summary="Create a new service listing (providers only)",
)
@router.post("", response_model=Service, status_code=201, include_in_schema=False)
def create_service_endpoint(
    payload: ServiceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> Service:
    """Publish a new service listing.

    Args:
        payload: Service creation data.
        current_user: Authenticated provider user.
        session: Database session.

    Returns:
        The newly created ``Service``.
    """
    return create_service(payload, current_user, session)


@router.get(
    "/",
    response_model=List[Service],
    summary="List active service listings with optional search and pagination",
)
@router.get("", response_model=List[Service], include_in_schema=False)
def list_services_endpoint(
    session: SessionDep,
    q: Optional[str] = Query(None, description="Search term matched against service title"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> List[Service]:
    """Return paginated active service listings.

    Args:
        session: Database session.
        q: Optional search term.
        category_id: Optional category filter.
        limit: Page size (1–100).
        offset: Number of records to skip.

    Returns:
        Filtered and paginated list of active ``Service`` records.
    """
    return list_services(session, q=q, category_id=category_id, limit=limit, offset=offset)


@router.get(
    "/mine",
    response_model=List[Service],
    summary="List the authenticated provider's own service listings",
)
def list_my_services_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Service]:
    """Return the caller's own service listings.

    Args:
        current_user: Authenticated provider or admin user.
        session: Database session.
        active: Optional filter by active status.
        limit: Page size.
        offset: Pagination offset.

    Returns:
        Filtered list of the caller's ``Service`` records.
    """
    return list_my_services(current_user, session, active=active, limit=limit, offset=offset)


@router.get(
    "/{service_id}",
    response_model=Service,
    summary="Get a single active service by ID",
)
def get_service_endpoint(service_id: int, session: SessionDep) -> Service:
    """Fetch an active service listing by its primary key.

    Args:
        service_id: Service primary key.
        session: Database session.

    Returns:
        The matching ``Service``.
    """
    return get_service_or_404(service_id, session)


@router.put(
    "/{service_id}",
    response_model=Service,
    summary="Update an existing service listing",
)
def update_service_endpoint(
    service_id: int,
    payload: ServiceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> Service:
    """Partially update a service listing.

    Args:
        service_id: Service primary key.
        payload: Partial update data.
        current_user: Authenticated provider or admin user.
        session: Database session.

    Returns:
        The updated ``Service``.
    """
    return update_service(service_id, payload, current_user, session)


@router.delete(
    "/{service_id}",
    status_code=204,
    summary="Deactivate (soft-delete) a service listing",
)
def deactivate_service_endpoint(
    service_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> None:
    """Soft-delete a service by marking it as inactive.

    Args:
        service_id: Service primary key.
        current_user: Authenticated provider or admin user.
        session: Database session.
    """
    deactivate_service(service_id, current_user, session)


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


@router.post(
    "/{service_id}/images",
    response_model=List[ServiceImage],
    summary="Replace all images for a service listing",
)
def upsert_images_endpoint(
    service_id: int,
    images: List[ServiceImageCreate],
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> List[ServiceImage]:
    """Replace the full set of images for a service.

    Args:
        service_id: Service primary key.
        images: New image list; replaces all existing images.
        current_user: Authenticated provider or admin user.
        session: Database session.

    Returns:
        The updated list of ``ServiceImage`` records ordered by sort_order.
    """
    return upsert_images(service_id, images, current_user, session)


@router.get(
    "/{service_id}/images",
    response_model=List[ServiceImage],
    summary="List all images for a service",
)
def list_images_endpoint(service_id: int, session: SessionDep) -> List[ServiceImage]:
    """Return all images for a service ordered by sort_order.

    Args:
        service_id: Service primary key.
        session: Database session.

    Returns:
        Ordered list of ``ServiceImage`` records.
    """
    return list_images(service_id, session)


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------


@router.post(
    "/{service_id}/schedule",
    response_model=List[ServiceSchedule],
    summary="Replace the weekly schedule for a service",
)
def upsert_schedule_endpoint(
    service_id: int,
    items: List[ServiceScheduleCreate],
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
) -> List[ServiceSchedule]:
    """Replace the full weekly availability schedule for a service.

    Args:
        service_id: Service primary key.
        items: New schedule slots; replaces all existing slots.
        current_user: Authenticated provider or admin user.
        session: Database session.

    Returns:
        The updated list of ``ServiceSchedule`` records.
    """
    return upsert_schedule(service_id, items, current_user, session)


@router.get(
    "/{service_id}/schedule",
    response_model=List[ServiceSchedule],
    summary="List the weekly schedule for a service",
)
def list_schedule_endpoint(
    service_id: int, session: SessionDep
) -> List[ServiceSchedule]:
    """Return all weekly time slots for a service ordered by weekday and time.

    Args:
        service_id: Service primary key.
        session: Database session.

    Returns:
        Ordered list of ``ServiceSchedule`` records.
    """
    return list_schedule(service_id, session)
