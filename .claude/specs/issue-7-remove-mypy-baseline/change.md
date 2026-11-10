# Change — issue #7: remove the mypy baseline

Tier: S. Kind: BUGFIX (type debt). Decided: DL-001.

## User Prompts

- "Work this project's open-issue backlog AUTONOMOUSLY, end to end" (the `/auto-work` run).
- Issue #7: "Remove the mypy baseline: fix the 45 findings in 10 modules"
- Issue #7, the operator's request: "Issue to file: remove the baseline module by module by fixing the findings
  (shipped modules first), ending with the overrides block deleted and `mypy src` clean on linux, win32 and darwin
  (`--platform`)."

## Ask

`pyproject.toml` exempts the baseline modules from mypy with a `[[tool.mypy.overrides]]` block
(`ignore_errors = true`) under a BASELINE comment. Fix every finding in those modules at the type level, shipped
modules first, in one change; delete the block and its comment, so `mypy src` is clean for `--platform linux`,
`win32` and `darwin`. `run_checks.py` keeps its one mypy run (DL-001).

## Acceptance criteria

- AC-1 The `pyproject.toml` SHALL contain no `[[tool.mypy.overrides]]` table that sets `ignore_errors`.
- AC-2 WHEN `python -m mypy src --ignore-missing-imports --platform <p>` runs for each of `linux`, `win32` and
  `darwin`, mypy SHALL report no errors.
- AC-3 WHEN the baseline modules' findings are fixed, the same change SHALL delete the baseline's `module` list
  together with its overrides block and BASELINE comment.
- AC-4 WHEN the change is pushed, the CI `types` check SHALL pass on the pushed SHA.

## Unchanged behaviour

- UB-1 The baseline modules' existing suites SHALL CONTINUE TO pass with no assertion relaxed and no test
  skipped, xfailed or deleted.
- UB-2 The shipped modules (`src/hooks/*.py`, `src/payload/scripts/*.py`, `src/payload/src/*.py`) SHALL CONTINUE
  TO be standard-library Python 3.9 code.

## Files and fixes

Every fix is an annotation, a declaration or a narrowing whose outcome equals today's on every input. "Bind
once" rewrites `x.get(k) if isinstance(x.get(k), T) else default` to read `x.get(k)` into a local once and test
that local in the same conditional expression (`local if isinstance(local, T) else default`), so no function
gains a branch; `dict.get` has no side effect, so one read and two reads give the same value.

Shipped (each already carries `from __future__ import annotations`):

- `src/payload/src/aws_config.py` — `_AWSConfig`: declare `_accounts: dict[str, AWSAccount]` at class level,
  annotation only (no value, so no class attribute exists; `__new__` still assigns it).
- `src/hooks/supervisor.py` — `model_replied_since`: bind once for `message`; `load_requests`: annotate
  `found: List[Dict[str, Any]]`.
- `src/hooks/gate_session_register.py` — `_upsert_registry`: bind once for `entry`.
- `src/hooks/hooks.py` — `_is_framework_entry`, `_launch_fields`: bind once for `args`; `registration_check`:
  bind once for `actual` and for `entries`.
- `src/payload/scripts/merge_steward.py` — `Steward.verdict`: in the `if red_before:` branch, narrow `red` with
  `assert red is not None` (`red_before` is set only when `red` is truthy, so it holds on every input);
  `Steward.status`: annotate `rows: List[Dict[str, Any]]`.
- `src/payload/scripts/run_tests.py` — module level: declare `suite_slot: Optional[Callable[..., Any]]` (names
  from `typing`) before the `try` that imports it, so the `except ImportError` fallback `suite_slot = None`
  type-checks; `main` keeps its `suite_slot is None` branch.

Tests:

- `src/payload/test/test_merge_steward.py` — `ms` is loaded with `importlib.util.module_from_spec`, so mypy cannot
  name its classes in a plain or a string annotation: annotate `Any` wherever one names `ms.Issue`,
  `ms.PullRequest`, `ms.Report` or `ms.Steward` (`FakeHost`, `World.tick`, `World.verdict`, `steward_of`);
  `FakeHost.__init__`: widen `prs` to `Dict[int, Dict[str, Any]]`, and delete the `type: ignore[...]` comments on
  `prs` entries (`FakeHost`, `World.amend_pr`, `test_the_train_commit_carries_no_pr_title`), which then cover no
  finding; `World.__init__`: name the `delivery.json` dict apart from the copy loop's `config` path and annotate
  it `Dict[str, Any]` (its `steward` value is a dict);
  `test_a_failed_deploy_job_allowed_to_fail_is_not_a_failure`: annotate `jobs: List[Dict[str, Any]]`.
