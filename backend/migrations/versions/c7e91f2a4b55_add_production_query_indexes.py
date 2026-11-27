"""add production query indexes

Revision ID: c7e91f2a4b55
Revises: b7c4d2e9f101
"""
from alembic import op

revision = "c7e91f2a4b55"
down_revision = "b7c4d2e9f101"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Feed exclusions, match detection and message/notification timelines are
    # hot paths. Composite indexes keep those lookups efficient as rows grow.
    op.create_index("ix_likes_from_to", "likes", ["from_user_id", "to_user_id"], unique=False)
    op.create_index("ix_likes_to_from", "likes", ["to_user_id", "from_user_id"], unique=False)
    op.create_index("ix_blocks_blocker_blocked", "blocks", ["blocker_id", "blocked_id"], unique=False)
    op.create_index("ix_blocks_blocked_blocker", "blocks", ["blocked_id", "blocker_id"], unique=False)
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at", "id"], unique=False)
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_index("ix_blocks_blocked_blocker", table_name="blocks")
    op.drop_index("ix_blocks_blocker_blocked", table_name="blocks")
    op.drop_index("ix_likes_to_from", table_name="likes")
    op.drop_index("ix_likes_from_to", table_name="likes")
