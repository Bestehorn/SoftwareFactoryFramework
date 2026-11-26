# Evidence report — issue #72: get-jobs, rerun and cancel in the product GitHub wrapper

Tier S. Branch `issue-72-get-jobs-rerun-cancel`. Tests: golden cases in `src/payload/test/github_wrapper_fixtures.py`
`CASES`, run on the product by `src/payload/test/test_github_wrapper_compat.py` and on the replaced copy
(`v2026.11.10.1:scripts/github_wrapper.py`) by `test/test_github_wrapper_fork_parity.py`.

| Criterion | Tests | Red | Green | Verdict |
|---|---|---|---|---|
| AC-1 get-jobs request and lines | `get-jobs/exit-0/latest-attempt`, `all-attempts` | red/wave-1 | green/wave-1, rework-1 | proven |
| AC-2 `--failed-only`, attempt suffix | `failed-only`, `all-attempts`, `every-column` | red/wave-1 | green/wave-1, rework-1 | proven |
| AC-3 steps, timing, runner, TOTAL, step lines | `every-column`, `failed-only`, `timing-edges` (rework) | red/wave-1 | green/rework-1 | proven |
| AC-4 rerun | `rerun/exit-0/whole-run`, `failed-only` | red/wave-1 | green/wave-1 | proven |
| AC-5 cancel | `cancel/exit-0/requested` | red/wave-1 | green/wave-1 | proven |
| AC-6 errors | the three `exit-1` rows, `_refusal_cases` | red/wave-1 | green/wave-1 | proven |
| AC-7 parsers, usage, oracle | parser-parity rows, `test_the_usage_names_the_ci_commands`, `test_the_oracle_is_the_replaced_copy` (rework) | red/wave-1 | green/rework-1 | proven |
| AC-8 prose | the diff of `prompts/setup-claude.txt`, `prompts/setup-kiro.txt`, `CLAUDE.md`, `docs/ci-capacity-ladder.md` | — | — | checked on the diff |
| UB-1 to UB-4 | the existing golden cases and parser rows on both sides; `test_the_wrapper_imports_only_the_standard_library`; `test_toolchain_integrity.py`; the setup-prompt copy-step tests | — | green/wave-1, rework-1 | proven |

## Verification

- Round 1 (`evidence/verify/refutation-report.md`): 47 of 49 mutants killed; REFUTED AC-3 (three timing branches no
  test reached, M48) and AC-7 (the parity oracle pointed back at `scripts/github_wrapper.py` went unnoticed, M47).
  Test-only rework (DL-005), green capture `green/rework-1.txt` (1439 passed).
- Round 2 (`evidence/verify/refutation-report-2.md`): M47 and M48 re-applied against the reworked tests.

## CI

The PR's CI run is the whole-suite verdict; its run id and SHA are in the PR and the closing note.
