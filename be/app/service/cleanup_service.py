from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_

from app.db.session import SessionLocal
from app.model.entity.refresh_token import RefreshToken

RETENTION_DAYS = 7


def cleanup_expired_refresh_tokens() -> int:
    """Xoá refresh token đã chết hẳn (revoked hoặc hết hạn quá RETENTION_DAYS).
    Giữ lại vài ngày đầu để còn dấu vết phát hiện reuse (nghi bị đánh cắp)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    db = SessionLocal()
    try:
        condition = or_(
            and_(RefreshToken.revoked_at.isnot(None), RefreshToken.revoked_at < cutoff),
            RefreshToken.expires_at < cutoff,
        )
        deleted = db.query(RefreshToken).filter(condition).delete(synchronize_session=False)
        db.commit()
        return deleted
    finally:
        db.close()
