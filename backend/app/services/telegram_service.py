from __future__ import annotations

import httpx

from app.core.config import settings


class TelegramApiError(RuntimeError):
    pass


class TelegramService:
    def __init__(self) -> None:
        if not settings.telegram_bot_token:
            raise TelegramApiError("Telegram bot token is not configured")
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    def call(self, method: str, payload: dict) -> dict:
        # Do not log payloads: they can contain invoice identifiers.
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{self.base_url}/{method}", json=payload)
        if response.status_code >= 400:
            raise TelegramApiError("Telegram API HTTP error")
        body = response.json()
        if not body.get("ok"):
            raise TelegramApiError("Telegram API rejected the request")
        return body["result"]

    def create_invoice_link(self, *, title: str, description: str, payload: str, amount: int) -> str:
        result = self.call(
            "createInvoiceLink",
            {
                "title": title[:32],
                "description": description[:255],
                "payload": payload,
                "currency": "XTR",
                "prices": [{"label": title[:32], "amount": amount}],
            },
        )
        return str(result)

    def answer_pre_checkout(self, query_id: str, ok: bool, error_message: str | None = None) -> None:
        payload = {"pre_checkout_query_id": query_id, "ok": ok}
        if not ok and error_message:
            payload["error_message"] = error_message[:200]
        self.call("answerPreCheckoutQuery", payload)

    def send_message(self, chat_id: int | str, text: str, reply_markup: dict | None = None) -> None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self.call("sendMessage", payload)

    def refund_star_payment(self, user_id: int, telegram_payment_charge_id: str) -> None:
        self.call(
            "refundStarPayment",
            {"user_id": user_id, "telegram_payment_charge_id": telegram_payment_charge_id},
        )
