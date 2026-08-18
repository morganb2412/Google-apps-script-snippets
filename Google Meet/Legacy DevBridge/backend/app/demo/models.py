from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SyncState(StrEnum):
    IDENTICAL = "IDENTICAL"
    LOCAL_MODIFIED = "LOCAL_MODIFIED"
    REMOTE_MODIFIED = "REMOTE_MODIFIED"
    LOCAL_ADDED = "LOCAL_ADDED"
    REMOTE_ADDED = "REMOTE_ADDED"
    CONFLICT = "CONFLICT"


class DemoFile(BaseModel):
    path: str
    content: str
    sha256: str
    source: str


class DemoChange(BaseModel):
    path: str
    state: SyncState
    diff: str
    requires_approval: bool = True


class DemoWorkspace(BaseModel):
    mode: str = "DEMO"
    project_name: str = "ATLAS Approval Automation"
    script_id: str = "DEMO_APPS_SCRIPT_PROJECT"
    repository: str | None = None
    branch: str = "main"
    branches: list[str] = Field(default_factory=lambda: ["main"])
    connected: bool = False
    changes: list[DemoChange] = Field(default_factory=list)
    latest_commit: str | None = None
    pull_request_url: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConnectDemoRequest(BaseModel):
    owner: str = Field(default="legacy-automations", min_length=1, max_length=100)
    repository: str = Field(default="atlas-demo", min_length=1, max_length=100)


class BranchRequest(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9._/-]+$", max_length=120)


class CommitRequest(BaseModel):
    message: str = Field(min_length=3, max_length=200)


class AgentRequest(BaseModel):
    request: str = Field(min_length=3, max_length=2000)


class AgentResult(BaseModel):
    mode: str = "DEMO"
    title: str
    summary: str
    items: list[str]
    files_affected: list[str]
    oauth_changes: list[str] = Field(default_factory=list)


class ProposedFix(BaseModel):
    proposal_id: str = "demo-fix-001"
    status: str = "PENDING_APPROVAL"
    file: str = "ApprovalService.gs"
    operation: str = "UPDATE"
    original_hash: str
    explanation: str
    standards_impacted: list[str]
    risk_level: str = "MEDIUM"
    diff: str


class AssistantResponse(BaseModel):
    mode: str = "DEMO"
    message: str
    findings: list[str] = Field(default_factory=list)
    proposal: ProposedFix | None = None


class ProposalDecision(BaseModel):
    proposal_id: str
