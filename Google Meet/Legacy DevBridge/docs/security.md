# Security

The extension contains no privileged secrets. Cloud Run uses least-privilege service identity, Secret Manager references, explicit CORS, and non-root containers. Sensitive values must be redacted from structured logs and audit metadata. Write operations will add authenticated authorization, idempotency, stale-state validation, approval records, and post-write verification before they are enabled.

Milestone 1 exposes only a non-sensitive health route. Debug documentation is disabled in production.
