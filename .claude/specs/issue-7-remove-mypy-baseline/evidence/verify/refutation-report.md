# Refutation report — issue #7, remove the mypy baseline (tier S)

Tree: branch `issue-7-remove-mypy-baseline` at 402f79d (rebased on origin/main 3d6cfc2, not pushed). Interpreters:
venv CPython 3.14.2 (pytest 9.2.0, mypy 2.4.1) and uv CPython 3.13.12; no 3.9 interpreter is installed.

## Step 1 — whole-suite verdict

`git ls-remote origin issue-7-remove-mypy-baseline` prints nothing: no pushed SHA, no CI run. Per the dispatch the
suite was not run locally; the whole-suite verdict and AC-4 are the CI run on the SHA pushed after this report. Per
the dispatch the worktree changes only by this file, so mutant runs are quoted here, not in `mutant-wave-N.txt`.

## Claims

| Claim | Command | Result |
|---|---|---|
| AC-1 no exempting overrides table | Read `pyproject.toml` (`[tool.mypy]`: 3 keys, no `overrides`); AC-1 test in the UB-1 run | FAILED-TO-REFUTE |
| T1 kills its mutant (M1: BASELINE block re-inserted) | `python scripts/run_tests.py test/test_mypy_baseline.py` | FAILED-TO-REFUTE: `1 failed, 4 passed`, AssertionError at test_mypy_baseline.py:53 listing the 10 modules; restored, `cmp` identical |
| AC-2 mypy clean, 3 platforms | `python -m mypy src --ignore-missing-imports --platform <linux, win32, darwin>` | FAILED-TO-REFUTE: `Success: no issues found in 56 source files`, exit 0, each |
| AC-2 fixes are load-bearing (M2: hooks `_launch_fields`, merge_steward assert, run_tests declaration, aws_config `_accounts`, supervisor `found`, gate_session_register `entry` undone) | mypy `--platform linux` | FAILED-TO-REFUTE: `Found 12 errors in 6 files` (hooks.py:460, merge_steward.py:1763, run_tests.py:68, aws_config.py x5, supervisor.py:128, gate_session_register.py x3); all 7 files restored, `cmp` identical |
| AC-3 list, block, comment deleted | `git diff origin/main..HEAD -- pyproject.toml` | FAILED-TO-REFUTE: 19 lines deleted, `[tool.mypy]` kept |
| AC-4 CI `types` on the pushed SHA | none possible | NOT GRADED: no CI run exists |
| UB-1 suites pass, nothing relaxed | `run_tests.py` the 8 UB-1 hook files + test_mypy_baseline + test_layout; `run_tests.py src/payload/test/test_merge_steward.py` | FAILED-TO-REFUTE: `341 passed in 18.13s`; `82 passed in 362.60s`; test hunks touch annotations, `type: ignore` comments and one local name, no assert |
| UB-2 3.9 stdlib | `ast.parse(..., feature_version=(3, 9))` on the 6 shipped files; `ruff check` + `ruff format --check` (py39 profile) on the 11 changed .py files | FAILED-TO-REFUTE: all parse; `All checks passed!`; `11 files already formatted`; the one new import is `typing` |
| Behaviour neutrality | bytecode of every code object, origin/main vs HEAD, on 3.14.2 and 3.13.12; code review | FAILED-TO-REFUTE (below) |
| Vacuity | read test_mypy_baseline.py and the test hunks | FAILED-TO-REFUTE |
| Red for the right reason | read evidence/red/wave-1.txt; M1 reproduced it | FAILED-TO-REFUTE |
| Coverage of the change | suite grep + reached-branch reading | FAILED-TO-REFUTE |

## Behaviour neutrality

- Identical bytecode: `supervisor.load_requests`, `merge_steward.Steward.status`. `run_tests` `<module>` and the
  `_AWSConfig` class body differ only by storing an annotation.
- Bytecode differs exactly in the bind-once functions (`hooks._is_framework_entry`, `_launch_fields`,
  `registration_check`, `supervisor.model_replied_since`, `gate_session_register._upsert_registry`), in
  `Steward.verdict` (the assert), and in `_NoHost`: only its `__firstlineno__` constant (2214 to 2215), `co_code` equal.
