# Decision Log

## DL-001 — 2026-11-11T15:44:05Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S, one wave: records for the keys the GitLab slices kept pending, the branch and existing-project writers refused by a `None` entry in `commands/call.py` `GATED_OPERATIONS`, and `orbit`'s glob read sent; the spec is written now and implementation waits for #43 and #63 to land.
**Driver:** issue #15 AC-3 ("pending list SHALL be empty"); the kept-key comments in the families' `PENDING` on origin/main 70c4dba; #63's Ask ("Not part of this: the gated kept ids").
**Alternatives considered:** a separate child issue (rejected: the last slice of #15's own AC-3, one existing mechanism, no design choice).
**Evidence:** src/payload/scripts/gitlab_api/families/*.py `PENDING` on 70c4dba; #44 design (the `None` gate form).
**Supersedes:** none
**Artifacts touched:** prompt.md, qa_log.md

## DL-002 — 2026-11-11T16:35:53Z — issue-work-orchestrator — phase:SPEC

**Decision:** Approve change.md at combined review iteration 02 (READY, 0 A, 0 B): 25 kept keys, 22 writers refused by a `None` gate whose constants are `OP_` plus the anchor in upper snake case, 3 reads (orbit's glob, verify's two artifact downloads) sent; `tenant-scale#update-a-project` stays callable with one open ledger row.
**Driver:** review/iteration-01.md B1 (agent_foundations Kinds), B2 (constant names); review/iteration-02.md READY.
**Alternatives considered:** gating `tenant-scale#update-a-project` too (rejected: an existing callable record; outside this ask).
**Evidence:** review/iteration-02.md; change.md AC-1..AC-4.
**Supersedes:** none
**Artifacts touched:** change.md
