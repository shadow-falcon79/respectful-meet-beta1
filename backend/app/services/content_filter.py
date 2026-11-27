"""Content safety for plaintext, publicly-visible text (backend master spec,
section 11): detect phone numbers, external links, and platform-bypass
keywords — including obvious obfuscation attempts.

Applied to the profile bio (app/api/v1/profiles.py), which is plaintext and
public. Deliberately NOT applied to message content: text messages are
end-to-end encrypted (see docs/E2EE_SECURITY.md), so the server never has
plaintext to inspect there — the equivalent restriction on messages is a
client-side pre-encryption gate (frontend/src/services/e2ee.ts) backed by
the server-authoritative entitlement check in
GET /messages/conversations/{id}/external-sharing.
"""

import re

# Matches sequences of digits that, once separators are stripped, look like
# a phone number (7+ consecutive digits). Deliberately broad: it's cheaper
# to review a false positive than to let a real number slip through.
_DIGIT_RUN_RE = re.compile(r"\d[\d\s\-.\(\)]{6,}\d")

_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)

# Keywords that indicate an attempt to move the conversation off-platform.
# Kept short and reviewable — extend via config later rather than growing
# this list ad hoc in multiple places.
_FORBIDDEN_KEYWORDS = [
    "whatsapp",
    "telegram",
    "instagram",
    "snapchat",
    "signal",
    "wechat",
    "viber",
]


def _normalize(text: str) -> str:
    """Collapses obvious obfuscation ("w h a t s a p p", "whats-app") so
    keyword matching still catches it."""
    lowered = text.lower()
    # Remove spaces/dashes/dots BETWEEN letters (e.g. "w h a t s a p p" ->
    # "whatsapp"), without merging separate words together.
    collapsed = re.sub(r"(?<=[a-z])[\s\-_.]+(?=[a-z])", "", lowered)
    return collapsed


def _contains_email(text: str) -> bool:
    return bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))


def find_violation(text: str) -> str | None:
    """Returns a short reason string if the message should be blocked, or
    None if it's clean. Kept as a single reason (not a list) since the
    frontend only needs to explain that *something* was blocked, not run a
    forensic report."""
    if _URL_RE.search(text):
        return "link"
    if _contains_email(text):
        return "email"

    normalized = _normalize(text)
    for keyword in _FORBIDDEN_KEYWORDS:
        if keyword in normalized:
            return "external_platform_keyword"

    # Phone-number-like digit run, checked on the raw text (not the
    # letter-collapsed version, which doesn't touch digits/separators).
    if _DIGIT_RUN_RE.search(text):
        return "phone_number"

    return None
