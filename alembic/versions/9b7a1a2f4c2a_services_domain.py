"""
Services domain: categories, services, images, schedules

Revision ID: 9b7a1a2f4c2a
Revises: 8f3d3e9c3b1a
Create Date: 2025-11-07
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9b7a1a2f4c2a'
down_revision = '8f3d3e9c3b1a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('slug', sa.String(length=255), nullable=False),
    )
    op.create_index('ix_categories_name', 'categories', ['name'], unique=False)
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)

    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price', sa.Numeric(12,2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='ARS'),
        sa.Column('duration_min', sa.Integer(), nullable=False),
        sa.Column('area_type', sa.String(length=32), nullable=False, server_default='CUSTOMER_LOCATION'),
        sa.Column('radius_km', sa.Numeric(6,2), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_services_provider', 'services', ['provider_id'], unique=False)
    op.create_index('ix_services_category', 'services', ['category_id'], unique=False)

    op.create_table(
        'service_images',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('is_cover', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_service_images_service', 'service_images', ['service_id'], unique=False)

    op.create_table(
        'service_schedules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=False),
        sa.Column('time_from', sa.Time(timezone=False), nullable=False),
        sa.Column('time_to', sa.Time(timezone=False), nullable=False),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='America/Argentina/Buenos_Aires'),
    )
    op.create_index('ix_service_schedules_service', 'service_schedules', ['service_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_service_schedules_service', table_name='service_schedules')
    op.drop_table('service_schedules')

    op.drop_index('ix_service_images_service', table_name='service_images')
    op.drop_table('service_images')

    op.drop_index('ix_services_category', table_name='services')
    op.drop_index('ix_services_provider', table_name='services')
    op.drop_table('services')

    op.drop_index('ix_categories_slug', table_name='categories')
    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_table('categories')
