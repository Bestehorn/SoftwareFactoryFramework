# Test architect — tasks review, iteration 01

Reviewed: `tasks.md` against the approved `design.md` (§ Correctness Properties, § Acceptance Criteria Mapping, D9,
D12) and the frozen `requirements.md`. The base was read in the issue-43 worktree: R, T, K, P, N, the family
suites, `test/test_gitlab_graphql_contract.py`, `src/payload/test/test_gitlab_api_graphql_only.py`,
`.claude/hooks/red_for_right_reason.py` and `.claude/specs/_workflow/phases/spec-phase-tasks.md`.

## Findings

### B1 — AC-5.3 is implemented in wave 1, but its only test comes in wave 2
Severity: B
Location: tasks.md § Wave 1, 1.7 and 1.8; § Wave 2, 2.5
Defect: 1.7 (the registry token in no URL, log record or exception message) and 1.8 (each failure of AC-5.3 a
  `GitLabAPIError` before step 4) both list AC-5.3 under Validates. No wave-1 TEST task validates AC-5.3, because G
  (1.4) checks only the job-token login. The only AC-5.3 test is F:package
  `test_no_registry_token_sends_nothing_to_the_registry` (2.5). In wave 2 that test fails only because the package
  records are missing, which gives exit 2 where it expects 1. So no red capture ever shows the failure path failing
  before its code exists. Wave 1's mutant kill also cannot catch it: stub out the checks and wave 1's paired tests
  still pass. And when 2.5 fails at green, no wave-2 IMPL task owns `container_registry.py` or `transport.py`.
Material-because: AC-5.3. Its code is written before any test of it, which breaks spec-phase-tasks.md "Test-first
  inside each wave: every TEST task precedes the IMPL task it pairs with". It also breaks the preamble's "minimal code
  that turns them green": 1.8 adds checks that no wave-1 test needs.
Proposed-edit: In 1.7, delete "; the registry token enters no URL, log record or exception message" and drop AC-5.3
  from its Validates. In 1.8, replace "`send` and its four steps, each failure of AC-5.3 a `GitLabAPIError` before
  step 4; the module docstring" with "`send` and its four steps on the answers they expect; the module docstring",
  Validates: AC-5.2, UB-2. Add "2.12 IMPL: `container_registry.py` and `transport.py` per D4 AC-5.3 — each failure
  of AC-5.3 a `GitLabAPIError` before step 4; the registry token in no URL, log record or exception message. —
  Files: src/payload/scripts/gitlab_api/container_registry.py, src/payload/scripts/gitlab_api/transport.py —
  Validates: AC-5.3, UB-2". The file sets of 2.7 to 2.12 stay disjoint. The Coverage table needs no change.

### B2 — Wave 3's Run line leaves out the existing tests that pin the texts wave 3 edits
Severity: B
Location: tasks.md § Wave 3 Run; § Coverage, UB-1
Defect: 3.4 rewrites the `src/payload/scripts/gitlab_api/` bullet of `docs/forLLMConsumption.md`. That bullet is
  also pinned by `test/test_gitlab_graphql_contract.py` `test_the_map_names_the_graphql_call` (`MAP_BULLET_START`,
  `call graphql#`, `--file NAME=PATH`, `Upload`). 3.3 edits the entry script's docstring. That docstring is also read
  by `src/payload/test/test_gitlab_api_graphql_only.py` `test_the_usage_names_every_graphql_record` and
  `test_the_usage_says_which_mutations_are_refused`. Wave 3's Run line holds neither file, so wave 3's green capture
  would not show a regression in either. The Coverage row for UB-1 ("the existing suites on every Run line") is
  false for wave 3.
Material-because: UB-1 (the existing tests SHALL CONTINUE TO pass). It is also unmaintainable-by-rule
  `post-activity.md` item 1 (run the AFFECTED tests).
