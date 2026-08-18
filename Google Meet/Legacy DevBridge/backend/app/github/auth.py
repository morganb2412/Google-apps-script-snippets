import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import jwt

from app.github.models import GitHubInstallStart, InstallationToken


class GitHubInstallationStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class PendingGitHubInstallation:
    session_id: str
    expires_at: datetime


class GitHubInstallationRepository(Protocol):
    def save(self, session_id: str, installation_id: int) -> None: ...
    def get(self, session_id: str) -> int | None: ...


class InMemoryGitHubInstallationRepository:
    def __init__(self) -> None:
        self._installations: dict[str, int] = {}

    def save(self, session_id: str, installation_id: int) -> None:
        self._installations[session_id] = installation_id

    def get(self, session_id: str) -> int | None:
        return self._installations.get(session_id)


class GitHubInstallationFlow:
    def __init__(self, app_name: str, installations: GitHubInstallationRepository) -> None:
        self.app_name = app_name
        self.installations = installations
        self._pending: dict[str, PendingGitHubInstallation] = {}

    def start(self, session_id: str) -> GitHubInstallStart:
        if not self.app_name:
            raise GitHubInstallationStateError("GitHub connection is not configured yet.")
        state = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        self._pending[_state_digest(state)] = PendingGitHubInstallation(session_id, expires_at)
        return GitHubInstallStart(
            installation_url=(
                f"https://github.com/apps/{self.app_name}/installations/new?state={state}"
            ),
            expires_at=expires_at,
        )

    def complete(self, state: str, installation_id: int) -> str:
        pending = self._pending.pop(_state_digest(state), None)
        if pending is None or pending.expires_at <= datetime.now(UTC):
            raise GitHubInstallationStateError(
                "This GitHub connection request expired. Start again."
            )
        self.installations.save(pending.session_id, installation_id)
        return pending.session_id


class GitHubAppClient(Protocol):
    async def create_installation_token(
        self, installation_id: int, app_jwt: str
    ) -> InstallationToken: ...


class GitHubJwtSigner(Protocol):
    def sign(self) -> str: ...


class PyJwtGitHubSigner:
    def __init__(self, app_id: str, private_key: str) -> None:
        self.app_id = app_id
        self.private_key = private_key.replace("\\n", "\n")

    def sign(self) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "iat": int((now - timedelta(seconds=30)).timestamp()),
                "exp": int((now + timedelta(minutes=9)).timestamp()),
                "iss": self.app_id,
            },
            self.private_key,
            algorithm="RS256",
        )


class GitHubInstallationAuth:
    def __init__(self, signer: GitHubJwtSigner, client: GitHubAppClient) -> None:
        self.signer = signer
        self.client = client
        self._tokens: dict[int, InstallationToken] = {}

    async def token_for(self, installation_id: int) -> str:
        cached = self._tokens.get(installation_id)
        if cached and cached.expires_at > datetime.now(UTC) + timedelta(minutes=2):
            return cached.token
        token = await self.client.create_installation_token(installation_id, self.signer.sign())
        self._tokens[installation_id] = token
        return token.token

    def invalidate(self, installation_id: int) -> None:
        self._tokens.pop(installation_id, None)


def _state_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
