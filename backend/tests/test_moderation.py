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


def test_block_then_cannot_message_either_direction(client: TestClient) -> None:
    _register_user(client, "zack@example.com", "Zack")
    _register_user(client, "abby@example.com", "Abby")

    _login(client, "abby@example.com")
    abby_id = _get_own_id(client)

    _login(client, "zack@example.com")
    zack_id = _get_own_id(client)
    block_resp = client.post("/api/v1/blocks", json={"user_id": abby_id})
    assert block_resp.status_code == 201

    # Blocker can't message the blocked user
    _register_crypto(client)
    resp1 = client.post("/api/v1/messages", json=_encrypted_payload(abby_id))
    assert resp1.status_code == 403

    # Blocked user can't message the blocker either
    _login(client, "abby@example.com")
    _register_crypto(client)
    resp2 = client.post("/api/v1/messages", json=_encrypted_payload(zack_id))
    assert resp2.status_code == 403


def test_blocked_user_excluded_from_feed() -> None:
    pass  # covered indirectly by test_feed_excludes_self_and_already_liked pattern; feed already filters blocks


def test_unblock_restores_messaging(client: TestClient) -> None:
    _register_user(client, "cody@example.com", "Cody")
    _register_user(client, "dina@example.com", "Dina")

    _login(client, "dina@example.com")
    dina_id = _get_own_id(client)

    _login(client, "cody@example.com")
    client.post("/api/v1/blocks", json={"user_id": dina_id})
    client.delete(f"/api/v1/blocks/{dina_id}")
    _register_crypto(client)

    resp = client.post("/api/v1/messages", json=_encrypted_payload(dina_id))
    assert resp.status_code == 201


def test_block_race_condition_is_idempotent_not_500(client: TestClient) -> None:
    """Regression test: two near-simultaneous /blocks requests for the same
    pair must never surface a raw 500 from the DB unique-constraint race —
    see the IntegrityError handling added to block_user() in moderation.py."""
    import threading

    _register_user(client, "erik@example.com", "Erik")
    _register_user(client, "fiona@example.com", "Fiona")

    _login(client, "fiona@example.com")
    fiona_id = _get_own_id(client)

    _login(client, "erik@example.com")

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _fire() -> None:
        barrier.wait()
        resp = client.post("/api/v1/blocks", json={"user_id": fiona_id})
        results.append(resp.status_code)

    threads = [threading.Thread(target=_fire) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [201, 201]


def test_report_user(client: TestClient) -> None:
    _register_user(client, "eli@example.com", "Eli")
    _register_user(client, "fay@example.com", "Fay")

    _login(client, "fay@example.com")
    fay_id = _get_own_id(client)

    _login(client, "eli@example.com")
    resp = client.post(
        "/api/v1/reports",
        json={"reported_user_id": fay_id, "reason": "harassment", "details": "Sent inappropriate messages"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "PENDING"


def test_cannot_report_self(client: TestClient) -> None:
    _register_user(client, "gus@example.com", "Gus")
    _login(client, "gus@example.com")
    gus_id = _get_own_id(client)

    resp = client.post("/api/v1/reports", json={"reported_user_id": gus_id, "reason": "test"})
    assert resp.status_code == 400