- Bind-once: every receiver is a builtin `dict` from `json.loads` behind an `isinstance(..., dict)` guard (`data`,
  `record`, `hook`) or the guarded result of one (`actual`); the only callers of `_is_framework_entry` and
  `_launch_fields` are `registration_check` and `_field_drift`, on JSON-loaded entries. `dict.get` is pure, so one
  read returns the object two reads return; type test and default literal unchanged. No input changes an outcome.
- `assert red is not None`: `_status_lines` returns `Dict[Tuple[str, str], Tuple[str, str]]`, so `red` is None or a
  2-tuple; `red_before` is non-None only through the `red and ...` operand and `red` is not rebound before the
  assert. It cannot fire. `test_an_issue_landed_into_a_red_environment_is_not_blamed` runs that branch (second
  `verdict` with `red-since` set) and passes. Bandit skips B101 here (`[tool.bandit]`) and in set-up projects
  (`prompts/setup-claude.txt`, `prompts/setup-kiro.txt`); the ruff profile selects no S rules.
- `run_tests.suite_slot`: imported with `src/payload/scripts` on the path it is `suite_semaphore.suite_slot`,
  `SLOT_IMPORT_ERROR` `''`; with `sys.modules['suite_semaphore'] = None` it is `None` with
  `ModuleNotFoundError: import of suite_semaphore halted; None in sys.modules`. Module `__annotations__` holds the
  string `'Optional[Callable[..., Any]]'` (PEP 563): never evaluated, binds no name. Same on 3.14.2 and 3.13.12.
- `_AWSConfig._accounts`: `'_accounts' in vars(cls)` False, `hasattr(cls, '_accounts')` False, annotation stored as
  the string `'dict[str, AWSAccount]'`, on both interpreters.

## Python 3.9

All six changed shipped modules carry `from __future__ import annotations`, so the new annotations are strings at
runtime (shown above); `Optional[Callable[..., Any]]` and `dict[str, ...]` (PEP 585) are valid 3.9 even evaluated.
The hunks hold no `X | Y`, `match` or parenthesised context manager. No 3.9 interpreter ran (none installed); the
evidence is the 3.9 parser mode, the py39 ruff profile and the string-stored annotations.

## Vacuity and red capture

test_mypy_baseline.py: no skip, xfail or deselection; both tests assert (`not found`; `len(found) == 1` and the
right table) and four parametrized cases pin the scanner. evidence/red/wave-1.txt: `# tasks: T1`, 5 collected,
`1 failed, 4 passed`, AssertionError at line 53 printing the baseline body — an assertion, not a load error.

## Coverage of the change

Runtime-changing lines are reached by the UB-1 suites: test_dispatcher.py (`registration_check` and both hooks
helpers), test_delivery_gates.py (supervisor), test_gate_overblock.py and test_reinject.py (`_upsert_registry`),
the red-environment test (the assert). The declarations in run_tests.py and aws_config.py and the identical-bytecode
annotations serve AC-2, and M2 shows the mypy check fails without them.

## Observations (not refutations)

- O1 `evidence/ac2/mypy-*.txt` say "55 source files": they and the green captures were taken on the pre-rebase base
  f13cf20, which lacks f124f53 (adds `src/payload/test/test_run_checks.py`). At 402f79d mypy checks 56 files, clean
  on all three platforms, and the suites give the same counts (341, 82). Regenerate the captures on the pushed SHA.
- O2 An inline-table override (`overrides = [{ module = ["hooks"], ignore_errors = true }]` under `[tool.mypy]`) is
  honoured by mypy (hooks.py:460 vanished: 11 errors in 5 files) and passes the AC-1 test (`5 passed`). It is outside
  the spec's header-scan plan and outside this procedure's refutation grounds (stress beyond the configured
  examples): a findings-ledger candidate.

## Tree restoration

Seven files copied to `tmp/verify/`, mutated, restored with `cp -p`, each `cmp`-identical; the probe script and
`tmp/` deleted (absent before). `git status --porcelain` empty before this file; the ignored set is unchanged
(`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `reports/`, `src/hooks/.ruff_cache/`); HEAD 402f79d.

AC-4 and the whole suite are the post-push CI run's; every gradable claim survived.

VERIFIED
