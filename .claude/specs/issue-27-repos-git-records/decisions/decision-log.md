# Decision Log

## DL-001 — 2026-11-11T02:56:16Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S (the issue's tier line): records and tests on #28's design; re-tier to M only for a missing record field or request form.
**Driver:** issue #27 Tier line; #28 design D8 (a slice edits its family module and test module).
**Alternatives considered:** tier M (rejected: no design choice in the ask).
**Evidence:** issue #27 body; .claude/specs/issue-28-generic-operation-command/design.md D8.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T03:25:16Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Split `repos/upload-release-asset` and the `307` re-send of `repos/update`/`repos/delete` into one issue (issue-intake, DESIGN-OPTIONS) and record the deferral of #27's "Both PENDING empty" item on #27; #27 stays tier S with `repos.PENDING` exactly `{repos/upload-release-asset}`.
**Driver:** review/spec-review-agent/iteration-01.md B1; `call` has no byte-body option, media type or route to `UPLOAD_ORIGIN` — choosing them is a design choice #28 left open.
**Alternatives considered:** re-tier #27 to M and build both under #28 D8's exceptions row (rejected: a design choice that also serves #33's `markdown/render-raw`, better made once).
**Evidence:** issue #27 Tier line; #28 design D8, Residuals; `transport.py` `Transport.upload`.
**Supersedes:** none
**Artifacts touched:** change.md, issue #27 comment

## DL-003 — 2026-11-11T03:44:10Z — issue-work-orchestrator — phase:SPEC_REVIEW

**Decision:** Approve change.md after combined review iteration 02 (READY, no findings); the Ask keeps the issue's wording, the deviation stated in AC-1, Residuals and the deferral comment.
**Driver:** review/spec-review-agent/iteration-02.md.
**Alternatives considered:** none
**Evidence:** change.md (7,994 bytes); #46 filed; deferral comment on #27.
**Supersedes:** none
**Artifacts touched:** change.md
