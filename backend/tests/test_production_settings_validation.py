from app.core.config import settings
from app.core.production import validate_production_settings


def test_production_can_boot_with_optional_beta_integrations_disabled(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "database_url", "postgresql://user:pass@neon.example/db?sslmode=require")
    monkeypatch.setattr(settings, "secret_key", "x" * 48)
    monkeypatch.setattr(settings, "cors_origins", "https://respectful-meet.vercel.app")
    monkeypatch.setattr(settings, "allowed_hosts", "respectful-meet-api.onrender.com,*.vercel.app")
    monkeypatch.setattr(settings, "render_external_hostname", "respectful-meet-api.onrender.com")
    monkeypatch.setattr(settings, "render_external_url", "https://respectful-meet-api.onrender.com")
    monkeypatch.setattr(settings, "public_backend_url", "")
    monkeypatch.setattr(settings, "admin_allowed_emails", "")
    monkeypatch.setattr(settings, "vapid_public_key", "")
    monkeypatch.setattr(settings, "vapid_private_key", "")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "")
    monkeypatch.setattr(settings, "storage_url", "")
    monkeypatch.setattr(settings, "storage_bucket", "")
    monkeypatch.setattr(settings, "storage_access_key", "")
    monkeypatch.setattr(settings, "storage_secret_key", "")
    monkeypatch.setattr(settings, "ads_enabled", False)

    validate_production_settings()


def test_production_rejects_weak_secret(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "database_url", "postgresql://user:pass@neon.example/db?sslmode=require")
    monkeypatch.setattr(settings, "secret_key", "weak")
    monkeypatch.setattr(settings, "cors_origins", "https://respectful-meet.vercel.app")
    monkeypatch.setattr(settings, "allowed_hosts", "respectful-meet-api.onrender.com")
    monkeypatch.setattr(settings, "render_external_hostname", "respectful-meet-api.onrender.com")
    monkeypatch.setattr(settings, "render_external_url", "https://respectful-meet-api.onrender.com")
    monkeypatch.setattr(settings, "public_backend_url", "")

    try:
        validate_production_settings()
    except RuntimeError as exc:
        assert "SECRET_KEY" in str(exc)
    else:
        raise AssertionError("Expected weak production SECRET_KEY to be rejected")
