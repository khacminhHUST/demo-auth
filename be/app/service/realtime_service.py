import asyncio
import json

import asyncpg
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

NEW_USER_CHANNEL = "new_user"


def publish_user_created(db: Session, payload: dict) -> None:
    """Bắn NOTIFY qua Postgres, không blocking nghiệp vụ chính nếu lỗi."""
    db.execute(text("SELECT pg_notify(:channel, :payload)"), {"channel": NEW_USER_CHANNEL, "payload": json.dumps(payload)})


async def subscribe_new_user() -> asyncio.Queue:
    """
    Mở 1 connection asyncpg riêng để LISTEN, trả về queue để endpoint SSE đọc.
    Mỗi client kết nối /users/stream sẽ có 1 connection LISTEN riêng.
    """
    queue: asyncio.Queue = asyncio.Queue()
    conn = await asyncpg.connect(dsn=settings.DATABASE_URL)

    def _on_notify(_conn, _pid, _channel, payload: str) -> None:
        queue.put_nowait(payload)

    await conn.add_listener(NEW_USER_CHANNEL, _on_notify)
    queue._listen_conn = conn  # giữ tham chiếu để đóng khi client disconnect
    return queue


async def close_listener(queue: asyncio.Queue) -> None:
    conn = getattr(queue, "_listen_conn", None)
    if conn is not None:
        await conn.close()
