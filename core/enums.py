# core/enums.py
from enum import Enum

class Role(str, Enum):
    USER = "USER"
    PROVIDER = "PROVIDER"
    ADMIN = "ADMIN"

class TaxStatus(str, Enum):
    MONOTRIBUTO = "MONOTRIBUTO"
    RESPONSABLE_INSCRIPTO = "RESPONSABLE_INSCRIPTO"
    EXENTO = "EXENTO"

# Opciones sugeridas para categorías y zonas de trabajo.
# Mantener sincronizadas con el frontend. Si en el futuro se modelan en BD,
# estas constantes pueden ser reemplazadas por una consulta.
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
