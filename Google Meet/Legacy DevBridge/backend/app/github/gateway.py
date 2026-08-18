import base64
from typing import Any, Protocol

import httpx

from app.github.auth import GitHubAppClient
from app.github.errors import (
    GitHubConnectionExpiredError,
    GitHubResourceNotFoundError,
    GitHubUnavailableError,
)
from app.github.models import (
    CreateBranchRequest,
    CreateRepositoryRequest,
    GitHubBranch,
    GitHubFile,
    GitHubOwner,
    GitHubRepository,
    InstallationToken,
)

GITHUB_API_VERSION = "2022-11-28"


class GitHubGateway(Protocol):
    async def list_repositories(self, token: str) -> list[GitHubRepository]: ...
    async def get_repository(self, owner: str, repo: str, token: str) -> GitHubRepository: ...
    async def create_repository(
        self, request: CreateRepositoryRequest, token: str
    ) -> GitHubRepository: ...
    async def list_branches(self, owner: str, repo: str, token: str) -> list[GitHubBranch]: ...
    async def create_branch(
        self, owner: str, repo: str, request: CreateBranchRequest, token: str
    ) -> GitHubBranch: ...
    async def get_file(
        self, owner: str, repo: str, path: str, ref: str, token: str
    ) -> GitHubFile: ...


class HttpGitHubGateway(GitHubAppClient):
    BASE_URL = "https://api.github.com"

    async def create_installation_token(
        self, installation_id: int, app_jwt: str
    ) -> InstallationToken:
        payload = await self._request(
            "POST", f"/app/installations/{installation_id}/access_tokens", app_jwt
        )
        return InstallationToken.model_validate(payload)

    async def list_repositories(self, token: str) -> list[GitHubRepository]:
        payload = await self._request("GET", "/installation/repositories?per_page=100", token)
        repositories = payload.get("repositories", [])
        return [self._repository(item) for item in repositories]

    async def get_repository(self, owner: str, repo: str, token: str) -> GitHubRepository:
        return self._repository(await self._request("GET", f"/repos/{owner}/{repo}", token))

    async def create_repository(
        self, request: CreateRepositoryRequest, token: str
    ) -> GitHubRepository:
        payload = await self._request(
            "POST",
            f"/orgs/{request.organization}/repos",
            token,
            json={
                "name": request.name,
                "description": request.description,
                "private": request.visibility.value == "private",
                "auto_init": False,
            },
        )
        return self._repository(payload)

    async def list_branches(self, owner: str, repo: str, token: str) -> list[GitHubBranch]:
        payload = await self._request("GET", f"/repos/{owner}/{repo}/branches?per_page=100", token)
        return [
            GitHubBranch(
                name=item["name"],
                commit_sha=item["commit"]["sha"],
                protected=item.get("protected", False),
            )
            for item in payload
        ]

    async def create_branch(
        self, owner: str, repo: str, request: CreateBranchRequest, token: str
    ) -> GitHubBranch:
        payload = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            token,
            json={"ref": f"refs/heads/{request.name}", "sha": request.from_sha},
        )
        return GitHubBranch(name=request.name, commit_sha=payload["object"]["sha"])

    async def get_file(self, owner: str, repo: str, path: str, ref: str, token: str) -> GitHubFile:
        payload = await self._request(
            "GET", f"/repos/{owner}/{repo}/contents/{path}?ref={ref}", token
        )
        if payload.get("type") != "file" or payload.get("encoding") != "base64":
            raise ValueError("GitHub returned an unsupported repository content type.")
        decoded = base64.b64decode(payload["content"], validate=False).decode("utf-8")
        return GitHubFile(
            path=payload["path"],
            name=payload["name"],
            sha=payload["sha"],
            content=decoded,
        )

    async def _request(
        self, method: str, path: str, token: str, json: dict[str, object] | None = None
    ) -> Any:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}{path}",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {token}",
                    "X-GitHub-Api-Version": GITHUB_API_VERSION,
                },
                json=json,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                if response.status_code in {401, 403}:
                    raise GitHubConnectionExpiredError(
                        "Your GitHub connection needs attention. Reconnect GitHub to continue."
                    ) from error
                if response.status_code == 404:
                    raise GitHubResourceNotFoundError(
                        "The requested GitHub repository or file is no longer available."
                    ) from error
                raise GitHubUnavailableError(
                    "GitHub could not complete this request. Try again shortly."
                ) from error
            return response.json()

    @staticmethod
    def _repository(payload: dict[str, Any]) -> GitHubRepository:
        return GitHubRepository(
            id=payload["id"],
            name=payload["name"],
            full_name=payload["full_name"],
            private=payload["private"],
            default_branch=payload.get("default_branch") or "main",
            html_url=payload["html_url"],
            owner=GitHubOwner.model_validate(payload["owner"]),
        )
