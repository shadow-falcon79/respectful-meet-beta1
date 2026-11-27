from datetime import datetime
from pydantic import BaseModel, Field
from app.models.notification import NotificationType

class NotificationOut(BaseModel):
    id:str; type:NotificationType; title:str; body:str|None; is_read:bool; created_at:datetime
    model_config={"from_attributes":True}
class DeviceSubscriptionIn(BaseModel):
    endpoint:str=Field(min_length=10,max_length=2000)
    p256dh:str=Field(min_length=1,max_length=500)
    auth:str=Field(min_length=1,max_length=500)
    language:str=Field(default="EN",max_length=10)
    timezone:str=Field(default="UTC",max_length=80)
    platform:str=Field(default="web",max_length=30)
class BroadcastIn(BaseModel):
    title:str=Field(min_length=1,max_length=255); body:str=Field(min_length=1,max_length=1000); language:str|None=None; country:str|None=None; send_push:bool=True
class NotificationStatsOut(BaseModel):
    unread:int; total:int
