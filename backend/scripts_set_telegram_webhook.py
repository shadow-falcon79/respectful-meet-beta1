"""Set Telegram webhook after the backend has a public HTTPS URL.

Run with the same environment variables as the backend:
  python backend/scripts_set_telegram_webhook.py
"""
from app.core.config import settings
from app.services.telegram_service import TelegramService

if not settings.public_backend_url:
    raise SystemExit("PUBLIC_BACKEND_URL is required")
if not settings.telegram_webhook_secret:
    raise SystemExit("TELEGRAM_WEBHOOK_SECRET is required")

url = settings.public_backend_url.rstrip("/") + "/api/v1/telegram/webhook"
result = TelegramService().call(
    "setWebhook",
    {
        "url": url,
        "secret_token": settings.telegram_webhook_secret,
        "allowed_updates": ["message", "pre_checkout_query"],
        "drop_pending_updates": True,
        "max_connections": 20,
    },
)
print(result)
