import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionPlan(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Subscription(Base):
    """The backend's single source of truth for Premium status (master
    spec section 12/50): frontend never decides isPremium itself. A user
    reverting to Free is reflected by status=EXPIRED, not by deleting the row —
    history is kept."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Set once the corresponding Payment is confirmed (Phase 6) — kept
    # nullable for now since payments don't exist yet.
    payment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
