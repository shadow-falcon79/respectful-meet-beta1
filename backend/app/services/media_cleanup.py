"""Periodic cleanup for expired chat media (spec section 14/27).

This module only exposes the cleanup function itself — wiring it to an
actual scheduler (cron, Celery beat, APScheduler...) is an infrastructure
decision to make once the app is actually deployed somewhere. For now it
can be run manually or via a simple cron entry calling this as a script.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.media import Media
from app.services.storage_service import get_storage_service


def delete_expired_media(db: Session) -> int:
    """Deletes every Media row whose expires_at has passed, along with its
    physical file. Returns the number of items deleted. Never touches the
    Message it was attached to — only the media reference is removed."""
    now = datetime.now(timezone.utc)
    expired = db.query(Media).filter(Media.expires_at < now).all()

    storage = get_storage_service()
    count = 0
    for item in expired:
        storage.delete(item.storage_key)
        db.delete(item)
        count += 1

    db.commit()
    return count


if __name__ == "__main__":
    # Manual invocation: `python -m app.services.media_cleanup`
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        deleted = delete_expired_media(session)
        print(f"Deleted {deleted} expired media file(s).")
    finally:
        session.close()
