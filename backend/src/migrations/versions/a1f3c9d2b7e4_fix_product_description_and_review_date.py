"""fix product description nullability and review date timezone

Revision ID: a1f3c9d2b7e4
Revises: 597b2e8b1859
Create Date: 2026-11-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1f3c9d2b7e4'
down_revision: Union[str, Sequence[str], None] = '597b2e8b1859'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Описание товара необязательно (ProductCreate.description: str | None)
    op.alter_column('products', 'description', existing_type=sa.String(length=500), nullable=True)
    # Дата отзыва хранилась без часового пояса, а приложение пишет aware-datetime (UTC)
    op.alter_column(
        'reviews',
        'comment_date',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="comment_date AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        'reviews',
        'comment_date',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        postgresql_using="comment_date AT TIME ZONE 'UTC'",
    )
    op.execute("UPDATE products SET description = '' WHERE description IS NULL")
    op.alter_column('products', 'description', existing_type=sa.String(length=500), nullable=False)
