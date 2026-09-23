from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

import uuid

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import decode_access_token
from app.db.session import get_db
from app.model.entity.user import User
from app.model.schema.auth_schema import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendCodeRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    auth_service.register_user(db, payload.full_name, payload.email, payload.password)
    return MessageResponse(message="Đã gửi mã xác nhận đến email của bạn")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    auth_service.verify_email(db, payload.email, payload.code)
    return MessageResponse(message="Xác thực email thành công, bạn có thể đăng nhập")


@router.post("/resend-code", response_model=MessageResponse)
def resend_code(payload: ResendCodeRequest, db: Session = Depends(get_db)):
    auth_service.resend_code(db, payload.email)
    return MessageResponse(message="Đã gửi lại mã xác nhận")


@router.post("/login", response_model=AccessTokenResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    access_token, raw_refresh_token, user = auth_service.login(
        db, payload.email, payload.password, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    _set_refresh_cookie(response, raw_refresh_token)
    return AccessTokenResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    access_token, new_raw_refresh_token = auth_service.refresh_access_token(
        db, raw_refresh_token, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    _set_refresh_cookie(response, new_raw_refresh_token)

    payload = decode_access_token(access_token)
    user = db.get(User, uuid.UUID(payload["sub"]))
    return AccessTokenResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    auth_service.logout(db, raw_refresh_token)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return MessageResponse(message="Đã đăng xuất")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
