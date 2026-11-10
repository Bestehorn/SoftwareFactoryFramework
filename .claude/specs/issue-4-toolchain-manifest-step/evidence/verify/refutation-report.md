# Refutation report — issue #4, tier S, wave 1 (tasks 1.1 + 1.2)

Round 1: 6524334. Round 2 (delta): 04a0bec. Both on `issue-4-toolchain-manifest-step`, base b496691, regenerated
2026-11-10. Test command: `python scripts/run_tests.py test/test_toolchain_manifest.py`.

## Round 1 (6524334), compressed

Step 1: no CI run (`git ls-remote --heads origin issue-4-toolchain-manifest-step` empty); by the launcher's direction
the CI run on the pushed SHA is the whole-suite verdict. UB-1 + paired files: `210 passed`.

Step 2, one mutant at a time, restored and hash-checked (baseline `34 passed`):

| Id | Mutation | Result |
|---|---|---|
| M0a | tool file absent | 32 errors, 2 passed |
| M0b/c/d | manifest / update.txt / map as on origin/main | 6 / 1 / 1 failed |
| M1 | LAYOUT row `clients/common/phases/` dropped | 7 failed |
| M2 | `fnmatch.fnmatch` for `fnmatchcase` | **34 passed** |
| M3 / M4 / M5 | `deviations` not carried / CRLF / `files` unsorted | 4 / 2 / 4 failed |
| M6 / M7 / M8 | `--check` 0 on a difference / unmapped mapped to itself / git failure exit 1 | 1 / 4 / 1 failed |
| X1 | `git ls-files` instead of the tag | 4 failed |
| X2 | `refs/tags/` prefix dropped | **34 passed** |
| X3 | empty reason accepted | 34 passed (no AC clause) |
| X5 / X6 / X7 | `--check` writes / removed reported as added / `not_installed` never dropped | 2 / 1 / 1 failed |

M2 refuted AC-2 (no source differing only in case) and X2 refuted AC-3 (no non-tag `--release`). CLI runs: v2026.11.09
changes only `release_tag`/`installed`; the origin/main manifest exits 2 naming three unmapped sources, file unchanged.
Security: `git.EXE`, argv list, no shell; eight hostile `--release` values (`--output=…`, `--full-tree`, `HEAD`, `main`,
`;`/`&` chains, `../heads/main`) each exit 2 with `fatal: Not a valid object name refs/tags/<value>`, nothing written.
`v2026.11.10~1` resolves after the prefix (no AC clause). Step 3: no skip/xfail/deselect. Step 4: red capture = 32
fixture `AssertionError: the manifest tool ... is not committed` + 2 assertion failures, no import error;
`.claude/hooks/red_for_right_reason.py` exits 0. Step 5: unreached tool branches serve no AC/UB clause.

## Re-verification (04a0bec, `git diff HEAD~1..HEAD`)

Delta: three tests (5 items) in `test/test_toolchain_manifest.py`, re-captured `evidence/green/wave-1.txt`, this
report; no production line. Step 1: `git ls-remote --heads origin issue-4-toolchain-manifest-step` prints nothing, so
no CI run exists for 04a0bec; the whole-suite verdict stays with CI on the pushed SHA (no local full suite, per the
launcher). R0: `39 passed`.

| Run | Mutation | Result |
|---|---|---|
| M2 | `fnmatchcase`→`fnmatch` in `names` | `1 failed, 38 passed`: `..._differing_only_in_case_names_no_source`, `Failed: DID NOT RAISE ManifestError` |
| C1 | unmutated tool; test patch `str.lower`→`str` (POSIX identity) | `1 failed`: guard `os.path.normcase must fold case here`, `fnmatch(name='templates/ci/github-deploy.yml.template', pat='TEMPLATES/CI/*')` is False |
| X2 | `f"refs/tags/{tag}"`→`tag` in `list_release`, worktree (local `main` exists) | `2 failed, 37 passed`: `[HEAD]`, `[main]` exit 1 (`differs from the regeneration for HEAD`/`main`); `[--full-tree]` passes |
| X2-ci | X2 in a `--no-hardlinks` clone at 04a0bec, detached, its local branch deleted (`git branch --list`: only `(HEAD detached at 04a0bec)`; `rev-parse --verify main` exit 1; tag present) | `1 failed, 38 passed`: `[HEAD]` exit 1; `[main]` passes |
| R1 | none, restored | `39 passed`; `git status --porcelain` empty |

