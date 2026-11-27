"""Server-side enforcement of daily call minutes per plan (spec: quotas
must never be trusted from the client). Minutes are derived from actual
persisted CallSession rows, not from a counter the client can desync.
"""

import math
from datetime import datetime, time, timezone

from sqlalchemy.orm import Session

from app.core.plans import FREE_DAILY_CALL_MINUTES, SUBSCRIPTION_PLANS
from app.models.call_session import CallSession
from app.services.ad_reward_service import get_bonus_call_minutes_today
from app.services.subscription_service import get_active_subscription


def _start_of_today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def _plan_minutes(db: Session, user_id: str) -> int:
    subscription = get_active_subscription(db, user_id)
    if subscription is None:
        return FREE_DAILY_CALL_MINUTES
    return SUBSCRIPTION_PLANS[subscription.plan].call_minutes_per_day


def get_minutes_used_today(db: Session, user_id: str) -> int:
    seconds = (
        db.query(CallSession)
        .filter(CallSession.user_id == user_id, CallSession.started_at >= _start_of_today_utc())
        .with_entities(CallSession.duration_seconds)
        .all()
    )
    total_seconds = sum(s[0] for s in seconds)
    return math.floor(total_seconds / 60)


def get_minutes_remaining_today(db: Session, user_id: str) -> int:
    quota = _plan_minutes(db, user_id) + get_bonus_call_minutes_today(db, user_id)
    used = get_minutes_used_today(db, user_id)
    return max(0, quota - used)


def get_seconds_remaining_today(db: Session, user_id: str) -> int:
    """Finer-grained than the minute-rounded view above — used to decide,
    mid-call, exactly when to force a hangup."""
    quota_seconds = (_plan_minutes(db, user_id) + get_bonus_call_minutes_today(db, user_id)) * 60
    used_seconds = (
        db.query(CallSession)
        .filter(CallSession.user_id == user_id, CallSession.started_at >= _start_of_today_utc())
        .with_entities(CallSession.duration_seconds)
        .all()
    )
    return max(0, quota_seconds - sum(s[0] for s in used_seconds))


def can_start_call(db: Session, user_id: str) -> bool:
    return get_seconds_remaining_today(db, user_id) > 0


def record_call_session(
    db: Session,
    conversation_id: str,
    user_id: str,
    peer_id: str,
    mode: str,
    started_at: datetime,
    ended_at: datetime,
    ended_reason: str,
) -> CallSession:
    duration = max(0, int((ended_at - started_at).total_seconds()))
    session = CallSession(
        conversation_id=conversation_id,
        user_id=user_id,
        peer_id=peer_id,
        mode=mode,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        ended_reason=ended_reason,
    )
    db.add(session)
    db.commit()
    return session
