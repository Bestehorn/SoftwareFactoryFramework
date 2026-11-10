# Review — design iteration 01 (issue #13), aggregated by the conductor

Combined A+B = 11 (A 1, B 10) across six lanes; all A/B pass the materiality gate. Lane files: `review/<lane>/iteration-01.md`. Security lane CLEAN (6 C).

## Surviving A/B (apply each lane's Proposed-edit unless a decision below overrides it)

| Id | Lane | Subject |
|---|---|---|
| BP-A1 / ST-B1 / SR-B4 / TA-B1 | best-practice, standards, spec-review, test-architect | `sys.stdlib_module_names` and Hypothesis in a shipped 3.9 suite → see X1 (SR-B4's find_spec form is NOT adopted: #17's test-architect showed it cannot fail) |
| BP-B1 | best-practice | GraphQL payload-error rule applies to `mutation` documents only (AC-4.3) |
| TA-B2 | test-architect | AC-2.3 oracle `parse_qsl(..., keep_blank_values=True)` |
| TA-B3 | test-architect | UB-1 one case per caller-used command form incl. `issue start` refusals |
| SR-B1 | spec-review | structural divergences from #17 → see X2 |
| SR-B2 | spec-review | `main` reconfigures stdout/stderr to UTF-8 (`errors="replace"`) as #17 D6 |
| SR-B3 | spec-review | `registry.py` row: edited only when a family needs a record type/field/enum member part 1 lacks, own commit landed first |
| DO-B1 | devops | setup prompts' copy step → see X3 |
| DO-B2 | devops | promotion residual restated → see X4 |

C/D findings of every lane are applied in the same pass (restate, never add) — incl. the security lane's C1–C6 (urllib-parse origin, re-add only on an origin-to-origin hop, Link next URLs on the configured origin only, token whitespace rejected without echo, `.`/`..`/empty path values rejected, random multipart boundary + escaped filename).

## Cross-wrapper decisions (orchestrator, shared with #17)

- X1 The standard-library import check (UB-2) and the Hypothesis properties (AC-2.2, AC-2.3) live in `test/` (framework-only, never installed into projects, runs on CI's Python 3.10) and use `sys.stdlib_module_names`. Shipped suites under `src/payload/test/` stay pytest-only and Python 3.9.
- X2 Adopt #17's forms where no GitLab reason exists: a discovered `gitlab_api/commands/` package whose modules register their subcommands; operations looked up by id through `registry`; a GraphQL record type; test seams that patch `HTTPSHandler.https_open` (and HTTP, so no real socket) with injected `sleep`/`clock`; #17's test-module naming. Exceptions in `gitlab_api/errors.py` (#17 adopts the same module), subclasses named with the base prefix (`GitLabClaimError`, …). Any remaining difference is a row with its forge reason.
- X3 This change edits the setup prompts' GitLab wrapper copy steps (`prompts/setup-claude.txt` Part 5.3, `prompts/setup-kiro.txt` Part 6.2 and their shipped-Python lists) to copy `gitlab_api/` with the entry script (`design-principles.md` 3); a test pins it.
- X4 Promotion residual: the next promotion records `src/payload/scripts/gitlab_api/*` and the new `src/payload/test/` GitLab files under `not_installed`; one findings-ledger row records it.
- X5 Origin = scheme + lower-cased host + port (443 when absent), from the same parse urllib connects with.
