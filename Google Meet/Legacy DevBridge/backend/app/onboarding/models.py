from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SetupStep(StrEnum):
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"
    PROJECT = "PROJECT"
    REPOSITORY = "REPOSITORY"
    STANDARDS = "STANDARDS"
    COMPLETE = "COMPLETE"


class ConnectionMode(StrEnum):
    MOCK = "MOCK"


class ConnectionRequest(BaseModel):
    mode: ConnectionMode = ConnectionMode.MOCK


class UserSetupState(BaseModel):
    user_id: str = "local-developer"
    google_connected: bool = False
    github_connected: bool = False
    organization_created: bool = False
    project_detected: bool = False
    project_connected: bool = False
    repository_connected: bool = False
    standards_configured: bool = False
    ai_ready: bool = False
    onboarding_completed: bool = False
    next_step: SetupStep = SetupStep.GOOGLE
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    connection_mode: str = "UNCONFIGURED"


class ProjectDetectedRequest(BaseModel):
    script_id: str = Field(min_length=10, max_length=256)
    name: str | None = Field(default=None, max_length=200)


class StandardsSelectionRequest(BaseModel):
    preset: str = Field(pattern="^(RECOMMENDED|BUSINESS|STRICT)$")


class IntegrationHealthItem(BaseModel):
    key: str
    label: str
    status: str
    message: str
    action: str | None = None


class IntegrationHealthResponse(BaseModel):
    ready: bool
    items: list[IntegrationHealthItem]
