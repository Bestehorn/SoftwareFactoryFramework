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

## DL-003 — 2026-11-11T13:50:35Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Design D1-D9 as authored: F1 several records per ID chosen by `call --endpoint 'METHOD path'`; F2 `positional_names` with `--path id=` repeated in path order; F3 `suffix_values` and `--path format=`; F4 host-root `Base`, the registry origin from `container_registry_image_prefix`, its token from `/jwt/auth` by HTTP Basic (`GET /user` username, or `gitlab-ci-token` for a job token) sent only to the configured origin, a `bearer` token refused; F5 `Location.HEADER` and `--header`; F6 a FORM-body record and N's widened `PARENT_KEY`.
**Driver:** requirements.md Requirements 2-7 (mechanisms left to design); issue #63 Open questions.
**Alternatives considered:** a registry host in `config/gitlab.json` (rejected: UB-2 keeps the config to the instance and token); one record per ID with an endpoint table (rejected: V's `record_key_problems` already accepts several keys per Reference).
**Evidence:** design.md D1-D9; docs.gitlab.com `authenticate_with_container_registry`, `api/container_registry`, `api/projects` (`container_registry_image_prefix`); RFC 7617, RFC 9110 sections 5.1 and 5.5.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-004 — 2026-11-11T13:50:35Z — issue-work-orchestrator — phase:DESIGN

**Decision:** Restate UB-1 (an existing assertion that pins what this change retires, such as a key's pending state, one record per ID, a JSON-only body or a table without `Symbolchecksum`, is restated to the new state) and UB-3 (one `None` gate for the S3 import), before the design review opens.
**Driver:** design author: AC-1.1 and AC-6.1 contradict UB-1's "no existing assertion edited"; the S3 import writes into an existing project (#38 DL-005) and the orchestrator settled its gate.
**Alternatives considered:** keep the S3 key pending (rejected: AC-1.1 maps it, F6 needs a record to prove).
**Evidence:** design.md D9 (the restated tests); #38 DL-004, #37 DL-005 (the same restatement).
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-005 — 2026-11-11T14:22:51Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Apply all of iteration 01's findings (7 B, every C and D) in one author pass; the GitLab real-instance run is #11's (devops B1); delta review iteration 02 goes to the four NOT-READY lanes only.
**Driver:** review/review-latest.md (iteration 01: 0 A, 7 B; security and best-practice READY).
**Alternatives considered:** none
**Evidence:** review/<lane>/iteration-01.md; issue #10 Ask ("GitHub first"), issue #11 work item "Real-GitLab integration tests".
**Supersedes:** none
**Artifacts touched:** requirements.md, design.md, prompt.md

## DL-006 — 2026-11-11T14:42:25Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Apply iteration 02's findings (spec B1 = test B3 the map test's spellings; the C/D items) in one author pass; standards and devops are READY at iteration 02, so iteration 03 goes to spec-review-agent and test-architect only.
**Driver:** review/<lane>/iteration-02.md (spec 1 B, test 1 B, standards READY, devops READY).
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-02.md B1; review/test-architect/iteration-02.md B3.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-007 — 2026-11-11T14:46:38Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md and design.md at iteration 03: every lane READY with 0 A and 0 B (security and best-practice at 01, standards and devops at 02, spec-review and test-architect at 03); scope frozen.
**Driver:** review/<lane>/iteration-0N.md verdicts.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-03.md, review/test-architect/iteration-03.md (30 COVERED, 0 GAP).
**Supersedes:** none
**Artifacts touched:** review/review-latest.md

## DL-008 — 2026-11-11T15:43:17Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md at tasks iteration 02 (both lanes READY, 0 A, 0 B; 30 criteria covered); AC-5.3's failure path moves to wave-2 task 2.12 after its test 2.5, wave 3 runs every GitLab suite; implementation waits for #43's PR #65 to merge, then this branch rebases.
**Driver:** review/spec-review-agent/tasks-iteration-01.md B1, review/test-architect/tasks-iteration-01.md B1 B2; both tasks-iteration-02.md READY.
**Alternatives considered:** none
**Evidence:** review/<lane>/tasks-iteration-02.md.
**Supersedes:** none
**Artifacts touched:** tasks.md
