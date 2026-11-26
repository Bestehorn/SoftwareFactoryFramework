# Combined review, iteration 01: issue-72-get-jobs-rerun-cancel (tier S, all six lenses)

### B1 — The get-jobs cases leave conditions of AC-1, AC-2 and AC-3 unfalsified
Severity: B
Location: change.md § Tests, the AC-1, AC-2 and AC-3 lines
Defect: A `ListRouteSpec` matches with `page`/`per_page` removed (`ListRoute.matches`) and names no next page below 30 jobs, so a product sending no `per_page`, or paging, passes. No case gives `--all-attempts` on one attempt, so a suffix keyed on the flag instead of the page's distinct `run_attempt` values passes. No case pairs `--timing` with a completed job `--failed-only` drops, so a TOTAL over every job passes. And if "every option" includes `--failed-only`, the running job (conclusion `null`) never prints, so `[wall=? billed=?]` goes untested.
Material-because: AC-1 (`per_page`, one request), AC-2 (the `run_attempt` WHEN) and AC-3 (TOTAL "over the printed jobs", `[wall=? billed=?]`) are untested; GitHub's default page is 30 (`docs/api-reference/github/rest/actions.md` "List jobs for a workflow run"), so a missing `per_page` drops jobs.
Proposed-edit: replace the three lines with
"- AC-1: `get-jobs/exit-0/latest-attempt` (one attempt, a job without a conclusion), `get-jobs/exit-0/all-attempts`; each a `StaticRouteSpec` whose query is the copy's `per_page` and `filter` and whose reply's `link` names a next page.
- AC-2: `get-jobs/exit-0/failed-only` with `--timing` (`success` completed, `failure`, `cancelled`, `timed_out`, `skipped`); the suffix in `all-attempts`, none in `every-column`.
- AC-3: `get-jobs/exit-0/every-column`: `--all-attempts --show-steps --timing --show-runner --step-status` on jobs of one attempt, with and without steps, runner and labels, one running (no `completed_at`), one under a minute; `failed-only`'s TOTAL leaves the `success` job out."
and delete "a `get-jobs` route's `filter` query pins the filter sent" from the Tests intro.

### B2 — AC-7's usage lines have no test
Severity: B
Location: change.md § Tests AC-7; § Tasks T1
Defect: AC-7 requires the copy's `get-jobs`, `rerun` and `cancel` usage lines in the entry script's usage, but no named test reads the docstring. `test_github_wrapper_compat.py` already pins usage text this way (`test_the_usage_names_the_operation_call`, `USAGE_CALL_TEXTS`).
Material-because: AC-7 is not tested: a T3 that omits the lines passes every named test.
Proposed-edit: append to the AC-7 line "; `test_the_usage_names_the_ci_commands` (`src/payload/test/test_github_wrapper_compat.py`): the copy's `get-jobs`, `rerun` and `cancel` usage lines in the entry script's `__doc__`", and add that file to T1 `Files:` and to § Files.

