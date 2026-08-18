# Legacy DevBridge

Legacy DevBridge is a production-oriented foundation for connecting Google Apps Script projects to GitHub and governed AI engineering workflows. Milestone 1 establishes the runnable API, Chrome extension shell, shared contracts, CI, security defaults, and deployment packaging. It intentionally does not fake Google, GitHub, or AI integrations.

## Architecture

```text
Apps Script Editor -> MV3 Extension -> FastAPI on Cloud Run
                                        |-- Apps Script API (planned)
                                        |-- GitHub App (planned)
                                        `-- Provider-neutral AI runtime (planned)
```

The extension contains no privileged credentials. Backend routes are versioned under `/api/v1`; business capabilities are separated from transport concerns. See [docs/architecture.md](docs/architecture.md).

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- Git
- Google Cloud CLI for deployment only

## Backend development

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
ruff check .
mypy app
```

The API is available at `http://127.0.0.1:8000`; health is at `/api/v1/health`.

## Extension development

```bash
cd extension
npm install
npm run dev
npm run typecheck
npm run lint
npm run test
npm run build
```

Load `extension/dist` via Chrome's **Extensions > Developer mode > Load unpacked**. The extension is scoped to `https://script.google.com/*` and calls the API base configured through `VITE_API_BASE_URL`.

## Configuration

Copy `.env.example` to `.env` for local development. Never commit `.env` or credentials. Production secrets belong in Google Secret Manager and are injected into Cloud Run.

## Authentication architecture

Google OAuth and GitHub App credentials will be handled server-side. The browser will receive only short-lived, least-privilege session material. Tokens and private keys must never be logged or stored in extension local storage. Details: [docs/authentication.md](docs/authentication.md).

## Current status

Milestone 1 includes the API health endpoint, extension navigation shell and API status, shared schema, tests, lint/type/build configuration, container, Cloud Build definition, CI, standards, and architecture/security documentation. Real account connections and project detection begin in later milestones.

## Roadmap

1. Apps Script page detection and project context
2. Guided onboarding and connection health
3. Apps Script and GitHub service integrations
4. Safe comparison/synchronization engine
5. Source-control workflows and governed AI Engineer

## Cloud Run

From the repository root with an authenticated `gcloud` CLI:

```bash
cd "Google Meet/Legacy DevBridge"
gcloud builds submit --project=moesautomationweekly --config=cloudbuild.yaml .
```

This builds and deploys only the backend service. The extension remains a separately built client artifact.
