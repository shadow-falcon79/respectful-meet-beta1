import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import func, case
from datetime import datetime, timedelta, timezone

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.core.plans import VIP_CAPACITY
from app.models.admin_action import AdminAction
from app.models.photo import Photo
from app.models.payment import Payment, PaymentStatus
from app.models.profile import Profile
from app.models.like import Like
from app.models.match import Match
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.call_session import CallSession
from app.models.notification import Notification
from app.core.config import settings
from app.models.report import Report, ReportStatus
from app.models.user import User
from app.schemas.admin import (
    AdminPaymentOut, AdminUserOut, VipCapacityOut, VipCreateIn, VipOut,
    AdminLikeMatchStatsOut, AdminMessageStatsOut, AdminMessageMetadataOut,
    AdminAnalyticsOut, AdminSubscriptionOut, AdminSettingOut, AdminSettingUpdate,
)
from app.schemas.moderation import ReportOut
from app.services.storage_service import MAX_IMAGE_SIZE_BYTES, StorageValidationError, get_storage_service
from app.services.photo_moderation_service import get_photo_moderation_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _log(db: DbSession, admin_id: str, action: str, target_type: str | None = None, target_id: str | None = None) -> None:
    db.add(AdminAction(admin_user_id=admin_id, action=action, target_type=target_type, target_id=target_id))
    db.commit()


# ---------- VIP ----------

@router.get("/vip/capacity", response_model=VipCapacityOut)
def get_vip_capacity(db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)) -> VipCapacityOut:
    used = db.query(User).filter(User.is_vip.is_(True)).count()
    return VipCapacityOut(used=used, capacity=VIP_CAPACITY, available=max(0, VIP_CAPACITY - used))


@router.get("/vip", response_model=list[VipOut])
def list_vip(db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)) -> list[VipOut]:
    storage = get_storage_service()
    vip_users = db.query(User).filter(User.is_vip.is_(True)).all()
    results = []
    for u in vip_users:
        profile = db.query(Profile).filter(Profile.user_id == u.id).first()
        photo = db.query(Photo).filter(Photo.user_id == u.id, Photo.is_primary.is_(True)).first()
        results.append(
            VipOut(
                user_id=u.id,
                first_name=profile.first_name if profile else "",
                country=profile.country if profile else "",
                city=profile.city if profile else "",
                photo_url=storage.url_for(photo.storage_key) if photo else None,
                created_at=u.created_at,
            )
        )
    return results


@router.post("/vip", response_model=VipOut, status_code=status.HTTP_201_CREATED)
async def create_vip(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    gender: str,
    country: str,
    city: str,
    file: UploadFile = File(...),
    bio: str = "",
    db: DbSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> VipOut:
    from datetime import date as date_cls

    used = db.query(User).filter(User.is_vip.is_(True)).count()
    if used >= VIP_CAPACITY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VIP_CAPACITY_FULL")

    # Bounded read: never buffer more than the max allowed size + 1 byte into
    # memory (same DoS hardening as /profiles/me/photos and messages.py).
    content = await file.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 8MB)")

    moderation = get_photo_moderation_service().screen(content, file.content_type or "")
    if not moderation.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo rejected by content moderation ({moderation.reason or 'policy violation'})",
        )

    storage = get_storage_service()
    try:
        storage_key = storage.save(content, file.content_type or "", folder="vip")
    except StorageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # A VIP profile is a real User+Profile row, flagged is_vip=True — it
    # goes through the exact same Feed/Like/Match/Message code paths as
    # any other user, which is what guarantees it looks identical to
    # everyone (spec rule: no separate VIP system, no visible difference).
    synthetic_email = f"vip+{uuid.uuid4()}@internal.respectfulmeet"
    vip_user = User(
        username=f"vip_{uuid.uuid4().hex[:16]}",
        email=synthetic_email,
        is_email_verified=True,
        is_vip=True,
    )
    db.add(vip_user)
    db.flush()

    profile = Profile(
        user_id=vip_user.id,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_cls.fromisoformat(date_of_birth),
        gender=gender,
        country=country,
        city=city,
        bio=bio or None,
        interests=[],
    )
    db.add(profile)

    photo = Photo(user_id=vip_user.id, storage_key=storage_key, is_primary=True, display_order=0)
    db.add(photo)
    db.commit()

    _log(db, admin.id, "vip_create", "user", vip_user.id)

    return VipOut(
        user_id=vip_user.id,
        first_name=profile.first_name,
        country=profile.country,
        city=profile.city,
        photo_url=storage.url_for(storage_key),
        created_at=vip_user.created_at,
    )


