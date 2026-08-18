import asyncio
from urllib.parse import parse_qs, urlparse

import pytest

from app.auth.models import GoogleIdentity, GoogleTokenSet
from app.auth.repository import InMemoryGoogleCredentialRepository
from app.auth.service import GoogleOAuthService, GoogleOAuthStateError, GoogleTenantDeniedError


class FakeGoogleProvider:
    def __init__(self, domain: str = "moesaidevspace.com") -> None:
        self.domain = domain
        self.verifier = ""

    async def exchange_code(self, code: str, code_verifier: str) -> GoogleTokenSet:
        assert code == "authorization-code"
        self.verifier = code_verifier
        return GoogleTokenSet(access_token="access-token", refresh_token="refresh-token")

    async def get_identity(self, access_token: str) -> GoogleIdentity:
        assert access_token == "access-token"
        return GoogleIdentity(
            subject="google-user-123",
            email=f"developer@{self.domain}",
            email_verified=True,
            hosted_domain=self.domain,
        )


def build_service(
    provider: FakeGoogleProvider,
) -> tuple[GoogleOAuthService, InMemoryGoogleCredentialRepository]:
    repository = InMemoryGoogleCredentialRepository()
    return GoogleOAuthService(
        repository=repository,
        provider=provider,
        client_id="client-id.apps.googleusercontent.com",
        redirect_uri="https://api.example.test/api/v1/onboarding/google/callback",
        allowed_domains={"moesaidevspace.com"},
    ), repository


def test_google_oauth_uses_state_pkce_and_connects_allowed_tenant() -> None:
    provider = FakeGoogleProvider()
    service, repository = build_service(provider)
    started = service.start("extension-session-1234567890")
    query = parse_qs(urlparse(started.authorization_url).query)

    assert query["code_challenge_method"] == ["S256"]
    assert query["access_type"] == ["offline"]
    assert "https://www.googleapis.com/auth/script.projects" in query["scope"][0]
    session_id, result = asyncio.run(service.complete("authorization-code", query["state"][0]))

    assert provider.verifier
    assert session_id == "extension-session-1234567890"
    assert result.connected is True
    assert repository.get_connection("google-user-123") is not None


def test_google_oauth_state_is_single_use() -> None:
    service, _ = build_service(FakeGoogleProvider())
    query = parse_qs(
        urlparse(service.start("extension-session-1234567890").authorization_url).query
    )
    state = query["state"][0]
    asyncio.run(service.complete("authorization-code", state))

    with pytest.raises(GoogleOAuthStateError):
        asyncio.run(service.complete("authorization-code", state))


def test_google_oauth_rejects_account_outside_allowed_tenant() -> None:
    service, _ = build_service(FakeGoogleProvider("unauthorized.example"))
    query = parse_qs(
        urlparse(service.start("extension-session-1234567890").authorization_url).query
    )

    with pytest.raises(GoogleTenantDeniedError):
        asyncio.run(service.complete("authorization-code", query["state"][0]))
