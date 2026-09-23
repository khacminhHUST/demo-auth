import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_from_query_token
from app.db.session import get_db
from app.model.entity.user import User
from app.model.schema.user_schema import UserListItem
from app.service import realtime_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserListItem])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [UserListItem.model_validate(u) for u in user_service.list_users(db)]


@router.get("/stream")
async def stream_users(current_user: User = Depends(get_current_user_from_query_token)):
    queue = await realtime_service.subscribe_new_user()

    async def event_generator():
        try:
            yield ": connected\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"  # keepalive để tránh proxy đóng connection
        finally:
            await realtime_service.close_listener(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
