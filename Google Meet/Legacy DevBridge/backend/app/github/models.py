from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, ValidationInfo, field_validator


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


class GitFileOperation(StrEnum):
    WRITE = "WRITE"
    DELETE = "DELETE"


class CommitFileChange(BaseModel):
    path: str = Field(min_length=1, max_length=1024)
    operation: GitFileOperation
    content: str | None = None

    @field_validator("content")
    @classmethod
    def content_matches_operation(cls, value: str | None, info: ValidationInfo) -> str | None:
        operation = info.data.get("operation")
        if operation == GitFileOperation.WRITE and value is None:
            raise ValueError("WRITE changes require content.")
        return value


class CreateCommitRequest(BaseModel):
    branch: str = Field(pattern=r"^[A-Za-z0-9._/-]{1,200}$")
    message: str = Field(min_length=1, max_length=1000)
    expected_head_sha: str = Field(pattern=r"^[a-f0-9]{40}$")
    changes: list[CommitFileChange] = Field(min_length=1)
    approved: bool = False


class GitHubCommit(BaseModel):
    sha: str
    html_url: HttpUrl


class GitWorkflowPolicy(BaseModel):
    prohibit_default_branch_commits: bool = True
    prohibit_protected_branch_commits: bool = True


class CreatePullRequestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    body: str = Field(default="", max_length=65536)
    head: str = Field(pattern=r"^[A-Za-z0-9._/-]{1,200}$")
    base: str = Field(pattern=r"^[A-Za-z0-9._/-]{1,200}$")
    validation_summary: str = Field(default="Not evaluated", max_length=2000)


class GitHubPullRequest(BaseModel):
    number: int
    title: str
    html_url: HttpUrl
    head: str
    base: str
    changed_files: int = 0
    validation_summary: str = "Not evaluated"
