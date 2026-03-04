"""Domain enumerations and static choice lists shared across the application.

Keep the static choice lists (CATEGORY_CHOICES, SERVICE_AREA_CHOICES) in sync
with the frontend until these are modelled as database tables.
"""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Platform roles assigned to user accounts."""

    USER = "USER"
    PROVIDER = "PROVIDER"
    ADMIN = "ADMIN"


class TaxStatus(str, Enum):
    """Argentine tax registration categories for providers."""

    MONOTRIBUTO = "MONOTRIBUTO"
    RESPONSABLE_INSCRIPTO = "RESPONSABLE_INSCRIPTO"
    EXENTO = "EXENTO"


class TipoArea(str, Enum):
    """Describes where a service is rendered.

    Values are stored in the database; do not rename without a migration.
    """

    CUSTOMER_LOCATION = "CUSTOMER_LOCATION"  # service goes to the client's address
    PROVIDER_LOCATION = "PROVIDER_LOCATION"  # client travels to the provider
    PRESENCIAL = "PRESENCIAL"                # on-site / physical location
    REMOTO = "REMOTO"                        # online / remote
    PERSONALIZADO = "PERSONALIZADO"          # free-text location_note required


# ---------------------------------------------------------------------------
# Static choice lists
# ---------------------------------------------------------------------------

CATEGORY_CHOICES: list[str] = [
    "Electricidad",
    "Plomería",
    "Pintura",
    "Carpintería",
    "Albañilería",
    "Jardinería",
    "Limpieza",
    "Gasista",
    "Herrería",
    "Mudanzas",
]

SERVICE_AREA_CHOICES: list[str] = [
    "CABA",
    "GBA Norte",
    "GBA Sur",
    "GBA Oeste",
    "La Plata",
    "Rosario",
    "Córdoba Capital",
]
