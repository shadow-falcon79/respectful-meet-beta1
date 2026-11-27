import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    """One row per Telegram Stars transaction attempt. telegram_charge_id
    is unique so the same Telegram confirmation received twice (webhook
    retried) can never activate a subscription a second time — the actual
    idempotency check happens in the payment service (Phase 6), this
    constraint is the database-level backstop."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telegram_charge_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    stars_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_provider: Mapped[str] = mapped_column(String(50), default="telegram", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
