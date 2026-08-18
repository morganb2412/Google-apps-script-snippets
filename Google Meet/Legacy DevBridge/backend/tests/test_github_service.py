import asyncio
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.audit.repository import InMemoryAuditRepository
from app.github.auth import (
    GitHubInstallationAuth,
    GitHubInstallationFlow,
    GitHubInstallationStateError,
    InMemoryGitHubInstallationRepository,
    PyJwtGitHubSigner,
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
        return [GitHubBranch(name="main", commit_sha="a" * 40, protected=True)]

    async def create_branch(
        self, owner: str, repo: str, request: CreateBranchRequest, token: str
    ) -> GitHubBranch:
        self.tokens.append(token)
        return GitHubBranch(name=request.name, commit_sha=request.from_sha)

    async def get_file(self, owner: str, repo: str, path: str, ref: str, token: str) -> GitHubFile:
        self.tokens.append(token)
        return GitHubFile(path=path, name="Code.gs", sha="b" * 40, content="function run() {}")


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
