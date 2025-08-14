import os
import secrets
from pathlib import Path

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

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
    # Инициализация redis
    app.state.redis = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )
    # Проверка подключения
    try:
        await app.state.redis.ping()
        log.info("Подключение к Redis установлено.")
    except Exception as e:
        log.error(f"Не удалось подключиться к Redis: {e}")

    try:
        model_manager.load_model()
    except Exception as e:
        log.error(f"Ошибка запуска: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Выгрузка модели при остановке приложения"""
    model_manager.unload_model()
    # Отключаем redis
    if hasattr(app.state, 'redis') and app.state.redis:
        await app.state.redis.close()
        log.info("Подключение к Redis закрыто.")

    log.info("Приложение остановлено")
