from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import SessionLocal

from app.api.v1.auth import router as auth_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.social import router as social_router
from app.api.v1.messages import router as messages_router
from app.api.v1.moderation import router as moderation_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.admin_auth import router as admin_auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.crypto import router as crypto_router
from app.api.v1.calls import router as calls_router
from app.api.v1.telegram import router as telegram_router
from app.api.v1.ads import router as ads_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.settings import router as settings_router
from app.api.v1.privacy import router as privacy_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(profiles_router)
router.include_router(social_router)
router.include_router(messages_router)
router.include_router(moderation_router)
router.include_router(subscriptions_router)
router.include_router(admin_auth_router)
router.include_router(admin_router)
router.include_router(crypto_router)
router.include_router(calls_router)
router.include_router(telegram_router)
router.include_router(ads_router)
router.include_router(notifications_router)
router.include_router(settings_router)
router.include_router(privacy_router)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "respectful-meet-backend"}


@router.get("/health/ready")
def readiness_check() -> dict[str, str]:
    """Readiness probe: verifies the application can reach PostgreSQL."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database unavailable")
    finally:
        db.close()
