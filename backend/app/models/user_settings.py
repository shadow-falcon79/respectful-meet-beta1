import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class UserSettings(Base):
    __tablename__ = "user_settings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="EN")
    push_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    marketing_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_online_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    profile_discoverable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_age: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_city: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_age: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    max_age: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    discovery_radius_km: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
