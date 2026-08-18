# Authentication

Milestone 1 defines boundaries but does not implement OAuth. Google sign-in will use authorization code flow with PKCE and server-side token exchange. GitHub uses a GitHub App installation flow rather than shared personal access tokens. Refresh tokens, installation tokens, private keys, and provider credentials stay server-side and are redacted from logs and audit metadata.
