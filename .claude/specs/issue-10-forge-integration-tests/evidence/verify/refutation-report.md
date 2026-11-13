# Refutation report: issue #10 (PR #68, HEAD 12d8df7)

Scope: the diff 590e4a9..12d8df7. Runs in `.claude/worktrees/issue-10` with `venv/Scripts/python.exe`. Paired files:
W `src/payload/test/test_github_wrapper_marker.py`, S `test/test_forge_support.py`, L `test/test_forge_suite_layout.py`,
B `test/test_instruction_corpus_budget.py`. A disposable driver applied one mutant at a time, ran
`scripts/run_tests.py <paired files>`, then wrote the original bytes back and compared sha256 (driver now deleted).
Baseline before mutation: W+S+L+B 55 passed (baseline-green.txt).

| # | Claim | Command | Result | Capture |
|---|---|---|---|---|
| 1 | Full suite green on 12d8df7 | wrapper capture of run 43295116103, not re-fetched (network barred); `git rev-parse HEAD` = its head_sha | FAILED-TO-REFUTE: verify lint, types, security and tests all success. The run's `failure` conclusion comes from `forge` (7 x HTTP 403, F.1, outside this verification's scope) and `report` | full-suite.txt |
| 2 | AC-4.1, AC-4.3, UB-3: refusal, userinfo withheld, marker read | 1a guard call removed, 1c `shown = owner`, 1d marker always set; W | FAILED-TO-REFUTE: 12, 5 and 1 failures | mutant-wave-1.txt |
| 3 | AC-4.1: every name that does not START with `sff-test-` is refused | 1b `repo.startswith(P)` -> `P in repo`; W | REFUTED: 13 passed. No W origin carries `sff-test-` after the start of the name (e.g. `x-sff-test-y`), so a containment guard passes every test | mutant-wave-1.txt |
| 4 | AC-5.1, AC-5.2, AC-5.4: forge job wiring | 1e forge guard line deleted, 1f `persist-credentials: true`, 1g `needs: [verify]`; L | FAILED-TO-REFUTE: 1 failure each | mutant-wave-1.txt |
| 5 | AC-6.3 helper reset, AC-1.1 xdist refusal, AC-6.1 lookup, AC-5.3 empty secret | 1h `credential.helper=` dropped (the run fails at the option assertion, `test_forge_support.py:309`, before any `git credential` runs), 1i, 1j, 1k; S | FAILED-TO-REFUTE: 1 failure each | mutant-wave-1.txt |
| 6 | AC-2.1, AC-2.2: teardown guard | 2a only the owner is compared; S | FAILED-TO-REFUTE: the `a-name-without-the-prefix` and `another-runs-id` cases fail | mutant-wave-2.txt |
| 7 | AC-3.1, AC-3.2: sweep | 2b `>` -> `>=`, 2c owner check dropped, 2d refusal dropped, 2e any exit 1 counted as deleted; S | FAILED-TO-REFUTE: 1, 2, 1 and 1 failures | mutant-wave-2.txt |
| 8 | AC-4.3 marker on every invocation, AC-1.2 run id, AC-8.6 PRODUCT_WRAPPER scope | 2f `-X` dropped, 2g no random part (S); 2h PRODUCT_WRAPPER named in `delete_ephemeral` (L) | FAILED-TO-REFUTE: each killed | mutant-wave-2.txt |
| 9 | AC-6.3, AC-1.4, AC-6.2, UB-2: token and teardown | 3a token in `.git/config`, 3b token logged at DEBUG, 3c deletion skipped on a raise, 3d workspace kept, 3e placeholder accepted, 3f no exclude line, 3g the checkout's `github-pat.txt` read; S | FAILED-TO-REFUTE: all 7 killed | mutant-wave-3.txt |
| 10 | AC-9.1 to AC-9.3: docs | 3h a permission's access, 3i the map's setup-note pointer (L+B), 3j debt line restored; L | FAILED-TO-REFUTE: each killed | mutant-wave-3.txt |
| 11 | AC-1.1 fixture, AC-5.2, AC-5.3 step, AC-7.2, AC-7.3 | 4a `-x`, 4b refusal removed, 4c yield outside the `with`, 4d `collect_ignore`, 4e module scope, 4f one module collected (L); 4g `main` returns 0 on the refusal (S) | FAILED-TO-REFUTE: all 7 killed | mutant-wave-4.txt |
| 12 | No vacuous tests | Grep for skip, xfail, importorskip, deselect, SkipTest, pytest.exit, commented-out tests and collect_ignore in W, S, L and test/forge/ | FAILED-TO-REFUTE: no hits outside L's own detector constants; every test body asserts | (this report) |
| 13 | Red for the right reason | `.claude/hooks/red_for_right_reason.py evidence/red/wave-N.txt`, N = 1 to 4 | FAILED-TO-REFUTE: OK four times. In wave 1, S fails on `_load_by_path`'s file-exists assertion inside each test body, as task 1.3 designed | (this report) |
| 14 | The change's lines are exercised | pytest-cov of W+S over `test/forge` and `src/payload/scripts` | Every new wrapper line ran. Lines of `ephemeral.py` no test exercises: 567, 756, 768-769, 815-825, 837, 841-846, 876-877 | coverage.txt |
| 15 | AC-1.1: a creation that is not private is refused | 3k `if private is not True` -> `if False`; S | REFUTED: 22 passed. No test answers a creation with `private` other than true (line 756) | mutant-wave-3.txt |
| 16 | AC-1.4: the repository and clone are removed whatever ends the run | 3l the refused creation's kept record dropped, so that repository is never deleted; 3n `remove_tree` gives up at the first refused removal; S | REFUTED: 22 passed each. Lines 768-769, 876-877, 815-846 are unexercised | mutant-wave-3.txt |
| 17 | AC-3.1: every run lists and sweeps | 3m a failed listing returns silently and the run goes on; S | REFUTED: 22 passed. Line 567 is unexercised | mutant-wave-3.txt |
| 18 | AC-8.1 to AC-8.6: forge modules (static) | Read of `test/forge/forge_*.py` | FAILED-TO-REFUTE: see the paragraph below | n/a |

