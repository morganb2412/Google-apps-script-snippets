from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.onboarding import router as onboarding_router
from app.api.v1.routes.projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(onboarding_router)
api_router.include_router(projects_router)
