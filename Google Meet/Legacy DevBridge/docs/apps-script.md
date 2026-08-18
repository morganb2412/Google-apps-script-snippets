# Apps Script integration

Milestone 2 detects project context from supported Apps Script editor URLs and the document title. Detection is read-only and does not retrieve project files or OAuth tokens. The Apps Script adapter planned for Milestone 4 will expose typed reads and guarded writes. Writes require retrieval, normalization, SHA-256 comparison, snapshot metadata, diff, approval, update, re-read verification, and audit. `appsscript.json` scope changes are security-sensitive.
