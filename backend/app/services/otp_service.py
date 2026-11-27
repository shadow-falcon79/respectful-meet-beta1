from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from app.auth.security import generate_otp_code, hash_otp_code, verify_otp_code
from app.models.otp import OtpCode
from app.services.email_service import get_email_service

OTP_VALIDITY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5

# Simple anti-spam window: how many codes can be requested for the same
# email in the given window before we stop sending new ones.
REQUEST_WINDOW_MINUTES = 15
REQUEST_WINDOW_MAX = 3


class OtpRateLimitExceeded(Exception):
    pass


class OtpInvalidOrExpired(Exception):
    pass


def request_otp(db: DbSession, email: str) -> None:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=REQUEST_WINDOW_MINUTES)

    recent_count = (
        db.query(OtpCode)
        .filter(OtpCode.email == email, OtpCode.created_at >= window_start)
        .count()
    )
    if recent_count >= REQUEST_WINDOW_MAX:
        raise OtpRateLimitExceeded()

    code = generate_otp_code()
    otp = OtpCode(
        email=email,
        code_hash=hash_otp_code(code),
        expires_at=now + timedelta(minutes=OTP_VALIDITY_MINUTES),
        max_attempts=OTP_MAX_ATTEMPTS,
    )
    db.add(otp)
    # Do not commit an OTP that we have not successfully delivered. If the
    # provider is unavailable, rollback so the user can retry immediately
    # instead of being rate-limited by a dead OTP row.
    try:
        get_email_service().send_otp(email, code)
        db.commit()
    except Exception:
        db.rollback()
        raise


def verify_otp(db: DbSession, email: str, code: str) -> bool:
    now = datetime.now(timezone.utc)

    otp = (
        db.query(OtpCode)
        .filter(OtpCode.email == email, OtpCode.used_at.is_(None))
        .order_by(OtpCode.created_at.desc())
        .first()
    )

    if otp is None:
        raise OtpInvalidOrExpired()

    if otp.expires_at.replace(tzinfo=timezone.utc) < now:
        raise OtpInvalidOrExpired()

    if otp.attempts >= otp.max_attempts:
        raise OtpInvalidOrExpired()

    otp.attempts += 1

    if not verify_otp_code(code, otp.code_hash):
        db.commit()
        return False

    otp.used_at = now
    db.commit()
    return True
