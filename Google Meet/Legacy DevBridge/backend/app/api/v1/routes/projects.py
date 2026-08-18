from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.project import ProjectContextRequest, ProjectContextResponse
from app.services.project_context import ProjectContextService, get_project_context_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/context/validate", response_model=ProjectContextResponse)
async def validate_project_context(
    context: ProjectContextRequest,
    service: Annotated[ProjectContextService, Depends(get_project_context_service)],
) -> ProjectContextResponse:
    return service.validate(context)
