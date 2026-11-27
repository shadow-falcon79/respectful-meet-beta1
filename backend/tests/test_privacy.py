import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.services import otp_service
from app import models as _all_models  # noqa: F401 — registers every table on Base.metadata

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://respectful_meet:devpassword@localhost:5432/respectful_meet_test",
)


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    sent_codes: dict[str, str] = {}

    class _CapturingEmailService:
        def send_otp(self, email: str, code: str) -> None:
            sent_codes[email] = code

    monkeypatch.setattr(otp_service, "get_email_service", lambda: _CapturingEmailService())

    test_client = TestClient(app)
    test_client.sent_codes = sent_codes  # type: ignore[attr-defined]
    yield test_client

    app.dependency_overrides.clear()


def _register(client: TestClient, email: str, first_name: str = "Alice") -> None:
    client.post("/api/v1/auth/request-code", json={"email": email})
    code = client.sent_codes[email]  # type: ignore[attr-defined]
    verify = client.post("/api/v1/auth/verify-code", json={"email": email, "code": code})
    ticket = verify.json()["verification_ticket"]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "verification_ticket": ticket,
            "first_name": first_name,
            "last_name": "Doe",
            "date_of_birth": "1995-06-01",
            "gender": "female",
            "country": "Burundi",
            "city": "Bujumbura",
            "accept_terms": True,
        },
    )
    assert response.status_code == 201


def test_export_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/privacy/export")
    assert response.status_code == 401


def test_export_returns_own_profile_and_empty_collections(client: TestClient) -> None:
    _register(client, "alice@example.com")

    response = client.get("/api/v1/privacy/export")
    assert response.status_code == 200
    body = response.json()

    assert body["account"]["email"] == "alice@example.com"
    assert body["profile"]["first_name"] == "Alice"
    assert body["likes_sent"] == []
    assert body["matches"] == []
    assert body["blocked_users"] == []
    assert "export_generated_at" in body


def test_export_reflects_a_like_the_user_sent(client: TestClient) -> None:
    _register(client, "alice@example.com", "Alice")
    alice_cookies = dict(client.cookies)

    client.cookies.clear()
    _register(client, "bob@example.com", "Bob")
    bob_id = client.get("/api/v1/auth/me").json()["id"]

    client.cookies.clear()
    client.cookies.update(alice_cookies)
    client.post("/api/v1/likes", json={"to_user_id": bob_id})

    export = client.get("/api/v1/privacy/export").json()
    assert any(l["to_user_id"] == bob_id for l in export["likes_sent"])


def test_export_never_includes_another_users_profile_fields(client: TestClient) -> None:
    _register(client, "alice@example.com", "Alice")
    export = client.get("/api/v1/privacy/export").json()
    dumped = str(export)
    assert "bob@example.com" not in dumped
