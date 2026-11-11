# Test-architect review — issue #46 tasks, iteration 01

## Findings

### TA-T-B1 — Waves 1, 2 and 4 leave out suites that drive the modules they change
Severity: B
Location: tasks.md § Wave 1, § Wave 2 and § Wave 4, the `Run:` lines
Defect: On origin/main (fe79965) every family suite sets `CALL = "call"` and runs its cases through
`fx.run_product_case`, so each one goes through `commands/call.py`, `registry.send` and `transport.py`. Three Run lines
miss some of them:
- Wave 1 omits `test_github_api_apps.py`, `_orgs.py`, `_teams.py` and `_users.py` (#29, PR #50, on the rebase target),
  although 1.5 changes `registry.py`, `transport.py` and the redirect handler that they reach.
- Wave 2 names no family suite but G, although 2.5 rewrites `cmd_call` steps 1, 4 and 6 and the parser, which all
  eleven reach.
- Wave 4 runs first after the rebase onto #33, but names none of the suites that rebase brings in.
Material-because: regression — a break that 1.5 or 2.5 causes in a family's `call` would pass the wave's green capture
and its commit, and show only in CI. `post-activity.md` item 1 requires the affected tests.
Proposed-edit: replace each of the three `Run:` lines with
Run: `python scripts/run_tests.py src/payload/test/test_github_*.py test/test_github_*.py`
At run time the shell expands this to every GitHub suite on the branch: T, R, K, C, G, M once #33 is in, each family
suite, H, N, V and P. Wave 3's line stays as it is. The edit makes tasks.md shorter, and the Coverage rows and F.2
stay true.

### TA-T-C1 — AC-1.3's `--input` file must exist
Severity: C
Location: tasks.md § Wave 2, task 2.1, `test_a_raw_body_with_body_members_is_refused`
Defect: If the path is missing, `read_input`'s argparse error ends the call before `cmd_call` step 1, so the
log-record oracle stays red after 2.5. The task does not say that the file exists.
Proposed-edit: replace "beside `--input` on `markdown/render-raw`" with "beside `--input <a file under tmp_path>` on
`markdown/render-raw`".

## Checks that pass

- **Order.** Each wave's TEST tasks come before its IMPL tasks. Each IMPL's paired tests are in the same wave or an
  earlier one:
  - 1.5 ← 1.1 to 1.3
  - 2.5 ← 2.1, 2.2
  - 2.6 ← 2.1, 2.3, 2.4
  - 3.2 ← 3.1
  - 3.3 ← B on wave 3's line
  - 4.3 ← 4.1, 4.2
- **Ownership.** The tasks of each wave own disjoint files.
- **Red for the right reason.** Before its IMPL, each new test fails on an assertion or on an exception raised in the
  test body:
  - T raw body: `AttributeError` on `request_raw`.
  - T same-origin: `GitHubAPIError` is raised.
  - T second `307`: one request is sent, not two.
  - R: `TypeError` on `root=`.
  - K `307`: exit 1.
  - K refusals: the exit 2 and the absence of a request already hold, but the log record is missing, and standard
    error reads `unrecognized arguments` rather than `argument --input:`.
  - K upload and K render: the exit is not 0.
  - H: `read_input` is missing.
  - G: `PENDING` is not empty.
  - C: the strings are absent.
  - M: `render-raw` is still pending.
- **The two green-by-design tests.** Their oracles kill the mutants they name:
  - The cross-origin re-send: the fake records the second request and `pytest.fail`s it as unrouted
    (`FakeGitHub`, `unrouted`).
  - N's reader at its default host: it fails the upload's `READ_SECTIONS` case.
  - N's routing at `section.host` is then proven by the every-record test after 2.6.
- **#33.** Waves 1 to 3 need neither `markdown.py` nor M:
  - 2.1's two `markdown/render-raw` cases end at argparse (the missing file) or at step 1, which comes before `lookup`.
  - H calls `request_raw` on `/markdown/raw` directly.
  - Only 4.1 to 4.3 need the record and M.
- **Fixture 1.4.** The product's `CONTENT_TYPE_JSON` and the fork's are both exactly `application/json`, so every
  existing row keeps `request.json()`. Only `assert_outcome` builds `NonGetRequest`, and C, P and K are on every Run
  line.
- **Final wave.** F.1 names the `verify` job of `.github/workflows/ci.yml`, matrix group `tests`, which runs
  `run_checks.py --group tests`. It also names C `test_the_script_runs_by_path`. Both exist on origin/main.

## Coverage

| Criterion | Test task(s) | Status |
|---|---|---|
| AC-1.1 | 1.1 (cross-origin `307`), 2.1 (JSON record; missing file); inspection of D1 to D3 | COVERED |
| AC-1.2 | 1.1, 1.2, 2.1 (upload, not UTF-8), 2.2 (property), 4.1 (standard input, `\r\n`, `\xff`) | COVERED |
| AC-1.3 | 2.1 (`-f`, `-F`) | COVERED |
| AC-2.1 | 2.1 (upload), 2.4 (N: host reader, routing) | COVERED |
| AC-2.2 | 1.1 (third root refused), 2.1 (credential only on the upload origin) | COVERED |
| AC-3.1 | 1.1 (four cases), 1.3 (K `repos/update`) | COVERED |
| AC-3.2 | 1.1 (`PATCH`, `DELETE`) | COVERED |
| AC-4.1 | 2.3 (G), 2.4 (N), 4.2 (M); N and V on the lines of waves 2 and 4 | COVERED |
| AC-4.2 | 2.1 | COVERED |
| AC-4.3 | 4.1 | COVERED |
| AC-5.1 | 3.1; C `test_the_usage_names_the_operation_call` on wave 3's line | COVERED |
| AC-5.2 | F.3 (inspection), B `test_llm_map_within_cap` on wave 3's line | COVERED |
| UB-1.1 | 1.4, F.2; C, P and K on every Run line | COVERED |
| UB-2.1 | F.2; C `test_the_credential_comes_only_from_the_file` on every Run line | COVERED |
| UB-2.2 | 1.1, F.2 (T `test_a_cross_origin_redirect_drops_the_credential`) | COVERED |
| UB-3.1 | F.2; V `test_the_wrapper_imports_only_the_standard_library` on every Run line | COVERED |

16 COVERED, 0 GAP. TA-T-B1 is about which unchanged suites each wave's capture runs, not about criterion coverage.

Verdict: NOT-CLEAN (0 A, 1 B)
