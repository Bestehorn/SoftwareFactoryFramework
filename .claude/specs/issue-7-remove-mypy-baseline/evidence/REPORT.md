# Evidence report — issue #7: remove the mypy baseline

Tier S, one wave (T1, I1 in two disjoint parts plus the config edit). Branch `issue-7-remove-mypy-baseline`.

| Criterion | Test / evidence | Capture | Verdict |
|---|---|---|---|
| AC-1 no `[[tool.mypy.overrides]]` table sets `ignore_errors` | `test/test_mypy_baseline.py` (+ scanner self-test, 4 cases) | red/wave-1.txt (block present); green/wave-1.txt | green |
| AC-2 mypy clean for linux, win32, darwin | `python -m mypy src --ignore-missing-imports --platform <p>` | ac2/mypy-linux.txt, mypy-win32.txt, mypy-darwin.txt ("Success: no issues found in 56 source files") | green |
| AC-3 the module list goes with the block | the same captures; the `pyproject.toml` diff | ac2/*; commit diff | green |
| AC-4 CI `types` passes on the pushed SHA | CI `verify (types)` | the PR's CI run (id in the PR and the closing comment) | pending CI |
| UB-1 the ten modules' suites pass, nothing relaxed | the named hook suites + test_layout; `src/payload/test/test_merge_steward.py` | green/wave-1.txt (341 passed); green/wave-1-merge-steward.txt (82 passed) | green |
| UB-2 shipped modules stay 3.9 standard library | diff adds only `typing` imports; ruff py39 profile; verifier's 3.9-parser check | verify/refutation-report.md | green |

**Verifier.** VERIFIED: bytecode comparison shows the annotation-only edits compile identically and the rest differ only where the change says; the `assert red is not None` cannot fire; the `suite_slot` fallback still works; undoing six shipped fixes brings back 12 mypy errors; the override block back makes the AC-1 test fail.

**Ledger.** One row: an inline `overrides = [...]` table under `[tool.mypy]` would pass the AC-1 scan (a spelling outside the criterion).

**Whole suite.** The CI run on the pushed head SHA (target: one run).

**Residual.** `CLAUDE.md` "This project" still mentions the baseline; it is corrected in this run's promotion PR (`framework-update-*` branch).
