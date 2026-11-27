import pytest

from app.core.config import settings
from app.services.photo_moderation_service import get_photo_moderation_service, NoOpModerationProvider


def test_moderation_disabled_by_default_returns_noop_provider():
    assert settings.photo_moderation_enabled is False
    provider = get_photo_moderation_service()
    assert isinstance(provider, NoOpModerationProvider)


def test_noop_provider_approves_everything():
    provider = NoOpModerationProvider()
    result = provider.screen(b"\xff\xd8\xff", "image/jpeg")
    assert result.approved is True
    assert result.reason is None


def test_enabling_without_a_configured_provider_fails_loudly(monkeypatch):
    monkeypatch.setattr(settings, "photo_moderation_enabled", True)
    monkeypatch.setattr(settings, "photo_moderation_provider", "none")
    with pytest.raises(RuntimeError):
        get_photo_moderation_service()


def test_enabling_with_an_unknown_provider_fails_loudly(monkeypatch):
    monkeypatch.setattr(settings, "photo_moderation_enabled", True)
    monkeypatch.setattr(settings, "photo_moderation_provider", "some_unregistered_vendor")
    with pytest.raises(RuntimeError):
        get_photo_moderation_service()
