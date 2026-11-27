from __future__ import annotations

import hmac

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.payment_service import fulfill_successful_payment, validate_precheckout
from app.services.telegram_service import TelegramApiError, TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _webhook_secret_ok(header_value: str | None) -> bool:
    # Constant-time comparison: a naive `==` on strings short-circuits at
    # the first mismatched byte, which leaks timing information an attacker
    # could use to guess the secret one byte at a time over many requests.
    if not settings.telegram_webhook_secret or not header_value:
        return False
    return hmac.compare_digest(header_value, settings.telegram_webhook_secret)


def _handle_update(update: dict, db: DbSession) -> None:
    pre = update.get("pre_checkout_query")
    if pre:
        query_id = str(pre.get("id", ""))
        payload = str(pre.get("invoice_payload", ""))
        currency = str(pre.get("currency", ""))
        total_amount = int(pre.get("total_amount", 0))
        ok = validate_precheckout(db, payload, currency, total_amount)
        try:
            TelegramService().answer_pre_checkout(
                query_id,
                ok,
                None if ok else "This payment request is no longer valid. Please start checkout again.",
            )
        except TelegramApiError:
            # Telegram retries the update if we fail to answer. Do not turn a
            # provider outage into a successful payment.
            raise
        return

    message = update.get("message") or {}
    successful = message.get("successful_payment")
    if successful:
        payload = str(successful.get("invoice_payload", ""))
        telegram_user_id = str((message.get("from") or {}).get("id", ""))
        charge_id = str(successful.get("telegram_payment_charge_id", ""))
        currency = str(successful.get("currency", ""))
        total_amount = int(successful.get("total_amount", 0))
        payment = fulfill_successful_payment(
            db,
            payload=payload,
            telegram_user_id=telegram_user_id,
            charge_id=charge_id,
            currency=currency,
            total_amount=total_amount,
        )
        if payment:
            try:
                TelegramService().send_message(
                    message.get("chat", {}).get("id"),
                    "✅ Payment confirmed. Your Respectful Meet Premium is now active. You can return to the app.",
                )
            except TelegramApiError:
                # Delivery of the confirmation message is best-effort; the
                # premium entitlement is already committed server-side.
                pass
        return

    text = (message.get("text") or "").strip()
    chat_id = (message.get("chat") or {}).get("id")
    if chat_id and text.startswith("/start"):
        TelegramService().send_message(
            chat_id,
            "❤️ Welcome to Respectful Meet.\n\nUse the Respectful Meet app to choose a Premium plan and pay securely with Telegram Stars.\n\nFor payment support use /paysupport.",
        )
    elif chat_id and text.startswith("/paysupport"):
        TelegramService().send_message(
            chat_id,
            "Payment support: keep your Telegram payment receipt and contact Respectful Meet support with the payment details. Never send your Telegram login code or bot token.",
        )
    elif chat_id and text.startswith("/help"):
        TelegramService().send_message(
            chat_id,
            "/start - Start\n/premium - Premium information\n/account - Account help\n/paysupport - Payment support\n/help - Help",
        )
    elif chat_id and text.startswith("/premium"):
        TelegramService().send_message(
            chat_id,
            "💎 Premium purchases are initiated from Respectful Meet. Open the app, choose your plan, and Telegram will handle the Stars checkout securely.",
        )


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    if not _webhook_secret_ok(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")
    body = await request.json()
    db = SessionLocal()
    try:
        _handle_update(body, db)
    finally:
        db.close()
    return {"ok": True}
