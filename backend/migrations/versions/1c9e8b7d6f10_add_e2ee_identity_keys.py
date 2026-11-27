"""add E2EE identity public keys

Revision ID: 1c9e8b7d6f10
Revises: f95f1394a56e
"""
from alembic import op
import sqlalchemy as sa

revision = "1c9e8b7d6f10"
down_revision = "f95f1394a56e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crypto_identities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("public_key_jwk", sa.String(length=4096), nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_crypto_identity_user"),
    )
    op.create_index("ix_crypto_identities_user_id", "crypto_identities", ["user_id"])
    op.create_index("ix_crypto_identities_fingerprint", "crypto_identities", ["fingerprint"])


def downgrade() -> None:
    op.drop_index("ix_crypto_identities_fingerprint", table_name="crypto_identities")
    op.drop_index("ix_crypto_identities_user_id", table_name="crypto_identities")
    op.drop_table("crypto_identities")
