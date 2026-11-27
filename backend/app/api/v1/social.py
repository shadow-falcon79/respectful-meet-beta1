from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.block import Block
from app.models.like import Like
from app.models.match import Match
from app.models.photo import Photo
from app.models.profile import Profile
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.notification import Notification, NotificationType
from app.services.notification_service import create_notification, deliver_push
from app.schemas.social import FeedProfileOut, LikeIn, LikeOut, MatchOut
from app.services.limit_service import can_like
from app.services.storage_service import get_storage_service
from app.core import error_codes

router = APIRouter(tags=["social"])


def _age_from_dob(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _photo_urls(db: DbSession, user_id: str) -> list[str]:
    return _photo_urls_bulk(db, [user_id]).get(user_id, [])


def _photo_urls_bulk(db: DbSession, user_ids: list[str]) -> dict[str, list[str]]:
    """Load all profile photos in one query to avoid N+1 queries."""
    if not user_ids:
        return {}
    storage = get_storage_service()
    rows = (
        db.query(Photo)
        .filter(Photo.user_id.in_(user_ids))
        .order_by(Photo.user_id, Photo.is_primary.desc(), Photo.display_order, Photo.id)
        .all()
    )
    result = {uid: [] for uid in user_ids}
    for photo in rows:
        result.setdefault(photo.user_id, []).append(storage.url_for(photo.storage_key))
    return result


@router.get("/feed", response_model=list[FeedProfileOut])
def get_feed(
    limit: int = Query(default=20, le=50),
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> list[FeedProfileOut]:
    # Keep exclusions in SQL instead of loading every historical Like/Block into
    # Python. This stays bounded as the user base grows.
    blocked_exists = exists().where(
        or_(
            (Block.blocker_id == current_user.id) & (Block.blocked_id == Profile.user_id),
            (Block.blocker_id == Profile.user_id) & (Block.blocked_id == current_user.id),
        )
    )
    liked_exists = exists().where(
        (Like.from_user_id == current_user.id) & (Like.to_user_id == Profile.user_id)
    )
    active_premium_exists = exists().where(
        (Subscription.user_id == Profile.user_id)
        & (Subscription.status == SubscriptionStatus.ACTIVE)
        & (Subscription.expires_at > func.now())
    )

    # Ranking is pushed into PostgreSQL: completion + Premium boost + recency.
    # We intentionally use the profile creation timestamp as the current
    # activity proxy, matching the existing ranking policy.
    from sqlalchemy import case

    completion_score = (
        case((Profile.bio.isnot(None) & (Profile.bio != ""), 0.5), else_=0.0)
        + case((func.coalesce(func.cardinality(Profile.interests), 0) > 0, 0.5), else_=0.0)
    )
    premium_score = case((active_premium_exists, 0.15), else_=0.0)

    profiles = (
        db.query(Profile)
        .filter(Profile.user_id != current_user.id)
        .filter(~liked_exists)
        .filter(~blocked_exists)
        .order_by((completion_score + premium_score).desc(), Profile.created_at.desc(), Profile.user_id.desc())
        .limit(limit)
        .all()
    )
    photo_map = _photo_urls_bulk(db, [p.user_id for p in profiles])

    return [
        FeedProfileOut(
            user_id=p.user_id,
            first_name=p.first_name,
            age=_age_from_dob(p.date_of_birth),
            city=p.city,
            country=p.country,
            bio=p.bio,
            interests=p.interests,
            photos=photo_map.get(p.user_id, []),
        )
        for p in profiles
    ]


@router.post("/likes", response_model=LikeOut, status_code=status.HTTP_201_CREATED)
def create_like(payload: LikeIn, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> LikeOut:
    if payload.to_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like yourself")
    target = db.query(User).filter(User.id == payload.to_user_id).first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    blocked = db.query(Block).filter(
        ((Block.blocker_id == current_user.id) & (Block.blocked_id == payload.to_user_id))
        | ((Block.blocker_id == payload.to_user_id) & (Block.blocked_id == current_user.id))
    ).first()
    if blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_codes.BLOCKED_USER)

    existing = db.query(Like).filter(Like.from_user_id == current_user.id, Like.to_user_id == payload.to_user_id).first()
    if existing is not None:
        reciprocal = db.query(Like).filter(Like.from_user_id == payload.to_user_id, Like.to_user_id == current_user.id).first()
        return LikeOut(id=existing.id, to_user_id=existing.to_user_id, matched=reciprocal is not None, created_at=existing.created_at)

    if not can_like(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_codes.LIMIT_REACHED)

    reciprocal = db.query(Like).filter(Like.from_user_id == payload.to_user_id, Like.to_user_id == current_user.id).first()
    like = Like(from_user_id=current_user.id, to_user_id=payload.to_user_id)
    db.add(like)
    n_like = create_notification(db, payload.to_user_id, NotificationType.LIKE)

    matched = reciprocal is not None
    new_match = False
    match_notifications: list[Notification] = []
    if matched:
        pair = sorted([current_user.id, payload.to_user_id])
        already_matched = db.query(Match).filter(Match.user_a_id == pair[0], Match.user_b_id == pair[1]).first()
        if already_matched is None:
            db.add(Match(user_a_id=pair[0], user_b_id=pair[1]))
            match_notifications = [
                create_notification(db, current_user.id, NotificationType.MATCH),
                create_notification(db, payload.to_user_id, NotificationType.MATCH),
            ]
            new_match = True

    # One atomic DB transaction owns the Like/Match/notification records.
    # Network push is strictly post-commit and only targets notifications
    # created by this request; unrelated recent notifications can never be sent.
    try:
        db.commit()
    except IntegrityError:
        # Two identical requests raced past the `existing is None` check
        # above (double-tap, retry, flaky network). The DB-level unique
        # constraint is the real guard; here we just make the response
        # idempotent instead of surfacing a raw 500.
        db.rollback()
        existing = db.query(Like).filter(Like.from_user_id == current_user.id, Like.to_user_id == payload.to_user_id).first()
        if existing is None:
            raise
        reciprocal = db.query(Like).filter(Like.from_user_id == payload.to_user_id, Like.to_user_id == current_user.id).first()
        return LikeOut(id=existing.id, to_user_id=existing.to_user_id, matched=reciprocal is not None, created_at=existing.created_at)
    db.refresh(like)
    for notification in ([n_like] + match_notifications if new_match else [n_like]):
        deliver_push(db, notification)
    db.commit()
    return LikeOut(id=like.id, to_user_id=like.to_user_id, matched=matched, created_at=like.created_at)


@router.get("/likes/usage")
def get_like_usage(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> dict:
    from app.core.plans import FREE_DAILY_LIKE_LIMIT, PREMIUM_DAILY_LIKE_LIMIT
    from app.services.subscription_service import is_premium
    from app.services.limit_service import get_likes_today_count

    premium = is_premium(db, current_user.id)
    limit = PREMIUM_DAILY_LIKE_LIMIT if premium else FREE_DAILY_LIKE_LIMIT
    used = get_likes_today_count(db, current_user.id)
    return {"used": used, "limit": limit, "remaining": max(0, limit - used), "premium": premium}


@router.get("/likes/received", response_model=list[FeedProfileOut])
def get_likes_received(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> list[FeedProfileOut]:
    liker_ids = [row[0] for row in db.query(Like.from_user_id).filter(Like.to_user_id == current_user.id).all()]
    profiles = db.query(Profile).filter(Profile.user_id.in_(liker_ids)).all() if liker_ids else []
    photo_map = _photo_urls_bulk(db, [p.user_id for p in profiles])
    return [
        FeedProfileOut(
            user_id=p.user_id,
            first_name=p.first_name,
            age=_age_from_dob(p.date_of_birth),
            city=p.city,
            country=p.country,
            bio=p.bio,
            interests=p.interests,
            photos=photo_map.get(p.user_id, []),
        )
        for p in profiles
    ]


@router.get("/matches", response_model=list[MatchOut])
def get_matches(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> list[MatchOut]:
    matches = (
        db.query(Match)
        .filter((Match.user_a_id == current_user.id) | (Match.user_b_id == current_user.id))
        .all()
    )
    other_ids = [m.user_b_id if m.user_a_id == current_user.id else m.user_a_id for m in matches]
    profiles = db.query(Profile).filter(Profile.user_id.in_(other_ids)).all() if other_ids else []
    profile_map = {p.user_id: p for p in profiles}
    photo_map = _photo_urls_bulk(db, other_ids)
    return [
        MatchOut(
            id=m.id,
            other_user_id=(m.user_b_id if m.user_a_id == current_user.id else m.user_a_id),
            other_first_name=profile_map.get(m.user_b_id if m.user_a_id == current_user.id else m.user_a_id).first_name
            if profile_map.get(m.user_b_id if m.user_a_id == current_user.id else m.user_a_id) else "",
            other_photo_url=(photo_map.get(m.user_b_id if m.user_a_id == current_user.id else m.user_a_id) or [None])[0],
            created_at=m.created_at,
        )
        for m in matches
    ]
