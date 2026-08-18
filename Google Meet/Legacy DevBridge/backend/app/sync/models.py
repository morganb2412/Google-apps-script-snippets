from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.appsscript.models import ProjectSnapshot


class SyncState(StrEnum):
    IDENTICAL = "IDENTICAL"
    LOCAL_MODIFIED = "LOCAL_MODIFIED"
    REMOTE_MODIFIED = "REMOTE_MODIFIED"
    LOCAL_ADDED = "LOCAL_ADDED"
    REMOTE_ADDED = "REMOTE_ADDED"
    LOCAL_DELETED = "LOCAL_DELETED"
    REMOTE_DELETED = "REMOTE_DELETED"
    CONFLICT = "CONFLICT"


class SyncDirection(StrEnum):
    PULL = "PULL"
    PUSH = "PUSH"


class SyncOperationType(StrEnum):
    WRITE = "WRITE"
    DELETE = "DELETE"


class FileComparison(BaseModel):
    path: str
    state: SyncState
    local_sha256: str | None = None
    remote_sha256: str | None = None
    base_sha256: str | None = None
    diff: str = ""


class ProjectComparison(BaseModel):
    local_hash: str
    remote_hash: str
    base_hash: str | None = None
    files: list[FileComparison]
    has_conflicts: bool


class SyncOperation(BaseModel):
    path: str
    operation: SyncOperationType
    state: SyncState
    diff: str = ""


class SyncPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    direction: SyncDirection
    expected_local_hash: str
    expected_remote_hash: str
    target_snapshot: ProjectSnapshot
    operations: list[SyncOperation]
    requires_approval: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SyncApplyResult(BaseModel):
    plan_id: str
    direction: SyncDirection
    verified_destination_hash: str
    fully_synchronized: bool
    operations_applied: int
