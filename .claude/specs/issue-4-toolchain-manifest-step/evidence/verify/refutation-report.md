# Refutation report — issue #4, tier S, wave 1 (tasks 1.1 + 1.2)

Subject: 6524334 on `issue-4-toolchain-manifest-step` (base b496691). All runs regenerated 2026-11-10. Test
command: `python scripts/run_tests.py test/test_toolchain_manifest.py` (baseline `34 passed`).

## Step 1 — whole-suite verdict

Not graded. `git ls-remote --heads origin issue-4-toolchain-manifest-step` is empty, so no CI run exists for 6524334.
By the launcher's direction, the CI run on the SHA pushed after this report is the whole-suite verdict; no local full
suite was run. UB-1 plus paired: `test_toolchain_integrity.py test_gate_toolchain_paths.py test_layout.py
test_toolchain_manifest.py` → `210 passed`.

## Step 2 — mutants (one at a time, restored and hash-checked after each)

| Id | Mutation | Result | Killed by |
|---|---|---|---|
| M0a | tool file absent (wave revert) | 2 passed, 32 errors | fixture `assert SCRIPT.is_file()` |
| M0b | `config/toolchain.json` as on origin/main | 6 failed | AC-4/AC-5 CLI tests, `exit 2` |
| M0c | `prompts/update.txt` as on origin/main | 1 failed | step-7 test |
| M0d | `docs/forLLMConsumption.md` as on origin/main | 1 failed | map test |
| M1 | LAYOUT row `clients/common/phases/` dropped | 7 failed | mapping[phases], sorted, AC-4, AC-5 |
| M2 | `fnmatch.fnmatch` for `fnmatchcase` | **34 passed** | none |
| M3 | `deviations` not carried | 4 failed | AC-4, written form, check, UB-2 |
| M4 | manifest written with CRLF | 2 failed | "the manifest is written with LF line endings" |
| M5 | `files` in source order | 4 failed | "files must be sorted by install path", AC-4 |
| M6 | `--check` returns 0 on a difference | 1 failed | later-date check, `exit 0` |
| M7 | unmapped source mapped to itself | 4 failed | 3 unmapped params, CLI exit-2 test |
| M8 | git failure exits 1 | 1 failed | unknown-tag test, `exit 1` |
| X1 | `git ls-files` (index) instead of the tag | 4 failed | AC-4, AC-5, unknown tag |
| X2 | `refs/tags/` prefix dropped (`tag, "--"`) | **34 passed** | none |
| X3 | empty `not_installed`/`deviations` reason accepted | **34 passed** | none (no AC clause, see step 5) |
| X5 | `--check` writes the manifest | 2 failed | "--check must not write the manifest" |
| X6 | removed entries reported as added | 1 failed | report test |
| X7 | `not_installed` entries never dropped | 1 failed | UB-2 test |
| R0 | restored tree, no mutant | 34 passed | — |

Surviving mutants that remove a specified behaviour:

- **M2 → AC-2.** AC-2 names `fnmatch.fnmatchcase`. On this host `fnmatch.fnmatch('templates/ci/x.yml',
  'Templates/CI/*')` prints `True` and `fnmatchcase` prints `False`, so on Windows, where the promotion runs, the
  mutant changes which sources a pattern excludes. On CI's `ubuntu-latest` it is equivalent, because `normcase` is
  the identity on POSIX. No test pairs an entry with a source that differs only in case.
- **X2 → AC-3.** AC-3 fixes the listing to `git ls-tree -r -z --name-only refs/tags/<tag> --`. Under X2, git
  receives the bare value. `--release HEAD` or `main` would then list a branch, and `--release=--<opt>` would reach
  git as an option. All 34 tests still pass. No test feeds a non-tag ref. The unmutated code is correct (security
  lens below); the criterion has no test.

## Launcher item 2 — direct CLI runs

- `--release v2026.11.10 --installed 2026-11-10 --check` → `... config\toolchain.json is current for v2026.11.10
  (installed 2026-11-10)`, exit 0.
- `--release v2026.11.09 --installed 2026-11-09 --manifest <tmp copy>` → `wrote ...: v2026.11.09, installed
  2026-11-09, 110 files`, exit 0. Compared to the committed file (ignoring whitespace), only `release_tag` and
  `installed` change. No `added`, `removed` or `dropped` lines are logged. This manifest is coherent and correct per
  AC-1, AC-2 and UB-2. `git diff --name-status v2026.11.09 v2026.11.10` over the installable trees lists only `M`
  entries, so the path set, the deviation and every `not_installed` path are the same in both tags. The tool does not
  consult `.claude/FRAMEWORK_COMMIT`, and no AC asks it to.
