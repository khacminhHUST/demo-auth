from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth_api import REFRESH_COOKIE_NAME
from app.core.deps import get_current_user
from app.db.session import get_db
from app.model.entity.user import User
from app.model.schema.auth_schema import MessageResponse
from app.model.schema.password_schema import ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.service import password_service

router = APIRouter(prefix="/password", tags=["password"])


@router.post("/forgot", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    password_service.forgot_password(db, payload.email)
    return MessageResponse(message="Đã gửi email hướng dẫn đặt lại mật khẩu")


@router.post("/reset", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    password_service.reset_password(db, payload.token, payload.new_password)
    return MessageResponse(message="Đặt lại mật khẩu thành công, vui lòng đăng nhập lại")


@router.post("/change", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    password_service.change_password(
        db, current_user, payload.current_password, payload.new_password, current_raw_refresh_token
    )
    return MessageResponse(message="Đổi mật khẩu thành công, các thiết bị khác đã bị đăng xuất")
