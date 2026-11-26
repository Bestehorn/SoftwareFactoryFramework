# Refutation report: issue #72 (tier S, wave 1), HEAD de1434e

`RT` = `venv/Scripts/python.exe scripts/run_tests.py`; `P2` = `src/payload/test/test_github_wrapper_compat.py
test/test_github_wrapper_fork_parity.py`; `NEW` = `-k "get-jobs or rerun or cancel or ci_commands"` (42 tests). Every
mutant: `sed -i` on HEAD, `git diff HEAD` shown, tests run, `git checkout HEAD -- <file>`, `git diff HEAD --stat`
empty. Captures under `evidence/verify/`.

## 1. Whole-suite verdict

The branch is not pushed, so no CI run exists for de1434e. The CI verdict follows the push. Local verdict, regenerated
at HEAD over the green capture's file set: `1436 passed`, `exit=0` (`full-suite.txt`).

## 2-5. Claims

| Claim | Command | Result | Capture |
|---|---|---|---|
| Wave 1: T3 reverted (ci.py, actions.py, wrapper at ce950f4) fails P2 | M00 `RT P2` | 14 failed, 522 passed: FAILED-TO-REFUTE | mutants.txt M00 |
| AC-1 filter, per_page, widths, `None` | M01, M02, M07, M08, M09, M10 `RT P2 NEW` | each killed (unrouted GET or stdout differs): FAILED-TO-REFUTE | M01-M10 |
| AC-2 failed-only set; attempt suffix always/never; attempts counted over the printed jobs only | M03, M04, M05, M06 | each killed: FAILED-TO-REFUTE | M03-M06 |
| AC-3 steps/timing/runner suffixes, `?` form, ceil, `(none)`, `-`, `,`, order runner<timing, timing<attempt, timing<steps, TOTAL over every job, TOTAL absent, step order/indent/absent | M11-M26 | each killed by `every-column` or `failed-only`: FAILED-TO-REFUTE | M11-M26 |
| AC-3 coverage: every new line exercised | M48 `RT P2` (whole files): lines `_parse_timestamp` blank-value `return None`, naive `parsed.replace(tzinfo=timezone.utc)`, `_job_billed_minutes` negative `return wall_seconds, None` each replaced by `raise RuntimeError` | **536 passed**: no test executes the three lines, so the copy's blank/naive/negative-duration billing is untested | M48 |
| AC-4 rerun record with `--failed-only`, line text, segment | M27, M28, M29 | each killed: FAILED-TO-REFUTE | M27-M29 |
| AC-5 cancel line, record | M30, M31 | each killed: FAILED-TO-REFUTE | M30-M31 |
| AC-6 nothing on stdout on a host error | M32 (cancel), M33 (rerun) print before the request | killed by `exit-1` rows: FAILED-TO-REFUTE | M32-M33 |
| AC-6 exit 2, nothing sent | M41 kills `rerun/exit-2/usage-error`; M44 kills `cancel/exit-2/usage-error`; `assert_outcome` asserts no request on exit 2 | FAILED-TO-REFUTE | M41, M44 |
| AC-7 parser options of each command | M34-M40 (get-jobs `type=int`, `--all-attempts` store_false, `--failed-only`, `--show-runner`, `--timing`, `--step-status`, `--show-steps`), M41-M42 (rerun), M43-M44 (cancel) | each killed; M38/M39 (abbreviation still parses) killed by parser parity alone: FAILED-TO-REFUTE | M34-M44 |
| AC-7 usage lines | M45 (`cancel <run_id>`), M46 (`get-jobs <run_id> --timing`) dropped | killed by `test_the_usage_names_the_ci_commands`: FAILED-TO-REFUTE | M45-M46 |
| AC-7 oracle is the tag's copy | M47 `fork_script` returns `ROOT / "scripts" / "github_wrapper.py"`; `RT P2 NEW` then `RT P2` | **42 passed; 536 passed** | M47, M47-full |
| AC-8 prose | `git diff ce950f4..HEAD -- prompts CLAUDE.md docs`; Grep for `get-jobs <run-id> --steps`, `arrive in a later framework release` | both setup prompts drop the sentence; CLAUDE.md sentence replaced; ladder text names `--show-steps --show-runner` in both files; the one remaining hit is the GitLab sentence: FAILED-TO-REFUTE | diff |
| UB-1 golden values unedited | `git diff --numstat` fixtures: 379 added, 7 removed | the 7 removed lines are module-docstring and `CASES` comment prose; no golden row edited; all existing cases green on product and copy: FAILED-TO-REFUTE | full-suite.txt |
| UB-2 standard library only | new imports `math`, `datetime`; `test_github_wrapper_coverage.py` in the set | green: FAILED-TO-REFUTE | full-suite.txt |
| UB-3 no toolchain file edited | diff paths vs `config/toolchain.json` `files` keys | none listed (`scripts/` untouched; CLAUDE.md, `docs/ci-capacity-ladder.md`, `test/test_github_wrapper_fork_parity.py` are not keys); `test_toolchain_integrity.py` green: FAILED-TO-REFUTE | full-suite.txt |
| UB-4 GitLab sentences | Grep `prompts/setup-kiro.txt`; setup-prompt tests | intact, green: FAILED-TO-REFUTE | full-suite.txt |
| Vacuity scan | `git diff ce950f4..HEAD -- src test` grep for skip, xfail, skipif, importorskip, deselect, commented test/assert | no hit (exit 1). Golden strings come from test-side `job_line`/`billed_total_line` and literals, never product code, and are confirmed against the stdlib-only tag copy (no `github_api` import, `git grep` exit 1): FAILED-TO-REFUTE | none |
| Red for the right reason | `.claude/hooks/red_for_right_reason.py evidence/red/wave-1.txt` | exit 0. The 14 failures are assertion failures (exit 2 against golden 0/1 for an unknown subcommand, missing usage lines, parser without the subcommand), no load error. Red declares `T1 T2`, green declares `T1 T2 T3 T4`: FAILED-TO-REFUTE | red/wave-1.txt |

