import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()

VERIFICATION_TICKET_PURPOSE = "email_verified"


def generate_otp_code() -> str:
    """Cryptographically random 6-digit code (zero-padded, e.g. '004821')."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp_code(code: str) -> str:
    return _hasher.hash(code)


def verify_otp_code(code: str, code_hash: str) -> bool:
    try:
        return _hasher.verify(code_hash, code)
    except VerifyMismatchError:
        return False
    except Exception:
        return False




def hash_password(password: str) -> str:
    """Hash a user password with Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password without exposing the stored hash to clients."""
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def generate_session_token() -> str:
    """High-entropy opaque token. Only its hash is ever stored server-side."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    # SHA-256 is appropriate here: the token itself already has 256 bits of
    # entropy (unlike a short password/OTP), so a slow hash isn't needed.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_verification_ticket(email: str, expires_in_minutes: int = 10) -> str:
    """Short-lived, single-purpose proof that `email` just passed OTP
    verification. Required by /register so account creation can't be
    triggered without a verified email, without re-sending a new OTP."""
    payload = {
        "purpose": VERIFICATION_TICKET_PURPOSE,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def read_verification_ticket(ticket: str) -> str:
    """Returns the verified email, or raises jwt exceptions if invalid/expired."""
    payload = jwt.decode(ticket, settings.secret_key, algorithms=["HS256"])
    if payload.get("purpose") != VERIFICATION_TICKET_PURPOSE:
        raise jwt.InvalidTokenError("Wrong ticket purpose")
    return payload["email"]
