"""Alembic environment configuration.

Reads DATABASE_URL from the project .env file and imports all SQLModel
table models so that ``alembic --autogenerate`` can detect the full schema.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# ---------------------------------------------------------------------------
# Path & environment setup
# ---------------------------------------------------------------------------

# Ensure the project root (one level above alembic/) is on sys.path so that
# `app.*` imports work when Alembic is invoked from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from the canonical .env at the project root.
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Model registration — MUST happen before target_metadata is set
# ---------------------------------------------------------------------------

# Importing app.models registers every SQLModel table with SQLModel.metadata,
# which is required for `alembic revision --autogenerate` to work correctly.
import app.models  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Alembic config
# ---------------------------------------------------------------------------

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Make sure a .env file exists in the project root."
    )

target_metadata = SQLModel.metadata


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in offline mode (no live DB connection required).

    Configures the Alembic context with the connection URL only, which
    lets migration scripts be generated and inspected without a database.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode (connects to the live database)."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
