"""
Initial schema: users, provider_profiles

Revision ID: 8f3d3e9c3b1a
Revises: 
Create Date: 2025-11-05
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8f3d3e9c3b1a'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('province', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='USER'),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'provider_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('cuit_or_cuil', sa.String(length=32), nullable=False),
        sa.Column('tax_status', sa.String(length=50), nullable=False),
        sa.Column('fiscal_address', sa.String(length=255), nullable=True),
        sa.Column('service_areas', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('has_invoice', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('bank_alias', sa.String(length=64), nullable=True),
        sa.Column('bank_cbu', sa.String(length=22), nullable=True),
        sa.UniqueConstraint('user_id', name='uq_provider_user'),
    )
    op.create_index('ix_provider_cuit', 'provider_profiles', ['cuit_or_cuil'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_provider_cuit', table_name='provider_profiles')
    op.drop_table('provider_profiles')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
