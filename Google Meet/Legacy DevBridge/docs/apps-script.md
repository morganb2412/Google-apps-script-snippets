# Apps Script integration

The Apps Script domain contains a typed `AppsScriptGateway` protocol and an `HttpAppsScriptGateway` for Google API calls. Tests use an in-memory fake gateway; no test claims a live Google connection.

## Read workflow

1. Retrieve project metadata from `script.googleapis.com/v1/projects/{scriptId}`.
2. Retrieve content from `/projects/{scriptId}/content` using a backend-held access token.
3. Normalize `SERVER_JS`, `HTML`, and `JSON` files to `.gs`, `.html`, and `.json` paths.
4. Normalize line endings and calculate per-file SHA-256 hashes.
5. Sort normalized paths and calculate a deterministic project hash.
6. Parse `appsscript.json` and validate the `oauthScopes` shape.

## Guarded write workflow

`AppsScriptService.safe_update` requires explicit approval and the exact project hash observed when the proposal was created. It retrieves current content again before writing and rejects the operation if the hash is stale. New OAuth scopes stop the write and require a separate security approval workflow. After an accepted update, the service retrieves content again, verifies the resulting project hash, and writes an audit event containing hashes and file counts but no provider tokens.

The current service boundary deliberately has no public write route. Routes are added only after authenticated session-to-Google-credential lookup and durable snapshot/audit persistence are available.

## Remaining live validation

Issue #6 remains open until a tenant OAuth connection can retrieve a real project, the manifest is observed from Google, and the guarded update workflow passes end-to-end against a non-production test script. No production project should be used for the initial write test.
