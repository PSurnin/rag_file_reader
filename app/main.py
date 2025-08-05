from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import secrets
from pathlib import Path

from .routes import web
from .model import model_manager
from .logger import log

# TODO: Redis + FAISS + Docker deploy

BASE_DIR = Path(__file__).parent

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32)
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(web.router)


@app.on_event("startup")
async def startup_event():
    try:
        model_manager.load_model()
    except Exception as e:
        log.error(f"Ошибка запуска: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Выгрузка модели при остановке приложения"""
    model_manager.unload_model()
    log.info("Приложение остановлено")
