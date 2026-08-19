from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.models import AgentChatRequest, AgentChatResponse
from app.agents.provider import VertexGeminiProvider
from app.agents.service import AgentService
from app.api.v1.routes.onboarding import SessionId, get_onboarding_service
from app.core.config import Settings, get_settings
from app.onboarding.service import OnboardingService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_agent_service(settings: Annotated[Settings, Depends(get_settings)]) -> AgentService:
    if not settings.managed_ai_enabled or not settings.google_cloud_project:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Code Assistant is not configured yet.",
        )
    return AgentService(
        VertexGeminiProvider(
            settings.google_cloud_project,
            settings.vertex_location,
            settings.vertex_model,
        )
    )


@router.post("/chat", response_model=AgentChatResponse)
async def chat(
    request: AgentChatRequest,
    session_id: SessionId,
    service: Annotated[AgentService, Depends(get_agent_service)],
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> AgentChatResponse:
    if not onboarding.status(session_id).google_connected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Connect your Google account before using the Code Assistant.",
        )
    try:
        return await service.chat(request)
    except (httpx.HTTPError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The Code Assistant could not respond. Try again shortly.",
        ) from error
