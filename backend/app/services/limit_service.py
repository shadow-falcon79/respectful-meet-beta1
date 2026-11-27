"""Central place for quota/limit rules (backend master spec section 4/6/54:
a single LimitService instead of rules scattered across files).

Now wired to the real Subscription status (subscription_service.py) —
Free vs Premium limits from app.core.plans, the single source of truth
for these numbers.
"""

from datetime import datetime, time, timezone

from sqlalchemy.orm import Session

from app.core.plans import FREE_DAILY_LIKE_LIMIT, PREMIUM_DAILY_LIKE_LIMIT
from app.models.like import Like
from app.services.subscription_service import is_premium


def _start_of_today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def get_likes_today_count(db: Session, user_id: str) -> int:
    return (
        db.query(Like)
        .filter(Like.from_user_id == user_id, Like.created_at >= _start_of_today_utc())
        .count()
    )


def can_like(db: Session, user_id: str) -> bool:
    limit = PREMIUM_DAILY_LIKE_LIMIT if is_premium(db, user_id) else FREE_DAILY_LIKE_LIMIT
    return get_likes_today_count(db, user_id) < limit
