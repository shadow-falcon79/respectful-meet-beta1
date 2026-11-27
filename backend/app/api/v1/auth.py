from datetime import date, datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import SESSION_COOKIE_NAME, get_current_user
from app.auth.security import hash_password, verify_password
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.profile import Profile
from app.models.user import User
from app.models.notification import NotificationType
from app.services.notification_service import create_notification
from app.schemas.auth import SignInIn, SignUpIn, UserOut
from app.services.session_service import create_session, revoke_session

router = APIRouter(prefix="/auth", tags=["auth"])

MINIMUM_AGE_YEARS = 18
AUTH_SIGNUP_LIMIT = "5/minute"
AUTH_SIGNIN_LIMIT = "10/minute"


def _set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="none" if settings.environment != "development" else "lax",
        expires=expires_at,
        path="/",
    )


def _validate_profile_and_terms(payload: SignUpIn) -> None:
    today = date.today()
    age_years = today.year - payload.date_of_birth.year - (
        (today.month, today.day) < (payload.date_of_birth.month, payload.date_of_birth.day)
    )
    if age_years < MINIMUM_AGE_YEARS:
        raise HTTPException(status_code=400, detail=f"You must be at least {MINIMUM_AGE_YEARS} years old to register")
    if not payload.accept_terms:
        raise HTTPException(status_code=400, detail="You must accept the Terms of Service and Privacy Policy to register")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")


def _user_out(user: User, profile: Profile | None) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=profile.first_name if profile else None,
        last_name=profile.last_name if profile else None,
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_SIGNUP_LIMIT)
def signup(request: Request, payload: SignUpIn, response: Response, db: DbSession = Depends(get_db)) -> UserOut:
    _validate_profile_and_terms(payload)

    if db.query(User).filter(User.username == payload.username).first() is not None:
        raise HTTPException(status_code=409, detail="Username already exists")

    now = datetime.now(timezone.utc)
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        email=None,
        is_email_verified=False,
        terms_accepted_at=now,
        privacy_accepted_at=now,
        terms_version=payload.terms_version,
    )
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        country=payload.country,
        city=payload.city,
        interests=payload.interests,
    )
    db.add(profile)
    create_notification(db, user.id, NotificationType.WELCOME)
    db.commit()
    db.refresh(user)

    token, expires_at = create_session(db, user.id)
    _set_session_cookie(response, token, expires_at)
    return _user_out(user, profile)


@router.post("/signin", response_model=UserOut)
@limiter.limit(AUTH_SIGNIN_LIMIT)
def signin(request: Request, payload: SignInIn, response: Response, db: DbSession = Depends(get_db)) -> UserOut:
    user = db.query(User).filter(User.username == payload.username).first()
    # Keep the response generic so username enumeration is not useful to an attacker.
    if user is None or not user.is_active or user.is_suspended or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    token, expires_at = create_session(db, user.id)
    _set_session_cookie(response, token, expires_at)
    return _user_out(user, profile)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> UserOut:
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    return _user_out(current_user, profile)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: DbSession = Depends(get_db),
) -> None:
    if session_token is not None:
        revoke_session(db, session_token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: DbSession = Depends(get_db),
) -> None:
    db.delete(current_user)
    db.commit()
    if session_token is not None:
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return None
