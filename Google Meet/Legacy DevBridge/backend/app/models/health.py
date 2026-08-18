from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "legacy-devbridge-api"
    version: str = "0.2.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
