from app.appsscript.models import ProjectFile, ProjectSnapshot
from app.audit.models import AuditEvent
from app.audit.repository import AuditRepository
from app.github.auth import GitHubInstallationAuth
from app.github.gateway import GitHubGateway
from app.github.models import (
    CreateBranchRequest,
    CreateRepositoryRequest,
    GitHubBranch,
    GitHubFile,
    GitHubRepository,
)
from app.github.normalization import create_github_snapshot


class GitHubService:
    def __init__(
        self,
        auth: GitHubInstallationAuth,
        gateway: GitHubGateway,
        audit_repository: AuditRepository,
    ) -> None:
        self.auth = auth
        self.gateway = gateway
        self.audit_repository = audit_repository

    async def list_repositories(self, installation_id: int) -> list[GitHubRepository]:
        return await self.gateway.list_repositories(await self.auth.token_for(installation_id))

    async def get_repository(self, installation_id: int, owner: str, repo: str) -> GitHubRepository:
        return await self.gateway.get_repository(
            owner, repo, await self.auth.token_for(installation_id)
        )

    async def create_repository(
        self, actor_id: str, installation_id: int, request: CreateRepositoryRequest
    ) -> GitHubRepository:
        repository = await self.gateway.create_repository(
            request, await self.auth.token_for(installation_id)
        )
        self.audit_repository.append(
            AuditEvent(
                actor_id=actor_id,
                action="REPOSITORY_CREATED",
                repository=repository.full_name,
                metadata={"private": repository.private},
            )
        )
        return repository

    async def list_branches(
        self, installation_id: int, owner: str, repo: str
    ) -> list[GitHubBranch]:
        return await self.gateway.list_branches(
            owner, repo, await self.auth.token_for(installation_id)
        )

    async def create_branch(
        self,
        actor_id: str,
        installation_id: int,
        owner: str,
        repo: str,
        request: CreateBranchRequest,
    ) -> GitHubBranch:
        branch = await self.gateway.create_branch(
            owner, repo, request, await self.auth.token_for(installation_id)
        )
        self.audit_repository.append(
            AuditEvent(
                actor_id=actor_id,
                action="BRANCH_CREATED",
                repository=f"{owner}/{repo}",
                branch=branch.name,
            )
        )
        return branch

    async def get_file(
        self, installation_id: int, owner: str, repo: str, path: str, ref: str
    ) -> GitHubFile:
        return await self.gateway.get_file(
            owner, repo, path, ref, await self.auth.token_for(installation_id)
        )

    async def create_initial_commit(
        self,
        actor_id: str,
        installation_id: int,
        owner: str,
        repo: str,
        branch: str,
        files: list[ProjectFile],
    ) -> str:
        commit_sha = await self.gateway.create_initial_commit(
            owner,
            repo,
            branch,
            files,
            "chore: import Apps Script project",
            await self.auth.token_for(installation_id),
        )
        self.audit_repository.append(
            AuditEvent(
                actor_id=actor_id,
                action="INITIAL_IMPORT_COMMITTED",
                repository=f"{owner}/{repo}",
                branch=branch,
                metadata={"commit_sha": commit_sha, "file_count": len(files)},
            )
        )
        return commit_sha

    async def get_snapshot(
        self, installation_id: int, owner: str, repo: str, branch: str, script_id: str
    ) -> ProjectSnapshot:
        files = await self.gateway.list_repository_files(
            owner, repo, branch, await self.auth.token_for(installation_id)
        )
        return create_github_snapshot(script_id, files)
