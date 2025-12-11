import os
import secrets
from pathlib import Path

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.app.routes import web, upload, generate, status_check
from src.app.ai_model import model_manager
from src.logger import log

BASE_DIR = Path(__file__).parent

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32)
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(web.router)
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(status_check.router)


@app.on_event("startup")
async def startup_event():
    # Инициализация redis
    app.state.redis = redis.from_url(redis_url, decode_responses=True)
    # Проверка подключения
    try:
        await app.state.redis.ping()
        log.info("Подключение к Redis установлено.")
    except Exception as e:
        log.error(f"Не удалось подключиться к Redis: {e}")

    # try:
    #     # TODO: Одно из решений загрузки модели - model server
    #     model_manager.load_model()
    # except Exception as e:
    #     log.error(f"Ошибка запуска: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Выгрузка модели при остановке приложения"""
    model_manager.unload_model()
    # Отключаем redis
    if hasattr(app.state, 'redis') and app.state.redis:
        await app.state.redis.close()
        log.info("Подключение к Redis закрыто.")

    log.info("Приложение остановлено")
