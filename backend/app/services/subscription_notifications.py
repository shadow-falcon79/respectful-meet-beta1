from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.models.subscription import Subscription, SubscriptionStatus
from app.services.notification_service import create_notification, deliver_push


def notify_expiring_subscriptions(db: Session, hours: int = 24) -> int:
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours)
    subscriptions = (db.query(Subscription)
        .filter(Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at > now,
                Subscription.expires_at <= cutoff).all())
    created = 0
    for sub in subscriptions:
        expiry = sub.expires_at.replace(tzinfo=timezone.utc) if sub.expires_at.tzinfo is None else sub.expires_at
        body = f"Your Premium subscription expires on {expiry.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}."
        exists = (db.query(Notification).filter(
            Notification.user_id == sub.user_id,
            Notification.type == NotificationType.SUBSCRIPTION_EXPIRING,
            Notification.body == body).first())
        if exists:
            continue
        n = create_notification(db, sub.user_id, NotificationType.SUBSCRIPTION_EXPIRING,
                                 body=body)
        deliver_push(db, n)
        created += 1
    db.commit()
    return created
