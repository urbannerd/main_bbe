"""merge admin and email verification heads

Revision ID: b14c0c041c74
Revises: 71c7adbdd687, af77fb93b57e
Create Date: 2026-08-04 21:56:02.658173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b14c0c041c74'
down_revision: Union[str, Sequence[str], None] = ('71c7adbdd687', 'af77fb93b57e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
