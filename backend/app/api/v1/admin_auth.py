import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DbSession

from app.auth.security import create_verification_ticket, read_verification_ticket
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import AUTH_OTP_REQUEST_LIMIT, AUTH_OTP_VERIFY_LIMIT, limiter
from app.models.admin_action import AdminAction
from app.models.user import User, UserRole
from app.schemas.auth import RequestCodeIn, RequestCodeOut
from app.schemas.admin import AdminVerifyCodeIn, AdminVerifyCodeOut
from app.services.otp_service import OtpInvalidOrExpired, OtpRateLimitExceeded, request_otp, verify_otp
from app.services.session_service import create_session
from app.api.v1.auth import _set_session_cookie
import jwt

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/request-code", response_model=RequestCodeOut)
@limiter.limit(AUTH_OTP_REQUEST_LIMIT)
def admin_request_code(request: Request, payload: RequestCodeIn, db: DbSession = Depends(get_db)) -> RequestCodeOut:
    email = payload.email.lower()

    # Never reveal whether the address is on the allowlist — same generic
    # response either way, and no OTP is actually sent for a non-admin
    # email (backend master spec, section 19: "Access denied", no OTP).
    if email not in settings.admin_allowed_emails_list:
        return RequestCodeOut()

    try:
        request_otp(db, email)
    except OtpRateLimitExceeded:
        pass
    return RequestCodeOut()


@router.post("/verify-code", response_model=AdminVerifyCodeOut)
@limiter.limit(AUTH_OTP_VERIFY_LIMIT)
def admin_verify_code(request: Request, payload: AdminVerifyCodeIn, response: Response, db: DbSession = Depends(get_db)) -> AdminVerifyCodeOut:
    email = payload.email.lower()

    if email not in settings.admin_allowed_emails_list:
        # Deliberately the same error whether the OTP would have been right
        # or wrong — don't help an attacker distinguish "wrong code" from
        # "not an admin".
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ACCESS_DENIED")

    try:
        is_valid = verify_otp(db, email, payload.code)
    except OtpInvalidOrExpired:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP_EXPIRED")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP_INCORRECT")

    # First successful admin OTP for an allowlisted email promotes (or
    # creates) that user to ADMIN. This is the only path that can ever set
    # role=ADMIN — never the regular /auth/register flow.
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            username=f"admin_{uuid.uuid4().hex[:16]}",
            email=email,
            is_email_verified=True,
            role=UserRole.ADMIN,
        )
        db.add(user)
    elif user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
    db.commit()
    db.refresh(user)

    token, expires_at = create_session(db, user.id)
    _set_session_cookie(response, token, expires_at)

    db.add(AdminAction(admin_user_id=user.id, action="admin_login"))
    db.commit()

    return AdminVerifyCodeOut(admin_id=user.id, email=user.email)
