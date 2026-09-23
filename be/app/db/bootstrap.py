from app.db.session import Base, engine
# import để SQLAlchemy biết các bảng cần tạo
from app.model.entity import user, refresh_token, verification_code  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
