from urllib.parse import urlparse

from app.core.config import settings


def validate_production_settings() -> None:
    """Fail fast on required production settings, but keep optional beta
    integrations (email, push, Telegram, ads, object storage) optional unless
    their credentials/features are explicitly enabled.
    """
    if settings.environment.lower() not in {"production", "prod"}:
        return

    errors: list[str] = []
    database_url = settings.database_url.strip()
    if not database_url or "localhost" in database_url or "changeme" in database_url:
        errors.append("DATABASE_URL must point to the hosted PostgreSQL database")

    if not settings.secret_key or settings.secret_key == "changeme" or len(settings.secret_key) < 32:
        errors.append("SECRET_KEY must be a strong value of at least 32 characters")

    origins = settings.cors_origins_list
    if not origins or any(not origin.startswith("https://") for origin in origins):
        errors.append("CORS_ORIGINS must contain the HTTPS frontend origin(s)")

    hosts = settings.allowed_hosts_list
    if not hosts or "*" in hosts:
        errors.append("ALLOWED_HOSTS must contain explicit production hostnames")

    # Admin OTP is only available when an admin allowlist is configured.
    # Regular beta users authenticate with username/password and do not need SMTP.
    if settings.admin_allowed_emails_list:
        email_provider = settings.email_provider.lower().strip()
        if email_provider not in ("smtp", "gmail_smtp", "gmail"):
            errors.append("EMAIL_PROVIDER must be configured for admin OTP when ADMIN_ALLOWED_EMAILS is set")
        if not settings.smtp_username or not settings.smtp_app_password or not settings.email_sender_email:
            errors.append("SMTP credentials and EMAIL_SENDER_EMAIL are required for admin OTP")

    # Optional integrations: reject partial configuration, not an intentionally
    # disabled integration. This lets a zero-budget beta boot safely.
    vapid_values = (settings.vapid_public_key, settings.vapid_private_key)
    if any(vapid_values) and not all(vapid_values):
        errors.append("Configure both VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY, or leave push disabled")

    telegram_values = (settings.telegram_bot_token, settings.telegram_webhook_secret)
    if any(telegram_values) and not all(telegram_values):
        errors.append("Configure both Telegram bot credentials, or leave Telegram payments disabled")

    storage_values = (settings.storage_url, settings.storage_bucket, settings.storage_access_key, settings.storage_secret_key)
    if any(storage_values) and not all(storage_values):
        errors.append("Configure all S3 storage credentials, or use temporary local storage for beta testing")

    if settings.ads_enabled and (settings.ads_mock_mode or not settings.ads_postback_secret):
        errors.append("Rewarded ads require a real provider and ADS_POSTBACK_SECRET in production")

    backend_url = settings.effective_public_backend_url
    if backend_url:
        if not backend_url.startswith("https://"):
            errors.append("PUBLIC_BACKEND_URL / RENDER_EXTERNAL_URL must use HTTPS")
        backend_host = urlparse(backend_url).hostname
        if backend_host and backend_host not in hosts:
            errors.append("ALLOWED_HOSTS must include the PUBLIC_BACKEND_URL hostname")

    if errors:
        raise RuntimeError("Production configuration invalid: " + "; ".join(errors))
