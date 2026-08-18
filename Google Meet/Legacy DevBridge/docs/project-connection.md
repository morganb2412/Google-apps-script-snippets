# Project mapping and Add to GitHub

`ProjectMapping` is the durable relationship between a DevBridge user, optional organization, Apps Script project, GitHub App installation, repository, active/default branches, standards profile, AI provider profile, timestamps, and the last verified synchronization base hash. The in-memory repository is for local development; its document shape and user/project key are designed for a Firestore adapter.

## Create and connect

1. Reject an Apps Script project that already has a mapping.
2. Retrieve and hash the current Apps Script snapshot.
3. Create an empty organization repository through the session-owned GitHub installation.
4. Create Git blobs, one tree, one initial commit, and the default branch atomically through GitHub's Git Data API.
5. Retrieve the repository snapshot and normalize it into the same SHA-256 representation as Apps Script.
6. Refuse to create the mapping if GitHub does not match the imported snapshot.
7. Save the mapping and synchronization base, then write a sanitized audit event.

## Connect existing repository

1. Retrieve Apps Script and repository snapshots without writing either source.
2. Compare file paths and hashes and return the changed paths in a confirmation proposal.
3. Require an explicit confirmation referencing that proposal.
4. Retrieve both sources again and reject the connection if either hash changed after comparison.
5. Save the mapping. A synchronization base is recorded only when both initial states are identical.

No automatic conflict resolution or source overwrite occurs during first connection.

## Remaining production wiring

Authenticated routes are intentionally withheld until the backend can resolve the opaque session to durable Google credentials and a durable GitHub installation mapping. Firestore persistence, live route authorization, UI repository selection, and end-to-end provider verification remain open in Issue #8.
