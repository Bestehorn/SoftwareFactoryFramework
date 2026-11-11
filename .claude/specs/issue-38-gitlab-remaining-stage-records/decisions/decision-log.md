# Decision Log

## DL-001 — 2026-11-11T07:56:44Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S, re-tiered down from the issue's M: the only design element of the ask is the optional `(*path/)` segment of deploy's three `ml_models` keys, and those keys move to #40, which owns that form; the rest is data records on #41's design in one cycle (the issue's split question: one cycle, the records are transcription).
**Driver:** issue #38 Tier line and open questions; issue #40 Tier line (owns "the glob, optional-segment and raw-body forms part 1 left to #15") and Ask (the `ml_models` keys "belong to `deploy`"); #42 delivered 219 records in five modules as tier S.
**Alternatives considered:** tier M building the segment form here (rejected: it would duplicate #40's form); splitting along the work items (rejected: no design choice separates them).
**Evidence:** issues #38 and #40 bodies; .claude/specs/issue-41-gitlab-generic-operation-command/design.md D8; #40 DL-001.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:SPEC

**Decision:** Keep 18 keys pending: other endpoints of several-endpoint References, the four two-`:id` group token paths, the orbit glob (to #40), the S3 import's two-level rows N cannot read, and the flow trigger/restart and the two imports that write into an existing project; everything else gets a record (286).
**Driver:** change.md author's read-only analysis through N's `reference_sections`, `index_rows`, `page_headings`; GitLab docs (Flows API, Developer Flow, project import/export; issue 425798).
**Alternatives considered:** declaring the existing-project imports (rejected: they create issues or MRs in a project, with no no-subcommand gate on GitLab).
**Evidence:** change.md AC-2, Residuals; test/test_gitlab_wrapper_contract.py `PARENT_KEY`, `endpoint_problems`.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:SPEC

**Decision:** Records follow V's family rule: the three tenant-scale References whose keys sort to developer_experience live there; "List" sections answering one object are `Paging.NONE`, GETs with a `page` row are `OFFSET`; `growth#force-a-variant-assignment` is `BodyFormat.FORM`; `FILE` follows a Notes cell beginning "file upload".
**Driver:** test/test_gitlab_wrapper_coverage.py `key_families`, `record_key_problems`; the Sidekiq, Service Ping, orbit, agent-privileges and pending-migrations pages; #41 D5 (rows with no parent).
**Alternatives considered:** `FILE` from `In form` (rejected: several `form` rows are text).
**Evidence:** change.md AC-3..AC-5; rest/<stage>.md sections.
**Supersedes:** none
**Artifacts touched:** change.md

## DL-004 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:SPEC

**Decision:** Edit N's `test_an_unreachable_call_matches_its_reference_section` only so its synthetic `gitlab-dedicated#update-a-geo-site` record replaces the one this slice declares, assertions unchanged — the one departure from #41 D8's "never" row, as #37 restated K.
**Driver:** once declared, `registry.lookup` would find the id twice and `call` exit 2; keeping `PUT /geo_sites/:id` pending contradicts the ask.
**Alternatives considered:** keep the key pending (rejected: the ask).
**Evidence:** test/test_gitlab_wrapper_contract.py `test_an_unreachable_call_matches_its_reference_section`; #37 DL-005 (K restated for the same reason).
**Supersedes:** none
**Artifacts touched:** change.md

## DL-005 — 2026-11-11T08:53:03Z — issue-work-orchestrator — phase:SPEC

**Decision:** The imports kept pending are the three that write into an existing project (`gitlab-dedicated#import-project-resources`, and the local and remote archive imports, which take `overwrite`); the S3 import is kept for its two-level rows N cannot read; the importers into a new project (`#import-repository-from-github`, `#import-repository-from-bitbucket-server`, `#import-repository-from-bitbucket-cloud`, `#start-a-group-or-project-migration`) get records, as #35 kept only the existing-project writes.
**Driver:** review/iteration-01.md C3; change.md AC-2.
**Alternatives considered:** none
**Evidence:** review/iteration-01.md C3; change.md AC-2, Residuals.
**Supersedes:** DL-002 (its import list only)
**Artifacts touched:** change.md

## DL-006 — 2026-11-11T08:57:23Z — issue-work-orchestrator — phase:SPEC

**Decision:** Approve change.md after combined review iteration 02 READY (B1, C1-C3, D1 closed; 7,981 B).
**Driver:** review/iteration-02.md verdict.
**Alternatives considered:** none
**Evidence:** review/iteration-01.md; review/iteration-02.md.
**Supersedes:** none
**Artifacts touched:** change.md
