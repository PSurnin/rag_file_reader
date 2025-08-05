from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
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


# TODO: Кэширование запросов для повторных запросов
# TODO: Чат по итогу анализа, возвращаешь суммирование, но можно задать вопросы (после RAG)

@router.post("/")
async def summarize(
    request: Request,
    file: UploadFile = File(None),
    action: str = Form("generate"),
    max_words: int = Form(150),
    style: str = Form("formal"),
):
    try:
        if action == "generate" and file:
            processor = get_processor(file.content_type)
            if not processor:
                supported = ", ".join(get_supported_types())
                raise HTTPException(
                    status_code=400,
                    detail=f"Неподдерживаемый формат. Поддерживаемые: {supported}"
                )

            text = await processor.extract_text(file)
            request.session["document_text"] = text
            log.info(f"Извлечен текст: {text[:150]}...")

        elif action == "regenerate":
            # Перегенерация из сессии
            text = request.session.get("document_text")
            if not text:
                raise HTTPException(
                    status_code=400,
                    detail="Нет текста для перегенерации",
                )

        else:
            raise HTTPException(status_code=400, detail="Неверный запрос")

        summary = model_manager.summarize(
            text,
            max_words=max_words,
            style=style,
            )

        return templates.TemplateResponse("result.html", {
            "request": request,
            "summary": summary,
            "model_name": model_manager.model_name    # взять из model_manager
        })
    except Exception as e:
        log.error(f"Ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки")
