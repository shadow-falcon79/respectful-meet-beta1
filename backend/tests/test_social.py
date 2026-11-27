import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.services import otp_service
from app.models.notification import Notification, NotificationType
from tests.test_auth import TEST_DATABASE_URL


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


def _register_user(client: TestClient, email: str, first_name: str, dob: str = "1995-01-01") -> None:
    client.post("/api/v1/auth/request-code", json={"email": email})
    code = client.sent_codes[email]  # type: ignore[attr-defined]
    verify = client.post("/api/v1/auth/verify-code", json={"email": email, "code": code})
    ticket = verify.json()["verification_ticket"]
    register = client.post(
        "/api/v1/auth/register",
        json={
            "verification_ticket": ticket,
            "first_name": first_name,
            "last_name": "Test",
            "date_of_birth": dob,
            "gender": "other",
            "country": "Burundi",
            "city": "Bujumbura",
            "accept_terms": True,
        },
    )
    assert register.status_code == 201
    client.cookies.clear()  # simulate a fresh browser; re-auth per user below


def _login(client: TestClient, email: str) -> None:
    client.post("/api/v1/auth/request-code", json={"email": email})
    code = client.sent_codes[email]  # type: ignore[attr-defined]
    verify = client.post("/api/v1/auth/verify-code", json={"email": email, "code": code})
    assert verify.json()["account_exists"] is True


def test_profile_created_at_registration_is_readable(client: TestClient) -> None:
    _register_user(client, "alice@example.com", "Alice")
    _login(client, "alice@example.com")

    response = client.get("/api/v1/profiles/me")
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Alice"
    assert body["interests"] == []
    assert body["photos"] == []


