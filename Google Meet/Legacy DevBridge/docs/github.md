# GitHub App integration

DevBridge uses a GitHub App rather than shared personal access tokens. The extension requests an installation URL from the backend and opens GitHub in a separate tab. A single-use state value binds the GitHub setup callback to the opaque DevBridge extension session. The backend retains the resulting installation ID; the extension never chooses installation IDs or receives installation tokens.

## Authentication

`PyJwtGitHubSigner` creates an RS256 application JWT with a backdated issue time and an expiration below GitHub's ten-minute maximum. `GitHubInstallationAuth` exchanges that JWT for a short-lived installation token and caches the token only until two minutes before expiration. Tokens and private keys use redacted Pydantic fields and are never placed in audit metadata.

Production configuration is disabled by default with `DEVBRIDGE_GITHUB_APP_ENABLED=false`. The private key must be injected from Google Secret Manager into the Cloud Run service; it must never be committed or sent to the extension. The current in-memory installation mapping must be replaced by Firestore persistence before production enablement.

## Repository API boundary

The typed gateway supports:

- listing repositories available to an installation;
- retrieving repository metadata;
- creating an organization repository;
- listing branches and their protected status;
- creating a branch from an explicit commit SHA;
- retrieving and decoding a repository file at an explicit ref.

Repository and branch creation emit sanitized audit events. GitHub 401/403 responses become a reconnect message, 404 responses become a missing-resource message, and other failures become a retryable availability message. Protected branches are exposed but never bypassed.

Creating a repository under an individual account may require a separate GitHub user OAuth grant; the MVP implementation starts with organization repositories available to the GitHub App and does not pretend an installation token can perform unsupported user-scoped operations.

## Remaining live validation

Issue #7 remains open until the private GitHub App is registered, its setup URL points to `/api/v1/onboarding/github/callback`, its private key is supplied through Secret Manager, installation mapping is durable, and repository/branch/file operations pass against a non-production test repository.
