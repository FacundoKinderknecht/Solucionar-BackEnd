"""
Add transaction_status and gateway_response to payments

Revision ID: e3_add_txn_status
Revises: e2_modify_payments_table
Create Date: 2025-12-14
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3_add_txn_status'
down_revision = 'e2_modify_payments_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('payments') as batch:
        batch.add_column(sa.Column('transaction_status', sa.String(length=32), nullable=True))
        batch.add_column(sa.Column('gateway_response', sa.JSON(), nullable=True))

    op.create_index('ix_payments_transaction_status', 'payments', ['transaction_status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_payments_transaction_status', table_name='payments')
    with op.batch_alter_table('payments') as batch:
        batch.drop_column('gateway_response')
        batch.drop_column('transaction_status')
