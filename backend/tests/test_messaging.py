from fastapi.testclient import TestClient

from tests.test_social import client, _register_user, _login  # noqa: F401


def _get_own_id(client: TestClient) -> str:
    return client.get("/api/v1/profiles/me").json()["user_id"]


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


def test_two_free_messages_then_limit(client: TestClient) -> None:
    _register_user(client, "amy@example.com", "Amy")
    _register_user(client, "ben@example.com", "Ben")
    _login(client, "ben@example.com")
    ben_id = _get_own_id(client)
    _login(client, "amy@example.com")
    _register_crypto(client)
    assert client.post("/api/v1/messages", json=_encrypted_payload(ben_id)).status_code == 201
    assert client.post("/api/v1/messages", json=_encrypted_payload(ben_id)).status_code == 201
    assert client.post("/api/v1/messages", json=_encrypted_payload(ben_id)).status_code == 429


def test_plaintext_message_is_rejected_under_e2ee(client: TestClient) -> None:
    _register_user(client, "eve@example.com", "Eve")
    _register_user(client, "finn@example.com", "Finn")
    _login(client, "finn@example.com")
    finn_id = _get_own_id(client)
    _login(client, "eve@example.com")
    _register_crypto(client)
    resp = client.post("/api/v1/messages", json={"to_user_id": finn_id, "text": "plaintext"})
    assert resp.status_code == 422


def test_encrypted_message_has_no_plaintext(client: TestClient) -> None:
    _register_user(client, "enc-a@example.com", "EncA")
    _register_user(client, "enc-b@example.com", "EncB")
    _login(client, "enc-b@example.com")
    other_id = _get_own_id(client)
    _login(client, "enc-a@example.com")
    _register_crypto(client)
    response = client.post("/api/v1/messages", json=_encrypted_payload(other_id))
    assert response.status_code == 201
    body = response.json()
    assert body["text"] is None
    assert body["ciphertext"]
    assert body["nonce"]


def test_conversation_list_hides_plaintext_preview(client: TestClient) -> None:
    _register_user(client, "oli@example.com", "Oli")
    _register_user(client, "pam@example.com", "Pam")
    _login(client, "pam@example.com")
    pam_id = _get_own_id(client)
    _login(client, "oli@example.com")
    _register_crypto(client)
    assert client.post("/api/v1/messages", json=_encrypted_payload(pam_id)).status_code == 201
    _login(client, "pam@example.com")
    conversations = client.get("/api/v1/conversations").json()
    assert conversations[0]["last_message"] == "Encrypted message"
    assert conversations[0]["unread_count"] == 1


def test_cannot_access_conversation_you_are_not_part_of(client: TestClient) -> None:
    _register_user(client, "quin@example.com", "Quin")
    _register_user(client, "rex@example.com", "Rex")
    _register_user(client, "sam@example.com", "Sam")
    _login(client, "rex@example.com")
    rex_id = _get_own_id(client)
    _login(client, "quin@example.com")
    _register_crypto(client)
    client.post("/api/v1/messages", json=_encrypted_payload(rex_id))
    conv_id = client.get("/api/v1/conversations").json()[0]["id"]
    _login(client, "sam@example.com")
    assert client.get(f"/api/v1/conversations/{conv_id}/messages").status_code == 404


def test_crypto_identity_is_user_scoped(client: TestClient) -> None:
    _register_user(client, "crypto-a@example.com", "CryptoA")
    _login(client, "crypto-a@example.com")
    response = _register_crypto(client)
    assert response.status_code == 200
    identity = client.get("/api/v1/crypto/identity/me")
    assert identity.status_code == 200
    assert identity.json()["user_id"] == _get_own_id(client)
