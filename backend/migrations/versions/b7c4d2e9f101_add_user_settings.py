"""add user settings

Revision ID: b7c4d2e9f101
Revises: a1b2c3d4e5f6
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
revision: str = "b7c4d2e9f101"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="EN"),
        sa.Column("push_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("marketing_notifications", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("show_online_status", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("profile_discoverable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_age", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_city", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_age", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("max_age", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("discovery_radius_km", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("timezone", sa.String(80), nullable=False, server_default="UTC"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")
