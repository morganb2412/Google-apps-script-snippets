# Legacy DevBridge

Legacy DevBridge is a production-oriented foundation for connecting Google Apps Script projects to GitHub and governed AI engineering workflows. Milestone 1 establishes the runnable API, Chrome extension shell, shared contracts, CI, security defaults, and deployment packaging. It intentionally does not fake Google, GitHub, or AI integrations.

## Architecture

```text
Apps Script Editor -> MV3 Extension -> FastAPI on Cloud Run
                                        |-- Apps Script API adapter
                                        |-- GitHub App adapter
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

### Test in Apps Script

1. Build the extension with `npm run build` from `extension/`.
2. Open `chrome://extensions`, enable **Developer mode**, and choose **Load unpacked**.
3. Select the `extension/dist` directory.
4. Open or reload a project at `https://script.google.com/home/projects/<project-id>/edit`.
5. Pin and click **Legacy DevBridge** in Chrome's extension menu.
6. Confirm the side panel shows the project title and ID. The repository remains **Not connected** until the GitHub integration milestone.

The extension includes the isolated Apps Script toolbar, guided onboarding, and an explicitly labeled Demo Workspace covering repository, branch, commit, pull request, comparison/diff, conversational code assistance, standards, and health workflows. Demo actions perform no external writes. Follow [docs/demo-script.md](docs/demo-script.md).

After rebuilding, use the extension card's **Reload** button and reload the Apps Script tab so its content script is refreshed.

For tenant-only distribution, build the private package with `npm run package:private` and follow [docs/private-tenant-deployment.md](docs/private-tenant-deployment.md). The listing should use private domain visibility and a pilot Google Group; it does not need to be public.

## Configuration

Copy `.env.example` to `.env` for local development. Never commit `.env` or credentials. Production secrets belong in Google Secret Manager and are injected into Cloud Run.

## Authentication architecture

Google OAuth and GitHub App credentials will be handled server-side. The browser will receive only short-lived, least-privilege session material. Tokens and private keys must never be logged or stored in extension local storage. Details: [docs/authentication.md](docs/authentication.md).

## Current status

Version 0.10 includes the API and extension foundations, Apps Script editor detection, tenant OAuth and GitHub App handshakes behind disabled production gates, typed provider adapters, guarded Apps Script writes, and project mapping/Create-or-Connect orchestration. Provider credentials, durable Firestore mappings, authenticated live routes, and end-to-end connection tests are not yet complete and are never simulated as production success.

## Roadmap

1. Apps Script page detection and project context
2. Guided onboarding and connection health
3. Apps Script and GitHub service integrations
4. Safe comparison/synchronization engine
5. Source-control workflows and governed conversational Code Assistant

## Cloud Run

From the repository root with an authenticated `gcloud` CLI:

```bash
cd "Google Meet/Legacy DevBridge"
gcloud builds submit --project=moesautomationweekly --config=cloudbuild.yaml .
```

This builds and deploys only the backend service. The extension remains a separately built client artifact.
