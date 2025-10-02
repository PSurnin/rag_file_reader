from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).parent.parent / "templates"
)


@router.get("/status", response_class=JSONResponse)
async def check_status(request: Request):
    redis_client = request.app.state.redis

    documents = []
    async for key in redis_client.scan_iter("*"):
        status, created_at = await redis_client.hmget(
            key,
            "status",
            "created_at",
        )
        documents.append({
            "document_id": key,
            "status": status,
            "created_at": created_at,
        })
    return {"documents": documents}
