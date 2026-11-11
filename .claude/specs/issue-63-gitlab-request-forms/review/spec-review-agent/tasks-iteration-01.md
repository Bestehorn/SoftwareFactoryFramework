# Tasks review — iteration 01 — lane spec-review-agent

Reviewed: `tasks.md` (untracked on 13dabdb; 14,891 B, cap 15,000 B) against the frozen `requirements.md` and the
approved `design.md` (DL-007). The rebased base is read from #43's worktree at 7d20ead, the head of PR #65 (open).

Checked, no finding:

- Design trace. Every test the design's Acceptance Criteria Mapping names sits in a task. The IMPL Files are D12's rows.
  No task adds a criterion, mechanism or file.
- Waves. Files are disjoint within each wave. The same-wave interface dependencies (1.6 on 1.8, 2.11 on 2.10) are
  stated, as in #44 2.4, which was approved.
- The red reasons hold on the base:
  - R, T, K and P import `gitlab_api` inside each test (`gitlab_module`).
  - `lookup(*, operation_id)` takes no `endpoint`, `RestOperation` has none of D12's fields, `Location` is QUERY and
    BODY only, and `send` has no `project`.
  - `placeholders` gives `("id",)` for the archive row and `()` for the delete-by-reference row, so 1.5 fails on an
    assertion.
  - `call.py`'s docstring holds a single `--path id=7` and no `--endpoint` or `--header`. The entry docstring and the
    map bullet hold none of the spellings.
  - In `rest/`, only the two openapi-only `header` rows and the external control's `- Request headers:` line carry
    headers, so 2.1's red is exactly the NuGet downloads.
  - `red_for_right_reason.py` refuses a red only beside a collection marker.
- Existing tests outside D9 survive:
  - The typing literals of package and create are keyed by ID, and an F1 copy leaves them unchanged.
  - V `record_key_problems` takes several keys per Reference.
  - P's scan `rglob`s the package, so it reaches `container_registry.py` unedited.
  - K `test_call_takes_no_token_option` reads every option string.
  - R's is the only fake `lookup`.
- Run lines. All three go through `scripts/run_tests.py`; the globs are #43's and #46's; wave 3 names C and N.
- Final. F.1 is the design's E2E: `ci.yml` `verify`, matrix `tests`. F.2 is #43's F.2. F.3 is D12, D9 and UB-3.

Assumptions the author listed:

1. 1.5 in wave 1: right. 1.6 changes what `placeholders` gives for the archive and registry rows, so the unrestated
   test would fail wave 1's green.
2. 2.1 on real records: right, and needed. Wave 1 writes `positional_names`, `suffix_values`, `Base` and
   `Location.HEADER`, so a synthetic record is green at red. The wording gap is C2.
3. G red on `ModuleNotFoundError`: the error is raised in the body, so the judge accepts it. The mismatch with "as T
   does" is D1.
4. 2.11 on 2.10's constant: accepted. The task states it, and it has #44 2.4's shape.
5. The fenced Run: fine. It is one `run_tests.py` call whose `\` continuation Git Bash runs, and no tool parses Run
   lines.
6. Grouped family tasks: fine. The files are disjoint, it is one behaviour, and the 27 tasks are within M's ceiling.
   #41 2.5 grouped families the same way.
7. The dropped "Not installed here" clause: fine. D11 does not name it, no `.py` file pins it, and the bullet keeps it.

### B1 — AC-8.3 reaches no TEST task
Severity: B
Location: tasks.md § Wave 2, `Validates:` of 2.2 to 2.6; § Coverage, row AC-8.3
Defect: The Coverage row credits AC-8.3 to 2.2–2.6, but none of their `Validates:` lines names it; only F.1, an E2E
  task, does. So no TEST implementer is dispatched with AC-8.3, and the oracles of AC-2.1 to AC-2.3, AC-3.2 and AC-4.1
  assert method, URL and at most body names. The headers AC-8.3 requires are asserted for none of them.
Material-because: AC-8.3 ("asserts the sent method, URL, headers and body names"). It also breaks
  `spec-phase-tasks.md` § Traceability: every criterion is to appear in a TEST task's `Validates:`.
Proposed-edit: append ", AC-8.3" to the `Validates:` of 2.2, 2.3, 2.4, 2.5 and 2.6.

### C1 — `test_send_fetches_the_registry_token_before_the_registry` can be green on the base
Severity: C
Location: tasks.md § Wave 1, task 1.1
Defect: Its oracle is "a container-registry record sent without `project` raises `ValueError`, nothing recorded".
  Take a synthetic record built without `token_scope` and given its `${NAME}` values. On the base it already behaves
  that way: `placeholders` reads no `${NAME}`, so `_declared_values` raises "neither a path parameter nor a declared
  attribute" before any request (`registry.py` `_declared_values`, `send`). None of 1.1's red reasons applies to it.
Proposed-edit: after "`test_send_fetches_the_registry_token_before_the_registry`" insert " (its record built with
  `token_scope`)".

### C2 — 2.1 does not say where a "built" record comes from
Severity: C
Location: tasks.md § Wave 2, task 2.1
Defect: Two new tests judge only readings that 2.1 itself writes:
  - `test_an_endpoint_a_place_a_suffix_and_a_base_are_read_as_written` runs `route_problems` over sent paths;
  - `test_a_request_header_is_read_and_sent_as_written` uses "the external control built without `X-Gitlab-Nonce`".
  After wave 1, a record written as `RestOperation(...)` constructs, so each test is red only if its records come from
  D8's declared ones. "the declared records its oracle names" leaves a "built" record open.
Proposed-edit: replace "each on the declared records its oracle names" with "each on the declared records of the IDs
  whose sections or paths its oracle names, a "built" record a `dataclasses.replace` of one".

### C3 — AC-1.4 is in no task's `Validates:`
Severity: C
Location: tasks.md § Final, F.3; § Coverage, row AC-1.4
Defect: Row AC-1.4 names only V's tests on wave 2's Run line, but `spec-phase-tasks.md` § Traceability wants a task.
  F.3 already verifies that every other existing test, V's included, passes in each wave's green run.
Proposed-edit: F.3 "Validates: AC-1.4, UB-1, UB-2, UB-3"; row AC-1.4 "F.3; V's two tests it names, on wave 2's Run
  line".

### D1 — 1.4 names a red reason that T's helper does not raise
Severity: D
Location: tasks.md § preamble; § Wave 1, task 1.4
Defect: The preamble has G import `gitlab_api` "as T does". T's `gitlab_module` first asserts that the file exists,
  so the red is that `AssertionError`, not the `ModuleNotFoundError` 1.4 names. Both are raised in the body.
Material-because: none (wording).
Proposed-edit: in 1.4, replace "(`ModuleNotFoundError` inside the test)" with "(T's `gitlab_module` assertion, inside
  the test)"; in the preamble, drop ", `ModuleNotFoundError`".

Cap: B1 and C1 to C3 add about 120 B. D1's preamble cut saves about 25 B. The preamble clause "the other
`test_gitlab_*` suites run as regression" can also go, saving about 55 B, because the Run globs already run them.

NOT-CLEAN (0 A, 1 B)
Verdict: NOT-READY
