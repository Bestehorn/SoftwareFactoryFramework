# Refutation report 2 (delta): issue #72, test-only rework, HEAD c08859a

Scope: `git diff 2742f81..HEAD -- src test` (the golden case `get-jobs/exit-0/timing-edges` in
`src/payload/test/github_wrapper_fixtures.py`; `test_the_oracle_is_the_replaced_copy` in
`test/test_github_wrapper_fork_parity.py`), graded against round 1's survivors M47 (AC-7) and M48 (AC-3).
`RT` = `venv/Scripts/python.exe scripts/run_tests.py`; `P2` = `src/payload/test/test_github_wrapper_compat.py
test/test_github_wrapper_fork_parity.py`, run TOGETHER (the setup in which M47 survived). Every mutant: Edit on HEAD,
`git diff HEAD` captured, `RT P2`, `git checkout HEAD -- <file>`, `git diff HEAD --stat` empty. All runs are in
`mutants-2.txt`.

## 1. Whole-suite verdict

No CI run exists for c08859a: `git branch -r --contains HEAD` prints nothing and `origin/issue-72-get-jobs-rerun-cancel`
is an unknown revision. This delta's dispatch bounds local runs to the paired files; the whole-suite verdict is the CI
run on the pushed SHA. `RT P2` on the restored tree: `539 passed`, `exit=0` (536 in round 1, plus the new case on the
product and on the copy, plus the oracle test).

## 2-5. Claims

| Claim | Command | Result | Capture |
|---|---|---|---|
| AC-7 oracle pinned: M47 (round-1 edit, `fork_script` returns `ROOT / "scripts" / "github_wrapper.py"`) fails | M47 `RT P2` | `1 failed, 538 passed`: `test_the_oracle_is_the_replaced_copy` fails with `the fork ...\scripts\github_wrapper.py is under ...\scripts`. Killed: FAILED-TO-REFUTE | M47 |
| AC-3 blank `started_at` line executed and asserted | M48a: `if not value: return None` -> `raise RuntimeError` | `1 failed, 538 passed`: `test_a_subcommand_matches_its_golden_case[get-jobs/exit-0/timing-edges]`, `RuntimeError: M48 blank timestamp line executed`. Killed: FAILED-TO-REFUTE | M48a |
| AC-3 naive start read as UTC, executed | M48b: `parsed = parsed.replace(tzinfo=timezone.utc)` -> `raise RuntimeError` | `1 failed, 538 passed`, same test, `RuntimeError: M48 naive timestamp line executed`. Killed: FAILED-TO-REFUTE | M48b |
| AC-3 negative duration unbilled, executed | M48c: `return wall_seconds, None` -> `raise RuntimeError` | `1 failed, 538 passed`, same test, `RuntimeError: M48 negative duration line executed`. Killed: FAILED-TO-REFUTE | M48c |
| AC-3 golden discriminates the naive branch's value, not only its execution | M48d (extra): naive timestamp -> `return None` | `1 failed, 538 passed`: `timing-edges: the standard output differs from the golden`. Killed: FAILED-TO-REFUTE | M48d |
| AC-3 golden discriminates the negative branch's value | M48e (extra): negative duration -> `return wall_seconds, 0` | `1 failed, 538 passed`, stdout differs. Killed: FAILED-TO-REFUTE | M48e |
| AC-7 oracle pin holds when the revision, not the path, points at the product | M47d (extra): `FORK_REVISION = f"HEAD:{FORK_SOURCE}"` (blob 4ae9739, the installed product entry script) | `1 failed, 538 passed`: `the fork's source names the product's package 'github_api'`; every fork golden case passes, so the new test alone holds the pin. Killed: FAILED-TO-REFUTE | M47d |
| AC-7 tag swap | M47c (extra): `FORK_TAG = "v2026.11.26"` | `539 passed`. Equivalent mutant: `git rev-parse` gives blob `99e0fc1` for both `v2026.11.10.1:` and `v2026.11.26:scripts/github_wrapper.py` (the product reached `scripts/` at ce950f4, blob `4ae9739`); the oracle bytes are unchanged, so no test can fail. Not a survivor | M47c, M47c-note |
| New test's helper lines run | M47e: `_is_in_package` `return False` (None module) -> `raise RuntimeError`, `RT test/test_github_wrapper_fork_parity.py -k oracle_is_the_replaced_copy` | `1 failed`: `RuntimeError: M47e module_name None line executed`. FAILED-TO-REFUTE | M47e |
| Golden values are the copy's | `git show v2026.11.10.1:scripts/github_wrapper.py` into `tmp/verify2_copy/`, the case run on it through the fixtures' fake host (disposable probe, deleted) | copy `_job_billed_minutes`: blank start `(None, None)`, naive start `(105.0, 2)`, completed-before-start `(-300.0, None)`; one `GET ...jobs?per_page=100&filter=latest`; copy stdout equals the golden byte for byte, exit 0 = golden 0; no `github_api` module loaded. FAILED-TO-REFUTE | COPY-CHECK |
| Vacuity: new tests | Read of both tests; diff grep for `skip`, `xfail`, `importorskip`, `deselect`, `pytest.mark`, commented `def test`/`assert` | One hit, diff line 135: the unchanged context line `@pytest.mark.parametrize` of `test_the_fork_produces_the_golden_case`, not an added marker. The golden stdout is built by test-side `job_line`/`billed_total_line` (the fixtures import the standard library and pytest only) plus literal suffixes, and equals the tag copy's output (COPY-CHECK): no oracle through the code under test. The oracle test compares the fixture's file with its own `git show FORK_REVISION`, a check the fixture can fail (M47, M47d): no tautology. FAILED-TO-REFUTE | VACUITY |
| Red for the right reason | `evidence/red/` for the rework | The rework adds tests over code already implemented, so it has no red capture; its failing runs are the mutant runs above, each an `AssertionError` or the mutant's `RuntimeError` inside the test, none a collection or load error. FAILED-TO-REFUTE | M47-M48e |
| Coverage of the change | M48a-c, M47e, and the restored run | The three `ci.py` lines round 1 found unexecuted now run in `timing-edges` (M48a-c); every added test line runs (`539 passed`, the new tests among them, M47e). FAILED-TO-REFUTE | M48a-c, M47e, RECONFIRM |

## Refuted

None. Round 1's survivors M47 (AC-7) and M48 (AC-3) are killed by the rework. M48 was run as three separate mutants,
and each fails on its own. The extra probes M47d, M48d, M48e and M47e are also killed. M47c is equivalent, because
both tags carry the same blob.

Killed: M47, M47d, M47e, M48a, M48b, M48c, M48d, M48e. Equivalent: M47c. Survivors: none.

## Tree restored

Every mutant was restored with `git checkout HEAD -- <file>`, and `git diff HEAD --stat` was empty after each one
(`mutants-2.txt`). The probe files under `tmp/` (the copy, the fake project, the probe script) were deleted. Re-run on
the restored tree at c08859a: `RT P2` gave `539 passed`, `exit=0` (RECONFIRM). Running `git status --porcelain` shows
`evidence/verify/mutants-2.txt`, this report, and `?? .claude/specs/issue-72-get-jobs-rerun-cancel/evidence/REPORT.md`.
That last file appeared during this run. The verifier did not write it, and it was left untouched.

VERIFIED
