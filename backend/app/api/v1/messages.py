from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core import error_codes
from app.core.database import get_db
from app.core.rate_limit import MESSAGE_SEND_LIMIT, UPLOAD_LIMIT, limiter
from app.models.block import Block
from app.models.crypto_identity import CryptoIdentity
from app.models.conversation import Conversation
from app.models.media import Media, MediaType
from app.models.message import Message, MessageType
from app.models.photo import Photo
from app.models.profile import Profile
from app.models.user import User
from app.models.notification import NotificationType
from app.services.notification_service import create_notification, deliver_push
from app.schemas.messaging import ConversationOut, MessageOut, SendMessageIn, StartConversationIn
from app.services.message_service import can_send_message, get_or_create_conversation
from app.services.subscription_service import is_premium
from app.services.storage_service import MAX_IMAGE_SIZE_BYTES, StorageValidationError, get_storage_service

router = APIRouter(tags=["messaging"])


def _primary_photo_url(db: DbSession, user_id: str) -> str | None:
    storage = get_storage_service()
    photo = (
        db.query(Photo)
        .filter(Photo.user_id == user_id)
        .order_by(Photo.is_primary.desc(), Photo.display_order)
        .first()
    )
    return storage.url_for(photo.storage_key) if photo else None


def _other_user_id(conversation: Conversation, current_user_id: str) -> str:
    if current_user_id == conversation.user_a_id:
        return conversation.user_b_id
    if current_user_id == conversation.user_b_id:
        return conversation.user_a_id
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")


def _get_conversation_for_user(db: DbSession, conversation_id: str, user_id: str) -> Conversation:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None or user_id not in (conversation.user_a_id, conversation.user_b_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def _message_out(db: DbSession, message: Message) -> MessageOut:
    media_url = None
    if message.media_id:
        media = db.query(Media).filter(Media.id == message.media_id).first()
        if media:
            media_url = get_storage_service().url_for(media.storage_key)
    return MessageOut(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        type=message.type.value,
        text=None,
        ciphertext=message.ciphertext,
        nonce=message.nonce,
        sender_public_key_jwk=message.sender_public_key_jwk,
        crypto_version=message.crypto_version,
        media_url=media_url,
        is_read=message.is_read,
        created_at=message.created_at,
    )


def _conversation_out(db: DbSession, conversation: Conversation, current_user_id: str) -> ConversationOut:
    other_id = _other_user_id(conversation, current_user_id)
    other_profile = db.query(Profile).filter(Profile.user_id == other_id).first()
    last_message = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .first()
    )
    unread_count = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != current_user_id,
            Message.is_read.is_(False),
        )
        .count()
    )
    last_preview = None
    if last_message:
        last_preview = "Encrypted message" if last_message.type == MessageType.TEXT else f"{last_message.type.value.title()}"
    return ConversationOut(
        id=conversation.id,
        other_user_id=other_id,
        other_first_name=other_profile.first_name if other_profile else "",
        other_photo_url=_primary_photo_url(db, other_id),
        is_matched=conversation.is_matched,
        last_message=last_preview,
        last_message_at=last_message.created_at if last_message else None,
        unread_count=unread_count,
    )


