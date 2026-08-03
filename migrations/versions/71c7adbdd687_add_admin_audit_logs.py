"""add admin audit logs

Revision ID: 71c7adbdd687
Revises: 13c22d281237
Create Date: 2026-08-03 14:35:31.981540
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "71c7adbdd687"
down_revision: Union[str, Sequence[str], None] = "13c22d281237"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("admin_email", sa.String(length=320), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("target_email", sa.String(length=320), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["admin_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_admin_audit_logs_action",
        "admin_audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_admin_email",
        "admin_audit_logs",
        ["admin_email"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_admin_user_id",
        "admin_audit_logs",
        ["admin_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_created_at",
        "admin_audit_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_id",
        "admin_audit_logs",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_target_email",
        "admin_audit_logs",
        ["target_email"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_target_user_id",
        "admin_audit_logs",
        ["target_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_admin_audit_logs_target_user_id",
        table_name="admin_audit_logs",
    )
    op.drop_index(
        "ix_admin_audit_logs_target_email",
        table_name="admin_audit_logs",
    )
    op.drop_index(
        "ix_admin_audit_logs_id",
        table_name="admin_audit_logs",
    )
    op.drop_index(
        "ix_admin_audit_logs_created_at",
        table_name="admin_audit_logs",
    )
    op.drop_index(
        "ix_admin_audit_logs_admin_user_id",
        table_name="admin_audit_logs",
    )
    op.drop_index(
        "ix_admin_audit_logs_admin_email",
        table_name="admin_audit_logs",
    )
    op.drop_index(
        "ix_admin_audit_logs_action",
        table_name="admin_audit_logs",
    )
    op.drop_table("admin_audit_logs")