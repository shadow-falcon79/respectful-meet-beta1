from datetime import datetime, timedelta, timezone
from app.models.notification import Notification, NotificationType
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.services.subscription_notifications import notify_expiring_subscriptions


def test_like_notification_is_persisted(client):
    from tests.test_social import _register_user, _login
    _register_user(client, "like-a@example.com", "LikeA")
    _register_user(client, "like-b@example.com", "LikeB")
    _login(client, "like-b@example.com")
    b_id = client.get("/api/v1/profiles/me").json()["user_id"]
    _login(client, "like-a@example.com")
    assert client.post("/api/v1/likes", json={"to_user_id": b_id}).status_code == 201
    _login(client, "like-b@example.com")
    notes = client.get("/api/v1/notifications").json()
    assert any(n["type"] == "LIKE" for n in notes)


def test_subscription_expiry_notification_is_idempotent(client):
    from tests.test_social import _register_user, _login, TEST_DATABASE_URL
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    _register_user(client, "exp@example.com", "Expiry")
    _login(client, "exp@example.com")
    uid = client.get("/api/v1/profiles/me").json()["user_id"]
    db = sessionmaker(bind=create_engine(TEST_DATABASE_URL))()
    sub = Subscription(user_id=uid, plan=SubscriptionPlan.MONTHLY, status=SubscriptionStatus.ACTIVE,
                       started_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc)+timedelta(hours=12))
    db.add(sub); db.commit()
    assert notify_expiring_subscriptions(db) == 1
    assert notify_expiring_subscriptions(db) == 0
    assert db.query(Notification).filter(Notification.user_id==uid, Notification.type==NotificationType.SUBSCRIPTION_EXPIRING).count() == 1
    db.close()