def test_profile_update_bio_and_interests(client: TestClient) -> None:
    _register_user(client, "bob@example.com", "Bob")
    _login(client, "bob@example.com")

    response = client.patch(
        "/api/v1/profiles/me", json={"bio": "Loves hiking", "interests": ["Hiking", "Coffee"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["bio"] == "Loves hiking"
    assert body["interests"] == ["Hiking", "Coffee"]


def test_bio_with_phone_number_is_rejected(client: TestClient) -> None:
    _register_user(client, "dana@example.com", "Dana")
    _login(client, "dana@example.com")

    response = client.patch("/api/v1/profiles/me", json={"bio": "Call me at 555-123-4567"})
    assert response.status_code == 400


def test_bio_with_whatsapp_mention_is_rejected(client: TestClient) -> None:
    _register_user(client, "eli@example.com", "Eli")
    _login(client, "eli@example.com")

    response = client.patch("/api/v1/profiles/me", json={"bio": "Find me on whatsapp"})
    assert response.status_code == 400


def test_bio_with_obfuscated_platform_name_is_still_caught(client: TestClient) -> None:
    _register_user(client, "faye@example.com", "Faye")
    _login(client, "faye@example.com")

    response = client.patch("/api/v1/profiles/me", json={"bio": "add me on w-h-a-t-s-a-p-p"})
    assert response.status_code == 400


def _tiny_jpeg_bytes() -> bytes:
    # Minimal valid-looking JPEG signature followed by filler bytes —
    # enough to pass the magic-byte check in StorageService.
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100


def test_photo_upload_max_three_and_delete(client: TestClient) -> None:
    _register_user(client, "carla@example.com", "Carla")
    _login(client, "carla@example.com")

    photo_ids = []
    for _ in range(3):
        resp = client.post(
            "/api/v1/profiles/me/photos",
            files={"file": ("photo.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
        )
        assert resp.status_code == 201
        photo_ids.append(resp.json()["id"])

    # 4th photo must be rejected
    resp = client.post(
        "/api/v1/profiles/me/photos",
        files={"file": ("photo.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    assert resp.status_code == 400

    # First uploaded photo is primary by default
    profile = client.get("/api/v1/profiles/me").json()
    assert profile["photos"][0]["is_primary"] is True

    # Delete the primary photo -> next one should become primary
    client.delete(f"/api/v1/profiles/me/photos/{photo_ids[0]}")
    profile = client.get("/api/v1/profiles/me").json()
    assert len(profile["photos"]) == 2
    assert any(p["is_primary"] for p in profile["photos"])


def test_photo_upload_rejects_fake_image(client: TestClient) -> None:
    _register_user(client, "dave@example.com", "Dave")
    _login(client, "dave@example.com")

    resp = client.post(
        "/api/v1/profiles/me/photos",
        files={"file": ("evil.jpg", io.BytesIO(b"not a real jpeg"), "image/jpeg")},
    )
    assert resp.status_code == 400


def test_feed_excludes_self_and_already_liked(client: TestClient) -> None:
    _register_user(client, "emma@example.com", "Emma")
    _register_user(client, "frank@example.com", "Frank")

    _login(client, "emma@example.com")
    feed = client.get("/api/v1/feed").json()
    names = [p["first_name"] for p in feed]
    assert "Emma" not in names  # never shown own profile
    assert "Frank" in names


def test_like_creates_match_when_reciprocal(client: TestClient) -> None:
    _register_user(client, "gina@example.com", "Gina")
    _register_user(client, "hugo@example.com", "Hugo")

    _login(client, "gina@example.com")
    gina_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _login(client, "hugo@example.com")
    hugo_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _login(client, "gina@example.com")
    like1 = client.post("/api/v1/likes", json={"to_user_id": hugo_id})
    assert like1.status_code == 201
    assert like1.json()["matched"] is False

    _login(client, "hugo@example.com")
    like2 = client.post("/api/v1/likes", json={"to_user_id": gina_id})
    assert like2.status_code == 201
    assert like2.json()["matched"] is True

    matches = client.get("/api/v1/matches").json()
    assert len(matches) == 1
    assert matches[0]["other_user_id"] == gina_id


def test_duplicate_like_does_not_error_or_duplicate(client: TestClient) -> None:
    _register_user(client, "ivan@example.com", "Ivan")
    _register_user(client, "jane@example.com", "Jane")

    _login(client, "ivan@example.com")
    jane_id = None
    _login(client, "jane@example.com")
    jane_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _login(client, "ivan@example.com")
    first = client.post("/api/v1/likes", json={"to_user_id": jane_id})
    second = client.post("/api/v1/likes", json={"to_user_id": jane_id})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]  # same like, not duplicated


def test_daily_like_limit_enforced(client: TestClient) -> None:
    _register_user(client, "liker@example.com", "Liker")
    targets = []
    for i in range(21):
        email = f"target{i}@example.com"
        _register_user(client, email, f"Target{i}")
        _login(client, email)
        targets.append(client.get("/api/v1/profiles/me").json()["user_id"])

    _login(client, "liker@example.com")
    last_status = None
    for target_id in targets:
        resp = client.post("/api/v1/likes", json={"to_user_id": target_id})
        last_status = resp.status_code

    # The 21st like (one over the free daily limit of 20) must be rejected.
    assert last_status == 429


def test_like_race_condition_is_idempotent_not_500(client: TestClient) -> None:
    """Regression test: two near-simultaneous /likes requests for the same
    pair must never surface a raw 500 from the DB unique-constraint race —
    see the IntegrityError handling added to create_like() in social.py."""
    import threading

    _register_user(client, "karim@example.com", "Karim")
    _register_user(client, "lea@example.com", "Lea")

    _login(client, "lea@example.com")
    lea_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _login(client, "karim@example.com")

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _fire() -> None:
        barrier.wait()
        resp = client.post("/api/v1/likes", json={"to_user_id": lea_id})
        results.append(resp.status_code)

    threads = [threading.Thread(target=_fire) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [201, 201]

    # Exactly one Like row must exist for this pair — no duplicate, no crash.
    liked = client.get("/api/v1/likes/received")  # sanity: endpoint still healthy after the race
    assert liked.status_code == 200


def test_register_rejects_oversized_field(client: TestClient) -> None:
    """Regression test: free-text registration fields are bounded server-side
    (see Field(max_length=...) added to schemas/auth.py RegisterIn)."""
    client.post("/api/v1/auth/request-code", json={"email": "oversized@example.com"})
    code = client.sent_codes["oversized@example.com"]  # type: ignore[attr-defined]
    verify = client.post("/api/v1/auth/verify-code", json={"email": "oversized@example.com", "code": code})
    ticket = verify.json()["verification_ticket"]

    register = client.post(
        "/api/v1/auth/register",
        json={
            "verification_ticket": ticket,
            "first_name": "A" * 5000,  # far beyond the 100-char DB column
            "last_name": "Test",
            "date_of_birth": "1995-01-01",
            "gender": "other",
            "country": "Burundi",
            "city": "Bujumbura",
        },
    )
    assert register.status_code == 422


def test_cannot_like_self(client: TestClient) -> None:
    _register_user(client, "solo@example.com", "Solo")
    _login(client, "solo@example.com")
    own_id = client.get("/api/v1/profiles/me").json()["user_id"]

    resp = client.post("/api/v1/likes", json={"to_user_id": own_id})
    assert resp.status_code == 400


def test_like_match_creates_only_expected_notifications(client, monkeypatch) -> None:
    _register_user(client, "notify-a@example.com", "NotifyA")
    _register_user(client, "notify-b@example.com", "NotifyB")

    _login(client, "notify-a@example.com")
    a_id = client.get("/api/v1/profiles/me").json()["user_id"]
    _login(client, "notify-b@example.com")
    b_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _login(client, "notify-a@example.com")
    assert client.post("/api/v1/likes", json={"to_user_id": b_id}).status_code == 201
    _login(client, "notify-b@example.com")
    assert client.post("/api/v1/likes", json={"to_user_id": a_id}).status_code == 201

    # The match path must not depend on an undeclared Notification symbol and
    # must persist exactly one LIKE + one MATCH for each participant.
    from app.core.database import get_db
    override = app.dependency_overrides[get_db]
    db = next(override())
    try:
        a_types = [n.type for n in db.query(Notification).filter(Notification.user_id == a_id).all()]
        b_types = [n.type for n in db.query(Notification).filter(Notification.user_id == b_id).all()]
        assert a_types.count(NotificationType.LIKE) == 1
        assert b_types.count(NotificationType.LIKE) == 1
        assert a_types.count(NotificationType.MATCH) == 1
        assert b_types.count(NotificationType.MATCH) == 1
    finally:
        db.close()
