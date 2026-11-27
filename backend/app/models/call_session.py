import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CallMode(str, enum.Enum):
    AUDIO = "audio"
    VIDEO = "video"


class CallSession(Base):
    """One completed (or ongoing) call, used to enforce the daily per-plan
    minutes quota server-side. The server never sees media — only the
    signalling timeline — so duration is measured from 'offer' (call
    actually connecting) to hangup/disconnect.
    """

    __tablename__ = "call_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    peer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    mode = Column(Enum(CallMode), nullable=False, default=CallMode.AUDIO)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=False, default=0)
    ended_reason = Column(String(30), nullable=True)  # hangup | peer_left | quota_exceeded | disconnect

    user = relationship("User", foreign_keys=[user_id])
