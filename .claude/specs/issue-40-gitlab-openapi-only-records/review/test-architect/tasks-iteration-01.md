# Test-architect review — tasks, iteration 01

Scope: `tasks.md` against the frozen `requirements.md`, `design.md` § D6, § D7 and § Correctness Properties, and
DL-001..DL-009. I checked these against the worktree at 9dcd0e9: `registry.py` `RestOperation`, `placeholders`,
`lookup`; `transport.py` `request`, `_send`, `CONTENT_TYPE_OCTET_STREAM`; N `record_problems`, `sent_record_problems`;
fx `run_main`; T `TOKEN_TYPES`; K `OP_GRAPHQL_PROJECT`; C `USAGE_CALL_TEXTS`; `.github/workflows/ci.yml` `verify`.
`tasks.md` is 14,952 B, under its 15,000 B cap. The edits below shrink it overall.

## Checks the conductor asked for

- **Every AC and UB has a TEST or VERIFY task.** All 20 do (table below). F.1 names the check and its CI job, the
  `verify` job's `tests` leg.
- **Merging `call.py` into wave 2 is sound.** K's two new tests (2.3) call the real `openapi-only#` IDs that 2.4
  writes. F's and G's group-left-out and `--input` calls need both the records and 2.6. So no part of 2.6 can go green
  in wave 1. The wave's files are disjoint: F, G and K for the tests, then `openapi_only.py`, `deploy.py` and `call.py`.
- **N's existing tests going red in wave 1 is acceptable. Do not split the wave.**
  - The `AttributeError` is raised at run time, in an N helper the test calls. It is not a collection error, and it
    comes from a product attribute that is not written yet, which the preamble names as a right reason.
  - The wave commits only after its green run, so UB-4 holds at every commit.
  - A split would make things worse. With 1.5 landed first, the new N test would be green on its first run, because
    the product would be done and N's helpers would be written in the same task. It would then never have been red.
- **The one G test that is green at red is acceptable.** `test_no_record_declares_an_openapi_only_model_id` can still
  fail: it fails if 2.4 declares an `openapi-only#` ml_models ID.
- **The Run lines are complete.**
  - Wave 1 runs every suite that reads `registry` or `transport`: R, T, P, N, K, C, H and the three family suites.
    V reads only `discover_families`, so it is not needed there.
  - Wave 2 adds F, G and V.
  - Wave 3 runs the only test that reads the entry script's `__doc__` (C's `test_the_usage_names_the_operation_call`),
    plus the map and ledger caps and `test_layout`.
- **Each wave's red result is what the tasks state, except 1.4 (C1).**
  - For K: argparse refuses `--input`, and `lookup` raises `ValueError`. The case still exits 2 with no request, so it
    fails on its log-record or standard-error assertion.
  - For P: `expand` leaves `*glob` in the path and raises nothing, so its assertions fail.

## Findings

### C1 — 1.4 states a red reason for the deploy case that the red run cannot show
Severity: C
Location: tasks.md § Wave 1, task 1.4 (AC-1.4, AC-3.3)
Defect: D5 has `record_problems` read the section through `documented_raw_body`, which reads `record.content_type`.
Until 1.5, every `record_problems` call therefore raises `AttributeError` before its result is asserted. The deploy
case fails on that error, not on the "(assertion)" the task states. The test is still red for a right reason, so this
is not a coverage gap. It is a stated reason the red capture will contradict.
Proposed-edit: replace "Red: the new test's `deploy#download-a-machine-learning-model-package-file` case names the
`path` row, which `registry.placeholders` does not read yet (assertion), and its raw-body record raises `TypeError`
on `content_type`; N's existing record tests raise `AttributeError` on `content_type` inside `documented_raw_body`
until 1.5." with "Red until 1.5: every `record_problems` call, the new test's and N's existing record tests', raises
`AttributeError` on `content_type` inside `documented_raw_body`, and the raw-body record raises `TypeError`; 1.5 also
makes `registry.placeholders` read the deploy case's `path` row."

