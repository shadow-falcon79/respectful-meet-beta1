from datetime import datetime, time, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.plans import FREE_MESSAGES_PER_NEW_CONTACT, PREMIUM_DAILY_MESSAGE_LIMIT
from app.models.conversation import Conversation
from app.models.match import Match
from app.models.message import Message
from app.services.ad_reward_service import get_bonus_messages
from app.services.subscription_service import is_premium


def _sorted_pair(user_a: str, user_b: str) -> tuple[str, str]:
    if user_a == user_b:
        raise ValueError("A conversation requires two distinct users")
    a, b = sorted((user_a, user_b))
    return a, b


def is_matched(db: Session, user_a: str, user_b: str) -> bool:
    a, b = _sorted_pair(user_a, user_b)
    return db.query(Match).filter(Match.user_a_id == a, Match.user_b_id == b).first() is not None


def get_or_create_conversation(db: Session, user_a: str, user_b: str) -> Conversation:
    a, b = _sorted_pair(user_a, user_b)
    conversation = db.query(Conversation).filter(Conversation.user_a_id == a, Conversation.user_b_id == b).first()
    if conversation is None:
        conversation = Conversation(user_a_id=a, user_b_id=b, is_matched=is_matched(db, user_a, user_b))
        try:
            with db.begin_nested():
                db.add(conversation)
                db.flush()
        except IntegrityError:
            conversation = db.query(Conversation).filter(
                Conversation.user_a_id == a, Conversation.user_b_id == b
            ).first()
            if conversation is None:
                raise
        else:
            db.commit()
            db.refresh(conversation)
    elif not conversation.is_matched and is_matched(db, user_a, user_b):
        conversation.is_matched = True
        db.commit()
    return conversation


def _start_of_today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def _messages_sent_today(db: Session, user_id: str) -> int:
    return db.query(Message).filter(
        Message.sender_id == user_id,
        Message.created_at >= _start_of_today_utc(),
    ).count()


def can_send_message(db: Session, sender_id: str, conversation: Conversation) -> bool:
    if is_premium(db, sender_id):
        return _messages_sent_today(db, sender_id) < PREMIUM_DAILY_MESSAGE_LIMIT

    if conversation.is_matched:
        return True

    sent_count = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_id == sender_id,
    ).count()
    limit = FREE_MESSAGES_PER_NEW_CONTACT + get_bonus_messages(db, sender_id, conversation.id)
    return sent_count < limit
