from typing import Protocol

from app.appsscript.models import ProjectSnapshot
from app.appsscript.service import AppsScriptService
from app.audit.models import AuditEvent
from app.audit.repository import AuditRepository
from app.github.models import CreateRepositoryRequest, GitHubRepository
from app.github.service import GitHubService
from app.organizations.models import ExistingRepositoryProposal, ProjectMapping
from app.organizations.repository import ProjectMappingRepository


class ProjectSourcePort(Protocol):
    async def apps_script_snapshot(self, script_id: str) -> ProjectSnapshot: ...
    async def repository_snapshot(
        self, installation_id: int, owner: str, repo: str, branch: str
    ) -> ProjectSnapshot: ...
    async def create_repository(
        self, actor_id: str, installation_id: int, request: CreateRepositoryRequest
    ) -> GitHubRepository: ...
    async def import_initial_files(
        self,
        actor_id: str,
        installation_id: int,
        owner: str,
        repo: str,
        branch: str,
        snapshot: ProjectSnapshot,
    ) -> str: ...


class ProjectConnectionError(RuntimeError):
    pass


class LiveProjectSource:
    """Internal adapter; provider credentials are supplied by the authenticated backend session."""

    def __init__(
        self, apps_script: AppsScriptService, github: GitHubService, google_access_token: str
    ) -> None:
        self.apps_script = apps_script
        self.github = github
        self.google_access_token = google_access_token

    async def apps_script_snapshot(self, script_id: str) -> ProjectSnapshot:
        return await self.apps_script.get_snapshot(script_id, self.google_access_token)

    async def repository_snapshot(
        self, installation_id: int, owner: str, repo: str, branch: str
    ) -> ProjectSnapshot:
        return await self.github.get_snapshot(
            installation_id, owner, repo, branch, script_id=f"github:{owner}/{repo}"
        )

    async def create_repository(
        self, actor_id: str, installation_id: int, request: CreateRepositoryRequest
    ) -> GitHubRepository:
        return await self.github.create_repository(actor_id, installation_id, request)

    async def import_initial_files(
        self,
        actor_id: str,
        installation_id: int,
        owner: str,
        repo: str,
        branch: str,
        snapshot: ProjectSnapshot,
    ) -> str:
        return await self.github.create_initial_commit(
            actor_id, installation_id, owner, repo, branch, snapshot.files
        )


class ProjectConnectionService:
    def __init__(
        self,
        mappings: ProjectMappingRepository,
        source: ProjectSourcePort,
        audit: AuditRepository,
    ) -> None:
        self.mappings = mappings
        self.source = source
        self.audit = audit
        self._proposals: dict[str, ExistingRepositoryProposal] = {}

    async def create_and_connect(
        self,
        user_id: str,
        script_project_id: str,
        installation_id: int,
        request: CreateRepositoryRequest,
        default_branch: str = "main",
    ) -> ProjectMapping:
        if self.mappings.get(user_id, script_project_id):
            raise ProjectConnectionError("This Apps Script project is already connected.")
        script_snapshot = await self.source.apps_script_snapshot(script_project_id)
        repository = await self.source.create_repository(user_id, installation_id, request)
        await self.source.import_initial_files(
            user_id,
            installation_id,
            repository.owner.login,
            repository.name,
            default_branch,
            script_snapshot,
        )
        remote = await self.source.repository_snapshot(
            installation_id, repository.owner.login, repository.name, default_branch
        )
        if remote.project_hash != script_snapshot.project_hash:
            raise ProjectConnectionError(
                "GitHub did not retain the complete Apps Script import. "
                "The project was not connected."
            )
        mapping = self.mappings.save(
            ProjectMapping(
                user_id=user_id,
                script_project_id=script_project_id,
                github_installation_id=installation_id,
                repository_owner=repository.owner.login,
                repository_name=repository.name,
                default_branch=default_branch,
                active_branch=default_branch,
                sync_base_hash=script_snapshot.project_hash,
            )
        )
        self._audit_connected(mapping, "PROJECT_ADDED_TO_GITHUB")
        return mapping

    async def propose_existing_connection(
        self,
        user_id: str,
        script_project_id: str,
        installation_id: int,
        owner: str,
        repo: str,
        branch: str,
    ) -> ExistingRepositoryProposal:
        if self.mappings.get(user_id, script_project_id):
            raise ProjectConnectionError("This Apps Script project is already connected.")
        local = await self.source.apps_script_snapshot(script_project_id)
        remote = await self.source.repository_snapshot(installation_id, owner, repo, branch)
        local_files = {file.path: file.sha256 for file in local.files}
        remote_files = {file.path: file.sha256 for file in remote.files}
        paths = sorted(set(local_files) | set(remote_files))
        proposal = ExistingRepositoryProposal(
            user_id=user_id,
            script_project_id=script_project_id,
            github_installation_id=installation_id,
            repository_owner=owner,
            repository_name=repo,
            branch=branch,
            apps_script_hash=local.project_hash,
            repository_hash=remote.project_hash,
            changed_paths=[
                path for path in paths if local_files.get(path) != remote_files.get(path)
            ],
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    async def confirm_existing_connection(self, user_id: str, proposal_id: str) -> ProjectMapping:
        proposal = self._proposals.pop(proposal_id, None)
        if proposal is None or proposal.user_id != user_id:
            raise ProjectConnectionError("This repository connection proposal is no longer valid.")
        local = await self.source.apps_script_snapshot(proposal.script_project_id)
        remote = await self.source.repository_snapshot(
            proposal.github_installation_id,
            proposal.repository_owner,
            proposal.repository_name,
            proposal.branch,
        )
        if (
            local.project_hash != proposal.apps_script_hash
            or remote.project_hash != proposal.repository_hash
        ):
            raise ProjectConnectionError(
                "Source changed after comparison. Review a fresh comparison before connecting."
            )
        common_hash = local.project_hash if local.project_hash == remote.project_hash else None
        mapping = self.mappings.save(
            ProjectMapping(
                user_id=user_id,
                script_project_id=proposal.script_project_id,
                github_installation_id=proposal.github_installation_id,
                repository_owner=proposal.repository_owner,
                repository_name=proposal.repository_name,
                default_branch=proposal.branch,
                active_branch=proposal.branch,
                sync_base_hash=common_hash,
            )
        )
        self._audit_connected(mapping, "EXISTING_REPOSITORY_CONNECTED")
        return mapping

    def _audit_connected(self, mapping: ProjectMapping, action: str) -> None:
        self.audit.append(
            AuditEvent(
                actor_id=mapping.user_id,
                action=action,
                script_project_id=mapping.script_project_id,
                repository=mapping.repository_full_name,
                branch=mapping.active_branch,
            )
        )