## Refuted

- **AC-3 (coverage).** Three new lines of `src/payload/scripts/github_api/commands/ci.py` run in no test. These are
  the blank-timestamp `return None` and the naive-timestamp `parsed.replace(tzinfo=timezone.utc)` in
  `_parse_timestamp`, and the negative-duration `return wall_seconds, None` in `_job_billed_minutes`. M48 makes each
  one raise, and all 536 paired tests still pass. No other test references these helpers (Grep over the three suites).
  The AC-3 clause "as `_job_billed_minutes` bills it, else `[wall=? billed=?]`" is unproven for these inputs.
- **AC-7 (oracle not pinned).** Pointing the parity oracle back at `scripts/github_wrapper.py` (M47) leaves all 536
  paired tests green, including `test_the_fork_produces_the_golden_case[get-jobs/...]` and
  `test_the_parsers_match_option_by_option[get-jobs|rerun|cancel]`. Yet `scripts/` contains no `get-jobs` (Grep count
  0). So the "fork" ran the product's `github_api`, already in `sys.modules`, which `scripts/github_wrapper.py`
  imports. That is the product compared with itself, the defect DL-003 exists to remove. At HEAD the oracle is the
  stdlib-only tag copy, but no test fails when that is reverted.

Survivors: M47, M48. Killed: M00-M46.

## Tree restored

Every mutant was restored with `git checkout HEAD -- <file>`, and `git diff HEAD --stat` was empty after each.
Re-confirm on the restored tree: `RT P2` 536 passed, exit 0 (`mutants.txt` RECONFIRM). `git status --porcelain`
shows only `?? .claude/specs/issue-72-get-jobs-rerun-cancel/evidence/verify/`.

REFUTED AC-3 AC-7
