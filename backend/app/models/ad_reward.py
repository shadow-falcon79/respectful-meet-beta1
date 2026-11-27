import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AdRewardType(str, enum.Enum):
    UNLOCK_MESSAGES = "unlock_messages"   # bonus messages for one conversation
    EXTRA_CALL_MINUTES = "extra_call_minutes"  # bonus call minutes for today


class AdRewardStatus(str, enum.Enum):
    PENDING = "pending"       # ad session created, watch not confirmed yet
    COMPLETED = "completed"   # provider postback (or verified mock) confirmed the view
    EXPIRED = "expired"       # never confirmed within the time window
    FAILED = "failed"         # provider reported an invalid/fraudulent view


class AdReward(Base):
    """One rewarded-ad session. Mirrors the real flow we'll use with an
    offerwall provider (e.g. AdMantum): we open a session, the provider
    later confirms completion via a signed server-to-server postback, and
    only then do we grant the reward. Never grant on the client's say-so.
    """

    __tablename__ = "ad_rewards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)

    reward_type = Column(Enum(AdRewardType), nullable=False)
    status = Column(Enum(AdRewardStatus), nullable=False, default=AdRewardStatus.PENDING)

    provider = Column(String(50), nullable=False, default="mock")
    # Provider's own click/session id — this is what their postback references.
    external_ref = Column(String(128), nullable=False, unique=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    conversation = relationship("Conversation")
