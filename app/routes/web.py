import uuid

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from ..model import model_manager
from ..logger import log
from ..services import get_processor, get_supported_types

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).parent.parent / "templates"
)


@router.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# TODO: Чат по итогу анализа, возвращаешь суммирование, но можно задать вопросы (после RAG)
@router.post("/upload", response_class=HTMLResponse)
async def upload_and_summarize(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Загружает документ, извлекает текст и возвращает страницу с результатом
    """
    try:
        # Валидация файла
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="Файл не загружен")

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
        session_id = str(uuid.uuid4())

        # Сохранение в сессию
        redis_client = request.app.state.redis
        await redis_client.set(session_id, text, ex=500)

        # Генерация ответа
        summary = model_manager.summarize(text)

        response = templates.TemplateResponse("result.html", {
            "request": request,
            "summary": summary,
            "model_name": model_manager.model_name,
        })

        response.set_cookie(
            key="documentid",
            value=session_id,
            secure=False,
            samesite="lax",
            path="/",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки")


@router.post("/regenerate", response_class=HTMLResponse)
async def regenerate_summary(request: Request):
    """
    Перегенерирует суммаризацию из текста в сессии
    """
    try:
        # Получение текста из сессии
        document_id = request.cookies.get("documentid")
        redis_client = request.app.state.redis
        text = await redis_client.get(document_id)
        if not text:
            raise HTTPException(
                status_code=400,
                detail="Нет текста."
            )

        # Генерация новой суммаризации
        summary = model_manager.summarize(text)

        return templates.TemplateResponse("result.html", {
            "request": request,
            "summary": summary,
            "model_name": model_manager.model_name,
        })

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Ошибка при перегенерации: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка суммаризации")
