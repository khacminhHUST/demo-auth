from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.model.entity.user import User


def list_users(db: Session) -> list[User]:
    return db.query(User).filter(User.email_verified.is_(True)).order_by(desc(User.created_at)).all()