### C2 — the preamble's import rule contradicts 1.4's module-level helper
Severity: C
Location: tasks.md § preamble ("A product name this change adds … appears only inside a test body")
Defect: Task 1.4 (D5) writes `documented_raw_body`, a module-level helper of N, and it reads `content_type`. Read
literally, the rule forbids that. The rule exists to prevent collection errors, and any function body satisfies that.
Proposed-edit: replace "appears only inside a test body" with "appears only inside a function body, never at import".

### D1 — wave 3's documentation tasks claim AC-3.2
Severity: D
Location: tasks.md § Wave 3, tasks 3.1 and 3.2
Defect: No test on wave 3's Run line fails when `--input` is missing from the usage lines or the map. AC-3.2 is
covered by 1.1, 1.2 and 2.1 to 2.3, as the Coverage table already says.
Proposed-edit: in 3.1 replace "Validates: AC-3.2, UB-1" with "Validates: UB-1"; in 3.2 replace "Validates: AC-3.2"
with "Validates: none (D5 documentation)".

## Coverage

| Criterion | Test / verify tasks | Fails when | Status |
|---|---|---|---|
| AC-1.1 | 2.1; V on wave 2 | an ID is missing or doubled; `PENDING` is not empty; a key sits outside its family | COVERED |
| AC-1.2 | 2.2 | a `deploy#` ID is missing; an `openapi-only#` ml_models ID is declared | COVERED |
| AC-1.3 | 1.4, 2.1, 2.2; N on wave 2 | `KINDS`, `REQUIRED` or `RAW_BODIES` differ; a row is undeclared | COVERED |
| AC-1.4 | 1.4, 2.1, 2.2 | a `Param` names a path parameter; the glob skip holds a `:name` row | COVERED |
| AC-1.5 | 2.1, 2.2 | the set of paged IDs differs, or a record lacks `page` or `per_page` | COVERED |
| AC-1.6 | 2.1, 2.2; V on wave 2 | either `PENDING` is not empty; V fails | COVERED |
| AC-2.1 | 1.1, 1.3, 2.1 | a `/` is encoded or a part is not quoted (property and example) | COVERED |
| AC-2.2 | 1.1, 1.3, 2.1 | a refused part is sent, the exit is not 1, or the log does not name `*path` | COVERED |
| AC-2.3 | 1.1, 2.1, 2.2, 2.3 | a group is sent wrongly either way; `path=""` is accepted; a group parameter is required | COVERED |
| AC-2.4 | 1.1, 2.3 | `placeholders` or `required_placeholders` is wrong; a missing glob is accepted | COVERED |
| AC-2.5 | 1.1, 2.1 | a backslash is kept; `Packages()` is read as a group | COVERED |
| AC-2.6 | 2.1, 2.2 | a sent `(method, url)` differs through `main` | COVERED |
| AC-3.1 | 2.1; N and K on waves 1 and 2 | a record is sent off its section | COVERED |
| AC-3.2 | 1.1, 1.2, 2.1, 2.2, 2.3 | the bytes change; the multipart part is wrong; a refusal sends or does not exit 2 | COVERED |
| AC-3.3 | 1.4; N on wave 2 | an N record test finds a difference | COVERED |
| AC-3.4 | 2.1 | the output is not both pages, or a scripted page is not served | COVERED |
| UB-1 | F.3; C on every Run line | a C case fails, or its file is in the diff | COVERED |
| UB-2 | 2.1, F.3; P on waves 1 and 2 | a non-stdlib import or environment read; the token is in the body | COVERED |
| UB-3 | F.2 | a UB-3 file is in the diff, or its suites fail in CI | COVERED |
| UB-4 | F.3; R, P, K, N, family suites; V on wave 2 | an existing test fails or is edited | COVERED |

COVERED 20, GAP 0. Each TEST task comes before its IMPL tasks in its wave. The wave 3 tasks are documentation and
pair with no TEST task.

CLEAN (0 A, 0 B; 2 C, 1 D) — TEST-READY

Verdict: READY
