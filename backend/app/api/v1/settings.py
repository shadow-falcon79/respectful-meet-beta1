from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsOut, UserSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

def _get_or_create(db: DbSession, user: User) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings is None:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.get("/me", response_model=UserSettingsOut)
def get_settings(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    return _get_or_create(db, current_user)

@router.patch("/me", response_model=UserSettingsOut)
def update_settings(payload: UserSettingsUpdate, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    settings = _get_or_create(db, current_user)
    updates = payload.model_dump(exclude_unset=True)
    if "min_age" in updates or "max_age" in updates:
        minimum = updates.get("min_age", settings.min_age)
        maximum = updates.get("max_age", settings.max_age)
        if minimum > maximum:
            raise HTTPException(status_code=400, detail="min_age cannot exceed max_age")
    for field, value in updates.items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings
