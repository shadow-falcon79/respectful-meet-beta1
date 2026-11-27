import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdminAction(Base):
    """Audit log for admin logins and sensitive admin actions (suspend,
    delete, moderation, Premium changes, config changes) — required by the
    backend master spec, section 19."""

    __tablename__ = "admin_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "admin_login", "user_suspend"
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "user", "report"
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
