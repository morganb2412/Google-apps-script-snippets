import asyncio
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.appsscript.models import ProjectFile
from app.audit.repository import InMemoryAuditRepository
from app.github.auth import (
    GitHubInstallationAuth,
    GitHubInstallationFlow,
    GitHubInstallationStateError,
    InMemoryGitHubInstallationRepository,
    PyJwtGitHubSigner,
)
from app.github.models import (
    CommitFileChange,
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
from app.github.service import GitHubService


class FakeSigner:
    def __init__(self) -> None:
        self.calls = 0

    def sign(self) -> str:
        self.calls += 1
        return "signed-app-jwt"


class FakeAppClient:
    def __init__(self) -> None:
        self.calls = 0

    async def create_installation_token(
        self, installation_id: int, app_jwt: str
    ) -> InstallationToken:
        assert installation_id == 42
        assert app_jwt == "signed-app-jwt"
        self.calls += 1
        return InstallationToken(
            token=f"installation-token-{self.calls}",
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )


class FakeGateway:
    def __init__(self) -> None:
        self.tokens: list[str] = []
        self.commit_calls = 0

    @staticmethod
    def repository(name: str = "atlas") -> GitHubRepository:
        return GitHubRepository(
            id=1,
            name=name,
            full_name=f"acme/{name}",
            private=True,
            default_branch="main",
            html_url=f"https://github.com/acme/{name}",
            owner=GitHubOwner(login="acme", type="Organization"),
        )

    async def list_repositories(self, token: str) -> list[GitHubRepository]:
        self.tokens.append(token)
        return [self.repository()]

    async def get_repository(self, owner: str, repo: str, token: str) -> GitHubRepository:
        self.tokens.append(token)
        return self.repository(repo)

    async def create_repository(
        self, request: CreateRepositoryRequest, token: str
    ) -> GitHubRepository:
        self.tokens.append(token)
        return self.repository(request.name)

    async def list_branches(self, owner: str, repo: str, token: str) -> list[GitHubBranch]:
        self.tokens.append(token)
        return [
            GitHubBranch(name="main", commit_sha="a" * 40, protected=True),
            GitHubBranch(name="feature/safe", commit_sha="b" * 40),
        ]

    async def create_branch(
        self, owner: str, repo: str, request: CreateBranchRequest, token: str
    ) -> GitHubBranch:
        self.tokens.append(token)
        return GitHubBranch(name=request.name, commit_sha=request.from_sha)

    async def get_file(self, owner: str, repo: str, path: str, ref: str, token: str) -> GitHubFile:
        self.tokens.append(token)
        return GitHubFile(path=path, name="Code.gs", sha="b" * 40, content="function run() {}")

    async def create_initial_commit(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[ProjectFile],
        message: str,
        token: str,
    ) -> str:
        self.tokens.append(token)
        assert files
        assert message == "chore: import Apps Script project"
        return "c" * 40

    async def create_commit(
        self, owner: str, repo: str, request: CreateCommitRequest, token: str
    ) -> GitHubCommit:
        self.tokens.append(token)
        self.commit_calls += 1
        return GitHubCommit(
            sha="c" * 40,
            html_url="https://github.com/acme/atlas/commit/cccc",
        )

    async def create_pull_request(
        self, owner: str, repo: str, request: CreatePullRequestRequest, token: str
    ) -> GitHubPullRequest:
        self.tokens.append(token)
        return GitHubPullRequest(
            number=7,
            title=request.title,
            html_url="https://github.com/acme/atlas/pull/7",
            head=request.head,
            base=request.base,
            changed_files=2,
            validation_summary=request.validation_summary,
        )


def build_service() -> tuple[
    GitHubService, FakeSigner, FakeAppClient, FakeGateway, InMemoryAuditRepository
]:
    signer = FakeSigner()
    client = FakeAppClient()
    gateway = FakeGateway()
    audit = InMemoryAuditRepository()
    auth = GitHubInstallationAuth(signer, client)
    return GitHubService(auth, gateway, audit), signer, client, gateway, audit


def test_installation_tokens_are_server_side_and_cached() -> None:
    service, signer, client, gateway, _ = build_service()
    first = asyncio.run(service.list_repositories(42))
    second = asyncio.run(service.list_branches(42, "acme", "atlas"))

    assert first[0].full_name == "acme/atlas"
    assert second[0].protected is True
    assert signer.calls == 1
    assert client.calls == 1
    assert gateway.tokens == ["installation-token-1", "installation-token-1"]


def test_repository_and_branch_creation_are_audited_without_tokens() -> None:
    service, _, _, _, audit = build_service()
    repository = asyncio.run(
        service.create_repository(
            "actor",
            42,
            CreateRepositoryRequest(organization="acme", name="new-automation"),
        )
    )
    branch = asyncio.run(
        service.create_branch(
            "actor",
            42,
            "acme",
            repository.name,
            CreateBranchRequest(name="feature/approval", from_sha="a" * 40),
        )
    )

    assert branch.name == "feature/approval"
    events = audit.list_for_actor("actor")
    assert [event.action for event in events] == ["REPOSITORY_CREATED", "BRANCH_CREATED"]
    assert "installation-token" not in str([event.model_dump() for event in events])


def test_repository_details_and_file_retrieval_use_installation_auth() -> None:
    service, _, client, _, _ = build_service()
    repository = asyncio.run(service.get_repository(42, "acme", "atlas"))
    file = asyncio.run(service.get_file(42, "acme", "atlas", "Code.gs", "main"))
    assert repository.default_branch == "main"
    assert file.content == "function run() {}"
    assert client.calls == 1


def test_installation_flow_uses_single_use_state() -> None:
    installations = InMemoryGitHubInstallationRepository()
    flow = GitHubInstallationFlow("legacy-devbridge", installations)
    started = flow.start("extension-session-1234567890")
    state = str(started.installation_url).split("state=", 1)[1]
    assert str(started.installation_url).startswith(
        "https://github.com/apps/legacy-devbridge/installations/new"
    )
    assert flow.complete(state, 42) == "extension-session-1234567890"
    assert installations.get("extension-session-1234567890") == 42
    with pytest.raises(GitHubInstallationStateError):
        flow.complete(state, 42)


def test_installation_flow_requires_configured_app_name() -> None:
    with pytest.raises(GitHubInstallationStateError, match="not configured"):
        GitHubInstallationFlow("", InMemoryGitHubInstallationRepository()).start(
            "extension-session-1234567890"
        )


def test_github_app_signer_creates_short_lived_rs256_jwt() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    token = PyJwtGitHubSigner("12345", private_pem).sign()
    claims = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["RS256"],
        issuer="12345",
    )
    assert claims["exp"] - claims["iat"] <= 600