Proposed-edit: Replace wave 3's Run line with `python scripts/run_tests.py src/payload/test/test_gitlab_*.py
  test/test_gitlab_*.py test/test_instruction_corpus_budget.py test/test_toolchain_manifest.py test/test_layout.py`.

### C1 — AC-1.4 is in no task's Validates
Severity: C
Location: tasks.md § Wave 2, 2.3 to 2.6; § Coverage, AC-1.4
Defect: AC-1.4's oracle is V, which runs unedited on wave 2's Run line, so the criterion is tested. But no task
  lists AC-1.4, and spec-phase-tasks.md "Traceability" asks for every criterion in some TEST task's Validates.
Proposed-edit: Add AC-1.4 to the Validates of 2.3, 2.4, 2.5 and 2.6. Their `PENDING` restatements are what V
  judges as mapped or pending.

### D1 — 2.2's red reason covers only the refusal cases
Severity: D
Location: tasks.md § Wave 2, 2.2
Defect: Some K cases expect the call to be accepted: the snippet endpoint of
  `test_an_endpoint_is_named_by_its_method_and_path`, and `--header x-gitlab-nonce=n1`. On the base those fail on
  their exit-code or recorded-request assertion, not on a standard-error or log assertion.
Proposed-edit: Replace "so each case fails on its standard-error or log assertion" with "so each refusal fails on
  its standard-error or log assertion and each accepted call on its exit code".

## Checked, no finding

- Disjoint files: within each wave, every pair of tasks owns disjoint files. N is edited once per wave (1.5, 2.1,
  3.2). F:sscs, F:package, F:openapi_only and F:gitlab_dedicated each belong to one TEST task.
- Red for the right reason: every TEST task fails on the base on an assertion, or on an exception raised inside
  the test body. R, T and the family suites import `gitlab_api` inside a test (`gitlab_module`). The new R, T and P
  tests fail on `TypeError` from the new `RestOperation` fields or `lookup(endpoint=)`, or on `AttributeError` for
  `Base` and `Location.HEADER`. The judge in `red_for_right_reason.py` refuses only a collection error, and none of
  these is one.
  1.5 is red on the base because `placeholders` gives `("id",)` for `archive[.format]` and no `${NAME}` for the
  delete-by-reference row (`operations-index.md`).
- D9 placement: #43's N rule changes with 1.6's `placeholders`, so it is restated in wave 1 (1.5). Every `PENDING`,
  record, typing and #43 F restatement changes with 2.7 to 2.10, so each is restated in wave 2 (2.3 to 2.6). The
  family tests D9 does not list (typing and paging in create, fulfillment, plan, verify and package) build literals
  keyed by ID or by (ID, name). The new records add no non-SCALAR or required row. For example, "Retrieve file
  archive" has only SCALAR, non-required query rows, and the registry sections have no table. So those tests pass
  unedited.
- No other assertion is weakened. Beyond D9, the only edit is D7's send loop, and judging an F1 record against its
  own endpoint alone makes that test stricter.
- Final wave: F.1 names the `verify` job, matrix group `tests`, of `.github/workflows/ci.yml`
  (`run_checks.py --group ${{ matrix.group }}`). P `test_standard_library_only` scans the package with `rglob`, so
  F.3's claim that it reaches `container_registry.py` holds.

## Coverage

| Criterion | Test / verify tasks | Status |
|---|---|---|
| AC-1.1 | 2.3–2.6; V | COVERED |
| AC-1.2 | 2.1, 2.3, 2.4, 2.6; N record test | COVERED |
| AC-1.3 | 2.3–2.6; V | COVERED |
| AC-1.4 | V on wave 2's Run line (C1) | COVERED |
| AC-2.1 | 2.2, 2.3, 2.4 | COVERED |
| AC-2.2 | 1.1, 2.3 | COVERED |
| AC-2.3 | 2.3 | COVERED |
| AC-2.4 | 1.1, 1.3, 2.2 | COVERED |
| AC-3.1 | 1.1, 1.3, 2.3 | COVERED |
| AC-3.2 | 1.1, 1.3, 2.3 | COVERED |
| AC-3.3 | 2.2 | COVERED |
| AC-4.1 | 1.1, 2.3 | COVERED |
| AC-4.2 | 1.3, 2.2 | COVERED |
| AC-5.1 | 1.1, 1.2, 2.4 | COVERED |
| AC-5.2 | 1.1, 1.2, 1.4, 2.5 | COVERED |
| AC-5.3 | 2.5 (paired wrongly, B1) | COVERED |
| AC-6.1 | 2.1 | COVERED |
| AC-6.2 | 1.1, 1.2, 2.4, 2.6 | COVERED |
| AC-6.3 | 2.2 | COVERED |
| AC-7.1 | 2.2, 2.6 | COVERED |
| AC-7.2 | 2.1 | COVERED |
| AC-8.1 | 2.1; N record and send tests; F.1 | COVERED |
| AC-8.2 | 2.1 | COVERED |
| AC-8.3 | 2.2–2.6; F.1 | COVERED |
| AC-9.1 | 2.2, 3.1 | COVERED |
| AC-9.2 | 3.2; `test_llm_map_within_cap` | COVERED |
| UB-1 | 1.1, 1.5, F.3; existing suites (wave 3 short, B2) | COVERED |
| UB-2 | 1.2, 2.5, F.3 | COVERED |
| UB-3 | 2.2, F.3 | COVERED |
| UB-4 | F.2 | COVERED |

Counts: 0 A, 2 B, 1 C, 1 D; 30 COVERED, 0 GAP.

NOT-CLEAN (0 A, 2 B)

Verdict: NOT-READY
