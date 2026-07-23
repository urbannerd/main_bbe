"""add stripe user indexes

Revision ID: 3bc876b2257d
Revises: 
Create Date: 2026-07-23 13:25:37.919752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bc876b2257d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_users_stripe_customer_id",
        "users",
        ["stripe_customer_id"],
        unique=True,
    )
    op.create_index(
        "ix_users_stripe_subscription_id",
        "users",
        ["stripe_subscription_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_users_stripe_subscription_id",
        table_name="users",
    )
    op.drop_index(
        "ix_users_stripe_customer_id",
        table_name="users",
    )
