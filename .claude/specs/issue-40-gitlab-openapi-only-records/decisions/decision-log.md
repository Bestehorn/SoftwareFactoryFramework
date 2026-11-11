# Decision Log

## DL-001 — 2026-11-11T07:56:44Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M (the issue's tier line): records plus the glob, optional-segment and OData path forms in `registry.py`; the three `ml_models` file keys of `families/deploy.py` (they link to `rest/openapi-only.md` and need the optional segment) join this slice from #38, so the form and its records land together.
**Driver:** issue #40 Tier line and Ask ("the other three (`ml_models` files) belong to `deploy`"); issue #38 open question on deploy's `(*path/)` keys; #43 needs the glob too.
**Alternatives considered:** the forms in #38 or #43 (rejected: #40's Tier line owns them, and it holds most glob keys); deploy's keys kept in #38 (rejected: #38 would need the form too).
**Evidence:** issue #40 body; issue #38 body; src/payload/scripts/gitlab_api/registry.py `PLACEHOLDER`, `expand`.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** No exclusions: the Workhorse `authorize`, runner, Geo-internal and admin routes get records like the rest (AC-1.1); #41 D5's unreachable arm proves the ones a test project cannot reach.
**Driver:** issue #40 open question; #41 Requirement 6, DL-001, D6 ("one rule, with no exclusion"), D5's path arm.
**Alternatives considered:** an exclusion list in the coverage test (rejected: #41 D8, a slice never edits it).
**Evidence:** .claude/specs/issue-41-gitlab-generic-operation-command/design.md D5, D6, D8; test/test_gitlab_wrapper_contract.py `test_the_unreachable_rule_has_two_arms`.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-003 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** The three `ml_models` records go in `families/deploy.py` with `deploy#` ids; a glob or optional-group name is a path parameter whatever its `In` column says; a GET whose table has `page`/`per_page` query rows is `Paging.OFFSET`; a glob value with an empty, `.` or `..` part is refused, the existing one-segment rule applied to each part.
**Driver:** index rows link each `ml_models` key to `rest/deploy.md` and `rest/openapi-only.md`, `key_families` assigns them to deploy (#13 D2); the glob sections list the name as query/body/form; conventions.md "Offset-based"; registry.py `REFUSED_SEGMENTS`.
**Alternatives considered:** `openapi-only#` ids for the deploy records (rejected: the prefix would name another module); allowing traversal parts in a glob (rejected: the segment rule exists for that).
**Evidence:** docs/api-reference/gitlab/operations-index.md; rest/openapi-only.md glob sections; registry.py `_segment`.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-004 — 2026-11-11T08:20:12Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** Upload records follow their entries (multipart through `--file`); the raw-bytes generic-package body, the NuGet `Symbolchecksum` header and the `openapi-only#` `status` attribute are residuals; `GATED_OPERATIONS` is unchanged (no key ends in `/merge` or creates an issue); the design names the `commands/call.py` edit an optional path parameter needs.
**Driver:** commands/call.py docstring, registry.encode, transport.request_body (no raw body); conventions.md "Generic packages"; both PENDING sets read in full; call.py reads documented and missing names from `registry.placeholders`.
**Alternatives considered:** a raw-body form here (rejected: DL-001 and prompt.md name only the path forms).
**Evidence:** requirements.md Residuals, UB-4; src/payload/scripts/gitlab_api/commands/call.py.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-005 — 2026-11-11T08:37:16Z — issue-work-orchestrator — phase:DESIGN

**Decision:** `PLACEHOLDER` gains a `[:*]` sigil; `OPTIONAL_GROUP` and `ESCAPED_PARENTHESIS` patterns; `required_placeholders` and `_glob` (the one-segment check and `quote(safe="")` per part) in registry; `expand` resolves groups, then unescapes, then substitutes, so no value is read as template syntax; an empty value for a group parameter is refused.
**Driver:** requirements AC-2.1..AC-2.6; registry.py `PLACEHOLDER`, `_segment`, `expand`; RFC 3986 §2.2, §3.3; a scan found no existing record path with `*`, `(` or a backslash (UB-4).
**Alternatives considered:** a parsed path-template type (rejected: every reader of `placeholders` changes); a separate glob regex (rejected: loses path order).
**Evidence:** design.md D1.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-006 — 2026-11-11T08:37:16Z — issue-work-orchestrator — phase:DESIGN

**Decision:** `commands/call.py`'s `missing_path_parameters` reads `registry.required_placeholders` (the one call.py edit, where #41 D8's "never" row yields); N gains the `*` sigil, group/escape handling in `expanded_path` and one test for the path forms; deploy's three records get a new `src/payload/test/test_gitlab_api_deploy.py`; AC-2.1/AC-2.2 each get a Hypothesis property in `test/test_gitlab_api_properties.py`.
**Driver:** requirements AC-2.3, AC-2.4 (an optional parameter may be named but is not required); #41 D8 (a slice may edit registry.py and N for a new request form); testing.md item 3.
**Alternatives considered:** shrinking `placeholders` (rejected: `--path path=` refused, AC-2.4); defaulting in `expand` (rejected: `call` still refuses, AC-2.3).
**Evidence:** design.md D2, D3, D5; src/payload/scripts/gitlab_api/commands/call.py `missing_path_parameters`.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-007 — 2026-11-11T08:52:23Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Build the raw-body form in this slice: the Workhorse body-upload routes (generic package, Terraform module, Terraform state, and the ML-model file upload per its route) send the file's bytes as the request body with their documented query values, through a `call --input FILE|-` modelled on GitHub's #46 (a record-level media type; `--input` refused beside `-f/-F` and on a JSON record); the job-artifacts upload stays multipart; requirements AC-3.2 and its Residual are restated to match.
**Driver:** issue #40 Tier line and work item 1 name "the glob, optional-segment and raw-body forms"; review/spec-review-agent/iteration-01.md A1 and review/best-practice-reviewer/iteration-01.md A1 (Workhorse `routes.go` `requestBodyUploader`, `body_uploader.go` store the raw body).
**Alternatives considered:** keep the four uploads pending with a residual (rejected: the ask names the raw-body form); declare them multipart (rejected: GitLab stores the envelope as the file).
**Evidence:** review/*/iteration-01.md A1; .claude/specs/issue-46-github-call-raw-bodies/design.md D1-D4 (merged precedent, on the GitHub branch).
**Supersedes:** DL-004 (its raw-body clause only)
**Artifacts touched:** requirements.md, design.md

## DL-008 — 2026-11-11T09:23:47Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** The raw-body records (generic package, Terraform module, Terraform state, `deploy#send-the-file`) declare no `file` `Param`, read their other body rows as `Location.QUERY`, and send `application/octet-stream`; N finds the raw-body row by its name `file`; no refusal beyond `--input` beside `-f/-F` and on any other record; raw bytes tested by examples (a CRLF and a non-UTF-8 byte), not a property; #41 D8 yields for `call.py`'s `--input`, N's `documented_raw_body` and the `gitlab_wrapper.py` usage lines.
**Driver:** Workhorse `routes.go` (`requestBodyUploader` for `packages/ml_models/` too) and `body_uploader.go` (`RequestBody` drops the original body); conventions.md gives `status` and `select` as query attributes; transport.py `CONTENT_TYPE_OCTET_STREAM`.
**Alternatives considered:** a FILE `Param` on the raw records (rejected: `--file` would still send the envelope); a Hypothesis property over bytes (rejected for now: examples pin the two bytes that break text handling; reversible).
**Evidence:** design.md D4, D5, D6; requirements.md AC-3.2; review/review-latest.md A1.
**Supersedes:** none
**Artifacts touched:** requirements.md, design.md

## DL-009 — 2026-11-11T09:43:17Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md and design.md after design review iteration 03: every lane READY (test, spec and standards at iteration 03; security, best-practice, devops at iteration 02 or 01); the last C (K's both-bodies oracle names `--query` too) applied by the conductor as the lanes' sentence; the D6 Tests section is what DL-006's "D5" pointed to before the renumbering.
**Driver:** review/{test-architect,spec-review-agent,standards-reviewer}/iteration-03.md; review/security-reviewer/iteration-02.md; review/best-practice-reviewer/iteration-02.md; review/devops-iac-reviewer/iteration-01.md.
**Alternatives considered:** none
**Evidence:** the lane files' Verdict lines.
**Supersedes:** none
**Artifacts touched:** design.md

## DL-010 — 2026-11-11T10:23:19Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 01 (both lanes READY, 0 A, 0 B; the C/D applied, 14,965 B); three waves, `call.py` with the records in wave 2 because neither goes green alone.
**Driver:** review/test-architect/tasks-iteration-01.md; review/spec-review-agent/tasks-iteration-01.md.
**Alternatives considered:** four waves (rejected by both lanes' reading: K's new tests need the records, F's and G's need `call.py`).
**Evidence:** both tasks-iteration-01.md Verdict lines.
**Supersedes:** none
**Artifacts touched:** tasks.md

## DL-011 — 2026-11-11T13:16:59Z — issue-work-orchestrator — phase:VERIFY

**Decision:** Pin the verifier's two surviving mutants with tests before the merge (K `test_a_raw_body_beside_a_field_is_refused_first`, T `test_a_raw_body_answered_429_is_retried`), no product file changed; M1.03/M1.04 stay as equivalent mutants and wave 3's text needs no pin.
**Driver:** refutation-report.md rows M2.03 and M1.25 (D5 "first" and `request_raw` through `_send` pinned by no test); issue-filing-discipline.md branch 2 (small and clear, fix now).
**Alternatives considered:** ledger rows (rejected: a few lines of test, no design choice).
**Evidence:** evidence/green/rework-1.txt (285 passed); each test failed under its mutant (implementer report).
**Supersedes:** none
**Artifacts touched:** src/payload/test/test_gitlab_api_call.py, src/payload/test/test_gitlab_api_transport.py
