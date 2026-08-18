# Authentication architecture

## Google connection

DevBridge uses Google OAuth 2.0 authorization code flow with PKCE. The extension creates an opaque installation session identifier, requests an authorization URL from the backend, and opens Google in a separate tab. The backend creates a single-use state value and PKCE verifier, exchanges the callback code, validates the verified Workspace email/domain, stores provider tokens behind a server-side repository interface, marks onboarding connected, and writes a sanitized audit event.

The browser extension never receives the OAuth client secret, authorization code, access token, or refresh token. Its opaque session identifier is not a provider credential.

Requested MVP scopes are `openid`, `email`, `profile`, and `https://www.googleapis.com/auth/script.projects`. Scope expansion requires security review. Tenant access is restricted with `DEVBRIDGE_GOOGLE_ALLOWED_DOMAINS` and will later add Google Group membership enforcement.

## Production gate

`DEVBRIDGE_GOOGLE_OAUTH_ENABLED` defaults to `false`. The current in-memory credential repository is suitable only for local adapter testing because restarts discard tokens and it does not provide durable encryption. Production OAuth must remain disabled until the repository is replaced by encrypted Firestore/Secret Manager-backed persistence and the OAuth client secret is injected from Google Secret Manager. The API returns a plain-language unavailable response while disabled.

Required configuration:

- `DEVBRIDGE_GOOGLE_OAUTH_ENABLED`
- `DEVBRIDGE_GOOGLE_OAUTH_CLIENT_ID`
- `DEVBRIDGE_GOOGLE_OAUTH_CLIENT_SECRET` (local only; Secret Manager injection in production)
- `DEVBRIDGE_GOOGLE_OAUTH_REDIRECT_URI`
- `DEVBRIDGE_GOOGLE_ALLOWED_DOMAINS`

The redirect URI must exactly match the OAuth web client configuration. For Cloud Run it will use the private service URL plus `/api/v1/onboarding/google/callback`.

## GitHub

GitHub authentication will use a GitHub App installation flow rather than shared personal access tokens. Installation tokens and private keys remain server-side and are implemented under Issue #7.
