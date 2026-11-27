import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessageType(str, enum.Enum):
    TEXT = "TEXT"
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    type: Mapped[MessageType] = mapped_column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    # Plaintext is intentionally not persisted. `text` is retained only for
    # legacy rows created before E2EE migration; new rows must use ciphertext.
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sender_public_key_jwk: Mapped[str | None] = mapped_column(Text, nullable=True)
    crypto_version: Mapped[str] = mapped_column(String(16), default="v1", nullable=False)

    # Media (photo/video) lives in its own `media` table (Phase 6), linked
    # here by id — keeps text and media cleanly separable per the spec
    # (deleting a photo must never delete the message text).
    media_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