def _check_not_blocked(db: DbSession, user_id: str, other_id: str) -> None:
    is_blocked = (
        db.query(Block)
        .filter(
            ((Block.blocker_id == user_id) & (Block.blocked_id == other_id))
            | ((Block.blocker_id == other_id) & (Block.blocked_id == user_id))
        )
        .first()
    )
    if is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_codes.BLOCKED_USER)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> list[ConversationOut]:
    conversations = (
        db.query(Conversation)
        .filter(or_(Conversation.user_a_id == current_user.id, Conversation.user_b_id == current_user.id))
        .all()
    )
    results = [_conversation_out(db, conv, current_user.id) for conv in conversations]
    results.sort(key=lambda c: c.last_message_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return results


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def start_conversation(
    payload: StartConversationIn,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> ConversationOut:
    if payload.to_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself")
    target = db.query(User).filter(User.id == payload.to_user_id).first()
    if target is None or not target.is_active or target.is_suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _check_not_blocked(db, current_user.id, target.id)
    conversation = get_or_create_conversation(db, current_user.id, target.id)
    return _conversation_out(db, conversation, current_user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> ConversationOut:
    conversation = _get_conversation_for_user(db, conversation_id, current_user.id)
    return _conversation_out(db, conversation, current_user.id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> list[MessageOut]:
    conversation = _get_conversation_for_user(db, conversation_id, current_user.id)
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
        .all()
    )

    db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != current_user.id,
        Message.is_read.is_(False),
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()

    messages.reverse()
    return [_message_out(db, message) for message in messages]


@router.get("/conversations/{conversation_id}/external-sharing")
def external_sharing_status(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> dict[str, object]:
    """Whether this conversation has earned the right to share off-platform contact details.

    E2EE means the server cannot inspect plaintext. The client therefore uses this
    server-authoritative entitlement before applying its local content gate.
    Premium users are eligible immediately; free conversations unlock after 20 days.
    """
    conversation = _get_conversation_for_user(db, conversation_id, current_user.id)
    premium = is_premium(db, current_user.id)
    unlock_at = conversation.created_at + timedelta(days=20)
    unlocked = premium or datetime.now(timezone.utc) >= unlock_at.replace(tzinfo=timezone.utc)
    return {"allowed": unlocked, "reason": "premium" if premium else ("conversation_age" if unlocked else "new_conversation"), "unlock_at": unlock_at}


@router.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(MESSAGE_SEND_LIMIT)
def send_message(request: Request, payload: SendMessageIn, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> MessageOut:
    """Store only an authenticated E2EE envelope. The API deliberately has no
    plaintext message input; decryption happens only on recipient devices."""
    if payload.to_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself")

    target = db.query(User).filter(User.id == payload.to_user_id).first()
    if target is None or not target.is_active or target.is_suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _check_not_blocked(db, current_user.id, target.id)

    identity = db.query(CryptoIdentity).filter(CryptoIdentity.user_id == current_user.id).first()
    if identity is None or identity.public_key_jwk != payload.sender_public_key_jwk:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CRYPTO_IDENTITY_REQUIRED_OR_MISMATCH")

    conversation = get_or_create_conversation(db, current_user.id, payload.to_user_id)
    if not can_send_message(db, current_user.id, conversation):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_codes.LIMIT_REACHED)

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        type=MessageType.TEXT,
        text=None,
        ciphertext=payload.ciphertext,
        nonce=payload.nonce,
        sender_public_key_jwk=payload.sender_public_key_jwk,
        crypto_version=payload.crypto_version,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    n=create_notification(db,target.id,NotificationType.MESSAGE,title="New message",body="You have a new encrypted message.")
    deliver_push(db,n); db.commit()
    return _message_out(db, message)


@router.post("/messages/media", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(UPLOAD_LIMIT)
async def send_media_message(
    request: Request,
    to_user_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> MessageOut:
    """Temporary chat-photo endpoint. Full media UX, video support, quotas,
    compression and expiry enforcement are completed in the media phase."""
    if to_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself")
    target = db.query(User).filter(User.id == to_user_id).first()
    if target is None or not target.is_active or target.is_suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _check_not_blocked(db, current_user.id, to_user_id)

    conversation = get_or_create_conversation(db, current_user.id, to_user_id)
    if not can_send_message(db, current_user.id, conversation):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_codes.LIMIT_REACHED)

    if file.size is not None and file.size > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 8MB)")

    content = await file.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 8MB)")

    storage = get_storage_service()
    storage_key = None
    try:
        storage_key = storage.save(content, file.content_type or "", folder=f"chat/{current_user.id}")
        message = Message(conversation_id=conversation.id, sender_id=current_user.id, type=MessageType.PHOTO)
        db.add(message)
        db.flush()
        media = Media(
            user_id=current_user.id,
            message_id=message.id,
            type=MediaType.PHOTO,
            storage_key=storage_key,
            size_bytes=len(content),
        )
        db.add(media)
        db.flush()
        message.media_id = media.id
        db.commit()
        db.refresh(message)
        return _message_out(db, message)
    except StorageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        db.rollback()
        if storage_key:
            storage.delete(storage_key)
        raise
