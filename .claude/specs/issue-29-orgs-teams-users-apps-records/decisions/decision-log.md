# Decision Log

## DL-001 — 2026-11-11T03:59:22Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #28's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #29 Tier line; #28 design D8 (a slice edits its family module and test module).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #29 body; .claude/specs/issue-28-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T03:59:22Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** The issue's open questions: an `apps` record that authenticates as the app (JWT, client ID and secret) is declared and sent with the configured token like every record (UB-2: no other credential), its real-forge proof being #28 D5's method; the target is the `operations-index.md` committed at the worktree's base.
**Driver:** issue #29 Open questions; UB-2; #28 design D5.
**Alternatives considered:** leave app-authenticated ids pending (rejected: AC-1 wants every PENDING empty, and a record sends nothing a caller does not ask for).
**Evidence:** issue #29 body; docs/api-reference/github/conventions.md "Authentication".
**Supersedes:** none
**Artifacts touched:** prompt.md, change.md

## DL-003 — 2026-11-11T04:28:57Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 01 READY (0 A, 0 B); its C1–C3 and D1–D2 are applied in one author pass (C1 deletes the false bulk-list cursor residual, so no ledger row for it).
**Driver:** review/spec-review-agent/iteration-01.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-01.md Verdict line.
**Supersedes:** none
**Artifacts touched:** change.md
