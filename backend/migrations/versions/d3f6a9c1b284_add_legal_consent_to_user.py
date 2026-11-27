"""add terms/privacy consent timestamps to user

Revision ID: d3f6a9c1b284
Revises: c7e91f2a4b55
"""
import sqlalchemy as sa
from alembic import op

revision = "d3f6a9c1b284"
down_revision = "c7e91f2a4b55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable: existing rows (pre-launch test accounts) have no consent
    # event to backfill honestly. New registrations always populate both
    # from now on — enforced in app/api/v1/auth.py, not just at the DB
    # layer, so the API rejects registration without acceptance rather
    # than silently storing NULL.
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("privacy_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("terms_version", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "terms_version")
    op.drop_column("users", "privacy_accepted_at")
    op.drop_column("users", "terms_accepted_at")
