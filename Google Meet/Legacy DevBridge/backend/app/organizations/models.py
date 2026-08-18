from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class ProjectMapping(BaseModel):
    mapping_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    organization_id: str | None = None
    script_project_id: str
    github_installation_id: int
    repository_owner: str
    repository_name: str
    default_branch: str = "main"
    active_branch: str = "main"
    standards_profile: str = "RECOMMENDED"
    ai_provider_profile: str = "DEVBRIDGE_MANAGED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latest_sync_at: datetime | None = None
    sync_base_hash: str | None = None

    @property
    def repository_full_name(self) -> str:
        return f"{self.repository_owner}/{self.repository_name}"


class ExistingRepositoryProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    script_project_id: str
    github_installation_id: int
    repository_owner: str
    repository_name: str
    branch: str
    apps_script_hash: str
    repository_hash: str
    changed_paths: list[str]
    requires_confirmation: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
