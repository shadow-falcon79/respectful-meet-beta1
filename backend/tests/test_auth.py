import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app import models as _all_models  # noqa: F401

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://respectful_meet:devpassword@localhost:5432/respectful_meet_test",
)


@pytest.fixture()
def client():
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
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def signup_payload(**overrides):
    payload = {
        "username": "alice",
        "password": "StrongPass123!",
        "confirm_password": "StrongPass123!",
        "first_name": "Alice",
        "last_name": "Doe",
        "date_of_birth": "1995-06-01",
        "gender": "female",
        "country": "Burundi",
        "city": "Bujumbura",
        "interests": ["Music"],
        "accept_terms": True,
    }
    payload.update(overrides)
    return payload


def test_health_check_still_works(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_signup_creates_account_and_session(client: TestClient) -> None:
    response = client.post("/api/v1/auth/signup", json=signup_payload())
    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert "session_token" in response.cookies

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_signin_works_after_signup(client: TestClient) -> None:
    client.post("/api/v1/auth/signup", json=signup_payload())
    client.cookies.clear()
    response = client.post("/api/v1/auth/signin", json={"username": "alice", "password": "StrongPass123!"})
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert "session_token" in response.cookies


def test_wrong_password_is_rejected(client: TestClient) -> None:
    client.post("/api/v1/auth/signup", json=signup_payload())
    response = client.post("/api/v1/auth/signin", json={"username": "alice", "password": "wrong-password"})
    assert response.status_code == 401


def test_duplicate_username_is_rejected(client: TestClient) -> None:
    client.post("/api/v1/auth/signup", json=signup_payload())
    response = client.post("/api/v1/auth/signup", json=signup_payload(first_name="Other"))
    assert response.status_code == 409


def test_password_mismatch_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/signup", json=signup_payload(confirm_password="Different123!"))
    assert response.status_code == 400


def test_underage_signup_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/signup", json=signup_payload(date_of_birth="2015-01-01"))
    assert response.status_code == 400


def test_terms_are_required(client: TestClient) -> None:
    response = client.post("/api/v1/auth/signup", json=signup_payload(accept_terms=False))
    assert response.status_code == 400


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
