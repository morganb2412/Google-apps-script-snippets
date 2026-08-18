from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.onboarding.health import build_integration_health
from app.onboarding.models import (
    ConnectionRequest,
    IntegrationHealthResponse,
    ProjectDetectedRequest,
    StandardsSelectionRequest,
    UserSetupState,
)
from app.onboarding.repository import InMemoryOnboardingRepository
from app.onboarding.service import (
    MockConnectionsDisabledError,
    OnboardingPreconditionError,
    OnboardingService,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
_repository = InMemoryOnboardingRepository()


def get_onboarding_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OnboardingService:
    return OnboardingService(_repository, allow_mock_connections=settings.environment == "local")


Service = Annotated[OnboardingService, Depends(get_onboarding_service)]


@router.get("/status", response_model=UserSetupState)
async def onboarding_status(service: Service) -> UserSetupState:
    return service.status("local-developer")


@router.post("/google", response_model=UserSetupState)
async def connect_google(_: ConnectionRequest, service: Service) -> UserSetupState:
    return _execute(service.connect_google)


@router.post("/github", response_model=UserSetupState)
async def connect_github(_: ConnectionRequest, service: Service) -> UserSetupState:
    return _execute(service.connect_github)


@router.post("/project", response_model=UserSetupState)
async def detect_project(_: ProjectDetectedRequest, service: Service) -> UserSetupState:
    return _execute(service.detect_project)


@router.post("/standards", response_model=UserSetupState)
async def configure_standards(_: StandardsSelectionRequest, service: Service) -> UserSetupState:
    return _execute(service.configure_standards)


@router.post("/complete", response_model=UserSetupState)
async def complete_onboarding(service: Service) -> UserSetupState:
    return _execute(service.complete)


@router.get("/health", response_model=IntegrationHealthResponse)
async def onboarding_health(service: Service) -> IntegrationHealthResponse:
    return build_integration_health(service.status("local-developer"))


def _execute(operation: Callable[[str], UserSetupState]) -> UserSetupState:
    try:
        return operation("local-developer")
    except MockConnectionsDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except OnboardingPreconditionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
