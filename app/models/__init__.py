"""Expose all SQLModel table models so that Alembic autogenerate can discover them.

Importing this package registers every model's metadata with
``SQLModel.metadata``, which is required for ``alembic --autogenerate``
to detect all tables.
"""
from app.models.user import User as User
from app.models.provider import ProviderProfile as ProviderProfile
from app.models.service import (
    Category as Category,
    Service as Service,
    ServiceImage as ServiceImage,
    ServiceSchedule as ServiceSchedule,
)
from app.models.reservation import (
    Reservation as Reservation,
    ReservationStatus as ReservationStatus,
)
from app.models.review import ReservationReview as ReservationReview
from app.models.payment import (
    Payment as Payment,
    PaymentGateway as PaymentGateway,
    PaymentStatus as PaymentStatus,
    TransactionStatus as TransactionStatus,
)

__all__ = [
    "User",
    "ProviderProfile",
    "Category",
    "Service",
    "ServiceImage",
    "ServiceSchedule",
    "Reservation",
    "ReservationStatus",
    "ReservationReview",
    "Payment",
    "PaymentGateway",
    "PaymentStatus",
    "TransactionStatus",
]
