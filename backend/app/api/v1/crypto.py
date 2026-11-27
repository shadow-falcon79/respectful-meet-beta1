from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.crypto_identity import CryptoIdentity
from app.models.user import User
from app.schemas.crypto import CryptoIdentityIn, CryptoIdentityOut

router = APIRouter(prefix="/crypto", tags=["crypto"])


def _validate_fingerprint(value: str) -> str:
    value = value.strip().lower()
    if len(value) < 32 or any(c not in "0123456789abcdef:" for c in value):
        raise HTTPException(status_code=400, detail="Invalid crypto fingerprint")
    return value


@router.put("/identity", response_model=CryptoIdentityOut)
def upsert_identity(
    payload: CryptoIdentityIn,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    fingerprint = _validate_fingerprint(payload.fingerprint)
    identity = db.query(CryptoIdentity).filter(CryptoIdentity.user_id == current_user.id).first()
    if identity is None:
        identity = CryptoIdentity(
            user_id=current_user.id,
            public_key_jwk=payload.public_key_jwk,
            fingerprint=fingerprint,
        )
        db.add(identity)
    elif identity.public_key_jwk != payload.public_key_jwk:
        # Key rotation is explicit. The client must generate a new identity and
        # existing conversations will show a changed safety fingerprint.
        identity.public_key_jwk = payload.public_key_jwk
        identity.fingerprint = fingerprint
        from datetime import datetime, timezone
        identity.rotated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(identity)
    return CryptoIdentityOut(user_id=identity.user_id, public_key_jwk=identity.public_key_jwk, fingerprint=identity.fingerprint)


@router.get("/identity/me", response_model=CryptoIdentityOut)
def get_my_identity(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    identity = db.query(CryptoIdentity).filter(CryptoIdentity.user_id == current_user.id).first()
    if identity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CRYPTO_IDENTITY_NOT_INITIALIZED")
    return CryptoIdentityOut(user_id=identity.user_id, public_key_jwk=identity.public_key_jwk, fingerprint=identity.fingerprint)

@router.get("/conversations/{conversation_id}/peer", response_model=CryptoIdentityOut)
def get_conversation_peer_identity(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    from app.models.conversation import Conversation
    from app.models.block import Block
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None or current_user.id not in (conversation.user_a_id, conversation.user_b_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    other_id = conversation.user_b_id if current_user.id == conversation.user_a_id else conversation.user_a_id
    blocked = db.query(Block).filter(
        ((Block.blocker_id == current_user.id) & (Block.blocked_id == other_id)) |
        ((Block.blocker_id == other_id) & (Block.blocked_id == current_user.id))
    ).first()
    if blocked:
        raise HTTPException(status_code=403, detail="BLOCKED_USER")
    identity = db.query(CryptoIdentity).filter(CryptoIdentity.user_id == other_id).first()
    if identity is None:
        raise HTTPException(status_code=409, detail="PEER_CRYPTO_IDENTITY_NOT_INITIALIZED")
    return CryptoIdentityOut(user_id=identity.user_id, public_key_jwk=identity.public_key_jwk, fingerprint=identity.fingerprint)
