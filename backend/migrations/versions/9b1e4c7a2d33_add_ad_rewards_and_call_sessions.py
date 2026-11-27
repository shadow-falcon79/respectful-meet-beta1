"""add ad_rewards and call_sessions

Revision ID: 9b1e4c7a2d33
Revises: 2f7a8c9d0e11
Create Date: 2026-09-01 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '9b1e4c7a2d33'
down_revision: str | None = '2f7a8c9d0e11'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'ad_rewards',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('reward_type', sa.Enum('unlock_messages', 'extra_call_minutes', name='adrewardtype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'expired', 'failed', name='adrewardstatus'), nullable=False, server_default='pending'),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='mock'),
        sa.Column('external_ref', sa.String(length=128), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ad_rewards_user_id', 'ad_rewards', ['user_id'])
    op.create_index('ix_ad_rewards_external_ref', 'ad_rewards', ['external_ref'], unique=True)

    op.create_table(
        'call_sessions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('peer_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mode', sa.Enum('audio', 'video', name='callmode'), nullable=False, server_default='audio'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ended_reason', sa.String(length=30), nullable=True),
    )
    op.create_index('ix_call_sessions_conversation_id', 'call_sessions', ['conversation_id'])
    op.create_index('ix_call_sessions_user_id', 'call_sessions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_call_sessions_user_id', table_name='call_sessions')
    op.drop_index('ix_call_sessions_conversation_id', table_name='call_sessions')
    op.drop_table('call_sessions')
    op.execute('DROP TYPE IF EXISTS callmode')

    op.drop_index('ix_ad_rewards_external_ref', table_name='ad_rewards')
    op.drop_index('ix_ad_rewards_user_id', table_name='ad_rewards')
    op.drop_table('ad_rewards')
    op.execute('DROP TYPE IF EXISTS adrewardstatus')
    op.execute('DROP TYPE IF EXISTS adrewardtype')
