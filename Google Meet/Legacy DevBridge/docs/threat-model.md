# Threat model

Primary threats include extension/page message spoofing, token theft, confused-deputy access across organizations, stale or malicious AI changes, repository and Apps Script overwrite, OAuth scope escalation, secret leakage, and supply-chain compromise. Planned mitigations include authenticated origin-bound sessions, tenant authorization on every resource, short-lived provider tokens, hash preconditions, explicit approvals, immutable audit events, dependency pinning, and least-privilege IAM.
