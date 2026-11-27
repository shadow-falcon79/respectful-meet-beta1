"""Machine-readable error codes returned in HTTPException.detail (backend
master spec, section 22): the backend returns a stable code, the frontend
maps it to a translated string once i18n exists. Never return a hardcoded
English sentence as the source of truth for an error condition.
"""

LIMIT_REACHED = "LIMIT_REACHED"
PREMIUM_REQUIRED = "PREMIUM_REQUIRED"
INSUFFICIENT_STARS = "INSUFFICIENT_STARS"
PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
PAYMENT_FAILED = "PAYMENT_FAILED"
PHOTO_EXPIRED = "PHOTO_EXPIRED"
CALL_LIMIT_REACHED = "CALL_LIMIT_REACHED"

BLOCKED_USER = "BLOCKED_USER"
CONTENT_PHONE_NUMBER = "CONTENT_PHONE_NUMBER"
CONTENT_EMAIL = "CONTENT_EMAIL"
CONTENT_EXTERNAL_PLATFORM = "CONTENT_EXTERNAL_PLATFORM"
CONTENT_LINK = "CONTENT_LINK"
