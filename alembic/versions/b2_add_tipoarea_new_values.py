"""add new values to tipoarea enum: PRESENCIAL, REMOTO, PERSONALIZADO

Revision ID: b2add_tipoarea_vals
Revises: b1add_serv_loc_price
Create Date: 2025-11-07
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b2add_tipoarea_vals'
down_revision = 'b1add_serv_loc_price'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add enum values if not existing
    op.execute("ALTER TYPE tipoarea ADD VALUE IF NOT EXISTS 'PRESENCIAL'")
    op.execute("ALTER TYPE tipoarea ADD VALUE IF NOT EXISTS 'REMOTO'")
    op.execute("ALTER TYPE tipoarea ADD VALUE IF NOT EXISTS 'PERSONALIZADO'")


def downgrade() -> None:
    # Cannot easily drop enum values in Postgres without complex type recreation
    pass
