"""Personal data export (GDPR Art. 15/20 — right of access & portability).

Returns everything the platform holds that is tied to the requesting user's
own account, in one machine-readable JSON document. This intentionally
mirrors delete_my_account's scope (app/api/v1/auth.py) so "what would be
exported" and "what would be deleted" never silently drift apart.

Design notes:
- Only the current user's own data. Never another user's profile/photos
  beyond the minimal counterpart id needed to make a like/match/block/report
  row meaningful (e.g. "you liked user X") — that id is already visible to
  the user through the normal product UI for matches/likes.
- Message ciphertext is included as-is: it is the user's own account data,
  but it is opaque without the recipient's private key, so exporting it
  does not leak plaintext of anyone's messages.
- Session token hashes, OTP hashes and other security material are never
  exported — those are not "your data" in the GDPR sense, they're auth
  plumbing, and exporting them would be a security smell for no user benefit.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.ad_reward import AdReward
from app.models.block import Block
from app.models.call_session import CallSession
from app.models.crypto_identity import CryptoIdentity
from app.models.conversation import Conversation
from app.models.like import Like
from app.models.match import Match
from app.models.message import Message
from app.models.notification import Notification, NotificationDevice
from app.models.payment import Payment
from app.models.photo import Photo
from app.models.profile import Profile
from app.models.report import Report
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_settings import UserSettings
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/privacy", tags=["privacy"])

# Generous but not free: this is a heavier query than normal browsing, and
# an unauthenticated cost per call, so it gets its own named limit rather
# than relying only on the global default.
DATA_EXPORT_LIMIT = "5/hour"


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


@router.get("/export")
@limiter.limit(DATA_EXPORT_LIMIT)
def export_my_data(request: Request, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> dict:
    storage = get_storage_service()

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    photos = db.query(Photo).filter(Photo.user_id == current_user.id).order_by(Photo.display_order).all()
    settings_row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    identity = db.query(CryptoIdentity).filter(CryptoIdentity.user_id == current_user.id).first()

    likes_sent = db.query(Like).filter(Like.from_user_id == current_user.id).all()
    likes_received = db.query(Like).filter(Like.to_user_id == current_user.id).all()
    matches = (
        db.query(Match)
        .filter((Match.user_a_id == current_user.id) | (Match.user_b_id == current_user.id))
        .all()
    )
    blocks = db.query(Block).filter(Block.blocker_id == current_user.id).all()
    reports_filed = db.query(Report).filter(Report.reporter_id == current_user.id).all()

    conversations = (
        db.query(Conversation)
        .filter((Conversation.user_a_id == current_user.id) | (Conversation.user_b_id == current_user.id))
        .all()
    )
    conversation_ids = [c.id for c in conversations]
    messages_sent = (
        db.query(Message).filter(Message.sender_id == current_user.id).all() if conversation_ids else []
    )

    subscriptions = db.query(Subscription).filter(Subscription.user_id == current_user.id).all()
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).all()
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).all()
    devices = db.query(NotificationDevice).filter(NotificationDevice.user_id == current_user.id).all()
    call_sessions = (
        db.query(CallSession)
        .filter((CallSession.user_id == current_user.id) | (CallSession.peer_id == current_user.id))
        .all()
    )
    ad_rewards = db.query(AdReward).filter(AdReward.user_id == current_user.id).all()

    return {
        "export_generated_at": _iso(datetime.now(timezone.utc)),
        "account": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "is_vip": current_user.is_vip,
            "created_at": _iso(current_user.created_at),
        },
        "profile": None
        if profile is None
        else {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "date_of_birth": profile.date_of_birth.isoformat(),
            "gender": profile.gender,
            "country": profile.country,
            "city": profile.city,
            "bio": profile.bio,
            "interests": profile.interests,
        },
        "photos": [{"id": p.id, "url": storage.url_for(p.storage_key), "is_primary": p.is_primary} for p in photos],
        "settings": None
        if settings_row is None
        else {
            "language": settings_row.language,
            "push_notifications": settings_row.push_notifications,
            "email_notifications": settings_row.email_notifications,
            "marketing_notifications": settings_row.marketing_notifications,
            "show_online_status": settings_row.show_online_status,
            "profile_discoverable": settings_row.profile_discoverable,
            "min_age": settings_row.min_age,
            "max_age": settings_row.max_age,
            "discovery_radius_km": settings_row.discovery_radius_km,
        },
        "crypto_identity": None
        if identity is None
        else {"fingerprint": identity.fingerprint, "created_at": _iso(identity.created_at)},
        "likes_sent": [{"to_user_id": l.to_user_id, "created_at": _iso(l.created_at)} for l in likes_sent],
        "likes_received": [{"from_user_id": l.from_user_id, "created_at": _iso(l.created_at)} for l in likes_received],
        "matches": [
            {
                "id": m.id,
                "other_user_id": m.user_b_id if m.user_a_id == current_user.id else m.user_a_id,
                "created_at": _iso(m.created_at),
            }
            for m in matches
        ],
        "blocked_users": [{"user_id": b.blocked_id, "created_at": _iso(b.created_at)} for b in blocks],
        "reports_filed": [
            {"id": r.id, "reported_user_id": r.reported_user_id, "reason": r.reason, "status": r.status.value, "created_at": _iso(r.created_at)}
            for r in reports_filed
        ],
        "messages_sent": [
            {
                "conversation_id": m.conversation_id,
                "type": m.type.value,
                "ciphertext": m.ciphertext,
                "nonce": m.nonce,
                "crypto_version": m.crypto_version,
                "created_at": _iso(m.created_at),
            }
            for m in messages_sent
        ],
        "subscriptions": [
            {"plan": s.plan.value, "status": s.status.value, "started_at": _iso(s.started_at), "expires_at": _iso(s.expires_at)}
            for s in subscriptions
        ],
        "payments": [
            {"id": p.id, "plan": p.plan, "stars_amount": p.stars_amount, "status": p.status.value, "created_at": _iso(p.created_at)}
            for p in payments
        ],
        "notifications": [
            {"type": n.type.value, "title": n.title, "body": n.body, "is_read": n.is_read, "created_at": _iso(n.created_at)}
            for n in notifications
        ],
        "push_devices": [{"platform": d.platform, "language": d.language, "last_seen_at": _iso(d.last_seen_at)} for d in devices],
        "call_sessions": [
            {
                "mode": c.mode.value,
                "started_at": _iso(c.started_at),
                "ended_at": _iso(c.ended_at),
                "duration_seconds": c.duration_seconds,
            }
            for c in call_sessions
        ],
        "ad_rewards": [
            {"reward_type": a.reward_type.value, "status": a.status.value, "created_at": _iso(a.created_at)}
            for a in ad_rewards
        ],
    }
