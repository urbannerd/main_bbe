"""backfill legacy email verification

Revision ID: 33dfc5056243
Revises: b14c0c041c74
Create Date: 2026-08-04 22:46:33.602730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33dfc5056243'
down_revision: Union[str, Sequence[str], None] = 'b14c0c041c74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET email_verified = 1
        WHERE email_verified = 0
          AND created_at < '2026-08-05 00:00:00'
        """
    )


def downgrade() -> None:
    # Intentionally irreversible because we cannot safely distinguish
    # users changed by this migration from users verified previously.
    pass