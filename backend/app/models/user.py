import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # Email is optional for the Beta user account. It remains available for
    # admin/legacy accounts and future notification providers.
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)

    # User authentication uses a password hash (Argon2id). Never store the
    # raw password in PostgreSQL.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ADMIN is never granted through the app itself — only ever set
    # directly in the database for an email on the ADMIN_ALLOWED_EMAILS
    # allowlist, as part of the admin OTP login flow (see backend master
    # spec, section 19). Regular signups always get USER.
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # VIP status is strictly internal to the admin dashboard (backend
    # master spec, section 19/VIP rules): never rendered as a badge or any
    # indication to end users — a VIP profile must be indistinguishable
    # from a regular one in the Feed.
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Set by an admin action (suspend), distinct from is_active (which is
    # reserved for the account's own lifecycle, e.g. future self-deletion).
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Legal consent (GDPR Art. 7 — must be able to demonstrate consent).
    # Populated once at registration (see app/api/v1/auth.py) and never
    # cleared afterwards; re-acceptance of a new terms_version is a future
    # feature, not required for the beta launch scope.
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    privacy_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terms_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # NOTE: extended profile fields (first/last name, DOB, gender, country,
    # city — see models/profile.py) live in a separate `profiles` table so
    # this model only covers account/authentication concerns.
