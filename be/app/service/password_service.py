from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import generate_raw_token, hash_password, hash_token, verify_password
from app.model.entity.refresh_token import RefreshToken
from app.model.entity.user import User
from app.model.entity.verification_code import VerificationCode, VerificationType
from app.service import mail_service


def forgot_password(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email chưa được đăng ký")

    raw_token = generate_raw_token()
    verification = VerificationCode(
        user_id=user.id,
        code_hash=hash_token(raw_token),
        type=VerificationType.PASSWORD_RESET,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_TTL_MINUTES),
    )
    db.add(verification)
    db.commit()

    reset_link = f"{settings.FE_BASE_URL}/reset-password?token={raw_token}"
    mail_service.send_reset_password_email(user.email, user.full_name, reset_link)


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    invalid_error = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Liên kết không hợp lệ hoặc đã hết hạn")

    token_hash = hash_token(raw_token)
    verification = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.type == VerificationType.PASSWORD_RESET,
            VerificationCode.code_hash == token_hash,
            VerificationCode.consumed_at.is_(None),
        )
        .first()
    )

    if verification is None or verification.expires_at < datetime.now(timezone.utc):
        raise invalid_error

    user = db.get(User, verification.user_id)
    if user is None:
        raise invalid_error

    user.password_hash = hash_password(new_password)
    verification.consumed_at = datetime.now(timezone.utc)

    # đổi mật khẩu xong thì bắt đăng nhập lại trên mọi thiết bị
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": datetime.now(timezone.utc)}
    )
    db.commit()


def change_password(
    db: Session, user: User, current_password: str, new_password: str, current_raw_refresh_token: str | None
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mật khẩu hiện tại không đúng")

    user.password_hash = hash_password(new_password)

    # revoke mọi refresh token khác của user (đăng xuất các thiết bị/trình duyệt khác),
    # giữ lại phiên hiện tại để không tự đăng xuất chính mình
    current_token_hash = hash_token(current_raw_refresh_token) if current_raw_refresh_token else None
    query = db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    if current_token_hash is not None:
        query = query.filter(RefreshToken.token_hash != current_token_hash)
    query.update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()
