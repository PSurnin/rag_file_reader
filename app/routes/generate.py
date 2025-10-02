import asyncio
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..schemas.redis_document import DocumentDTO

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).parent.parent / "templates"
)


async def fake_processing(redis_client, document_id: str):
    # Имитация обработки celery task
    await asyncio.sleep(20)
    raw = await redis_client.hgetall(document_id)
    doc = DocumentDTO.from_redis(document_id, raw)
    doc.status = "done"
    doc.result = "This is example summary text."
    # Записываем результат
    await redis_client.hset(
        doc.document_id,
        mapping=doc.to_redis(),
    )


@router.post("/generate", response_class=JSONResponse)
async def generate_summary(request: Request):
    """
    Отправляет документ на генерацию (имитация celery).
    """
    data = await request.json()
    document_id = data.get("document_id")
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id обязателен")

    redis_client = request.app.state.redis
    doc_data = await redis_client.hgetall(document_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Документ не найден")

    doc = DocumentDTO.from_redis(document_id, doc_data)

    if doc.status != "uploaded":
        raise HTTPException(
            status_code=400,
            detail=f"Документ в статусе {doc.status}",
        )

    # Ставим статус "processing"
    doc.status = "processing"
    doc.updated_at = datetime.utcnow()
    await redis_client.hset(document_id, mapping=doc.to_redis())

    # Имитация таски
    asyncio.create_task(fake_processing(redis_client, doc.document_id))

    return JSONResponse(
        {"document_id": doc.document_id, "status": doc.status},
        status_code=202,
    )
