# Architecture

## Milestone 1 decision record

Legacy DevBridge is a modular project embedded in the existing snippets repository. The deployable product is isolated under `Google Meet/Legacy DevBridge/`; repository-level workflows use subdirectory working directories.

The FastAPI application uses versioned routes, Pydantic boundary models, application services, and dependency injection. Future domains (`auth`, `agents`, `appsscript`, `github`, `sync`, `policies`, `organizations`, `onboarding`, and `audit`) will be added as independently testable packages when their milestones begin rather than as empty behavior.

The React MV3 extension uses a side panel so it can accompany the Apps Script editor without injecting privileged logic into the page. A minimal content script recognizes supported editor URLs and titles, then sends typed project context through the background worker. It does not inspect or modify source code. External credentials remain exclusively on the backend.

## Milestone 2 context flow

```text
Apps Script editor URL + title
        | minimal content script
Tab-scoped background context
        | typed extension message
React side panel
        | optional validation
POST /api/v1/projects/context/validate
```

Detection supports `/home/projects/{scriptId}` and `/d/{scriptId}` editor URL forms. Context contains only the project ID, normalized display name, editor URL without query parameters, and detection time.

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
