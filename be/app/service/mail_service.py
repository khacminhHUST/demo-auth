import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def _send_email(to_email: str, subject: str, html_body: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        raise RuntimeError("SMTP chưa được cấu hình (SMTP_USER/SMTP_PASS trống trong .env)")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(settings.SMTP_USER, [to_email], message.as_string())


def send_otp_email(to_email: str, full_name: str, code: str) -> None:
    subject = "Mã xác nhận đăng ký tài khoản"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>Xin chào {full_name},</h2>
        <p>Mã xác nhận đăng ký tài khoản của bạn là:</p>
        <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #4f46e5;">{code}</p>
        <p>Mã có hiệu lực trong {settings.OTP_TTL_MINUTES} phút. Nếu không phải bạn yêu cầu, hãy bỏ qua email này.</p>
    </div>
    """
    _send_email(to_email, subject, html_body)


def send_reset_password_email(to_email: str, full_name: str, reset_link: str) -> None:
    subject = "Yêu cầu đặt lại mật khẩu"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>Xin chào {full_name},</h2>
        <p>Bạn vừa yêu cầu đặt lại mật khẩu. Nhấn vào liên kết bên dưới để tiếp tục:</p>
        <p><a href="{reset_link}" style="color: #4f46e5;">Đặt lại mật khẩu</a></p>
        <p>Liên kết có hiệu lực trong {settings.RESET_TOKEN_TTL_MINUTES} phút. Nếu không phải bạn yêu cầu, hãy bỏ qua email này.</p>
    </div>
    """
    _send_email(to_email, subject, html_body)
