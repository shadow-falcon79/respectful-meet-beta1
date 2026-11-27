"""add E2EE message envelope fields

Revision ID: 2f7a8c9d0e11
Revises: 1c9e8b7d6f10
"""
from alembic import op
import sqlalchemy as sa
revision="2f7a8c9d0e11"
down_revision="1c9e8b7d6f10"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("messages", sa.Column("ciphertext", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("nonce", sa.String(length=64), nullable=True))
    op.add_column("messages", sa.Column("sender_public_key_jwk", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("crypto_version", sa.String(length=16), nullable=False, server_default="v1"))

def downgrade():
    op.drop_column("messages", "crypto_version")
    op.drop_column("messages", "sender_public_key_jwk")
    op.drop_column("messages", "nonce")
    op.drop_column("messages", "ciphertext")
