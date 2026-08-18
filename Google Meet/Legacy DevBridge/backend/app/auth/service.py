import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from app.auth.google import GoogleOAuthProvider
from app.auth.models import GoogleConnection, GoogleOAuthStart, OAuthCallbackResult
from app.auth.repository import GoogleCredentialRepository, PendingGoogleAuthorization

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_SCOPES = (
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/script.projects",
)


class GoogleOAuthConfigurationError(RuntimeError):
    pass


class GoogleOAuthStateError(RuntimeError):
    pass


class GoogleTenantDeniedError(RuntimeError):
    pass


class GoogleOAuthService:
    def __init__(
        self,
        repository: GoogleCredentialRepository,
        provider: GoogleOAuthProvider,
        client_id: str,
        redirect_uri: str,
        allowed_domains: set[str],
    ) -> None:
        self.repository = repository
        self.provider = provider
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.allowed_domains = {domain.lower() for domain in allowed_domains}

    def start(self, session_id: str) -> GoogleOAuthStart:
        if not self.client_id or not self.redirect_uri:
            raise GoogleOAuthConfigurationError("Google connection is not configured yet.")
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = _base64_digest(verifier)
        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        self.repository.save_pending(
            PendingGoogleAuthorization(
                session_id=session_id,
                state_digest=_digest(state),
                code_verifier=verifier,
                expires_at=expires_at,
            )
        )
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": " ".join(GOOGLE_SCOPES),
                "access_type": "offline",
                "include_granted_scopes": "true",
                "prompt": "consent",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return GoogleOAuthStart(
            authorization_url=f"{GOOGLE_AUTHORIZATION_URL}?{query}", expires_at=expires_at
        )

    async def complete(self, code: str, state: str) -> tuple[str, OAuthCallbackResult]:
        pending = self.repository.consume_pending(_digest(state))
        if pending is None or pending.expires_at <= datetime.now(UTC):
            raise GoogleOAuthStateError("This Google connection request expired. Start again.")
        tokens = await self.provider.exchange_code(code, pending.code_verifier)
        identity = await self.provider.get_identity(tokens.access_token)
        if not identity.email_verified:
            raise GoogleTenantDeniedError("Google could not verify this account email.")
        email_domain = identity.email.rsplit("@", 1)[-1].lower()
        hosted_domain = (identity.hosted_domain or "").lower()
        if self.allowed_domains and not ({email_domain, hosted_domain} & self.allowed_domains):
            raise GoogleTenantDeniedError(
                "This Google Workspace account is not authorized for DevBridge."
            )
        user_id = identity.subject
        self.repository.save_tokens(user_id, tokens)
        self.repository.save_connection(
            GoogleConnection(
                user_id=user_id,
                email=identity.email,
                hosted_domain=identity.hosted_domain,
            )
        )
        return pending.session_id, OAuthCallbackResult(connected=True, email=identity.email)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _base64_digest(value: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(value.encode()).digest()).rstrip(b"=").decode()
