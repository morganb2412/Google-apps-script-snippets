import re
from collections.abc import Callable
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.audit.models import AuditEvent
from app.audit.repository import InMemoryAuditRepository
from app.auth.google import HttpGoogleOAuthProvider
from app.auth.models import GoogleOAuthStart
from app.auth.repository import InMemoryGoogleCredentialRepository
from app.auth.service import (
    GoogleOAuthConfigurationError,
    GoogleOAuthService,
    GoogleOAuthStateError,
    GoogleTenantDeniedError,
)
from app.core.config import Settings, get_settings
from app.github.auth import (
    GitHubInstallationFlow,
    GitHubInstallationStateError,
    InMemoryGitHubInstallationRepository,
)
from app.github.models import GitHubInstallStart
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
_google_credentials = InMemoryGoogleCredentialRepository()
_audit_repository = InMemoryAuditRepository()
_github_installation_flows: dict[str, GitHubInstallationFlow] = {}
_github_installations = InMemoryGitHubInstallationRepository()


def get_session_id(
    settings: Annotated[Settings, Depends(get_settings)],
    session_id: Annotated[str | None, Header(alias="X-DevBridge-Session")] = None,
) -> str:
    if session_id is None and settings.environment == "local":
        return "local-developer"
    if session_id is None or re.fullmatch(r"[A-Za-z0-9_-]{20,128}", session_id) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Open DevBridge again to start a secure session.",
        )
    return session_id


def get_onboarding_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OnboardingService:
    return OnboardingService(_repository, allow_mock_connections=settings.environment == "local")


Service = Annotated[OnboardingService, Depends(get_onboarding_service)]
SessionId = Annotated[str, Depends(get_session_id)]


def get_google_oauth_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GoogleOAuthService:
    if not settings.google_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google connection is not configured yet.",
        )
    provider = HttpGoogleOAuthProvider(
        settings.google_oauth_client_id,
        settings.google_oauth_client_secret,
        settings.google_oauth_redirect_uri,
    )
    return GoogleOAuthService(
        _google_credentials,
        provider,
        settings.google_oauth_client_id,
        settings.google_oauth_redirect_uri,
        settings.google_allowed_domains,
    )


GoogleService = Annotated[GoogleOAuthService, Depends(get_google_oauth_service)]


def get_github_installation_flow(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GitHubInstallationFlow:
    if not settings.github_app_enabled or not settings.github_app_name:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub connection is not configured yet.",
        )
    return _github_installation_flows.setdefault(
        settings.github_app_name,
        GitHubInstallationFlow(settings.github_app_name, _github_installations),
    )


GitHubFlow = Annotated[GitHubInstallationFlow, Depends(get_github_installation_flow)]


@router.get("/status", response_model=UserSetupState)
async def onboarding_status(service: Service, session_id: SessionId) -> UserSetupState:
    return service.status(session_id)


@router.get("/google/start", response_model=GoogleOAuthStart)
async def start_google_oauth(service: GoogleService, session_id: SessionId) -> GoogleOAuthStart:
    try:
        return service.start(session_id)
    except GoogleOAuthConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error


@router.get("/google/callback", response_class=HTMLResponse)
async def complete_google_oauth(
    service: GoogleService,
    onboarding: Service,
    code: Annotated[str, Query(min_length=1, max_length=4096)],
    state_value: Annotated[str, Query(alias="state", min_length=20, max_length=512)],
) -> HTMLResponse:
    try:
        session_id, result = await service.complete(code, state_value)
        onboarding.connect_google_live(session_id)
        _audit_repository.append(
            AuditEvent(
                actor_id=session_id,
                action="GOOGLE_CONNECTED",
                metadata={"email_domain": result.email.rsplit("@", 1)[-1].lower()},
            )
        )
    except GoogleOAuthStateError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except GoogleTenantDeniedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google could not complete the connection. Try again.",
        ) from error
    return HTMLResponse(_oauth_completion_page())


@router.post("/google", response_model=UserSetupState)
async def connect_google(
    _: ConnectionRequest, service: Service, session_id: SessionId
) -> UserSetupState:
    return _execute_for(service.connect_google, session_id)


@router.post("/github", response_model=UserSetupState)
async def connect_github(
    _: ConnectionRequest, service: Service, session_id: SessionId
) -> UserSetupState:
    return _execute_for(service.connect_github, session_id)


@router.get("/github/start", response_model=GitHubInstallStart)
async def start_github_installation(flow: GitHubFlow, session_id: SessionId) -> GitHubInstallStart:
    return flow.start(session_id)


@router.get("/github/callback", response_class=HTMLResponse)
async def complete_github_installation(
    flow: GitHubFlow,
    onboarding: Service,
    installation_id: Annotated[int, Query(gt=0)],
    state_value: Annotated[str, Query(alias="state", min_length=20, max_length=512)],
) -> HTMLResponse:
    try:
        session_id = flow.complete(state_value, installation_id)
        onboarding.connect_github_live(session_id)
        _audit_repository.append(
            AuditEvent(
                actor_id=session_id,
                action="GITHUB_CONNECTED",
                metadata={"installation_id": installation_id},
            )
        )
    except GitHubInstallationStateError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except OnboardingPreconditionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return HTMLResponse(_connection_completion_page("GitHub"))


@router.post("/project", response_model=UserSetupState)
async def detect_project(
    _: ProjectDetectedRequest, service: Service, session_id: SessionId
) -> UserSetupState:
    return _execute_for(service.detect_project, session_id)


@router.post("/standards", response_model=UserSetupState)
async def configure_standards(
    _: StandardsSelectionRequest, service: Service, session_id: SessionId
) -> UserSetupState:
    return _execute_for(service.configure_standards, session_id)


@router.post("/complete", response_model=UserSetupState)
async def complete_onboarding(service: Service, session_id: SessionId) -> UserSetupState:
    return _execute_for(service.complete, session_id)


@router.get("/health", response_model=IntegrationHealthResponse)
async def onboarding_health(service: Service, session_id: SessionId) -> IntegrationHealthResponse:
    return build_integration_health(service.status(session_id))


def _execute(operation: Callable[[str], UserSetupState]) -> UserSetupState:
    return _execute_for(operation, "local-developer")


def _execute_for(operation: Callable[[str], UserSetupState], session_id: str) -> UserSetupState:
    try:
        return operation(session_id)
    except MockConnectionsDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except OnboardingPreconditionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def _oauth_completion_page() -> str:
    return _connection_completion_page("Google")


def _connection_completion_page(provider: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>DevBridge connected</title></head>
<body>
<main>
  <h1>{provider} connected</h1>
  <p>You can close this tab and return to Apps Script.</p>
</main>
<script>window.setTimeout(() => window.close(), 1200);</script>
</body>
</html>"""
