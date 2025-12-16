"""
Add payments table

Revision ID: c3_add_payments_table
Revises: b2add_tipoarea_vals
Create Date: 2025-12-14
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3_add_payments_table'
down_revision = 'b2add_tipoarea_vals'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('reservation_id', sa.Integer(), sa.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gateway', sa.String(length=32), nullable=False),
        sa.Column('monto', sa.Numeric(12, 2), nullable=False),
        sa.Column('moneda', sa.String(length=3), nullable=False, server_default='ARS'),
        sa.Column('comision', sa.Numeric(12, 2), nullable=True),
        sa.Column('neto', sa.Numeric(12, 2), nullable=True),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('estado', sa.String(length=32), nullable=False, server_default='initialized'),
        sa.Column('creado_en', sa.DateTime(timezone=False), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('actualizado_en', sa.DateTime(timezone=False), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_payments_reservation', 'payments', ['reservation_id'], unique=False)
    op.create_index('ix_payments_external_reference', 'payments', ['external_reference'], unique=False)
    op.create_index('ix_payments_transaction', 'payments', ['transaction_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_payments_transaction', table_name='payments')
    op.drop_index('ix_payments_external_reference', table_name='payments')
    op.drop_index('ix_payments_reservation', table_name='payments')
    op.drop_table('payments')