def commit_request(**changes: object) -> CreateCommitRequest:
    values: dict[str, object] = {
        "branch": "feature/safe",
        "message": "feat: validate approvals",
        "expected_head_sha": "b" * 40,
        "approved": True,
        "changes": [
            CommitFileChange(
                path="Code.gs",
                operation=GitFileOperation.WRITE,
                content="function run() { return true; }",
            )
        ],
    }
    values.update(changes)
    return CreateCommitRequest.model_validate(values)


def test_approved_feature_branch_commit_is_audited() -> None:
    service, _, _, gateway, audit = build_service()
    commit = asyncio.run(service.create_commit("actor", 42, "acme", "atlas", commit_request()))

    assert commit.sha == "c" * 40
    assert gateway.commit_calls == 1
    event = audit.list_for_actor("actor")[0]
    assert event.action == "COMMIT_CREATED"
    assert event.metadata["file_count"] == 1


@pytest.mark.parametrize(
    ("commit_input", "message"),
    [
        (commit_request(approved=False), "approve"),
        (commit_request(expected_head_sha="d" * 40), "branch changed"),
        (commit_request(branch="main", expected_head_sha="a" * 40), "default branch"),
    ],
)
def test_commit_policy_and_stale_head_fail_closed(
    commit_input: CreateCommitRequest, message: str
) -> None:
    service, _, _, gateway, audit = build_service()
    with pytest.raises(ValueError, match=message):
        asyncio.run(service.create_commit("actor", 42, "acme", "atlas", commit_input))
    assert gateway.commit_calls == 0
    assert audit.list_for_actor("actor") == []


def test_pull_request_requires_distinct_existing_branches_and_is_audited() -> None:
    service, _, _, _, audit = build_service()
    request = CreatePullRequestRequest(
        title="Add approval validation",
        body="Human-approved changes.",
        head="feature/safe",
        base="main",
        validation_summary="Standards passed",
    )
    pull_request = asyncio.run(service.create_pull_request("actor", 42, "acme", "atlas", request))
    assert pull_request.number == 7
    assert pull_request.changed_files == 2
    assert audit.list_for_actor("actor")[0].action == "PULL_REQUEST_CREATED"

    with pytest.raises(ValueError, match="must be different"):
        asyncio.run(
            service.create_pull_request(
                "actor", 42, "acme", "atlas", request.model_copy(update={"head": "main"})
            )
        )
