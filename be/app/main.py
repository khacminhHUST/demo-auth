from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_api, password_api, user_api
from app.config import settings
from app.db.bootstrap import init_db
from app.service.cleanup_service import cleanup_expired_refresh_tokens

app = FastAPI(title=settings.APP_NAME)
scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_api.router)
app.include_router(password_api.router)
app.include_router(user_api.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    cleanup_expired_refresh_tokens()
    scheduler.add_job(cleanup_expired_refresh_tokens, "interval", hours=24, id="cleanup_refresh_tokens")
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    scheduler.shutdown(wait=False)


@app.get("/health")
def health():
    return {"status": "ok"}
