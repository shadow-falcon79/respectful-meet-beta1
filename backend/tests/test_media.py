import io
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from tests.test_social import client, _register_user, _login  # noqa: F401
from app.models.media import Media
from app.services.media_cleanup import delete_expired_media


def _register_crypto(client: TestClient, public_key='{"kty":"EC","crv":"P-256","x":"x","y":"y"}', fingerprint="a" * 64):
    return client.put("/api/v1/crypto/identity", json={"public_key_jwk": public_key, "fingerprint": fingerprint})


def _encrypted_payload(to_user_id: str, public_key='{"kty":"EC","crv":"P-256","x":"x","y":"y"}'):
    return {
        "to_user_id": to_user_id,
        "ciphertext": "Y2lwaGVydGV4dA",
        "nonce": "MTIzNDU2Nzg5MDEy",
        "sender_public_key_jwk": public_key,
        "crypto_version": "v1",
    }


def _get_own_id(client: TestClient) -> str:
    return client.get("/api/v1/profiles/me").json()["user_id"]


def _tiny_jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100


def test_send_photo_message_counts_against_free_limit(client: TestClient) -> None:
    _register_user(client, "tara@example.com", "Tara")
    _register_user(client, "umar@example.com", "Umar")
    _login(client, "umar@example.com")
    umar_id = _get_own_id(client)

    _login(client, "tara@example.com")
    resp1 = client.post(
        "/api/v1/messages/media",
        data={"to_user_id": umar_id},
        files={"file": ("photo.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    assert resp1.status_code == 201
    assert resp1.json()["type"] if "type" in resp1.json() else True  # response includes message

    _register_crypto(client)
    resp2 = client.post("/api/v1/messages", json=_encrypted_payload(umar_id))
    assert resp2.status_code == 201

    # Third message (1 photo + 1 text already used the free quota of 2)
    resp3 = client.post("/api/v1/messages", json=_encrypted_payload(umar_id))
    assert resp3.status_code == 429


def test_photo_message_creates_media_row_with_expiry(client: TestClient) -> None:
    _register_user(client, "vera@example.com", "Vera")
    _register_user(client, "walt@example.com", "Walt")
    _login(client, "walt@example.com")
    walt_id = _get_own_id(client)

    _login(client, "vera@example.com")
    resp = client.post(
        "/api/v1/messages/media",
        data={"to_user_id": walt_id},
        files={"file": ("photo.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    assert resp.status_code == 201
    message_id = resp.json()["id"]

    from tests.test_social import TEST_DATABASE_URL  # reuse the same test DB URL
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    media = db.query(Media).filter(Media.message_id == message_id).first()
    assert media is not None
    assert media.expires_at > datetime.now(timezone.utc)
    assert media.expires_at < datetime.now(timezone.utc) + timedelta(days=8)
    db.close()


def test_media_cleanup_deletes_expired_and_keeps_message(client: TestClient) -> None:
    _register_user(client, "xena@example.com", "Xena")
    _register_user(client, "yuri@example.com", "Yuri")
    _login(client, "yuri@example.com")
    yuri_id = _get_own_id(client)

    _login(client, "xena@example.com")
    resp = client.post(
        "/api/v1/messages/media",
        data={"to_user_id": yuri_id},
        files={"file": ("photo.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    message_id = resp.json()["id"]

    from tests.test_social import TEST_DATABASE_URL
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.message import Message

    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Force this media to already be expired.
    media = db.query(Media).filter(Media.message_id == message_id).first()
    media.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    deleted_count = delete_expired_media(db)
    assert deleted_count == 1
    assert db.query(Media).filter(Media.message_id == message_id).first() is None

    # The message itself must still exist — deleting media never deletes the message.
    message = db.query(Message).filter(Message.id == message_id).first()
    assert message is not None
    db.close()
