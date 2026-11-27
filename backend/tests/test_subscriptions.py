from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.test_social import client, _register_user, _login, TEST_DATABASE_URL  # noqa: F401
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus


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


def _db_session():
    engine = create_engine(TEST_DATABASE_URL)
    return sessionmaker(bind=engine)()


def _grant_premium(user_id: str, plan: SubscriptionPlan = SubscriptionPlan.MONTHLY, days: int = 30) -> None:
    db = _db_session()
    sub = Subscription(
        user_id=user_id,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        expires_at=datetime.now(timezone.utc) + timedelta(days=days),
    )
    db.add(sub)
    db.commit()
    db.close()


def test_free_user_is_not_premium_by_default(client: TestClient) -> None:
    _register_user(client, "free1@example.com", "FreeUser")
    _login(client, "free1@example.com")
    status = client.get("/api/v1/subscriptions/me").json()
    assert status["is_premium"] is False
    assert status["likes_limit_today"] == 20


def test_premium_user_has_100_like_limit(client: TestClient) -> None:
    _register_user(client, "premium1@example.com", "PremiumUser")
    _login(client, "premium1@example.com")
    my_id = _get_own_id(client)
    _grant_premium(my_id)

    status = client.get("/api/v1/subscriptions/me").json()
    assert status["is_premium"] is True
    assert status["likes_limit_today"] == 100
    assert status["plan"] == "MONTHLY"


def test_premium_user_can_like_beyond_free_limit_of_20(client: TestClient) -> None:
    _register_user(client, "liker2@example.com", "Liker2")
    _login(client, "liker2@example.com")
    liker_id = _get_own_id(client)
    _grant_premium(liker_id)

    targets = []
    for i in range(25):  # more than the Free limit of 20, still under Premium's 100
        email = f"ptarget{i}@example.com"
        _register_user(client, email, f"PTarget{i}")
        _login(client, email)
        targets.append(_get_own_id(client))

    _login(client, "liker2@example.com")
    statuses = [client.post("/api/v1/likes", json={"to_user_id": t}).status_code for t in targets]
    assert all(s == 201 for s in statuses)  # all 25 succeed — would have failed at 21 for Free


def test_expired_subscription_reverts_to_free(client: TestClient) -> None:
    _register_user(client, "expired1@example.com", "ExpiredUser")
    _login(client, "expired1@example.com")
    my_id = _get_own_id(client)
    _grant_premium(my_id, days=-1)  # already expired

    status = client.get("/api/v1/subscriptions/me").json()
    assert status["is_premium"] is False
    assert status["likes_limit_today"] == 20

    # And the DB row itself must have flipped to EXPIRED, not just been ignored.
    db = _db_session()
    sub = db.query(Subscription).filter(Subscription.user_id == my_id).first()
    assert sub.status == SubscriptionStatus.EXPIRED
    db.close()


def test_plans_endpoint_returns_correct_prices() -> None:
    from app.core.plans import SUBSCRIPTION_PLANS
    from app.models.subscription import SubscriptionPlan as SP

    assert SUBSCRIPTION_PLANS[SP.DAILY].stars_price == 150
    assert SUBSCRIPTION_PLANS[SP.WEEKLY].stars_price == 300
    assert SUBSCRIPTION_PLANS[SP.MONTHLY].stars_price == 400
    assert SUBSCRIPTION_PLANS[SP.YEARLY].stars_price == 3800


def test_premium_message_limit_is_100_total_not_per_person(client: TestClient) -> None:
    _register_user(client, "chatty@example.com", "Chatty")
    _login(client, "chatty@example.com")
    chatty_id = _get_own_id(client)
    _grant_premium(chatty_id)

    _register_user(client, "listener@example.com", "Listener")
    _login(client, "listener@example.com")
    listener_id = _get_own_id(client)

    _login(client, "chatty@example.com")
    _register_crypto(client)
    # Premium ignores the free 2-per-contact rule entirely.
    for i in range(5):
        resp = client.post("/api/v1/messages", json=_encrypted_payload(listener_id))
        assert resp.status_code == 201
