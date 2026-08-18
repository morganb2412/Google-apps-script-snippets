# Git synchronization

The synchronization engine compares three normalized snapshots: current Apps Script, current GitHub, and the last state verified on both sides. This three-way base is required to distinguish one-sided edits from true conflicts.

## States

- `IDENTICAL`
- `LOCAL_MODIFIED`
- `REMOTE_MODIFIED`
- `LOCAL_ADDED`
- `REMOTE_ADDED`
- `LOCAL_DELETED`
- `REMOTE_DELETED`
- `CONFLICT`

When no common base exists, different content at the same path is a conflict. When a base exists, edits on both sides or a deletion opposed by an edit are conflicts. DevBridge never guesses a winner.

## Directional merge plans

A pull applies only remote modifications, additions, and deletions to a copy of the current Apps Script snapshot. Independent local-only changes remain intact. A push performs the inverse for GitHub. Each operation contains its path, write/delete operation, state, and unified line diff.

Plans capture both source hashes and require explicit approval. Immediately before applying, the service retrieves both snapshots again and rejects the plan if either hash changed. The destination adapter must also enforce its expected hash. After applying, DevBridge re-reads the destination and verifies the planned target hash.

The common sync base advances only when Apps Script and GitHub are identical after the operation. This allows independent changes to be synchronized safely in two directional operations without losing three-way history.

## Production wiring remaining

The engine and coordinator are fully tested behind `SyncStatePort`. Authenticated provider adapters, durable Firestore sync bases/plans, live routes, and extension rendering remain open. Conflicting code can never be applied through the generic pull or push workflow; it requires the later explicit conflict-resolution flow.
