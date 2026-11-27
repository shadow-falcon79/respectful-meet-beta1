from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.plans import SUBSCRIPTION_PLANS
from app.models.notification import Notification, NotificationType
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.services.telegram_service import TelegramApiError, TelegramService


def create_invoice_for_user(db: Session, user_id: str, plan_name: str) -> tuple[Payment, str]:
    try:
        plan = SubscriptionPlan(plan_name)
    except ValueError as exc:
        raise ValueError("Invalid subscription plan") from exc

    config = SUBSCRIPTION_PLANS[plan]
    now = datetime.now(timezone.utc)

    # Reuse a recent pending invoice for the same user/plan to avoid creating
    # an unlimited number of live invoices from repeated button taps.
    existing = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.plan == plan.value,
            Payment.status == PaymentStatus.PENDING,
            Payment.created_at >= now - timedelta(minutes=15),
        )
        .order_by(Payment.created_at.desc())
        .first()
    )
    if existing is not None:
        try:
            return existing, TelegramService().create_invoice_link(
                title=f"Respectful Meet {plan.value.title()} Premium",
                description=f"{config.duration_days} days of Respectful Meet Premium access.",
                payload=existing.id,
                amount=existing.stars_amount,
            )
        except TelegramApiError:
            existing.status = PaymentStatus.FAILED
            db.commit()

    payment = Payment(
        user_id=user_id,
        plan=plan.value,
        stars_amount=config.stars_price,
        payment_provider="telegram_stars",
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    try:
        invoice_url = TelegramService().create_invoice_link(
            title=f"Respectful Meet {plan.value.title()} Premium",
            description=f"{config.duration_days} days of Respectful Meet Premium access.",
            payload=payment.id,
            amount=config.stars_price,
        )
    except TelegramApiError:
        payment.status = PaymentStatus.FAILED
        db.commit()
        raise

    return payment, invoice_url


def validate_precheckout(db: Session, payload: str, currency: str, total_amount: int) -> bool:
    payment = db.query(Payment).filter(Payment.id == payload).first()
    if payment is None or payment.status != PaymentStatus.PENDING:
        return False
    return currency == "XTR" and total_amount == payment.stars_amount


def fulfill_successful_payment(
    db: Session,
    *,
    payload: str,
    telegram_user_id: str,
    charge_id: str,
    currency: str,
    total_amount: int,
) -> Payment | None:
    if currency != "XTR":
        return None

    payment = db.query(Payment).filter(Payment.id == payload).with_for_update().first()
    if payment is None:
        return None

    # Webhook retries are expected. A successful payment is delivered exactly
    # once to the business state even if Telegram retries the update.
    if payment.status == PaymentStatus.SUCCESSFUL:
        return payment
    if payment.status != PaymentStatus.PENDING or payment.stars_amount != total_amount:
        return None

    duplicate = (
        db.query(Payment)
        .filter(Payment.telegram_charge_id == charge_id, Payment.id != payment.id)
        .first()
    )
    if duplicate is not None:
        return None

    payment.telegram_user_id = telegram_user_id
    payment.telegram_charge_id = charge_id
    payment.status = PaymentStatus.SUCCESSFUL

    plan = SubscriptionPlan(payment.plan)
    plan_config = SUBSCRIPTION_PLANS[plan]
    now = datetime.now(timezone.utc)

    active = (
        db.query(Subscription)
        .filter(Subscription.user_id == payment.user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    if active is not None and active.expires_at.replace(tzinfo=timezone.utc) > now:
        start_at = active.expires_at.replace(tzinfo=timezone.utc)
        active.status = SubscriptionStatus.CANCELLED
    else:
        start_at = now
        if active is not None:
            active.status = SubscriptionStatus.EXPIRED

    subscription = Subscription(
        user_id=payment.user_id,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        started_at=now,
        expires_at=start_at + timedelta(days=plan_config.duration_days),
        payment_id=payment.id,
    )
    db.add(subscription)
    db.add(
        Notification(
            user_id=payment.user_id,
            type=NotificationType.PAYMENT,
            title="Premium activated",
            body=f"Your {plan.value.lower()} Premium plan is active until {subscription.expires_at.isoformat()}.",
            is_read=False,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # A duplicate webhook can race another worker. Re-read the payment;
        # the unique charge constraint is the final database backstop.
        return db.query(Payment).filter(Payment.id == payment.id).first()
    db.refresh(payment)
    return payment
