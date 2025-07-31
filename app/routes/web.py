from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import tempfile
from pathlib import Path
from pypdf import PdfReader

from ..model import model_manager
from ..logger import log

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).parent.parent / "templates"
)


@router.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/")
async def summarize(
    request: Request,
    file: UploadFile = File(None),
    action: str = Form("generate"),
):
    # Валидация
    if file:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Только PDF файлы разрешены",
            )

        if file.size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=413,
                detail="Файл слишком большой (max 50MB)",
            )

    tmp_file_name = None

    try:
        if action == "generate" and file:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                # Записываем содержимое
                log.info(f"Создан файл: {tmp}")
                content = await file.read()
                tmp.write(content)
                tmp.close()
                tmp_file_name = Path(tmp.name)

            text = extract_text_from_pdf(tmp.name)
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

        summary = model_manager.summarize(text)

        return templates.TemplateResponse("result.html", {
            "request": request,
            "summary": summary,
            "model_name": "HuggingFaceTB/SmolLM3-3B"  # или бери из конфига
        })
    except Exception as e:
        log.error(f"Ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки")

    finally:
        if tmp_file_name and tmp_file_name.exists():
            tmp_file_name.unlink()
            log.info(f"Файл удален: {tmp_file_name}")


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)
