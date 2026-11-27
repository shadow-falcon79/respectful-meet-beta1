from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from app.auth.security import generate_session_token, hash_session_token
from app.models.session import Session as SessionModel

SESSION_VALIDITY_DAYS = 30


def create_session(db: DbSession, user_id: str) -> tuple[str, datetime]:
    """Creates a session row and returns (raw_token, expires_at). The raw
    token is only returned here, to be set in a HttpOnly cookie — it is
    never stored in plaintext."""
    token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_VALIDITY_DAYS)

    session = SessionModel(
        user_id=user_id,
        session_token_hash=hash_session_token(token),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()

    return token, expires_at


def revoke_session(db: DbSession, raw_token: str) -> None:
    token_hash = hash_session_token(raw_token)
    session = db.query(SessionModel).filter(SessionModel.session_token_hash == token_hash).first()
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
