"""Rewarded-ads (offerwall) service.

Flow mirrors how a real provider like AdMantum works, so swapping the mock
for the real integration later only touches this file + ads.py:

  1. Client calls POST /ads/session  -> we create a PENDING AdReward and
     hand back an external_ref (their "click id" equivalent).
  2. Client shows the ad. When it finishes, the PROVIDER (not the client)
     confirms completion server-to-server via a signed postback.
  3. Only that postback (verified here) flips PENDING -> COMPLETED and
     grants the reward. The client can never self-report completion.

For local/dev use before AdMantum approval, app.core.config.ADS_MOCK_MODE
enables a mock postback endpoint that simulates the same signed call —
see api/v1/ads.py. It is refused in production settings.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.plans import (
    AD_REWARD_BONUS_CALL_MINUTES,
    AD_REWARD_BONUS_MESSAGES,
    AD_REWARD_SESSION_TTL_SECONDS,
)
from app.models.ad_reward import AdReward, AdRewardStatus, AdRewardType


def create_ad_session(
    db: Session,
    user_id: str,
    reward_type: AdRewardType,
    conversation_id: str | None,
    provider: str = "mock",
) -> AdReward:
    if reward_type == AdRewardType.UNLOCK_MESSAGES and not conversation_id:
        raise ValueError("conversation_id is required to unlock messages")

    external_ref = secrets.token_urlsafe(24)
    session = AdReward(
        user_id=user_id,
        conversation_id=conversation_id,
        reward_type=reward_type,
        status=AdRewardStatus.PENDING,
        provider=provider,
        external_ref=external_ref,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _expire_if_stale(db: Session, session: AdReward) -> AdReward:
    if session.status != AdRewardStatus.PENDING:
        return session
    age = datetime.now(timezone.utc) - session.created_at.replace(tzinfo=timezone.utc)
    if age > timedelta(seconds=AD_REWARD_SESSION_TTL_SECONDS):
        session.status = AdRewardStatus.EXPIRED
        db.commit()
    return session


def verify_postback_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Providers sign their postback with HMAC-SHA256 over the raw body.
    Swap this for AdMantum's actual documented scheme once we integrate
    for real — the shape (constant-time compare of an HMAC) is standard.
    """
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def complete_ad_session(db: Session, external_ref: str) -> AdReward | None:
    """Called only from a verified postback (real or mock). Idempotent:
    calling it twice for the same external_ref does not double-grant.
    """
    session = db.query(AdReward).filter(AdReward.external_ref == external_ref).first()
    if session is None:
        return None
    session = _expire_if_stale(db, session)
    if session.status != AdRewardStatus.PENDING:
        return session  # already completed/expired — no-op, avoids double reward

    session.status = AdRewardStatus.COMPLETED
    session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def get_bonus_messages(db: Session, user_id: str, conversation_id: str) -> int:
    count = (
        db.query(AdReward)
        .filter(
            AdReward.user_id == user_id,
            AdReward.conversation_id == conversation_id,
            AdReward.reward_type == AdRewardType.UNLOCK_MESSAGES,
            AdReward.status == AdRewardStatus.COMPLETED,
        )
        .count()
    )
    return count * AD_REWARD_BONUS_MESSAGES


def get_bonus_call_minutes_today(db: Session, user_id: str) -> int:
    start_of_day = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
    count = (
        db.query(AdReward)
        .filter(
            AdReward.user_id == user_id,
            AdReward.reward_type == AdRewardType.EXTRA_CALL_MINUTES,
            AdReward.status == AdRewardStatus.COMPLETED,
            AdReward.completed_at >= start_of_day,
        )
        .count()
    )
    return count * AD_REWARD_BONUS_CALL_MINUTES
