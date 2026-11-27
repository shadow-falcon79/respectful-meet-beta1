from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.auth.security import hash_session_token
from app.core.database import get_db
from app.models.session import Session as SessionModel
from app.models.user import User, UserRole

SESSION_COOKIE_NAME = "session_token"


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: DbSession = Depends(get_db),
) -> User:
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token_hash = hash_session_token(session_token)
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_token_hash == token_hash)
        .first()
    )

    now = datetime.now(timezone.utc)
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at.replace(tzinfo=timezone.utc) < now
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")

    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not available")
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ACCOUNT_SUSPENDED")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Every /api/v1/admin/* route depends on this, never on get_current_user
    alone — a valid session is not enough, the role must be ADMIN. This is
    the actual enforcement point; hiding a button in React is not security
    (backend master spec, section 19)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ADMIN_REQUIRED")
    return current_user
