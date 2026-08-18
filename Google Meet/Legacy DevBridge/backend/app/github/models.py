from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RepositoryVisibility(StrEnum):
    PRIVATE = "private"
    PUBLIC = "public"


class GitHubOwner(BaseModel):
    login: str
    type: str


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    default_branch: str
    html_url: HttpUrl
    owner: GitHubOwner


class GitHubBranch(BaseModel):
    name: str
    commit_sha: str
    protected: bool = False


class GitHubFile(BaseModel):
    path: str
    name: str
    sha: str
    content: str
    encoding: str = "utf-8"


class CreateRepositoryRequest(BaseModel):
    organization: str = Field(pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
    name: str = Field(pattern=r"^[A-Za-z0-9._-]{1,100}$")
    visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE
    description: str = Field(default="", max_length=350)


class CreateBranchRequest(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z0-9._/-]{1,200}$")
    from_sha: str = Field(pattern=r"^[a-f0-9]{40}$")

    @field_validator("name")
    @classmethod
    def safe_branch_name(cls, value: str) -> str:
        if value.startswith("/") or ".." in value or "//" in value:
            raise ValueError("Branch name contains an unsafe Git reference sequence.")
        return value


class InstallationToken(BaseModel):
    token: str = Field(repr=False)
    expires_at: datetime


class GitHubInstallStart(BaseModel):
    installation_url: HttpUrl
    expires_at: datetime