@router.delete("/vip/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vip(user_id: str, db: DbSession = Depends(get_db), admin: User = Depends(get_current_admin)) -> None:
    user = db.query(User).filter(User.id == user_id, User.is_vip.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIP profile not found")
    db.delete(user)  # cascades to Profile/Photo via FK ondelete
    db.commit()
    _log(db, admin.id, "vip_delete", "user", user_id)


# ---------- Users ----------

@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    limit: int = 50,
    db: DbSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[AdminUserOut]:
    users = db.query(User).filter(User.is_vip.is_(False)).order_by(User.created_at.desc()).limit(limit).all()
    results = []
    for u in users:
        profile = db.query(Profile).filter(Profile.user_id == u.id).first()
        results.append(
            AdminUserOut(
                id=u.id,
                email=u.email,
                first_name=profile.first_name if profile else None,
                country=profile.country if profile else None,
                is_active=u.is_active,
                is_suspended=u.is_suspended,
                role=u.role.value,
                created_at=u.created_at,
            )
        )
    return results


@router.post("/users/{user_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
def suspend_user(user_id: str, db: DbSession = Depends(get_db), admin: User = Depends(get_current_admin)) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_suspended = True
    db.commit()
    _log(db, admin.id, "user_suspend", "user", user_id)


@router.post("/users/{user_id}/unsuspend", status_code=status.HTTP_204_NO_CONTENT)
def unsuspend_user(user_id: str, db: DbSession = Depends(get_db), admin: User = Depends(get_current_admin)) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_suspended = False
    db.commit()
    _log(db, admin.id, "user_unsuspend", "user", user_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: DbSession = Depends(get_db), admin: User = Depends(get_current_admin)) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    _log(db, admin.id, "user_delete", "user", user_id)


# ---------- Reports ----------

@router.get("/reports", response_model=list[ReportOut])
def list_reports(db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)) -> list[ReportOut]:
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [
        ReportOut(id=r.id, reported_user_id=r.reported_user_id, reason=r.reason, status=r.status.value, created_at=r.created_at)
        for r in reports
    ]


@router.post("/reports/{report_id}/resolve", response_model=ReportOut)
def resolve_report(report_id: str, db: DbSession = Depends(get_db), admin: User = Depends(get_current_admin)) -> ReportOut:
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    from datetime import datetime, timezone

    report.status = ReportStatus.RESOLVED
    report.resolved_at = datetime.now(timezone.utc)
    db.commit()
    _log(db, admin.id, "report_resolve", "report", report_id)
    return ReportOut(id=report.id, reported_user_id=report.reported_user_id, reason=report.reason, status=report.status.value, created_at=report.created_at)


# ---------- Payments ----------

@router.get("/payments", response_model=list[AdminPaymentOut])
def list_payments(
    limit: int = 100,
    db: DbSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[AdminPaymentOut]:
    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(min(limit, 500)).all()
    return [
        AdminPaymentOut(
            id=p.id,
            user_id=p.user_id,
            plan=p.plan,
            stars_amount=p.stars_amount,
            status=p.status.value,
            telegram_user_id=p.telegram_user_id,
            telegram_charge_id=p.telegram_charge_id,
            created_at=p.created_at,
        )
        for p in payments
    ]


@router.post("/payments/{payment_id}/refund", response_model=AdminPaymentOut)
def refund_payment(
    payment_id: str,
    db: DbSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminPaymentOut:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != PaymentStatus.SUCCESSFUL or not payment.telegram_user_id or not payment.telegram_charge_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment is not refundable")
    try:
        from app.services.telegram_service import TelegramService
        TelegramService().refund_star_payment(int(payment.telegram_user_id), payment.telegram_charge_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram refund service unavailable") from exc
    payment.status = PaymentStatus.REFUNDED
    db.commit()
    _log(db, admin.id, "payment_refund", "payment", payment.id)
    return AdminPaymentOut(
        id=payment.id, user_id=payment.user_id, plan=payment.plan, stars_amount=payment.stars_amount,
        status=payment.status.value, telegram_user_id=payment.telegram_user_id,
        telegram_charge_id=payment.telegram_charge_id, created_at=payment.created_at,
    )


# ---------- Likes / Matches ----------

@router.get("/likes", response_model=AdminLikeMatchStatsOut)
def admin_like_match_stats(db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total_likes = db.query(Like).count()
    likes_today = db.query(Like).filter(Like.created_at >= day_start).count()
    total_matches = db.query(Match).count()
    matches_today = db.query(Match).filter(Match.created_at >= day_start).count()
    return AdminLikeMatchStatsOut(
        total_likes=total_likes, likes_today=likes_today,
        total_matches=total_matches, matches_today=matches_today,
        match_rate_percent=round((total_matches * 2 / total_likes * 100), 2) if total_likes else 0.0,
    )

# ---------- Messages (metadata only; never ciphertext/plaintext) ----------

@router.get("/messages", response_model=AdminMessageStatsOut)
def admin_message_stats(db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    return AdminMessageStatsOut(
        total_messages=db.query(Message).count(),
        messages_today=db.query(Message).filter(Message.created_at >= since).count(),
        total_conversations=db.query(Conversation).count(),
        active_conversations_24h=db.query(Conversation).join(Message, Message.conversation_id == Conversation.id).filter(Message.created_at >= since).distinct().count(),
    )

@router.get("/messages/metadata", response_model=list[AdminMessageMetadataOut])
def admin_message_metadata(limit: int = 100, db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    limit = min(max(limit, 1), 500)
    rows = (
        db.query(
            Conversation.id,
            Conversation.user_a_id,
            Conversation.user_b_id,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id, Conversation.user_a_id, Conversation.user_b_id)
        .order_by(func.max(Message.created_at).desc().nullslast())
        .limit(limit).all()
    )
    result = []
    for row in rows:
        last_type = None
        if row.last_message_at is not None:
            last = db.query(Message.type).filter(Message.conversation_id == row.id, Message.created_at == row.last_message_at).first()
            last_type = last[0].value if last else None
        result.append(AdminMessageMetadataOut(
            conversation_id=row.id, participant_a_id=row.user_a_id, participant_b_id=row.user_b_id,
            message_count=int(row.message_count), last_message_at=row.last_message_at, last_message_type=last_type,
        ))
    return result

# ---------- Subscriptions ----------

@router.get("/subscriptions", response_model=list[AdminSubscriptionOut])
def admin_subscriptions(limit: int = 100, db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    rows = db.query(Subscription).order_by(Subscription.expires_at.desc()).limit(min(max(limit, 1), 500)).all()
    return [AdminSubscriptionOut(
        id=s.id, user_id=s.user_id, plan=s.plan.value, status=s.status.value,
        started_at=s.started_at, expires_at=s.expires_at, payment_id=s.payment_id
    ) for s in rows]

# ---------- Analytics ----------

@router.get("/analytics", response_model=AdminAnalyticsOut)
def admin_analytics(db: DbSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    since24 = now - timedelta(hours=24)
    successful = db.query(Payment).filter(Payment.status == PaymentStatus.SUCCESSFUL).all()
    calls = db.query(CallSession).all()
    return AdminAnalyticsOut(
        users_total=db.query(User).filter(User.is_vip.is_(False)).count(),
        users_today=db.query(User).filter(User.is_vip.is_(False), User.created_at >= today).count(),
        active_users_24h=db.query(User).filter(User.is_vip.is_(False), User.updated_at >= since24).count(),
        likes_total=db.query(Like).count(),
        matches_total=db.query(Match).count(),
        messages_total=db.query(Message).count(),
        conversations_total=db.query(Conversation).count(),
        premium_active=db.query(Subscription).filter(Subscription.status == SubscriptionStatus.ACTIVE, Subscription.expires_at > now).count(),
        payments_successful=len(successful),
        revenue_stars=sum(p.stars_amount for p in successful),
        calls_total=len(calls),
        call_minutes_total=sum((c.duration_seconds or 0) for c in calls) // 60,
    )

# ---------- Safe admin settings ----------

@router.get("/settings", response_model=list[AdminSettingOut])
def admin_settings(_admin: User = Depends(get_current_admin)):
    return [
        AdminSettingOut(key="environment", value=settings.environment, editable=False, description="Runtime environment"),
        AdminSettingOut(key="email_provider", value=settings.email_provider, editable=False, description="Configured transactional email provider"),
        AdminSettingOut(key="telegram_configured", value=str(bool(settings.telegram_bot_token and settings.telegram_webhook_secret)).lower(), editable=False, description="Telegram Stars credentials configured"),
        AdminSettingOut(key="smtp_configured", value=str(bool(settings.smtp_username and settings.smtp_app_password and settings.email_sender_email)).lower(), editable=False, description="SMTP credentials configured"),
        AdminSettingOut(key="vapid_configured", value=str(bool(settings.vapid_public_key and settings.vapid_private_key)).lower(), editable=False, description="Web Push VAPID credentials configured"),
        AdminSettingOut(key="object_storage_configured", value=str(bool(settings.storage_url and settings.storage_bucket and settings.storage_access_key and settings.storage_secret_key)).lower(), editable=False, description="S3-compatible object storage configured"),
        AdminSettingOut(key="ads_enabled", value=str(settings.ads_enabled).lower(), editable=True, description="Enable rewarded ads"),
        AdminSettingOut(key="ads_mock_mode", value=str(settings.ads_mock_mode).lower(), editable=False, description="Mock ads are development-only"),
    ]

@router.patch("/settings/{key}", response_model=AdminSettingOut)
def update_admin_setting(key: str, payload: AdminSettingUpdate, db: DbSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    if key != "ads_enabled":
        raise HTTPException(status_code=400, detail="Setting is read-only")
    if settings.environment.lower() == "production" and settings.ads_mock_mode:
        raise HTTPException(status_code=409, detail="Mock ads cannot be enabled in production")
    if not isinstance(payload.value, bool):
        raise HTTPException(status_code=422, detail="ads_enabled must be boolean")
    settings.ads_enabled = payload.value
    _log(db, admin.id, "admin_setting_update", "setting", key)
    return AdminSettingOut(key=key, value=str(settings.ads_enabled).lower(), editable=True, description="Enable rewarded ads")
