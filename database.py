# ------------------------------------------------------------
# Conexión a la base de datos y utilidades de sesión.
# ------------------------------------------------------------
from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

SQLMODEL_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLMODEL_DATABASE_URL:
    # Fail-fast: si no hay URL, se avisa.
    raise RuntimeError("DATABASE_URL no está configurada en .env")

# pool_pre_ping=True mejora resiliencia con conexiones inactivas.
engine = create_engine(SQLMODEL_DATABASE_URL, pool_pre_ping=True)

def create_db_and_tables() -> None:
    """Crea todas las tablas definidas por SQLModel si no existen."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependencia de FastAPI: provee una sesión por request."""
    with Session(engine) as session:
        yield session
