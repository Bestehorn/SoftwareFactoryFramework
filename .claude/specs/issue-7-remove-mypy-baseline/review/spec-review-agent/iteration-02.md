# Spec review — issue-7-remove-mypy-baseline — iteration 02 (tier S, combined, delta)

Delta review of `change.md` against the worktree at `f285222`, covering the B1, C1, C2 and C3 fix sites. Text
that passed in iteration 01 was not re-opened. I copied `src/` to a scratch directory (deleted since) and
applied every fix as `change.md` now states it: the renamed `World.__init__` dict annotated `Dict[str, Any]`,
and each bind-once site rewritten as a fresh local followed by `local if isinstance(local, T) else default`.
With a scratch config that has no override, mypy reported "Success: no issues found in 55 source files" for
`--platform linux`, `win32` and `darwin`, where the unfixed tree reports "Found 45 errors in 10 files". On the
ten changed files, ruff 0.16.5 reported "All checks passed!" under the `src/hooks/ruff.toml` profile (C901 at
`max-complexity = 10`, PLR0912) and "10 files already formatted".

## Findings

### D1 — The `CLAUDE.md` residual names a route the run does not take
Severity: D
Location: change.md § Residuals (the `CLAUDE.md` entry)
Defect: The entry says the sentence "is routed per `issue-filing-discipline.md`". This run instead corrects it
in its promotion PR on a `framework-update-*` branch, which is the "promotion only" route that
`project-specific.md` gives `CLAUDE.md`.
Proposed-edit: replace "so the sentence is routed per `issue-filing-discipline.md`, not edited here." with "so
the sentence is corrected in this run's promotion PR (`framework-update-*` branch), not edited here."

## Judged, no finding

- B1 is fixed. `World.__init__` builds the `delivery.json` dict from an all-string literal and then assigns
  `["steward"] = {...}`. Annotated `Dict[str, Any]` under a new name, it type-checks on all three platforms,
  and the copy loop's `config` path keeps its `Path` type. The test module imports no `Any` today
  (`from typing import Dict, List, Optional, Sequence, Tuple`). The import comes with the `Any` annotations
  that passed in iteration 01, so the fix introduces no new import.
- C1 is fixed. All six bind-once sites are exactly the conditional-expression form the definition now names:
  `supervisor.model_replied_since` (`message`), `gate_session_register._upsert_registry` (`entry`),
  `hooks._is_framework_entry` and `hooks._launch_fields` (`args`), and `hooks.registration_check` (`actual`,
  `entries`). The restricted wording therefore excludes no listed site. The form adds an assignment and no
  branch, and ruff reports no C901 or PLR0912 on the scratch copy.
- C2 is fixed. `docs/ProjectPlan.md` § TODOs and open issues holds the one baseline debt line. Deleting it
  leaves a well-formed one-item list. `docs/ProjectPlan.md` is not in `config/toolchain.json` `files`, so the
  `toolchain-paths` gate does not refuse the edit. No other `docs/*.md` file outside `docs/reports/` describes
  the baseline. I1's Files list names `docs/ProjectPlan.md`.
- C3 is fixed. `src/hooks/tests/test_reinject.py` exists, is in the UB-1 command, and drives `_upsert_registry`
  with an existing registry entry (`owned_arena`, then `session-start`).
- The delta adds no acceptance criterion, requirement or mechanism. `change.md` is within the tier-S cap.

## Coverage

| Criterion | Test / evidence | Can fail |
|---|---|---|
| AC-1 | `test/test_mypy_baseline.py` (T1, example) | yes: red on today's `pyproject.toml` |
| AC-2 | three `mypy src --ignore-missing-imports --platform <p>` captures under `evidence/` | yes: today's tree gives 45 errors; the scratch copy with the fixes as written gives none |
| AC-3 | the AC-2 captures and the I1 diff of `pyproject.toml`; T1 for the `ignore_errors` key | yes |
| AC-4 | CI `types` leg on the pushed SHA | yes |
| UB-1 | the eight named suites locally (including `test_reinject.py`), then the CI `tests` group | yes |
| UB-2 | I1 diff (no import outside `typing`); CI `lint` group (ruff, py39) | yes |
| E2E | not applicable: no runtime behaviour changes | n/a |

## Residuals

- None beyond the existing `CLAUDE.md` entry (D1 corrects its route).

Verdict: CLEAN — READY