Detail for row 18:
- Every invocation goes through `ephemeral_repository.wrapper`, with the marker set and the clone as working directory.
- Each one asserts its exit code, and either its printed JSON or the status GitHub documents for it.
- #17: the issue and pull-request round trips read every step back.
- #27: `repos/get`, `git/get-commit` and `git/get-tree` are checked against the seed.
- #31: `actions` answers `[]`; code scanning, secret scanning and dependabot are called; `checks` is named in the docstring with its reason.
- #32: issues, pulls, reactions, search, activity and `gists/get` (a read) are called.
- No `--path owner=` or `--path repo=` is given, and no fake host is used. Every write lands inside the ephemeral repository.

Unexercised error branches, each raising a `ForgeSuiteError`, that implement no behaviour an acceptance criterion states (not counted as refutations): `ephemeral.py` 250-253, 319-320, 353, 361-362, 386-387, 444, 447, 453-455, 551, 630-631, 662, 731, 793.

`SubprocessGitRunner` (426-431), `conftest.py` and the `__main__` lines of `write_credential.py` run only in the forge job. CI run 43295116103 logs "Created ... sff-test-20261112195559-06227cf0..." and "Deleted ...", and 5 forge tests passed, so the authenticated fetch and the credential step ran there.

Tree restored:
- The sha256 of every mutated file (github_wrapper.py, ci.yml, ephemeral.py, conftest.py, pytest.ini, write_credential.py, forge-suite.md, forLLMConsumption.md, ProjectPlan.md) equals its pre-run value, and so does that of the untouched decision-log.md.
- `git status --porcelain` shows the starting `M decision-log.md` and `?? evidence/regress/`, plus `?? evidence/verify/`.
- After restoration, W+S+L+B: 55 passed (restored-green.txt).
- The ignored `.coverage` that the coverage run wrote has been removed; `.hypothesis/examples` is empty.
- No commit and no stash was made, and no credential was read.

REFUTED AC-1.1 AC-1.4 AC-3.1 AC-4.1
