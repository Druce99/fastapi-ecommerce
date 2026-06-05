"""add payment_id to orders

Revision ID: 597b2e8b1859
Revises: c321c25922c1
Create Date: 2026-06-05 11:51:17.322391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '597b2e8b1859'
down_revision: Union[str, Sequence[str], None] = 'c321c25922c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('payment_id', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'payment_id')
