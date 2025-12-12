"""
Seed default categories

Revision ID: a1c2seed_categories
Revises: 9b7a1a2f4c2a
Create Date: 2025-11-07
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = 'a1c2seed_categories'
down_revision = '9b7a1a2f4c2a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    existing = {r[0] for r in conn.execute(sa.text("SELECT slug FROM categories"))}
    data = [
        ("electricidad", "Electricidad"),
        ("plomeria", "Plomería"),
        ("pintura", "Pintura"),
        ("carpinteria", "Carpintería"),
        ("albanileria", "Albañilería"),
        ("jardineria", "Jardinería"),
        ("limpieza", "Limpieza"),
        ("gasista", "Gasista"),
        ("herreria", "Herrería"),
        ("mudanzas", "Mudanzas"),
    ]
    for slug, name in data:
        if slug not in existing:
            conn.execute(sa.text("INSERT INTO categories (name, slug) VALUES (:name, :slug)"), {"name": name, "slug": slug})

def downgrade() -> None:
    # No se eliminan para evitar perder datos referenciados
    pass