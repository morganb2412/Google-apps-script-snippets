# Architecture

## Milestone 1 decision record

Legacy DevBridge is a modular project embedded in the existing snippets repository. The deployable product is isolated under `Google Meet/Legacy DevBridge/`; repository-level workflows use subdirectory working directories.

The FastAPI application uses versioned routes, Pydantic boundary models, application services, and dependency injection. Future domains (`auth`, `agents`, `appsscript`, `github`, `sync`, `policies`, `organizations`, `onboarding`, and `audit`) will be added as independently testable packages when their milestones begin rather than as empty behavior.

The React MV3 extension uses a side panel so it can accompany the Apps Script editor without injecting privileged logic into the page. Content-page detection is deliberately deferred to Milestone 2. External credentials remain exclusively on the backend.

## Trust boundaries

```text
Untrusted Apps Script page
        | constrained project context
Unprivileged extension
        | authenticated HTTPS API requests
Cloud Run API
        | provider adapters + server-side credentials
Google / GitHub / AI providers
```

Cloud Run is stateless. Production persistence will use repository interfaces compatible with Firestore. Production secrets will be referenced from Secret Manager, never baked into images.
