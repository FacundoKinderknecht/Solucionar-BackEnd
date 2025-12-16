"""
Merge two c3 heads into a single head

Revision ID: d1_merge_c3_heads
Revises: c3_add_payments_table, c3add_service_avail
Create Date: 2025-12-14
"""
from __future__ import annotations
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd1_merge_c3_heads'
down_revision = ('c3_add_payments_table', 'c3add_service_avail')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # merge-only migration; no DB schema changes required
    pass


def downgrade() -> None:
    pass
