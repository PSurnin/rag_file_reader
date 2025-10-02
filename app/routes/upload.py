import uuid
from datetime import datetime

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from ..logger import log
from ..services import get_processor, get_supported_types
from ..schemas.redis_document import DocumentDTO

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).parent.parent / "templates"
)


async def extract_document_text(file) -> str:
    # Выбор обработчика по типу файла
    processor = get_processor(file.content_type)
    if not processor:
        supported = ", ".join(get_supported_types())
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Поддерживаемые: {supported}"
        )

    # Извлечение текста
    text = await processor.extract_text(file)
    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Не удалось извлечь текст из документа",
        )
    return text


@router.post("/upload", response_class=JSONResponse)
async def upload_and_extract(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Загружает документ, извлекает текст и возвращает страницу с результатом
    """
    try:
        # Валидация файла
        if not file.filename:
            raise HTTPException(status_code=400, detail="Файл не загружен")

        # Валидация размера
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="Файл слишком большой")

        text = await extract_document_text(file)

        # Сохранение в сессию
        redis_client = request.app.state.redis
        document_id = str(uuid.uuid4())

        now = datetime.utcnow()

        doc = DocumentDTO(
            document_id=document_id,
            status="uploaded",
            text=text,
            result=None,
            created_at=now,
            updated_at=now
        )
        await redis_client.hset(
            f'doc:{document_id}',
            mapping=doc.to_redis()
        )
        # Expire только после определения нагрузки
        # await redis_client.expire(document_id, 600)

        return JSONResponse(
            {"document_id": document_id, "status": doc.status},
            status_code=201,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки")