- Same release on the origin/main manifest, which lacks the five new entries → `ERROR: release sources neither mapped
  by the install layout nor named under not_installed ...: clients/claude/README.md, templates/README.md,
  templates/pre-commit-config.yaml.template`, exit 2. The copy is unchanged: its `git hash-object` equals the
  origin/main blob 1058c92. This is the loud failure AC-2 requires. `src/hooks/ruff.toml` and
  `templates/docs/README.md` are mapped by LAYOUT rows; their entries keep them out of `files`.

## Launcher item 3 — security lens

git resolves to `C:\Program Files\Git\mingw64\bin\git.EXE`, an executable and not a `.cmd` shim; the argv is a list
and no shell runs. Each value below was run as `--release=<value> --check --manifest <tmp copy>`. Each exited 2 with
`fatal: Not a valid object name refs/tags/<value>`:

- `--output=tmp/verify/injected-output.txt`
- `--full-tree`
- `HEAD`
- `main`
- `v2026.11.10; echo pwned > ...`
- `v2026.11.10&echo pwned>...`
- `v2026.11.10 --full-tree`
- `../heads/main`

Afterwards Glob finds no `injected*` or `pwned*` file; the copy's hash is unchanged. FAILED-TO-REFUTE for the
implementation.

Observation, no AC clause: `v2026.11.10~1` resolves, because git revision syntax applies after the prefix, and
`--check` exits 1. Without `--check` the tool would write `release_tag: v2026.11.10~1`.

## Step 3 — vacuity scan

A Grep of `test/test_toolchain_manifest.py` for `skip|xfail|deselect|importorskip|assert True|# def test` finds only
`parametrize` and `usefixtures` marks. Every test asserts. The diff touches neither `pyproject.toml` nor any
`conftest.py`. FAILED-TO-REFUTE.

## Step 4 — red for the right reason

The committed `evidence/red/wave-1.txt` holds 32 fixture-setup errors and 2 failures:

- the 32 errors are `AssertionError: the manifest tool scripts/toolchain_manifest.py is not committed`;
- the 2 failures are on the step-7 and map assertions;
- no `ImportError` or collection error appears.

`.claude/hooks/red_for_right_reason.py` exits 0 on the committed capture and on the regenerated M0a. The red at
fixture level is the explicit precondition assertion that task 1.1 prescribes; the module is never imported while
absent, so it is not a load error. Judged red for the right reason. FAILED-TO-REFUTE.

## Step 5 — coverage of the change

The diff lines of `config/toolchain.json`, `prompts/update.txt` and the map are each pinned (M0b to M0d). In the tool,
no test input reaches these branches:

- the `string_section` refusal (X3 survives);
- the non-dict guard in `derive`;
- the `list_release` OSError and empty-listing refusals;
- the `read_manifest` errors;
- the write OSError;
- the `iso_date` refusal;
- the generic handler in `main`;
- the `REQUIRED_KEYS` `setdefault` for a missing key.

None serves an AC or UB clause; they serve the Files-section exit-2 contract, whose git and unmapped cases are tested
(M7, M8). Not graded.

## Claims

| Claim | Command / evidence (capture id) | Result |
|---|---|---|
| AC-1 | M0c, M0d; derivation test; CLI run A | FAILED-TO-REFUTE |
| AC-2 | M1, M7, M2; CLI run C | REFUTED (M2 survives) |
| AC-3 | X1, X2; stdlib test; security runs | REFUTED (X2 survives) |
| AC-4 | M1, M3, M4, M5, X1 | FAILED-TO-REFUTE |
| AC-5 | M6, X5 | FAILED-TO-REFUTE |
| UB-1 | gate and integrity test absent from the diff; 210 passed | FAILED-TO-REFUTE |
| UB-2 | M3, X7; UB-2 test | FAILED-TO-REFUTE |

Captures were written to `tmp/verify/<id>.txt` and deleted after grading, because the launcher allows only this report
to remain. Their summary lines are quoted above.

## Restoration

The four implementation files were backed up byte for byte to `tmp/verify/backup/` and restored after every mutant.
The final SHA-256 comparison matched for all four, R0 gave `34 passed`, `git status --porcelain` shows only this
report, and `tmp/verify/` is deleted.

REFUTED AC-2 AC-3
