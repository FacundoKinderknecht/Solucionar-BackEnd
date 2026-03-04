"""Database engine and session factory.

Creates the SQLAlchemy/SQLModel engine from the DATABASE_URL setting and
exposes ``get_session`` as a FastAPI dependency.
"""
from __future__ import annotations

import logging

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    # Proactively test connections before using them from the pool,
    # improving resilience against idle connection drops.
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """Create all SQLModel-registered tables that do not yet exist.

    Called once at application startup via the lifespan handler.
    Schema evolution should be handled by Alembic migrations, not this
    function — it is kept only as a safety net for local development.
    """
    logger.info("Ensuring database tables exist...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables ready.")


def get_session():
    """FastAPI dependency that yields a database session per request.

    Yields:
        An open SQLModel ``Session`` that is automatically closed when
        the request finishes (whether it succeeded or raised an exception).
    """
    with Session(engine) as session:
        yield session
