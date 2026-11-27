from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from app.auth.dependencies import get_current_user, get_current_admin
from app.core.database import get_db
from app.core.config import settings
from app.models.notification import Notification, NotificationDevice, NotificationType
from app.models.profile import Profile
from app.models.user import User
from app.schemas.notifications import NotificationOut, DeviceSubscriptionIn, BroadcastIn, NotificationStatsOut
from app.services.notification_service import create_notification, deliver_push, daily_engagement
router=APIRouter(prefix="/notifications",tags=["notifications"])
@router.get("",response_model=list[NotificationOut])
def list_notifications(limit:int=50,current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id==current_user.id).order_by(Notification.created_at.desc()).limit(min(limit,100)).all()
@router.get("/stats",response_model=NotificationStatsOut)
def stats(current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    q=db.query(Notification).filter(Notification.user_id==current_user.id); return NotificationStatsOut(unread=q.filter(Notification.is_read.is_(False)).count(),total=q.count())
@router.get("/push/public-key")
def push_key(): return {"public_key":settings.vapid_public_key}
@router.post("/push/subscribe",status_code=204)
def subscribe(payload:DeviceSubscriptionIn,current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    d=db.query(NotificationDevice).filter(NotificationDevice.endpoint==payload.endpoint).first(); now=datetime.now(timezone.utc)
    if d is None:
        d=NotificationDevice(user_id=current_user.id,endpoint=payload.endpoint,p256dh=payload.p256dh,auth=payload.auth,platform=payload.platform,language=payload.language.upper(),timezone=payload.timezone,last_seen_at=now); db.add(d)
    else:
        d.user_id=current_user.id; d.p256dh=payload.p256dh; d.auth=payload.auth; d.language=payload.language.upper(); d.timezone=payload.timezone; d.last_seen_at=now
    db.commit()
@router.post("/heartbeat",status_code=204)
def heartbeat(current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    db.query(NotificationDevice).filter(NotificationDevice.user_id==current_user.id).update({"last_seen_at":datetime.now(timezone.utc)},synchronize_session=False); db.commit()
@router.post("/read-all",status_code=204)
def read_all(current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    db.query(Notification).filter(Notification.user_id==current_user.id,Notification.is_read.is_(False)).update({"is_read":True},synchronize_session=False); db.commit()
@router.post("/test-push")
def test_push(current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    n=create_notification(db,current_user.id,NotificationType.SYSTEM,title="Respectful Meet",body="Your notifications are connected."); ok=deliver_push(db,n); db.commit(); return {"push_sent":ok,"notification_id":n.id}
@router.post("/admin/broadcast")
def broadcast(payload:BroadcastIn,admin:User=Depends(get_current_admin),db:DbSession=Depends(get_db)):
    q=db.query(User).filter(User.is_active.is_(True),User.is_suspended.is_(False))
    if payload.country: q=q.join(Profile,Profile.user_id==User.id).filter(Profile.country==payload.country)
    users=q.all(); sent=0
    for u in users:
        n=create_notification(db,u.id,NotificationType.ANNOUNCEMENT,title=payload.title,body=payload.body)
        if payload.send_push and deliver_push(db,n): sent+=1
    db.commit(); return {"users":len(users),"push_sent":sent}
@router.post("/internal/run-engagement")
def run_engagement(admin:User=Depends(get_current_admin),db:DbSession=Depends(get_db)): return {"created":daily_engagement(db)}
@router.post("/{notification_id}/read",status_code=204)
def mark_read(notification_id:str,current_user:User=Depends(get_current_user),db:DbSession=Depends(get_db)):
    n=db.query(Notification).filter(Notification.id==notification_id,Notification.user_id==current_user.id).first()
    if n: n.is_read=True; db.commit()
