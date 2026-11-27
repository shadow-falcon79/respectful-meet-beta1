from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.plans import FREE_DAILY_LIKE_LIMIT, PREMIUM_DAILY_LIKE_LIMIT, SUBSCRIPTION_PLANS
from app.core.rate_limit import PAYMENT_INVOICE_LIMIT, limiter
from app.models.user import User
from app.services.payment_service import create_invoice_for_user
from app.schemas.subscription import PlanOut, SubscriptionStatusOut
from app.services.limit_service import get_likes_today_count
from app.services.subscription_service import get_active_subscription, is_premium

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=list[PlanOut])
def list_plans() -> list[PlanOut]:
    return [
        PlanOut(plan=plan.value, stars_price=cfg.stars_price, duration_days=cfg.duration_days, call_minutes_per_day=cfg.call_minutes_per_day)
        for plan, cfg in SUBSCRIPTION_PLANS.items()
    ]


@router.get("/me", response_model=SubscriptionStatusOut)
def get_my_subscription(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> SubscriptionStatusOut:
    subscription = get_active_subscription(db, current_user.id)
    premium = subscription is not None
    return SubscriptionStatusOut(
        is_premium=premium,
        plan=subscription.plan.value if subscription else None,
        expires_at=subscription.expires_at if subscription else None,
        likes_limit_today=PREMIUM_DAILY_LIKE_LIMIT if premium else FREE_DAILY_LIKE_LIMIT,
        likes_used_today=get_likes_today_count(db, current_user.id),
    )


@router.post("/checkout/{plan}")
@limiter.limit(PAYMENT_INVOICE_LIMIT)
def create_checkout(
    request: Request,
    plan: str,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> dict[str, object]:
    try:
        payment, invoice_url = create_invoice_for_user(db, current_user.id, plan.upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        # Do not leak Telegram/provider errors or secrets to clients.
        raise HTTPException(status_code=503, detail="Telegram payment service is temporarily unavailable") from exc
    return {
        "payment_id": payment.id,
        "plan": payment.plan,
        "stars_amount": payment.stars_amount,
        "invoice_url": invoice_url,
    }
