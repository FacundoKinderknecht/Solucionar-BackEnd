"""Business logic for the service catalog domain.

Covers categories, service listings, images, and schedules.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from sqlmodel import Session, select

from app.core.enums import Role, TipoArea
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.models.service import Category, Service, ServiceImage, ServiceSchedule
from app.models.user import User
from app.schemas.service import (
    CategoryCreate,
    ServiceCreate,
    ServiceImageCreate,
    ServiceScheduleCreate,
    ServiceUpdate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


def create_category(data: CategoryCreate, user: User, session: Session) -> Category:
    """Create a new service category (admin only).

    Args:
        data: Validated category creation data.
        user: The authenticated admin user.
        session: Active database session.

    Returns:
        The newly created ``Category``.

    Raises:
        ForbiddenError: If the user is not an admin.
        ConflictError: If the slug already exists.
    """
    if user.role != Role.ADMIN:
        raise ForbiddenError("Admin access required")

    existing = session.exec(select(Category).where(Category.slug == data.slug)).first()
    if existing:
        raise ConflictError("A category with this slug already exists")

    category = Category(name=data.name, slug=data.slug, parent_id=data.parent_id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def list_categories(session: Session) -> list[Category]:
    """Return all categories ordered alphabetically by name.

    Args:
        session: Active database session.

    Returns:
        List of all ``Category`` records.
    """
    return session.exec(select(Category).order_by(Category.name)).all()


def get_category_or_404(cat_id: int, session: Session) -> Category:
    """Fetch a category by ID or raise HTTP 404.

    Args:
        cat_id: Primary key of the category.
        session: Active database session.

    Returns:
        The ``Category`` instance.

    Raises:
        NotFoundError: If the category does not exist.
    """
    cat = session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Category", cat_id)
    return cat


def delete_category(cat_id: int, user: User, session: Session) -> None:
    """Delete a category (admin only).

    Args:
        cat_id: Primary key of the category to delete.
        user: The authenticated admin user.
        session: Active database session.

    Raises:
        ForbiddenError: If the user is not an admin.
        NotFoundError: If the category does not exist.
    """
    if user.role != Role.ADMIN:
        raise ForbiddenError("Admin access required")
    cat = get_category_or_404(cat_id, session)
    session.delete(cat)
    session.commit()


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def _validate_service_data(
    title: Optional[str],
    description: Optional[str],
    price: Optional[float],
    price_to_agree: bool,
    duration_min: Optional[int],
    area_type: Optional[TipoArea],
    location_note: Optional[str],
    availability_start_date: Optional[date],
    availability_end_date: Optional[date],
) -> None:
    """Centralised validation shared by create and update service operations.

    Raises:
        BusinessRuleError: On any validation failure.
    """
    if title is not None and not title.strip():
        raise BusinessRuleError("title cannot be empty")
    if description is not None and not description.strip():
        raise BusinessRuleError("description cannot be empty")
    if price is not None and price <= 0:
        raise BusinessRuleError("price must be greater than 0")
    if duration_min is not None and duration_min < 0:
        raise BusinessRuleError("duration_min cannot be negative")
    if area_type == TipoArea.PERSONALIZADO and not location_note:
        raise BusinessRuleError("location_note is required when area_type is PERSONALIZADO")
    if availability_start_date and availability_end_date:
        if availability_start_date > availability_end_date:
            raise BusinessRuleError("availability_start_date cannot be later than availability_end_date")


def create_service(data: ServiceCreate, user: User, session: Session) -> Service:
    """Publish a new service listing for the given provider.

    Args:
        data: Validated service creation data.
        user: The authenticated provider user.
        session: Active database session.

    Returns:
        The newly created ``Service``.

    Raises:
        ForbiddenError: If the user is not a provider.
        BusinessRuleError: On validation failures.
    """
    if user.role != Role.PROVIDER:
        raise ForbiddenError("Only providers can create service listings")

    if data.price is None and not data.price_to_agree:
        raise BusinessRuleError("price is required unless price_to_agree is set to true")

    _validate_service_data(
        title=data.title,
        description=data.description,
        price=data.price,
        price_to_agree=data.price_to_agree,
        duration_min=data.duration_min,
        area_type=data.area_type,
        location_note=data.location_note,
        availability_start_date=data.availability_start_date,
        availability_end_date=data.availability_end_date,
    )

    cat = session.get(Category, data.category_id)
    if not cat:
        raise NotFoundError("Category", data.category_id)

    service = Service(
        provider_id=user.id,
        category_id=data.category_id,
        title=data.title.strip(),
        description=data.description.strip(),
        price=data.price if not data.price_to_agree else 0.0,
        currency=data.currency,
        duration_min=data.duration_min,
        area_type=data.area_type,
        location_note=data.location_note,
        price_to_agree=data.price_to_agree,
        radius_km=data.radius_km,
        availability_start_date=data.availability_start_date,
        availability_end_date=data.availability_end_date,
    )
    session.add(service)
    session.commit()
    session.refresh(service)
    logger.info("Service created: id=%s provider=%s", service.id, user.id)
    return service


def list_services(
    session: Session,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Service]:
    """Return paginated active service listings with optional filters.

    Args:
        session: Active database session.
        q: Optional full-text search term matched against the service title.
        category_id: Optional filter by category ID.
        limit: Maximum number of records to return (default 20, max 100).
        offset: Number of records to skip for pagination.

    Returns:
        List of matching ``Service`` records.
    """
    limit = min(limit, 100)
    stmt = select(Service).where(Service.active == True)  # noqa: E712
    if q:
        stmt = stmt.where(Service.title.ilike(f"%{q}%"))
    if category_id:
        stmt = stmt.where(Service.category_id == category_id)
    stmt = stmt.order_by(Service.created_at.desc()).limit(limit).offset(offset)
    return session.exec(stmt).all()


def list_my_services(
    user: User,
    session: Session,
    active: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Service]:
    """Return the caller's own service listings with optional active filter.

    Args:
        user: The authenticated provider or admin user.
        session: Active database session.
        active: If provided, filter by the service's active status.
        limit: Maximum records to return.
        offset: Pagination offset.

    Returns:
        List of ``Service`` records belonging to the caller.

    Raises:
        ForbiddenError: If the user is neither a provider nor an admin.
    """
    if user.role not in (Role.PROVIDER, Role.ADMIN):
        raise ForbiddenError("Only providers or admins can list their own services")
    stmt = select(Service)
    if user.role != Role.ADMIN:
        stmt = stmt.where(Service.provider_id == user.id)
    if active is not None:
        stmt = stmt.where(Service.active == active)
    stmt = stmt.order_by(Service.created_at.desc()).limit(limit).offset(offset)
    return session.exec(stmt).all()


def get_service_or_404(service_id: int, session: Session) -> Service:
    """Fetch an active service by ID or raise HTTP 404.

    Args:
        service_id: Primary key of the service.
        session: Active database session.

    Returns:
        The active ``Service`` instance.

    Raises:
        NotFoundError: If the service does not exist or is inactive.
    """
    svc = session.get(Service, service_id)
    if not svc or not svc.active:
        raise NotFoundError("Service", service_id)
    return svc


def update_service(
    service_id: int,
    data: ServiceUpdate,
    user: User,
    session: Session,
) -> Service:
    """Apply a partial update to a service listing.

    Args:
        service_id: Primary key of the service to update.
        data: Partial update payload.
        user: The authenticated provider or admin user.
        session: Active database session.

    Returns:
        The updated ``Service`` instance.

    Raises:
        ForbiddenError: If the caller does not own the service.
        NotFoundError: If the service does not exist.
        BusinessRuleError: On validation failures.
    """
    svc = get_service_or_404(service_id, session)
    if user.role != Role.ADMIN and svc.provider_id != user.id:
        raise ForbiddenError()

    start_date = data.availability_start_date if data.availability_start_date is not None else svc.availability_start_date
    end_date = data.availability_end_date if data.availability_end_date is not None else svc.availability_end_date

    _validate_service_data(
        title=data.title,
        description=data.description,
        price=data.price,
        price_to_agree=data.price_to_agree if data.price_to_agree is not None else svc.price_to_agree,
        duration_min=data.duration_min,
        area_type=data.area_type,
        location_note=data.location_note,
        availability_start_date=start_date,
        availability_end_date=end_date,
    )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(svc, field, value)

    session.add(svc)
    session.commit()
    session.refresh(svc)
    return svc


def deactivate_service(service_id: int, user: User, session: Session) -> None:
    """Soft-delete a service by marking it inactive.

    Args:
        service_id: Primary key of the service to deactivate.
        user: The authenticated provider or admin user.
        session: Active database session.

    Raises:
        ForbiddenError: If the caller does not own the service.
        NotFoundError: If the service does not exist.
    """
    svc = get_service_or_404(service_id, session)
    if user.role != Role.ADMIN and svc.provider_id != user.id:
        raise ForbiddenError()
    svc.active = False
    session.add(svc)
    session.commit()
    logger.info("Service deactivated: id=%s by user=%s", service_id, user.id)


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


def upsert_images(
    service_id: int,
    images: list[ServiceImageCreate],
    user: User,
    session: Session,
) -> list[ServiceImage]:
    """Replace all images for a service with the provided list.

    Args:
        service_id: Primary key of the service.
        images: New list of image input DTOs.
        user: The authenticated provider or admin user.
        session: Active database session.

    Returns:
        The persisted list of ``ServiceImage`` records ordered by sort_order.

    Raises:
        ForbiddenError: If the caller does not own the service.
        BusinessRuleError: If more than one image is marked as the cover.
    """
    svc = get_service_or_404(service_id, session)
    if user.role != Role.ADMIN and svc.provider_id != user.id:
        raise ForbiddenError()

    cover_count = sum(1 for img in images if img.is_cover)
    if cover_count > 1:
        raise BusinessRuleError("Only one image may be marked as the cover")

    old = session.exec(
        select(ServiceImage).where(ServiceImage.service_id == service_id)
    ).all()
    for old_img in old:
        session.delete(old_img)

    for dto in images:
        session.add(ServiceImage(service_id=service_id, **dto.model_dump()))

    session.commit()
    return session.exec(
        select(ServiceImage)
        .where(ServiceImage.service_id == service_id)
        .order_by(ServiceImage.sort_order)
    ).all()


def list_images(service_id: int, session: Session) -> list[ServiceImage]:
    """Return all images for a service ordered by sort_order.

    Args:
        service_id: Primary key of the service.
        session: Active database session.

    Returns:
        Ordered list of ``ServiceImage`` records.
    """
    return session.exec(
        select(ServiceImage)
        .where(ServiceImage.service_id == service_id)
        .order_by(ServiceImage.sort_order)
    ).all()


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------


def upsert_schedule(
    service_id: int,
    items: list[ServiceScheduleCreate],
    user: User,
    session: Session,
) -> list[ServiceSchedule]:
    """Replace all weekly schedule slots for a service.

    Args:
        service_id: Primary key of the service.
        items: New list of schedule slot input DTOs.
        user: The authenticated provider or admin user.
        session: Active database session.

    Returns:
        The persisted list of ``ServiceSchedule`` records ordered by weekday/time.

    Raises:
        ForbiddenError: If the caller does not own the service.
        BusinessRuleError: If any slot has an invalid weekday or inverted time range.
    """
    svc = get_service_or_404(service_id, session)
    if user.role != Role.ADMIN and svc.provider_id != user.id:
        raise ForbiddenError()

    for slot in items:
        if not (0 <= slot.weekday <= 6):
            raise BusinessRuleError("weekday must be between 0 (Monday) and 6 (Sunday)")
        if slot.time_from >= slot.time_to:
            raise BusinessRuleError("time_from must be earlier than time_to")

    old = session.exec(
        select(ServiceSchedule).where(ServiceSchedule.service_id == service_id)
    ).all()
    for old_slot in old:
        session.delete(old_slot)

    for dto in items:
        session.add(ServiceSchedule(service_id=service_id, **dto.model_dump()))

    session.commit()
    return session.exec(
        select(ServiceSchedule)
        .where(ServiceSchedule.service_id == service_id)
        .order_by(ServiceSchedule.weekday, ServiceSchedule.time_from)
    ).all()


def list_schedule(service_id: int, session: Session) -> list[ServiceSchedule]:
    """Return all weekly schedule slots for a service.

    Args:
        service_id: Primary key of the service.
        session: Active database session.

    Returns:
        Ordered list of ``ServiceSchedule`` records.
    """
    return session.exec(
        select(ServiceSchedule)
        .where(ServiceSchedule.service_id == service_id)
        .order_by(ServiceSchedule.weekday, ServiceSchedule.time_from)
    ).all()
