from fastapi import APIRouter

from .health import router as health_router
from .tb_proxy import router as tb_router

# future routes can be imported and included here

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(tb_router) 