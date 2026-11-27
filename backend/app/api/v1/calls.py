"""Ephemeral WebRTC signalling for beta calls, with server-enforced daily
call-minute quotas (backend master spec section 8/54: quotas must be
enforced server-side, never trusted from the client).

The server never receives or stores microphone/camera media — only WebRTC
signalling. Duration is measured from the first 'offer' (the call actually
connecting) to hangup/disconnect, and persisted as CallSession rows so the
quota survives server restarts and can't be reset by refreshing the client.
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Cookie, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.auth.security import hash_session_token
from app.core.database import SessionLocal, get_db
from app.models.block import Block
from app.models.conversation import Conversation
from app.models.session import Session as SessionModel
from app.models.user import User
from app.schemas.calls import CallQuotaOut
from app.services.call_quota_service import (
    can_start_call,
    get_minutes_remaining_today,
    get_seconds_remaining_today,
    record_call_session,
)

router = APIRouter(tags=["calls"])

_connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)
_inboxes: dict[str, WebSocket] = {}

# One active-call record per conversation, tracking real wall-clock start
# so we can bill accurate duration and enforce quota mid-call.
_active_calls: dict[str, dict[str, Any]] = {}
_watchdogs: dict[str, asyncio.Task] = {}


@router.get("/calls/quota", response_model=CallQuotaOut)
def get_call_quota(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> CallQuotaOut:
    return CallQuotaOut(
        minutes_remaining_today=get_minutes_remaining_today(db, current_user.id),
        can_start_call=can_start_call(db, current_user.id),
    )


def _authenticate(token: str | None, db: DbSession) -> User | None:
    if not token:
        return None
    session = db.query(SessionModel).filter(
        SessionModel.session_token_hash == hash_session_token(token),
        SessionModel.revoked_at.is_(None),
    ).first()
    if session is None:
        return None
    # This mirrors app.auth.dependencies.get_current_user, which the REST
    # API uses. Without this check, a session that is past its 30-day
    # expiry but was never explicitly revoked (logout) could still open a
    # voice/video signalling socket indefinitely.
    now = datetime.now(timezone.utc)
    if session.expires_at.replace(tzinfo=timezone.utc) < now:
        return None
    user = db.query(User).filter(User.id == session.user_id, User.is_active.is_(True)).first()
    if user is None or user.is_suspended:
        return None
    return user


def _conversation_peer(db: DbSession, conversation_id: str, user_id: str) -> str | None:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None or user_id not in (conversation.user_a_id, conversation.user_b_id):
        return None
    peer = conversation.user_b_id if conversation.user_a_id == user_id else conversation.user_a_id
    blocked = db.query(Block).filter(
        ((Block.blocker_id == user_id) & (Block.blocked_id == peer)) |
        ((Block.blocker_id == peer) & (Block.blocked_id == user_id))
    ).first()
    return None if blocked else peer


async def _relay(conversation_id: str, sender_id: str, payload: dict[str, Any]) -> None:
    for peer_id, socket in list(_connections.get(conversation_id, {}).items()):
        if peer_id == sender_id:
            continue
        try:
            await socket.send_json(payload)
        except Exception:
            _connections[conversation_id].pop(peer_id, None)


async def _end_call(conversation_id: str, reason: str) -> None:
    """Persists the CallSession for both participants and clears in-memory
    state. Called on normal hangup, disconnect, or quota exhaustion."""
    call = _active_calls.pop(conversation_id, None)
    watchdog = _watchdogs.pop(conversation_id, None)
    if watchdog is not None and not watchdog.done():
        watchdog.cancel()
    if call is None:
        return

    db = SessionLocal()
    try:
        ended_at = datetime.now(timezone.utc)
        for uid, peer_uid in ((call["user_id"], call["peer_id"]), (call["peer_id"], call["user_id"])):
            record_call_session(
                db,
                conversation_id=conversation_id,
                user_id=uid,
                peer_id=peer_uid,
                mode=call["mode"],
                started_at=call["started_at"],
                ended_at=ended_at,
                ended_reason=reason,
            )
    finally:
        db.close()


async def _quota_watchdog(conversation_id: str, seconds_left: float) -> None:
    try:
        await asyncio.sleep(seconds_left)
    except asyncio.CancelledError:
        return
    # Time's up — force both sides to hang up, same as a real provider
    # cutting the line when a plan's minutes run out.
    for socket in list(_connections.get(conversation_id, {}).values()):
        try:
            await socket.send_json({"type": "quota_exceeded"})
        except Exception:
            pass
    await _end_call(conversation_id, "quota_exceeded")


async def _try_start_call(conversation_id: str, user_id: str, peer_id: str, mode: str) -> bool:
    """Called on the first 'offer' of a call. Checks both participants'
    remaining quota and starts the billing/watchdog clock. Returns False
    (and the caller must reject the offer) if either side is out of
    minutes."""
    if conversation_id in _active_calls:
        return True  # already running, nothing to (re)check

    db = SessionLocal()
    try:
        caller_seconds = get_seconds_remaining_today(db, user_id)
        callee_seconds = get_seconds_remaining_today(db, peer_id)
    finally:
        db.close()

    if caller_seconds <= 0 or callee_seconds <= 0:
        return False

    _active_calls[conversation_id] = {
        "user_id": user_id,
        "peer_id": peer_id,
        "mode": mode,
        "started_at": datetime.now(timezone.utc),
    }
    remaining = min(caller_seconds, callee_seconds)
    _watchdogs[conversation_id] = asyncio.create_task(_quota_watchdog(conversation_id, remaining))
    return True


@router.websocket("/ws/calls/{conversation_id}")
async def call_signalling(websocket: WebSocket, conversation_id: str, session_token: str | None = Cookie(default=None)):
    db = SessionLocal()
    user = _authenticate(session_token, db)
    if user is None:
        await websocket.close(code=4401)
        db.close()
        return

    peer_id = _conversation_peer(db, conversation_id, user.id)
    db.close()
    if peer_id is None:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    _connections[conversation_id][user.id] = websocket
    try:
        await websocket.send_json({"type": "presence", "peer_online": peer_id in _connections[conversation_id]})
        await _relay(conversation_id, user.id, {"type": "peer_joined"})
        while True:
            message = await websocket.receive_json()
            kind = message.get("type")

            if kind == "invite":
                db = SessionLocal()
                try:
                    allowed = can_start_call(db, user.id)
                finally:
                    db.close()
                if not allowed:
                    await websocket.send_json({"type": "quota_exceeded"})
                    continue
                inbox = _inboxes.get(peer_id)
                if inbox is not None:
                    await inbox.send_json({"type": "incoming_call", "conversation_id": conversation_id, "from": user.id, "mode": message.get("mode", "audio")})
                continue

            if kind == "offer":
                started = await _try_start_call(conversation_id, user.id, peer_id, message.get("mode", "audio"))
                if not started:
                    await websocket.send_json({"type": "quota_exceeded"})
                    continue

            if kind not in {"offer", "answer", "ice", "hangup", "reject", "busy"}:
                continue
            await _relay(conversation_id, user.id, {"type": kind, "from": user.id, "data": message.get("data")})
            if kind in {"hangup", "reject"}:
                await _end_call(conversation_id, kind)
                break
    except WebSocketDisconnect:
        pass
    finally:
        if _connections.get(conversation_id, {}).get(user.id) is websocket:
            _connections[conversation_id].pop(user.id, None)
        if not _connections.get(conversation_id):
            _connections.pop(conversation_id, None)
            if conversation_id in _active_calls:
                await _end_call(conversation_id, "disconnect")
        else:
            await _relay(conversation_id, user.id, {"type": "peer_left"})


@router.websocket("/ws/call-inbox")
async def call_inbox(websocket: WebSocket, session_token: str | None = Cookie(default=None)):
    db = SessionLocal()
    user = _authenticate(session_token, db)
    db.close()
    if user is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    _inboxes[user.id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if _inboxes.get(user.id) is websocket:
            _inboxes.pop(user.id, None)
