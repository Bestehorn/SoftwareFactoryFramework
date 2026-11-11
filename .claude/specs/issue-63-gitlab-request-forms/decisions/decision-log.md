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
