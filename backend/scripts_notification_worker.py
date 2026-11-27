"""Run the Respectful Meet engagement scheduler as ONE dedicated process.
Production: run one instance (cron/systemd/container worker), not one per web worker.
"""
import time
from app.core.database import SessionLocal
from app.services.notification_service import daily_engagement
from app.services.subscription_notifications import notify_expiring_subscriptions
from app.services.media_cleanup import delete_expired_media
while True:
    db=SessionLocal()
    try:
        daily_engagement(db)
        notify_expiring_subscriptions(db)
        delete_expired_media(db)
    finally: db.close()
    time.sleep(60*60)
