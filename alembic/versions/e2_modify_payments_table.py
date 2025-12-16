"""
Modify payments table to support reservation intent

Revision ID: e2_modify_payments_table
Revises: d1_merge_c3_heads
Create Date: 2025-12-14
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2_modify_payments_table'
down_revision = 'd1_merge_c3_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client_id (FK -> users.id)
    with op.batch_alter_table('payments') as batch:
        batch.add_column(sa.Column('client_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('service_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('reservation_datetime', sa.DateTime(timezone=False), nullable=True))
        batch.add_column(sa.Column('notes', sa.Text(), nullable=True))

    # create FK constraints separately to avoid issues in some DBs
    op.create_foreign_key('fk_payments_client_users', 'payments', 'users', ['client_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_payments_service', 'payments', 'services', ['service_id'], ['id'], ondelete='SET NULL')

    # Make reservation_id nullable (it was created non-nullable previously)
    with op.batch_alter_table('payments') as batch:
        batch.alter_column('reservation_id', existing_type=sa.Integer(), nullable=True)

    # Add indexes
    op.create_index('ix_payments_client', 'payments', ['client_id'], unique=False)
    op.create_index('ix_payments_service', 'payments', ['service_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_payments_service', table_name='payments')
    op.drop_index('ix_payments_client', table_name='payments')

    with op.batch_alter_table('payments') as batch:
        batch.alter_column('reservation_id', existing_type=sa.Integer(), nullable=False)

    op.drop_constraint('fk_payments_service', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_client_users', 'payments', type_='foreignkey')

    with op.batch_alter_table('payments') as batch:
        batch.drop_column('notes')
        batch.drop_column('reservation_datetime')
        batch.drop_column('service_id')
        batch.drop_column('client_id')
