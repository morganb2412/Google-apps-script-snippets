from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor_id: str
    action: str
    organization_id: str | None = None
    script_project_id: str | None = None
    repository: str | None = None
    branch: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