- `src/hooks/tests/test_session_verdict.py` — `prompt`: annotate `record: dict[str, object]` (it takes the bool
  `isMeta`).
- `src/hooks/tests/test_no_sleep.py` — `decide`: annotate `tool_input: dict[str, object]` (it takes the bool
  `run_in_background`).
- `src/hooks/tests/test_no_idle_wait.py` — `record`: annotate `content: list[dict[str, object]]` (it takes the
  `tool_use` block's `input` dict).

Configuration and the new test:

- `pyproject.toml` — delete the BASELINE comment and the `[[tool.mypy.overrides]]` block with its `module` list;
  `[tool.mypy]` stays.
- `docs/ProjectPlan.md` — delete the mypy-baseline debt line.
- `test/test_mypy_baseline.py` — new; pins AC-1.

## Tests

- AC-1 — `test/test_mypy_baseline.py` (example): reads `pyproject.toml` as text, splits it at each table-header
  line, and fails when a table headed `[[tool.mypy.overrides]]` holds an `ignore_errors` key. A plain-text scan:
  the CI Python (3.10) has no `tomllib`. Red before I1, green after.
- AC-2 — `python -m mypy src --ignore-missing-imports --platform <p>` for `linux`, `win32` and `darwin` after I1,
  each captured under `evidence/` (evidence, not a pytest test).
- AC-3 — the same captures (no override is left to exempt a module) and the I1 diff of `pyproject.toml`.
- AC-4 — the CI `types` group (`run_checks.py --group types`) on the pushed SHA.
- UB-1 — `python scripts/run_tests.py src/hooks/tests/test_session_verdict.py src/hooks/tests/test_no_sleep.py
  src/hooks/tests/test_no_idle_wait.py src/hooks/tests/test_dispatcher.py src/hooks/tests/test_delivery_gates.py
  src/hooks/tests/test_gate_overblock.py src/hooks/tests/test_reinject.py src/payload/test/test_merge_steward.py`,
  then the CI `tests` group. `test_dispatcher.py` drives `hooks.registration_check`, `test_delivery_gates.py`
  drives `supervisor`, `test_gate_overblock.py` drives `gate_session_register`; `test_reinject.py` drives it with
  an existing entry. `aws_config` and `run_tests` have no suite of their
  own; their edits are declarations only.
- UB-2 — the I1 diff adds no import outside `typing`; the CI `lint` group runs ruff at `target-version = "py39"`
  (`src/hooks/ruff.toml`).
- E2E: not applicable — type annotations and narrowing only; no runtime behaviour changes.

## Tasks

Wave 1

- [x] T1 TEST: `test/test_mypy_baseline.py` asserts that no `[[tool.mypy.overrides]]` table in `pyproject.toml`
  sets `ignore_errors`; red against today's `pyproject.toml`. — Files: `test/test_mypy_baseline.py` —
  Validates: AC-1
- [x] I1 IMPL: the fixes under "Files and fixes", shipped modules first, then the `pyproject.toml` deletion;
  green: T1, the UB-1 suites, the AC-2 captures. — Files: `src/payload/src/aws_config.py`,
  `src/hooks/supervisor.py`, `src/hooks/gate_session_register.py`, `src/hooks/hooks.py`,
  `src/payload/scripts/merge_steward.py`, `src/payload/scripts/run_tests.py`,
  `src/payload/test/test_merge_steward.py`, `src/hooks/tests/test_session_verdict.py`,
  `src/hooks/tests/test_no_sleep.py`, `src/hooks/tests/test_no_idle_wait.py`, `pyproject.toml`,
  `docs/ProjectPlan.md` —
  Validates: AC-1, AC-2, AC-3, AC-4, UB-1, UB-2

## Residuals

- mypy's `annotation-unchecked` notes in `src/payload/test/test_reap_agent_temp.py` are notes, not errors;
  `--check-untyped-defs` is outside the ask (`prompt.md`, Out of scope).
- `CLAUDE.md` § This project still names the mypy baseline; `project-specific.md` lists `CLAUDE.md` as toolchain
  (changed by promotion only), so the sentence is corrected in this run's promotion PR (`framework-update-*`
  branch), not edited here.
