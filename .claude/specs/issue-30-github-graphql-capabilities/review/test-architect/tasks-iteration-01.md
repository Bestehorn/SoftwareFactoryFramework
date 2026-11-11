# Test-architect review — tasks, iteration 01

## Findings

### B1 — `registry.graphql_call` is implemented in wave 1, and its only tests run in wave 2
Severity: B
Location: tasks.md § Wave 1, task 1.3 (Validates AC-2.1, AC-2.2, AC-2.3)
Defect: Task 1.3 writes `graphql_call` and claims AC-2.1, AC-2.2 and AC-2.3. No wave-1 test calls it: R's two new tests
  exercise only `declared_variables` and `graphql_lookup`, and V calls no registry function. Its paired tests are G's
  (task 2.2), which come a wave later.
Material-because: AC-2.1, AC-2.2, AC-2.3 — the code that sends a GraphQL record and pages its connection is written
  before any test of it has run red, so wave 1's green capture claims three criteria that no test in that run
  exercises.
Proposed-edit: In 1.3, delete "`graphql_call(transport, operation_id, *, variables)` (`graphql_lookup`, an undeclared
  name refused with `ValueError` as `_check_names` refuses, then `list(transport.graphql_nodes(...))` for a record
  with a `connection`, else `transport.graphql(...)`); " and replace "Validates: AC-1.4, AC-2.1, AC-2.2, AC-2.3,
  AC-2.5" with "Validates: AC-1.4, AC-2.5". After 2.4, add: "- [ ] 2.5 IMPL: `registry.graphql_call(transport,
  operation_id, *, variables)` per D3 (`graphql_lookup`, an undeclared name refused with `ValueError` as
  `_check_names` refuses, then `list(transport.graphql_nodes(...))` for a record with a `connection`, else
  `transport.graphql(...)`); nothing else of the module changes. — Files: src/payload/scripts/github_api/registry.py
  — Validates: AC-2.1, AC-2.2, AC-2.3". This keeps wave 2's files disjoint, because no other wave-2 task owns
  `registry.py`, and R is already on wave 2's Run line.

### B2 — Wave 2's Run line omits the only suites that pin the `GATED_OPERATIONS` entries task 2.4 edits
Severity: B
Location: tasks.md § Wave 2 "Run:"
Defect: Task 2.4 adds entries to `GATED_OPERATIONS` and rewrites its comment. After the rebase, the existing `None`
  entries are pinned only by `test_a_branch_writing_record_is_refused` in `src/payload/test/test_github_api_git.py`
  (`git/create-ref`, `git/update-ref`) and `src/payload/test/test_github_api_repos.py` (the five `repos/*` IDs).
  Neither file is on any Run line. K's `test_a_gated_operation_names_its_subcommand` covers only `pulls/merge`,
  `pulls/merge-async` and `issues/create`. N's `test_every_record_is_sent_as_its_section_documents` drops every gated
  ID before it sends (`record.operation_id not in gated`).
Material-because: regression — if 2.4's edit drops or remaps an existing entry, every test on wave 2's Run line still
  passes, and `call` then sends a record that commits to or moves a branch.
Proposed-edit: In wave 2's Run line, after `src/payload/test/test_github_api_call.py`, insert
  `src/payload/test/test_github_api_git.py src/payload/test/test_github_api_repos.py`.

### C1 — 2.2 names `GoldenCase.writes` as the body oracle, which cannot tell `true` from `1`
Severity: C
Location: tasks.md § Wave 2, task 2.2
Defect: `NonGetRequest` compares bodies with `==`, and under `==` `True == 1`. Design § Correctness Properties AC-2.1
  compares with `json.dumps(sort_keys=True)`, as K's `test_a_body_member_holds_the_given_json_value` does. The
  preamble already binds the design's oracle, so this edit only makes the comparison explicit in 2.2.
Proposed-edit: Replace "each posted body judged by `GoldenCase.writes`" with "each posted body judged by
  `GoldenCase.writes` and, in `test_a_variable_holds_the_given_json_value`, also by `json.dumps(sort_keys=True)`
  (design AC-2.1)".

### D1 — 2.1's red reason
Severity: D
Location: tasks.md § Wave 2, task 2.1 "Red:"
Defect: `test_the_reference_is_read_as_written` and `test_the_method_rejects_a_document_that_differs` take named
  records. If they look the records up through `registry.graphql_lookup`, they fail on its `ValueError`, not on an
  assertion. Both are red inside the test body, which `red_for_right_reason.judge` accepts (`FAILED .*::`).
Proposed-edit: Replace "each test fails on an assertion" with "each test fails on an assertion or, for a named record,
  on `registry.graphql_lookup`'s `ValueError`, inside the test body".

Checked with no finding: every test task comes before its implementation task in each wave. The files within each wave
are disjoint (W1: R, V, `registry.py`; W2: Q, G, `graphql_only.py`, `call.py`; W3: G, Q, `github_wrapper.py`, the map).
Each red is an assertion or an exception inside the test body: R and G import through `fx.import_api_module` inside
the test, Q and V through `scripts_on_path` and `_import_package_module`, and G parametrizes over constants. At red,
G's two exit-2 tests pass their exit and request checks and fail on the log check, because the unknown-ID message of
`registry.lookup` holds neither `merge-pr`, "no subcommand sends it", `["input"]` nor `["owner", "name"]`. 3.1 and 3.2
are red on text that is absent today: the docstring has no `call graphql/` line, and the map does not contain
`call graphql/`. F.1 names the `verify` job, matrix leg `tests` (`.github/workflows/ci.yml`), with the real-forge run
out of scope by the requirements. No existing test builds a GitHub `GraphQLOperation`, and none asserts the contents of
`PENDING_CAPABILITIES`.

## Coverage

| Criterion | TEST / VERIFY task(s) | Wave | Status |
|---|---|---|---|
| AC-1.1 | 2.1 (Q `test_every_record_matches_the_reference`); design inspection | 2 | COVERED |
| AC-1.2 | 2.1; V `…covered_or_pending`, `…its_own_ids` (W2 Run) | 2 | COVERED |
| AC-1.3 | 2.1 | 2 | COVERED |
| AC-1.4 | 1.2 | 1 | COVERED |
| AC-1.5 | 1.2; V's two tests (W2 Run) | 1, 2 | COVERED |
| AC-2.1 | 2.2; H (W2 Run) | 2 | COVERED (B1: implemented in W1) |
| AC-2.2 | 2.2 | 2 | COVERED (B1) |
| AC-2.3 | 2.2 | 2 | COVERED (B1) |
| AC-2.4 | 2.2 | 2 | COVERED |
| AC-2.5 | 1.1, 2.2 | 1, 2 | COVERED |
| AC-2.6 | 2.2 | 2 | COVERED |
| AC-3.1 | 2.1, 2.2 | 2 | COVERED |
| AC-3.2 | 2.2 | 2 | COVERED |
| AC-3.3 | 2.2 | 2 | COVERED |
| AC-4.1 | 3.1 | 3 | COVERED |
| AC-4.2 | 3.2, F.4 | 3 | COVERED |
| UB-1.1 | F.3; C, P on every Run line | all | COVERED |
| UB-1.2 | F.3; K, R (W1, W2), N (W2) | 1, 2 | COVERED |
| UB-2.1 | F.3; C on every Run line | all | COVERED |
| UB-2.2 | F.3; V on every Run line | all | COVERED |
| UB-3.1 | F.2; `test_wrapper_delivery.py` on every Run line | all | COVERED |

21 COVERED, 0 GAP.

Verdict: NOT-CLEAN (0 A, 2 B)
