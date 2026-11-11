# Decision Log

## DL-001 — 2026-11-11T04:00:36Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #28's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #31 Tier line; #28 design D8 (a slice edits its family module and test module).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #31 body; .claude/specs/issue-28-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T04:00:36Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** The issue's open questions: a secret write's `encrypted_value` (and `key_id`) is supplied by the caller as a `-f` value and sent as given — the wrapper encrypts nothing (UB-2: standard library only); `code-scanning/get-analysis` is one record with the default media type, its `application/sarif+json` form a residual for #46 (non-JSON and alternative bodies).
**Driver:** issue #31 Open questions; UB-2; #28 design D2 (values are sent as given), #46's scope.
**Alternatives considered:** encrypt in the wrapper (rejected: needs LibSodium, outside the standard library); one record per media type (rejected: a record field part 1 lacks, the M trigger).
**Evidence:** issue #31 body; issue #46 body.
**Supersedes:** none
**Artifacts touched:** prompt.md, change.md

## DL-003 — 2026-11-11T04:13:09Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep `code-scanning/commit-autofix` pending: it commits to `target_ref`, the branch-writing class no subcommand sends; gating it with a `None` mapping waits for #27's mapping type (ledger row).
**Driver:** #28 design Security "Destructive operations"; `commands/call.py` `GATED_OPERATIONS` is `Mapping[str, str]` at aafecbb.
**Alternatives considered:** rebase on #27 and gate it (rejected: adds a `commands/call.py` task and a cross-branch dependency; #32 DL-002 is the precedent).
**Evidence:** docs/api-reference/github/rest/code-scanning.md "Commit an autofix for a code scanning alert"; issue-32 decisions DL-002.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T04:13:09Z — issue-work-orchestrator — phase:SPEC

**Decision:** Extend DL-002's SARIF routing to `code-scanning/get-codeql-database`: its record sends the default media type; the `application/zip` form (the database itself) is a residual for #46.
**Driver:** change.md Residuals; #46 covers non-JSON and alternative bodies.
**Alternatives considered:** keep it pending (rejected: its JSON form is documented and callable).
**Evidence:** docs/api-reference/github/rest/code-scanning.md "Get a CodeQL database for a repository".
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T04:31:28Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Route the `application/sarif+json` form of `code-scanning/get-analysis` and the `application/zip` form of `code-scanning/get-codeql-database` to the findings ledger, not #46: #46 owns request bodies, uploads and the `307` re-send, not a per-call response media type.
**Driver:** review/spec-review-agent/iteration-01.md B1; issue #46 body and its prompt.md scope.
**Alternatives considered:** widen #46 (rejected: changes another issue's ask); file a new issue (rejected: no observed failure, no caller needs the form).
**Evidence:** review/spec-review-agent/iteration-01.md B1.
**Supersedes:** DL-002 (its SARIF routing only), DL-004
**Artifacts touched:** change.md Residuals

## DL-006 — 2026-11-11T04:38:24Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 02 READY (the tier-S cap); every iteration-01 fix site applied.
**Driver:** review/spec-review-agent/iteration-02.md.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-02.md Verdict line.
**Supersedes:** none
**Artifacts touched:** change.md
