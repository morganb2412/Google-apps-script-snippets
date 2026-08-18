from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.health import HealthResponse
from app.services.health import HealthService, get_health_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(service: Annotated[HealthService, Depends(get_health_service)]) -> HealthResponse:
    return service.status()
