from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    create_access_token,
    generate_otp_code,
    generate_raw_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.model.entity.refresh_token import RefreshToken
from app.model.entity.user import User
from app.model.entity.verification_code import VerificationCode, VerificationType
from app.service import mail_service, realtime_service


def register_user(db: Session, full_name: str, email: str, password: str) -> None:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được đăng ký")

    user = User(full_name=full_name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()  # có user.id trước khi tạo verification code

    code = _issue_otp(db, user, VerificationType.EMAIL_VERIFY)
    db.commit()

    mail_service.send_otp_email(user.email, user.full_name, code)


def _issue_otp(db: Session, user: User, v_type: VerificationType) -> str:
    code = generate_otp_code()

    verification = VerificationCode(
        user_id=user.id,
        code_hash=hash_token(code),
        type=v_type,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_TTL_MINUTES),
    )
    db.add(verification)
    return code


def resend_code(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email chưa được đăng ký")
    if user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được xác thực")

    code = _issue_otp(db, user, VerificationType.EMAIL_VERIFY)
    db.commit()
    mail_service.send_otp_email(user.email, user.full_name, code)


def verify_email(db: Session, email: str, code: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email chưa được đăng ký")

    verification = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.user_id == user.id,
            VerificationCode.type == VerificationType.EMAIL_VERIFY,
            VerificationCode.consumed_at.is_(None),
        )
        .order_by(VerificationCode.created_at.desc())
        .first()
    )

    _check_code(db, verification, code)

    user.email_verified = True
    verification.consumed_at = datetime.now(timezone.utc)
    db.flush()

    realtime_service.publish_user_created(
        db, {"id": str(user.id), "full_name": user.full_name, "email": user.email, "created_at": user.created_at.isoformat()}
    )
    db.commit()


def _check_code(db: Session, verification: VerificationCode | None, raw_code: str) -> None:
    invalid_error = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã xác nhận không đúng hoặc đã hết hạn")

    if verification is None:
        raise invalid_error

    if verification.expires_at < datetime.now(timezone.utc):
        raise invalid_error

    if verification.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise invalid_error

    if verification.code_hash != hash_token(raw_code):
        verification.attempts += 1
        db.commit()
        raise invalid_error


def login(db: Session, email: str, password: str, user_agent: str | None, ip: str | None) -> tuple[str, str, User]:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email chưa được đăng ký")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai mật khẩu")

    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email chưa được xác thực")

    access_token = create_access_token(user.id, user.email)
    raw_refresh_token = _issue_refresh_token(db, user, user_agent, ip)
    db.commit()

    return access_token, raw_refresh_token, user


def _issue_refresh_token(db: Session, user: User, user_agent: str | None, ip: str | None) -> str:
    raw_token = generate_raw_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        user_agent=user_agent,
        ip=ip,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)
    return raw_token


def refresh_access_token(
    db: Session, raw_refresh_token: str | None, user_agent: str | None, ip: str | None
) -> tuple[str, str]:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập không hợp lệ")

    if not raw_refresh_token:
        raise unauthorized

    token_hash = hash_token(raw_refresh_token)
    # khoá row ngay khi đọc để 2 request refresh cùng lúc (2 tab, StrictMode double-effect...)
    # không thể cùng đọc thấy "chưa revoke" rồi cùng xoay token từ 1 row gốc
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).with_for_update().first()

    if stored is None:
        raise unauthorized

    if stored.revoked_at is not None:
        # token cũ bị dùng lại sau khi đã rotate -> nghi ngờ bị đánh cắp, revoke toàn bộ token của user
        db.query(RefreshToken).filter(RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None)).update(
            {"revoked_at": datetime.now(timezone.utc)}
        )
        db.commit()
        raise unauthorized

    if stored.expires_at < datetime.now(timezone.utc):
        raise unauthorized

    user = db.get(User, stored.user_id)
    if user is None:
        raise unauthorized

    new_raw_token = _issue_refresh_token(db, user, user_agent, ip)
    stored.revoked_at = datetime.now(timezone.utc)
    stored.replaced_by = hash_token(new_raw_token)

    access_token = create_access_token(user.id, user.email)
    db.commit()

    return access_token, new_raw_token


def logout(db: Session, raw_refresh_token: str | None) -> None:
    if not raw_refresh_token:
        return
    token_hash = hash_token(raw_refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()
