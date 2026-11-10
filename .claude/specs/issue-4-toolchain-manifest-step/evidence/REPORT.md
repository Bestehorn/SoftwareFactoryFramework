# Evidence report — issue #4: a committed tool maintains config/toolchain.json

Tier S, one wave (1.1 TEST, 1.2 IMPL; 1.1 reopened once). Branch `issue-4-toolchain-manifest-step`.

| Criterion | Test (`test/test_toolchain_manifest.py`) | Capture | Verdict |
|---|---|---|---|
| AC-1 the committed procedure rewrites `release_tag` | step-7 and map tests; derivation sets tag and date; default date | red/wave-1.txt; green/wave-1.txt | green |
| AC-2 every installable release file is in `files` unless `not_installed` names it (case-sensitive) | mapping rows, sorted files, unmapped-source and collision errors, case-only pattern excludes nothing | red; green; verify (M1, M7, M2 killed) | green |
| AC-3 committed, stdlib-only, reads the release tag with git, never a working tree | stdlib-import test; non-tag releases (`main`, `HEAD`, an option) exit 2 | green; verify (X1, X2 killed) | green |
| AC-4 regenerating the committed manifest reproduces it byte for byte | regeneration from the committed `release_tag`/`installed`; LF, indent, key order | green; verify (M3, M4, M5 killed) | green |
| AC-5 `--check` exits 0 when current, 1 when not, writes nothing | check tests | green; verify (M6, X5 killed) | green |
| UB-1 the integrity test and the gate still read the manifest | not in the diff; `test/test_toolchain_integrity.py` in the green capture | green | green |
| UB-2 `deviations`/`not_installed` survive unless the release drops their path | drop-and-report test | green; verify (M3, X7 killed) | green |

Green capture (`# tasks: 1.1 1.2`): the module with `test/test_toolchain_integrity.py`, `test/test_layout.py`, `test/test_instruction_corpus_budget.py`, 216 passed. Direct run: `python scripts/toolchain_manifest.py --release v2026.11.10 --installed 2026-11-10 --check` → current, exit 0; for v2026.11.09 (the release the issue named) the verifier's run derived 110 files equal to the committed set, only `release_tag` and `installed` differing.

**Verifier.** First pass REFUTED AC-2 (`fnmatch` instead of `fnmatchcase` survived) and AC-3 (a dropped `refs/tags/` prefix survived); 1.1 reopened; re-verification VERIFIED, incl. a CI-shaped clone with no local `main`.

**Security.** `--release` reaches git only as `refs/tags/<value> --` in an argv list; eight hostile values exited 2 with no side effect.

**Whole suite.** The CI run on the pushed head SHA (target: one run).
