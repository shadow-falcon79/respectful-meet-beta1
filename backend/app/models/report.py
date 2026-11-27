import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reported_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional: a report can target a specific message rather than the user in general.
    message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)

    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
