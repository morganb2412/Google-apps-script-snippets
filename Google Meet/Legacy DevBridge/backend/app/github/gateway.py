import base64
from typing import Any, Protocol

import httpx

from app.appsscript.models import ProjectFile
from app.github.auth import GitHubAppClient
from app.github.errors import (
    GitHubConnectionExpiredError,
    GitHubResourceNotFoundError,
    GitHubUnavailableError,
)
from app.github.models import (
    CreateBranchRequest,
    CreateCommitRequest,
    CreatePullRequestRequest,
    CreateRepositoryRequest,
    GitFileOperation,
    GitHubBranch,
    GitHubCommit,
    GitHubFile,
    GitHubOwner,
    GitHubPullRequest,
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
    async def create_initial_commit(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[ProjectFile],
        message: str,
        token: str,
    ) -> str: ...
    async def list_repository_files(
        self, owner: str, repo: str, ref: str, token: str
    ) -> list[GitHubFile]: ...
    async def create_commit(
        self, owner: str, repo: str, request: CreateCommitRequest, token: str
    ) -> GitHubCommit: ...
    async def create_pull_request(
        self, owner: str, repo: str, request: CreatePullRequestRequest, token: str
    ) -> GitHubPullRequest: ...


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

    async def create_initial_commit(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[ProjectFile],
        message: str,
        token: str,
    ) -> str:
        tree_items: list[dict[str, str]] = []
        for file in files:
            blob = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/git/blobs",
                token,
                json={"content": file.content, "encoding": "utf-8"},
            )
            tree_items.append(
                {"path": file.path, "mode": "100644", "type": "blob", "sha": blob["sha"]}
            )
        tree = await self._request(
            "POST", f"/repos/{owner}/{repo}/git/trees", token, json={"tree": tree_items}
        )
        commit = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/commits",
            token,
            json={"message": message, "tree": tree["sha"], "parents": []},
        )
        await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            token,
            json={"ref": f"refs/heads/{branch}", "sha": commit["sha"]},
        )
        result: str = commit["sha"]
        return result

    async def list_repository_files(
        self, owner: str, repo: str, ref: str, token: str
    ) -> list[GitHubFile]:
        payload = await self._request(
            "GET", f"/repos/{owner}/{repo}/git/trees/{ref}?recursive=1", token
        )
        tree = payload.get("tree", [])
        files: list[GitHubFile] = []
        for item in tree:
            if item.get("type") == "blob":
                files.append(await self.get_file(owner, repo, item["path"], ref, token))
        return files

    async def create_commit(
        self, owner: str, repo: str, request: CreateCommitRequest, token: str
    ) -> GitHubCommit:
        tree_items: list[dict[str, str | None]] = []
        for change in request.changes:
            if change.operation == GitFileOperation.DELETE:
                tree_items.append(
                    {"path": change.path, "mode": "100644", "type": "blob", "sha": None}
                )
                continue
            blob = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/git/blobs",
                token,
                json={"content": change.content or "", "encoding": "utf-8"},
            )
            tree_items.append(
                {"path": change.path, "mode": "100644", "type": "blob", "sha": blob["sha"]}
            )
        tree = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/trees",
            token,
            json={"base_tree": request.expected_head_sha, "tree": tree_items},
        )
        commit = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/commits",
            token,
            json={
                "message": request.message,
                "tree": tree["sha"],
                "parents": [request.expected_head_sha],
            },
        )
        await self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/git/refs/heads/{request.branch}",
            token,
            json={"sha": commit["sha"], "force": False},
        )
        return GitHubCommit(sha=commit["sha"], html_url=commit["html_url"])

    async def create_pull_request(
        self, owner: str, repo: str, request: CreatePullRequestRequest, token: str
    ) -> GitHubPullRequest:
        payload = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            token,
            json={
                "title": request.title,
                "body": request.body,
                "head": request.head,
                "base": request.base,
            },
        )
        return GitHubPullRequest(
            number=payload["number"],
            title=payload["title"],
            html_url=payload["html_url"],
            head=payload["head"]["ref"],
            base=payload["base"]["ref"],
            changed_files=payload.get("changed_files", 0),
            validation_summary=request.validation_summary,
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
