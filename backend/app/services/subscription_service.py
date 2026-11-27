from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionStatus


def get_active_subscription(db: Session, user_id: str) -> Subscription | None:
    """Returns the user's active subscription, auto-expiring it first if
    its expires_at has passed (spec section 10/51: expiration must be
    enforced by the backend, and never deletes the row — only flips the
    status). Returns None for a Free user."""
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    if subscription is None:
        return None

    now = datetime.now(timezone.utc)
    if subscription.expires_at.replace(tzinfo=timezone.utc) <= now:
        subscription.status = SubscriptionStatus.EXPIRED
        db.commit()
        return None

    return subscription


def is_premium(db: Session, user_id: str) -> bool:
    return get_active_subscription(db, user_id) is not None
