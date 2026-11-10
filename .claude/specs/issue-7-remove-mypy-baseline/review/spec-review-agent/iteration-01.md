# Spec review — issue-7-remove-mypy-baseline — iteration 01 (tier S, combined)

Reviewed `change.md` with `prompt.md` and DL-001, against the worktree at `f285222`. The baseline-free mypy run
(scratch config without the override) reproduces the spec's finding set on linux, win32 and darwin. The spec's
per-symbol fixes, applied to a scratch copy of `src/` (deleted since), make mypy clean on all three platforms and
ruff clean, except for B1.

## Findings

### B1 — Renaming the `World.__init__` dict leaves a mypy error, so AC-2 is not met
Severity: B
Location: change.md § Files and fixes (Tests, `src/payload/test/test_merge_steward.py`); AC-2
Defect: A dict that is renamed apart from the loop's `config` path but left unannotated is inferred `dict[str, str]`
from its all-string literal. Its next statement, `["steward"] = {...}`, is then an `[assignment]` error
("expression has type dict[str, object], target has type str"). Reproduced with every other listed fix applied.
Material-because: AC-2 — after I1 is implemented as written, `mypy src` reports one error.
Proposed-edit: replace "`World.__init__`: name the `delivery.json` dict apart from the copy loop's `config` path;"
with "`World.__init__`: name the `delivery.json` dict apart from the copy loop's `config` path and annotate it
`Dict[str, Any]` (its `steward` value is a dict);"

### C1 — "Bind once" allows a statement form that breaks the ruff complexity cap in `_upsert_registry`
Severity: C
Location: change.md § Files and fixes (the "Bind once" definition; `src/hooks/gate_session_register.py`); UB-2
Defect: `_upsert_registry` is already at the `src/hooks/ruff.toml` mccabe cap. The conditional-expression form of
the rewrite keeps it there. The statement form the wording also allows (`v = x.get(k)`, then
`if not isinstance(v, T): v = default`) pushes it over the cap: ruff 0.16.5 reports C901 "11 > 10" on the
scratch copy, so the CI `lint` group goes red. That form also adds a branch.
Material-because: regression (the CI `lint` group goes red).
Proposed-edit: in the "Bind once" sentence, replace "and test that local" with "and test that local in the same
conditional expression (`local if isinstance(local, T) else default`), so no function gains a branch".

### C2 — Two documents describe the deleted baseline as current debt
Severity: C
Location: change.md § Files and fixes (Configuration and the new test); § Residuals
Defect: `docs/ProjectPlan.md` § TODOs and open issues ("the mypy baseline in `pyproject.toml` (10 modules) is to
be removed module by module") and `CLAUDE.md` § This project ("`pyproject.toml` carries a mypy baseline of 10
modules, removed as each is fixed") both describe the block this change deletes. Neither is in the file list, but
`post-activity.md` item 3 says to update `docs/` for any change.
Proposed-edit: under "Configuration and the new test" add "- `docs/ProjectPlan.md` — delete the mypy-baseline
debt line."; under `## Residuals` add "- `CLAUDE.md` § This project still names the mypy baseline;
`project-specific.md` lists `CLAUDE.md` as toolchain (changed by promotion only), so the sentence is routed per
`issue-filing-discipline.md`, not edited here."

### C3 — UB-1's local run leaves out the suite that calls `_upsert_registry` with an existing entry
Severity: C
Location: change.md § Tests (UB-1)
Defect: `test_gate_overblock.py` reaches `_upsert_registry` only when the registry has no entry for the session
(`test_f6_happy_path_seeds_and_registers`). The path where the entry already exists as a dict is the one the
rewrite must keep by identity. Only `src/hooks/tests/test_reinject.py` runs that path (`owned_arena`, then
`dispatch` of `session-start`).
Proposed-edit: add `src/hooks/tests/test_reinject.py` to the UB-1 command, and append to the next sentence
"`test_reinject.py` drives it with an existing entry".

## Judged, no finding

- Behaviour-neutral fixes. Every bind-once site reads a plain dict from `json.loads` (registry, transcript record,
  `settings.json`, `registration_block()`), so one read gives the same value as two. `_upsert_registry` still
  mutates the existing entry object.
- The `assert red is not None`. It sits under `if red_before:`, and `red_before` is non-None only when `red` is
  truthy; nothing reassigns `red` in between. `test_an_issue_landed_into_a_red_environment_is_not_blamed` runs it.
  Neither linter flags it: `[tool.bandit]` skips B101 (the setup prompt prescribes the same skip for projects),
  and no ruff `S` rule is selected.
- Declarations. The `_accounts` and `suite_slot` declarations bind no value. A pre-declared
  `Optional[Callable[..., Any]]` followed by the import type-checks, and ruff reports no F811.
- Python 3.9, standard library only. The new shipped annotations are `typing` names, or a class-level annotation
  under `from __future__ import annotations`, which all six shipped modules carry. The only new import is `typing`
  in `run_tests.py`. The test-local `dict[...]` annotations are never evaluated.
- `Any` in the tests hides no defect. mypy already cannot resolve the `ms.*` names (`name-defined`) and treats
  them as `Any`. The `prs` attribute reads were already under `type: ignore`. The two sites without an ignore
  (`prs[1]["pr"].head_sha`, `jobs[1]["allow_failure"] = False`) are correct at runtime (`ms.PullRequest` has
  `head_sha`; `jobs[1]` is a dict).
- UB-1 suites exercise the changed code. Through `registration_check`, `test_dispatcher.py` reaches
  `_is_framework_entry` and `_launch_fields`, with `args` both a list and absent. `test_delivery_gates.py` reaches
  `model_replied_since` in the recovered case. No test drives `load_requests` or `Steward.status`, but their edits
  are annotations only, like those in `aws_config` and `run_tests`.
- T1 and AC-1. CI runs Python 3.10 (`.github/workflows/ci.yml`), which has no `tomllib`, so the text scan is the
  right tool. T1 is red against today's `pyproject.toml`.
- Security: no auth, IAM or secret surface is touched, and the `isinstance` guards on registry and settings JSON
  stay. Operability: `run_checks.py` and CI are unchanged (DL-001).

## Coverage

| Criterion | Test / evidence | Can fail |
|---|---|---|
| AC-1 | `test/test_mypy_baseline.py` (T1, example) | yes: red on today's `pyproject.toml` |
| AC-2 | three `mypy src --ignore-missing-imports --platform <p>` captures under `evidence/` | yes: B1 fails it as written |
| AC-3 | the AC-2 captures and the I1 diff of `pyproject.toml`; T1 for the `ignore_errors` key | yes |
| AC-4 | CI `types` leg on the pushed SHA | yes |
| UB-1 | the named suites locally (plus `test_reinject.py`, C3), then the CI `tests` group | yes |
| UB-2 | I1 diff (no import outside `typing`); CI `lint` group (ruff, py39) | yes |
| E2E | not applicable: no runtime behaviour changes | n/a |

## Residuals

- None beyond the `CLAUDE.md` sentence in C2.

Verdict: NOT-CLEAN (0 A, 1 B) — NOT-READY
