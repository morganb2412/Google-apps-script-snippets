import asyncio

import pytest

from app.appsscript.models import (
    AppsScriptContent,
    AppsScriptFile,
    AppsScriptFileType,
    ProjectSnapshot,
)
from app.appsscript.normalization import create_snapshot
from app.audit.repository import InMemoryAuditRepository
from app.github.models import CreateRepositoryRequest, GitHubFile, GitHubOwner, GitHubRepository
from app.github.normalization import create_github_snapshot
from app.organizations.connection import ProjectConnectionError, ProjectConnectionService
from app.organizations.models import ProjectMapping
from app.organizations.repository import InMemoryProjectMappingRepository


def snapshot(source: str = "function run() {}") -> ProjectSnapshot:
    return create_snapshot(
        AppsScriptContent(
            script_id="script-project-123",
            files=[
                AppsScriptFile(name="Code", type=AppsScriptFileType.SERVER_JS, source=source),
                AppsScriptFile(
                    name="appsscript",
                    type=AppsScriptFileType.JSON,
                    source='{"runtimeVersion":"V8"}',
                ),
            ],
        )
    )


class FakeProjectSource:
    def __init__(self, local: ProjectSnapshot, remote: ProjectSnapshot | None = None) -> None:
        self.local = local
        self.remote = remote
        self.import_calls = 0

    async def apps_script_snapshot(self, script_id: str) -> ProjectSnapshot:
        return self.local.model_copy(deep=True)

    async def repository_snapshot(
        self, installation_id: int, owner: str, repo: str, branch: str
    ) -> ProjectSnapshot:
        if self.remote is None:
            raise AssertionError("Repository snapshot requested before import")
        return self.remote.model_copy(deep=True)

    async def create_repository(
        self, actor_id: str, installation_id: int, request: CreateRepositoryRequest
    ) -> GitHubRepository:
        return GitHubRepository(
            id=7,
            name=request.name,
            full_name=f"{request.organization}/{request.name}",
            private=True,
            default_branch="main",
            html_url=f"https://github.com/{request.organization}/{request.name}",
            owner=GitHubOwner(login=request.organization, type="Organization"),
        )

    async def import_initial_files(
        self,
        actor_id: str,
        installation_id: int,
        owner: str,
        repo: str,
        branch: str,
        snapshot: ProjectSnapshot,
    ) -> str:
        self.import_calls += 1
        self.remote = snapshot.model_copy(deep=True)
        return "c" * 40


def test_mapping_repository_is_user_and_project_scoped() -> None:
    repository = InMemoryProjectMappingRepository()
    saved = repository.save(
        ProjectMapping(
            user_id="user-one",
            script_project_id="script-one",
            github_installation_id=42,
            repository_owner="acme",
            repository_name="atlas",
        )
    )
    saved.repository_name = "mutated"
    stored = repository.get("user-one", "script-one")
    assert stored is not None
    assert stored.repository_name == "atlas"
    assert repository.get("user-two", "script-one") is None


def test_github_and_apps_script_snapshots_share_hash_representation() -> None:
    apps_script = snapshot()
    github = create_github_snapshot(
        "github:acme/atlas",
        [
            GitHubFile(
                path=file.path,
                name=file.path,
                sha="b" * 40,
                content=file.content,
            )
            for file in apps_script.files
        ],
    )
    assert github.project_hash == apps_script.project_hash


def test_create_and_connect_imports_verifies_and_saves_mapping() -> None:
    source = FakeProjectSource(snapshot())
    mappings = InMemoryProjectMappingRepository()
    audit = InMemoryAuditRepository()
    service = ProjectConnectionService(mappings, source, audit)
    mapping = asyncio.run(
        service.create_and_connect(
            "user-one",
            "script-project-123",
            42,
            CreateRepositoryRequest(organization="acme", name="atlas"),
        )
    )
    assert source.import_calls == 1
    assert mapping.repository_full_name == "acme/atlas"
    assert mapping.sync_base_hash == source.local.project_hash
    assert mappings.get("user-one", "script-project-123") is not None
    assert audit.list_for_actor("user-one")[0].action == "PROJECT_ADDED_TO_GITHUB"


def test_existing_repository_requires_confirmation_without_writes() -> None:
    source = FakeProjectSource(snapshot(), snapshot("function run() { return true; }"))
    mappings = InMemoryProjectMappingRepository()
    service = ProjectConnectionService(mappings, source, InMemoryAuditRepository())
    proposal = asyncio.run(
        service.propose_existing_connection(
            "user-one", "script-project-123", 42, "acme", "atlas", "main"
        )
    )
    assert proposal.requires_confirmation is True
    assert proposal.changed_paths == ["Code.gs"]
    assert source.import_calls == 0
    assert mappings.get("user-one", "script-project-123") is None
    mapping = asyncio.run(service.confirm_existing_connection("user-one", proposal.proposal_id))
    assert mapping.sync_base_hash is None
    assert source.import_calls == 0


def test_existing_connection_rejects_stale_comparison() -> None:
    source = FakeProjectSource(snapshot(), snapshot())
    service = ProjectConnectionService(
        InMemoryProjectMappingRepository(), source, InMemoryAuditRepository()
    )
    proposal = asyncio.run(
        service.propose_existing_connection(
            "user-one", "script-project-123", 42, "acme", "atlas", "main"
        )
    )
    source.remote = snapshot("function changedAfterReview() {}")
    with pytest.raises(ProjectConnectionError, match="fresh comparison"):
        asyncio.run(service.confirm_existing_connection("user-one", proposal.proposal_id))
