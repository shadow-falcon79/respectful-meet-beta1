import enum
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

PHOTO_RETENTION_DAYS = 7


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_photo_expiry() -> datetime:
    return _utcnow() + timedelta(days=PHOTO_RETENTION_DAYS)


class MediaType(str, enum.Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class Media(Base):
    """A photo (or, later, video) sent inside a conversation. Separate from
    `Photo` (profile pictures, which don't expire) — chat media is
    temporary per the spec (7 days for photos) and cleaned up by a
    periodic job (see services/media_cleanup.py).

    Deleting a Media row must never delete the Message it's attached to —
    the message text stays even if its media expires (spec section 65)."""

    __tablename__ = "media"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_default_photo_expiry, nullable=False)
