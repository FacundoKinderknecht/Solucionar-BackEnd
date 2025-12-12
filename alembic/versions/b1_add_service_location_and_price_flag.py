"""add service location_note and price_to_agree

Revision ID: b1add_serv_loc_price
Revises: a1c2seed_categories
Create Date: 2025-11-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1add_serv_loc_price'
down_revision = 'a1c2seed_categories'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('services') as batch:
        batch.add_column(sa.Column('location_note', sa.String(), nullable=True))
        batch.add_column(sa.Column('price_to_agree', sa.Boolean(), nullable=False, server_default=sa.false()))
    # map legacy area_type values if exist (optional safeguard)
    # no-op in SQL; keep existing values


def downgrade() -> None:
    with op.batch_alter_table('services') as batch:
        batch.drop_column('price_to_agree')
        batch.drop_column('location_note')
