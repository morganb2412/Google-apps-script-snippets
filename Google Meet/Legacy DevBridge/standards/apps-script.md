# Apps Script standards

- Use the V8 runtime and `PropertiesService` for runtime configuration.
- Normalize source before comparison and preserve `appsscript.json` as a security-sensitive file.
- Never overwrite conflicts or stale source automatically.
