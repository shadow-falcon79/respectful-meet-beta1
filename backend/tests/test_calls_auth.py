"""Regression test for the expired-session bug fixed in app/api/v1/calls.py.

_authenticate() previously only checked `revoked_at is None`, so a session
past its 30-day `expires_at` but never explicitly logged out (revoked)
could still open the /ws/calls signalling socket indefinitely. This test
exercises the fixed function directly against a real Postgres session, the
same way the REST auth dependency (app.auth.dependencies.get_current_user)
is already covered.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.calls import _authenticate
from app.auth.security import generate_session_token, hash_session_token
from app.core.database import Base
from app.models.profile import Profile
from app.models.session import Session as SessionModel
from app.models.user import User
from tests.test_auth import TEST_DATABASE_URL


@pytest.fixture()
def db_session():
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_user_with_session(db, expires_at: datetime) -> str:
    user = User(username="expiring_user", email="expiring@example.com", is_email_verified=True)
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            first_name="Expiring",
            last_name="User",
            date_of_birth=datetime(1995, 1, 1).date(),
            gender="other",
            country="Burundi",
            city="Bujumbura",
        )
    )
    token = generate_session_token()
    db.add(
        SessionModel(
            user_id=user.id,
            session_token_hash=hash_session_token(token),
            expires_at=expires_at,
        )
    )
    db.commit()
    return token


def test_calls_authenticate_rejects_expired_session(db_session) -> None:
    expired_token = _make_user_with_session(
        db_session, expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    assert _authenticate(expired_token, db_session) is None


def test_calls_authenticate_accepts_valid_session(db_session) -> None:
    valid_token = _make_user_with_session(
        db_session, expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    user = _authenticate(valid_token, db_session)
    assert user is not None
    assert user.email == "expiring@example.com"