Normcase patch. The fixture loads `scripts/toolchain_manifest.py` from its file and the test calls `tool.derive`, so
the matcher is the production `names`, not a copy. `fnmatch.fnmatch` reads `os.path.normcase` at call time
(`name = os.path.normcase(name)` in CPython 3.14, `C:\Program Files\Python314\Lib\fnmatch.py`, and in 3.10, CI's
`python-version: '3.10'`, cpython `3.10/Lib/fnmatch.py`). C1 shows the patched attribute decides the match, not
Windows' native `ntpath.normcase`. `setattr(target=os.path, ...)` patches whichever module `os.path` is, `posixpath`
on `ubuntu-latest`, so the M2 kill holds on CI. FAILED-TO-REFUTE.

`[HEAD]` without a local `main`. CI runs on `pull_request` and on pushes to `main` (`.github/workflows/ci.yml`); a PR
checkout is detached with no local branch, the shape X2-ci reproduces. There `[main]` stops killing (exit 2 either
way); `[HEAD]` alone kills: HEAD resolves, the listing succeeds, and `--check` exits 1 on `release_tag` `HEAD`. A PR
merge commit's installable trees match: `git diff --name-status refs/tags/v2026.11.10` to HEAD and to origin/main
list the same seven entries; the one `A`, `src/payload/test/test_run_checks.py`, is mapped. FAILED-TO-REFUTE.

Observations, no AC clause:
- `[--full-tree]` kills X2 in neither checkout.
- `[HEAD]`'s kill needs HEAD's installable trees to derive without exit 2, and the test does not assert that.
- X3 still survives.

Step 3 (delta): a Grep of the test file for `skip|xfail|deselect|importorskip|assert True|# def test|# assert` finds
nothing; each new test asserts (raises + message, equality, exit code + bytes). FAILED-TO-REFUTE.

Step 4 (delta): there is no new red capture. The new tests' red is M2 and X2, both assertion failures (`DID NOT RAISE`,
`assert 1 == 2`), not load errors. FAILED-TO-REFUTE.

Step 5 (delta): only test and evidence lines changed; every new test ran in R1.

## Claims

| Claim | Evidence | Result |
|---|---|---|
| AC-1 | M0c, M0d; derivation test | FAILED-TO-REFUTE |
| AC-2 | M1, M7; round 2 M2, C1 | FAILED-TO-REFUTE |
| AC-3 | X1; round 2 X2, X2-ci; stdlib test; security runs | FAILED-TO-REFUTE |
| AC-4 | M1, M3, M4, M5, X1 | FAILED-TO-REFUTE |
| AC-5 | M6, X5 | FAILED-TO-REFUTE |
| UB-1 | gate and integrity test absent from the diff; 210 passed | FAILED-TO-REFUTE |
| UB-2 | M3, X7 | FAILED-TO-REFUTE |

Runs went to the console and are quoted above; per the launcher, only this report remains.

## Restoration

`scripts/toolchain_manifest.py` and `test/test_toolchain_manifest.py` were backed up to `tmp/verify/backup/`. After
each mutant they were restored with `cp` and checked with `cmp`, and both now equal their HEAD blobs. The clone and
`tmp/verify/` are deleted, leaving `tmp/` empty as found. `git status --porcelain` was empty before this report. No
git stash was used.

VERIFIED
