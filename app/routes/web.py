from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).parent.parent / "templates"
)


@router.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    """
    Страница со списком документов и их статусами.
    Данные подтягиваются из API /status через JS.
    """
    # TODO - избавиться от JS, отправлять данные вручную
    return templates.TemplateResponse("documents.html", {"request": request})


@router.get("/documents/{doc_id}", response_class=HTMLResponse)
async def results_page(request: Request, doc_id: str):
    """
    Страница с итогом ответа конкретного документа
    """
    redis_client = request.app.state.redis
    doc_data = await redis_client.hgetall(doc_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "doc_data": doc_data},
    )

# TODO - эндпоинт на удаление результатов
