from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ProjectContextRequest(BaseModel):
    script_id: str = Field(min_length=10, max_length=256)
    name: str | None = Field(default=None, max_length=200)
    editor_url: HttpUrl
    detected_at: datetime

    @field_validator("script_id")
    @classmethod
    def validate_script_id(cls, value: str) -> str:
        if not all(character.isalnum() or character in "_-" for character in value):
            raise ValueError("script_id contains unsupported characters")
        return value

    @field_validator("editor_url")
    @classmethod
    def validate_editor_url(cls, value: HttpUrl) -> HttpUrl:
        if value.host != "script.google.com" or value.scheme != "https":
            raise ValueError("editor_url must be an HTTPS Google Apps Script URL")
        return value


class ProjectContextResponse(BaseModel):
    script_id: str
    name: str | None
    editor_url: str
    detected_at: datetime
    recognized: bool = True
