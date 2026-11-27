"""add username and password authentication

Revision ID: e4a7b9c2d1f3
Revises: d3f6a9c1b284
"""
from alembic import op
import sqlalchemy as sa

revision = "e4a7b9c2d1f3"
down_revision = "d3f6a9c1b284"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

    # Preserve existing beta/admin rows with a deterministic unique username.
    op.execute(sa.text("""
        UPDATE users
        SET username = left(
            lower(regexp_replace(coalesce(split_part(email, '@', 1), 'user'), '[^a-zA-Z0-9_-]+', '_', 'g'))
            || '_' || left(replace(id, '-', ''), 8),
            50
        )
        WHERE username IS NULL
    """))
    op.alter_column("users", "username", nullable=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # User emails are no longer required for the Beta password account flow.
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=False)
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
