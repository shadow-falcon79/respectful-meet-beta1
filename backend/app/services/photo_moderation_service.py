"""Automated photo moderation (backend master spec follow-up from the pre-
beta audit): screen uploaded photos for nudity, sexual content involving
minors, and graphic violence *before* they are stored and shown to other
users — the same "screen before trusting" posture already used for file
type/magic-byte checks in storage_service.py, applied to content rather
than format.

This follows the exact pattern already established for rewarded ads
(app/core/config.py ads_provider/ads_mock_mode, app/services/ad_reward_service.py):
a real, swappable interface with a safe no-op default, rather than a fake
"always approved" check pretending to be moderation. Enabling this for real
requires a provider account (see PhotoModerationProvider docstring below) —
until then, PHOTO_MODERATION_ENABLED stays false and every photo goes
through unscreened, exactly as today, which app/main.py's production
validator and PRODUCTION_AUDIT.md both call out explicitly so this is never
silently mistaken for "handled".
"""

from dataclasses import dataclass

from app.core.config import settings


@dataclass
class ModerationResult:
    approved: bool
    reason: str | None = None  # short machine-readable reason, e.g. "nudity", "violence"


class PhotoModerationProvider:
    """Abstract interface a real provider integration implements.

    To wire in a real provider (e.g. AWS Rekognition DetectModerationLabels,
    Hive Moderation, or Sightengine):
      1. Add a class here implementing `screen`.
      2. Add its name to the `if` chain in `get_photo_moderation_service()`.
      3. Set PHOTO_MODERATION_PROVIDER, PHOTO_MODERATION_ENABLED=true and
         PHOTO_MODERATION_API_KEY in the production environment.
    Nothing in app/api/v1/profiles.py or admin.py needs to change — they
    only ever call `get_photo_moderation_service().screen(...)`.
    """

    def screen(self, content: bytes, content_type: str) -> ModerationResult:
        raise NotImplementedError


class NoOpModerationProvider(PhotoModerationProvider):
    """Default when moderation is disabled or unconfigured. Approves
    everything — this is a deliberate, visible no-op, not a silent gap:
    callers and ops tooling can check `settings.photo_moderation_enabled`
    to know whether real screening is active."""

    def screen(self, content: bytes, content_type: str) -> ModerationResult:
        return ModerationResult(approved=True, reason=None)


def get_photo_moderation_service() -> PhotoModerationProvider:
    if not settings.photo_moderation_enabled:
        return NoOpModerationProvider()

    provider = settings.photo_moderation_provider.lower()
    if provider == "none" or not provider:
        # Enabled=true but no provider configured is a misconfiguration,
        # not a silent pass-through — fail loudly rather than pretend to
        # screen content.
        raise RuntimeError(
            "PHOTO_MODERATION_ENABLED is true but PHOTO_MODERATION_PROVIDER is not set"
        )
    raise RuntimeError(
        f"Unknown PHOTO_MODERATION_PROVIDER '{provider}' — implement and register it in "
        "app/services/photo_moderation_service.py before enabling it"
    )
