"""Rewarded ads (offerwall). See app/services/ad_reward_service.py for the
full flow explanation.

Three endpoints:
  POST /ads/session            — client asks to start watching an ad
  POST /ads/postback/{provider} — the REAL provider calls this server-to-
                                   server, signed. This is what AdMantum
                                   will hit once we're approved.
  POST /ads/mock/complete       — DEV ONLY, simulates the postback locally.
                                   Refuses to run unless ads_mock_mode=true,
                                   which must be false in production.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.plans import AD_REWARD_BONUS_CALL_MINUTES, AD_REWARD_BONUS_MESSAGES
from app.models.ad_reward import AdRewardStatus, AdRewardType
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.ads import AdPostbackResult, AdSessionCreate, AdSessionOut
from app.services import ad_reward_service

router = APIRouter(prefix="/ads", tags=["ads"])

# Realistic rewarded-video length — matches typical offerwall video ads
# (15-30s). Kept centralized so the mock and any future UI copy agree.
_MOCK_AD_DURATION_SECONDS = 20


@router.post("/session", response_model=AdSessionOut)
def start_ad_session(
    payload: AdSessionCreate,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> AdSessionOut:
    if not settings.ads_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ADS_DISABLED")
    try:
        reward_type = AdRewardType(payload.reward_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_REWARD_TYPE")

    if reward_type == AdRewardType.UNLOCK_MESSAGES:
        if not payload.conversation_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CONVERSATION_ID_REQUIRED")
        conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
        if conversation is None or current_user.id not in (conversation.user_a_id, conversation.user_b_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CONVERSATION_NOT_FOUND")

    session = ad_reward_service.create_ad_session(
        db,
        user_id=current_user.id,
        reward_type=reward_type,
        conversation_id=payload.conversation_id,
        provider=settings.ads_provider,
    )
    return AdSessionOut(
        session_id=session.id,
        external_ref=session.external_ref,
        reward_type=session.reward_type.value,
        mock_duration_seconds=_MOCK_AD_DURATION_SECONDS if settings.ads_mock_mode else None,
    )


def _apply_reward_response(session) -> AdPostbackResult:
    if session is None:
        return AdPostbackResult(status="not_found")
    if session.status != AdRewardStatus.COMPLETED:
        return AdPostbackResult(status=session.status.value)
    return AdPostbackResult(
        status="completed",
        reward_type=session.reward_type.value,
        bonus_messages=AD_REWARD_BONUS_MESSAGES if session.reward_type == AdRewardType.UNLOCK_MESSAGES else None,
        bonus_call_minutes=AD_REWARD_BONUS_CALL_MINUTES if session.reward_type == AdRewardType.EXTRA_CALL_MINUTES else None,
    )


@router.post("/postback/{provider}", response_model=AdPostbackResult)
async def provider_postback(provider: str, request: Request, db: DbSession = Depends(get_db)) -> AdPostbackResult:
    """Real server-to-server callback. Adjust field names/signature header
    to match AdMantum's actual documented postback format once we have
    their integration docs — the verification shape stays the same."""
    raw_body = await request.body()
    signature = request.headers.get("X-Signature", "")
    if not ad_reward_service.verify_postback_signature(raw_body, signature, settings.ads_postback_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_SIGNATURE")

    payload = await request.json()
    external_ref = payload.get("external_ref") or payload.get("click_id")
    if not external_ref:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MISSING_EXTERNAL_REF")

    session = ad_reward_service.complete_ad_session(db, external_ref)
    return _apply_reward_response(session)


@router.post("/mock/complete", response_model=AdPostbackResult)
def mock_complete_ad(
    external_ref: str,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> AdPostbackResult:
    """Simulates the provider postback for local dev/demo before AdMantum
    approval. Same effect as the real postback (idempotent completion),
    just triggered by our own frontend instead of their servers.
    """
    if settings.environment.lower() == "production" or not settings.ads_enabled or not settings.ads_mock_mode:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MOCK_MODE_DISABLED")

    from app.models.ad_reward import AdReward  # local import avoids a cycle at module load

    session = db.query(AdReward).filter(AdReward.external_ref == external_ref).first()
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")

    session = ad_reward_service.complete_ad_session(db, external_ref)
    return _apply_reward_response(session)
