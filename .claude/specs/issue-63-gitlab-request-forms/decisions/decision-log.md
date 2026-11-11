# Decision Log

## DL-001 — 2026-11-11T12:57:39Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M: six request forms across `gitlab_api/registry.py`, `transport.py`, `commands/call.py` and the contract test, each a design choice, plus the records of the keys they unblock; the spec is written now and implementation waits for #40 and #43 to land, then this branch rebases.
**Driver:** issue #63 "Tier: M" and "Filing-rationale: DESIGN-OPTIONS"; proportionality.md (a feature across several components with a design choice).
**Alternatives considered:** one issue per form (rejected: one ask, one coverage criterion, shared registry and contract changes).
**Evidence:** issue #63 body (Forms and keys, Where, Open questions).
**Supersedes:** none
**Artifacts touched:** prompt.md, qa_log.md

## DL-002 — 2026-11-11T13:18:28Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** The reference settles four of the issue's open questions in requirements (F1 endpoints are the spans on a section's first line, method included; F2's second `:id` is the certificate or token; F3 `.format` is an optional suffix from the documented list; F5 headers are the section's `Request headers` line and `In: header` rows) and leaves every mechanism to design; token information is the configured origin outside `/api/v4`, not another origin.
**Driver:** issue #63 Open questions; requirements.md Glossary and Requirements 2-7.
**Alternatives considered:** none
**Evidence:** docs/api-reference/gitlab/ sections the requirements cite (operations-index.md header on `https://HOST` paths).
**Supersedes:** none
**Artifacts touched:** requirements.md
