"""notification engagement and web push devices
Revision ID: a1b2c3d4e5f6
Revises: 9b1e4c7a2d33
"""
from alembic import op
import sqlalchemy as sa
revision="a1b2c3d4e5f6"
down_revision="9b1e4c7a2d33"
branch_labels=None
depends_on=None
def upgrade():
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'WELCOME'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'GUIDANCE'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ANNOUNCEMENT'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SAFETY'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'REENGAGEMENT'")
    op.add_column('notifications', sa.Column('push_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.alter_column('notifications','body',type_=sa.String(length=1000),existing_type=sa.String(length=500),existing_nullable=True)
    op.create_table('notification_devices',
      sa.Column('id',sa.String(36),primary_key=True),
      sa.Column('user_id',sa.String(36),nullable=False),
      sa.Column('endpoint',sa.String(2000),nullable=False),
      sa.Column('p256dh',sa.String(500),nullable=False),
      sa.Column('auth',sa.String(500),nullable=False),
      sa.Column('platform',sa.String(30),nullable=False),
      sa.Column('language',sa.String(10),nullable=False),
      sa.Column('timezone',sa.String(80),nullable=False),
      sa.Column('last_seen_at',sa.DateTime(timezone=True),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(['user_id'],['users.id'],ondelete='CASCADE'),
      sa.UniqueConstraint('endpoint'))
    op.create_index('ix_notification_devices_user_id','notification_devices',['user_id'])
def downgrade():
    op.drop_index('ix_notification_devices_user_id',table_name='notification_devices'); op.drop_table('notification_devices'); op.drop_column('notifications','push_sent_at')
