"""
Placeholder migration to satisfy missing revision reference

Revision ID: c3add_service_avail
Revises: b2add_tipoarea_vals
Create Date: 2025-12-14
"""
from __future__ import annotations
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c3add_service_avail'
down_revision = 'b2add_tipoarea_vals'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is an empty placeholder migration. The original migration
    # referenced by this revision ID is missing from the repository.
    # Creating this no-op revision allows Alembic to continue applying
    # later migrations without modifying the database schema.
    pass


def downgrade() -> None:
    pass
