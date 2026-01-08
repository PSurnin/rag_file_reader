from fastapi import APIRouter

from .web import router as web_router
from .upload import router as upload_router
from .generate import router as generate_router
from .status_check import router as status_router
from .auth import router as auth_router


router = APIRouter(prefix="/api/v1")
router.include_router(web_router)
router.include_router(upload_router)
router.include_router(generate_router)
router.include_router(status_router)
router.include_router(auth_router)
