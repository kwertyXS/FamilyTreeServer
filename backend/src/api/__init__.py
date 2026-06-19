from fastapi import APIRouter
from src.api.family import router as family_router
from src.api.test import router as test_router
from src.api.admin import router as admin_router

main_router = APIRouter(prefix="/api")

main_router.include_router(family_router)
main_router.include_router(test_router)
main_router.include_router(admin_router)