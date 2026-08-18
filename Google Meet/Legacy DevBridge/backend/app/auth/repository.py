from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.auth.models import GoogleConnection, GoogleTokenSet


@dataclass(frozen=True)
class PendingGoogleAuthorization:
    session_id: str
    state_digest: str
    code_verifier: str
    expires_at: datetime


class GoogleCredentialRepository(Protocol):
    def save_pending(self, pending: PendingGoogleAuthorization) -> None: ...
    def consume_pending(self, state_digest: str) -> PendingGoogleAuthorization | None: ...
    def save_tokens(self, user_id: str, tokens: GoogleTokenSet) -> None: ...
    def save_connection(self, connection: GoogleConnection) -> None: ...
    def get_connection(self, user_id: str) -> GoogleConnection | None: ...


class InMemoryGoogleCredentialRepository:
    """Development adapter. Production must replace this with encrypted persistence."""

    def __init__(self) -> None:
        self._pending: dict[str, PendingGoogleAuthorization] = {}
        self._tokens: dict[str, GoogleTokenSet] = {}
        self._connections: dict[str, GoogleConnection] = {}

    def save_pending(self, pending: PendingGoogleAuthorization) -> None:
        self._pending[pending.state_digest] = pending

    def consume_pending(self, state_digest: str) -> PendingGoogleAuthorization | None:
        return self._pending.pop(state_digest, None)

    def save_tokens(self, user_id: str, tokens: GoogleTokenSet) -> None:
        self._tokens[user_id] = tokens.model_copy(deep=True)

    def save_connection(self, connection: GoogleConnection) -> None:
        self._connections[connection.user_id] = connection.model_copy(deep=True)

    def get_connection(self, user_id: str) -> GoogleConnection | None:
        connection = self._connections.get(user_id)
        return connection.model_copy(deep=True) if connection else None

    def clear(self) -> None:
        self._pending.clear()
        self._tokens.clear()
        self._connections.clear()
