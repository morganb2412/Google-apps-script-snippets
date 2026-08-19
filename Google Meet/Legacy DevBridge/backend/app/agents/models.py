from typing import Literal

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    request: str = Field(min_length=3, max_length=12000)
    script_id: str | None = Field(default=None, max_length=256)


class AgentChatResponse(BaseModel):
    mode: Literal["LIVE"] = "LIVE"
    message: str
    provider: str
    model: str
    findings: list[str] = Field(default_factory=list)
    proposal: None = None
