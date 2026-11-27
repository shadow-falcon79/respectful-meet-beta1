import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

def _utcnow() -> datetime: return datetime.now(timezone.utc)

class NotificationType(str, enum.Enum):
    LIKE="LIKE"; MATCH="MATCH"; MESSAGE="MESSAGE"; PAYMENT="PAYMENT"; SUBSCRIPTION_EXPIRING="SUBSCRIPTION_EXPIRING"; REPORT="REPORT"; SYSTEM="SYSTEM"
    WELCOME="WELCOME"; GUIDANCE="GUIDANCE"; ANNOUNCEMENT="ANNOUNCEMENT"; SAFETY="SAFETY"; REENGAGEMENT="REENGAGEMENT"

class Notification(Base):
    __tablename__="notifications"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    user_id: Mapped[str]=mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType]=mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str]=mapped_column(String(255), nullable=False)
    body: Mapped[str|None]=mapped_column(String(1000), nullable=True)
    is_read: Mapped[bool]=mapped_column(Boolean, default=False, nullable=False)
    push_sent_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

class NotificationDevice(Base):
    __tablename__="notification_devices"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    user_id: Mapped[str]=mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint: Mapped[str]=mapped_column(String(2000), nullable=False, unique=True)
    p256dh: Mapped[str]=mapped_column(String(500), nullable=False)
    auth: Mapped[str]=mapped_column(String(500), nullable=False)
    platform: Mapped[str]=mapped_column(String(30), nullable=False, default="web")
    language: Mapped[str]=mapped_column(String(10), nullable=False, default="EN")
    timezone: Mapped[str]=mapped_column(String(80), nullable=False, default="UTC")
    last_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
