# Prompt — issue #7: remove the mypy baseline

Tier: S — type-level fixes inside existing modules, no new interface; no finding marks a runtime defect (each
was read during prompt synthesis: they are missing or too-wide annotations, narrowing mypy cannot see, and test
helpers typed against a dynamically loaded module).

Kind: BUGFIX (type debt).

## Goal

`pyproject.toml` exempts 10 modules from mypy with a `[[tool.mypy.overrides]]` block (`ignore_errors = true`)
and a BASELINE comment, recorded at the self-install of release v2026.11.09. Remove the baseline by fixing every
finding; done is the overrides block and its comment deleted and `mypy src --ignore-missing-imports` clean for
`--platform linux`, `win32` and `darwin`.

Measured during prompt synthesis (2026-11-10, mypy from the project venv, baseline removed via a scratch config,
`origin/main` f285222): the same 45 errors in 10 files on all three platforms — `aws_config` (`_accounts`
assigned in `__new__` without a class-level annotation), `supervisor`, `gate_session_register`, `hooks`
(Optional/union values used without narrowing), `merge_steward` (`Steward.verdict`: a tuple-or-None indexed
after a truthiness test on a derived value; `Steward.status`: `str + object` from a row dict typed `object`),
`run_tests` (a fallback `suite_slot = None`), `test_merge_steward` (annotations naming `ms.Issue`,
`ms.PullRequest`, `ms.Report`, `ms.Steward` of a module loaded with importlib, and stale `type: ignore` codes),
`test_session_verdict`, `test_no_sleep`, `test_no_idle_wait` (test tables typed too narrowly).

## Scope (the ask)

- Fix each module's findings at the type level — annotations, explicit narrowing (`assert x is not None` only
  where the value is provably non-None, else an explicit branch that keeps today's behaviour), correctly typed
  fallbacks, corrected `type: ignore[...]` codes only where no annotation can express the dynamic load — shipped
  modules first. No behaviour change: every existing test stays green unchanged (UB-1); shipped modules stay
  Python 3.9 standard library (UB-2: `from __future__ import annotations` where a 3.10 annotation form is used).
- Delete the `[[tool.mypy.overrides]]` block and its BASELINE comment from `pyproject.toml`.
- Decided (DL-001), the issue's first open question: `run_checks.py`'s `types` group keeps one mypy run (shipped
  behaviour for every project; and `run_checks.py` is issue #3's file in this run). AC-2 is proven once by
  captured three-platform runs; CI (Linux) and the pre-push hook (the developer's platform) keep it enforced.
- Decided (DL-001), the second open question: no finding in a shipped module marks a runtime defect, so the tier
  stays S.
- A test `test/test_mypy_baseline.py` pinning AC-1 (no `[tool.mypy]` override in `pyproject.toml` sets
  `ignore_errors`), so the baseline cannot silently return.

## Out of scope

- `--check-untyped-defs` (mypy's `annotation-unchecked` notes in `test_reap_agent_temp.py` are notes, not errors).
- `src/payload/scripts/run_checks.py`.

## Tests

AC-1 by the new test; AC-2 by captured `mypy` runs for the three platforms under `evidence/`; AC-3 by the same
captures (the module list is deleted with the block); AC-4 by the CI `types` leg on the pushed SHA; UB-1 by the
10 modules' own suites run locally (`python scripts/run_tests.py <their test files>`) and by CI.
E2E: not applicable — type annotations only; no runtime behaviour changes.
