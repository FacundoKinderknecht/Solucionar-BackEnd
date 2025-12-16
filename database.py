# ------------------------------------------------------------
# Conexión a la base de datos y utilidades de sesión.
# ------------------------------------------------------------
from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path
import os

# Cargar .env desde la carpeta del backend (misma carpeta que este archivo)
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

SQLMODEL_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLMODEL_DATABASE_URL:
    # Fail-fast: si no hay URL, se avisa.
    raise RuntimeError("DATABASE_URL no está configurada en .env")

# pool_pre_ping=True mejora resiliencia con conexiones inactivas.
engine = create_engine(SQLMODEL_DATABASE_URL, pool_pre_ping=True)

def _normalize_reservation_status_enum() -> None:
    """Asegura que los valores del enum reservationstatus sean minúsculos (pending, confirmed, ...)."""
    if engine.url.get_backend_name() != "postgresql":
        return

    renames = [
        ("PENDING", "pending"),
        ("CONFIRMED", "confirmed"),
        ("CANCELLED_BY_CLIENT", "cancelled_by_client"),
        ("CANCELLED_BY_PROVIDER", "cancelled_by_provider"),
        ("COMPLETED", "completed"),
    ]

    with engine.begin() as conn:
        for old_value, new_value in renames:
            # ¿Existe el valor en mayúsculas?
            has_old = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = :type_name AND e.enumlabel = :label
                    LIMIT 1
                    """
                ),
                {"type_name": "reservationstatus", "label": old_value},
            ).first()

            if not has_old:
                continue

            # Si ya existe el valor nuevo, no se puede renombrar.
            has_new = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = :type_name AND e.enumlabel = :label
                    LIMIT 1
                    """
                ),
                {"type_name": "reservationstatus", "label": new_value},
            ).first()

            if has_new:
                continue

            conn.exec_driver_sql(
                f"ALTER TYPE reservationstatus RENAME VALUE '{old_value}' TO '{new_value}'"
            )


def create_db_and_tables() -> None:
    """Crea todas las tablas definidas por SQLModel si no existen."""
    SQLModel.metadata.create_all(engine)
    _normalize_reservation_status_enum()

"""
Las migraciones en tiempo de ejecución fueron retiradas para evitar SQL crudo.
Usá una herramienta de migraciones (por ejemplo, Alembic) para evolucionar el esquema.
"""

def get_session():
    """Dependencia de FastAPI: provee una sesión por request."""
    with Session(engine) as session:
        yield session