### B3 — AC-8 names a get-jobs form that cannot produce the ladder's evidence
Severity: B
Location: change.md § AC-8, the ladder clause
Defect: Rung 0 of `docs/ci-capacity-ladder.md` (the same text is in `prompts/setup-kiro.txt`) classifies each job by runner name, labels and steps and says to quote the `runner_name=… labels=… steps=N` lines. `--show-steps` alone prints only `[steps=N]`; the runner and labels come from `--show-runner` (the copy's `cmd_get_jobs`), and DL-002's Driver says the ladder "reads the step and runner columns".
Material-because: wrong-behaviour: an agent following the corrected ladder runs a command whose output cannot tell shape (B) from shape (C).
Proposed-edit: in AC-8 replace "SHALL name `get-jobs <run-id> --show-steps` where they name `--steps`" with "SHALL name `get-jobs <run-id> --show-steps --show-runner` where they name `get-jobs <run-id> --steps`".

### C1 — T1's "Red on the product" does not hold for the refusal rows
Severity: C
Location: change.md § Tasks T1
Defect: Before T3 the product's parser rejects the three names with exit 2 and sends nothing, so the nine `_refusal_cases` rows already pass `assert_outcome`; only the exit-0 and exit-1 rows are red. The capture is judged as a whole (`red_for_right_reason.judge`), so nothing blocks.
Proposed-edit: "Red on the product, green on the copy." → "The exit-0 and exit-1 rows red on the product (an unknown subcommand exits 2), the refusal rows already exit 2 there; all green on the copy."

### C2 — The CLAUDE.md sentence AC-8 replaces carries a stale pointer
Severity: C
Location: change.md § AC-8, the CLAUDE.md clause
Defect: The recorded-deviation sentence ends "new subcommands go into `src/payload/scripts/github_wrapper.py`". The product's docstring adds a subcommand as a module of `github_api/commands/` defining `register(subparsers)`, and AC-8 does not say what replaces that clause.
Proposed-edit: append to the CLAUDE.md clause "and that a new subcommand is a module of `src/payload/scripts/github_api/commands/`".

### C3 — UB-4's GitLab half is mapped to tests that do not read it
Severity: C
Location: change.md § Tests UB-4
Defect: The two named tests pin the copy steps. No test in `test/test_setup_prompts_*.py` reads the GitLab "arrive in a later framework release" sentences, which share a paragraph with the edited GitHub clause.
Proposed-edit: append to the UB-4 line "; the GitLab sentences: checked on the diff, as AC-8".

### C4 — change.md is at its cap
Severity: C
Location: change.md (whole)
Defect: The file measures 7,940 B against the 8,000 B tier-S cap, and B1–B3 and C1–C3 add text.
Proposed-edit: offset the edits with cuts, for example the § Files prose that repeats the Tasks' `Files:` lists, and the Tests-intro clause that B1 deletes.

### D1 — AC-7 gives `int` for get-jobs' `run_id` only
Severity: D
Location: change.md § AC-7
Defect: The copy's `rerun` and `cancel` parsers also take `run_id` as `int`. The parity test pins the type either way.
Proposed-edit: "`rerun`: `run_id` as `int`, `--failed-only`; `cancel`: `run_id` as `int`".

### D2 — The compat docstring names the installed fork as the oracle
Severity: D
Location: change.md § Files
Defect: `test_github_wrapper_compat.py` says the golden values are "the installed fork's own output". That has been stale since PR #71 and contradicts DL-003.
Proposed-edit: with B2's file, add "its docstring names the copy at `v2026.11.10.1` as the oracle".

## Lenses without a finding
Security: `rerun` and `cancel` call `Transport.request` with `body=None` (no data, no `Content-Type`). The token goes only in `Authorization` to the API origin (`Transport._send`). Only the explicit subcommands reach them, after `main`'s credential, repository and test-marker refusals; `call` already reaches the records. DevOps: the CI `verify` checkout has `fetch-depth: 0`, so the tag resolves. The tag's commit is the pre-promotion `.claude/FRAMEWORK_COMMIT`, and its wrapper equals the copy PR #71 replaced (empty `git diff`). The forge residual holds: `test/forge/forge_fixture.py` asserts the seed has no workflow. Best practice: the records match `rest/actions.md`.

## Coverage
| Criterion | Named test | Finding | Row |
|---|---|---|---|
| AC-1 | latest-attempt, all-attempts | `per_page` and the single page unpinned | GAP (B1) |
| AC-2 | failed-only, all-attempts | the suffix condition is not separated from the flag | GAP (B1) |
| AC-3 | every-column | TOTAL over printed jobs, `[wall=? billed=?]` | GAP (B1) |
| AC-4 | rerun whole-run, failed-only | the POST path and its absent body are pinned (`NonGetRequest`) | OK |
| AC-5 | cancel requested | the same | OK |
| AC-6 | exit-1 rows, `_refusal_cases` | exit-1 is red first; refusals (C1) | OK |
| AC-7 | parser rows, parity on the tag | the usage lines are untested | GAP (B2) |
| AC-8 | the diff | prose, no test pins it | OK |
| UB-1 | existing `CASES` and parser rows | | OK |
| UB-2 | `test_the_wrapper_imports_only_the_standard_library` | | OK |
| UB-3 | `test_an_installed_file_equals_its_source_at_the_release` | | OK |
| UB-4 | the copy-step tests | GitLab half (C3) | OK |

NOT-CLEAN (0 A, 3 B)
Coverage: NOT-TEST-READY
Verdict: NOT-READY (A 0, B 3, C 4, D 2)
