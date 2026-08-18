from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AppsScriptFileType(StrEnum):
    SERVER_JS = "SERVER_JS"
    HTML = "HTML"
    JSON = "JSON"


class AppsScriptFile(BaseModel):
    name: str
    type: AppsScriptFileType
    source: str = ""
    function_set: dict[str, Any] | None = Field(default=None, alias="functionSet")


class AppsScriptContent(BaseModel):
    script_id: str
    files: list[AppsScriptFile]


class AppsScriptProject(BaseModel):
    script_id: str = Field(alias="scriptId")
    title: str
    create_time: str | None = Field(default=None, alias="createTime")
    update_time: str | None = Field(default=None, alias="updateTime")


class ProjectFileSource(StrEnum):
    APPS_SCRIPT = "APPS_SCRIPT"
    GITHUB = "GITHUB"
    GENERATED = "GENERATED"


class ProjectFile(BaseModel):
    path: str
    name: str
    extension: str
    content: str
    sha256: str
    source: ProjectFileSource
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectSnapshot(BaseModel):
    script_id: str
    project_hash: str
    files: list[ProjectFile]


class SafeUpdateRequest(BaseModel):
    expected_project_hash: str = Field(min_length=64, max_length=64)
    approved: bool = False
    files: list[AppsScriptFile]


class SafeUpdateResult(BaseModel):
    script_id: str
    previous_hash: str
    verified_hash: str
    files_updated: int
    oauth_scopes_added: list[str] = Field(default_factory=list)
