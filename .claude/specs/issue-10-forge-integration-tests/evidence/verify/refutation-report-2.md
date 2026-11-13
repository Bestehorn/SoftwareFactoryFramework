# Refutation report, round 2 (delta): issue #10, test-only rework on HEAD 12d8df7

Scope: round 1's rows 3, 15, 16 and 17 (refutation-report.md) after the DL-007 rework. The rework is uncommitted on
12d8df7 and changes only W `src/payload/test/test_github_wrapper_marker.py` and S `test/test_forge_support.py`.
`git diff --quiet -- src/payload/scripts/github_wrapper.py test/forge/ephemeral.py` exits 0, so the production code
is round 1's.

Method: a disposable driver (now deleted) applied each surviving mutant, one at a time, by a single byte replacement
of its recorded target text. It ran `venv/Scripts/python.exe scripts/run_tests.py <W or S>` from the worktree, wrote
the original bytes back, and compared sha256 and `git diff --quiet -- <file>`. Every round-2 mutation diff carries the
blob id round 1 recorded: 1b `4ae9739..9cf78df`, 3k `6ed17b8..8769e35`, 3l `..9ee61e5`, 3m `..b1d267f`,
3n `..36387fd`. The mutants that round 1 killed were not re-run, and `test/forge` was not run.

| # | Claim (round-1 row) | Command | Result | Capture |
|---|---|---|---|---|
| R1 | Baseline: W+S+L+B green on the reworked tree | `run_tests.py W S L B` | FAILED-TO-REFUTE: 70 passed (round 1: 55; W +10, S +5) | round2-baseline-green.txt |
| R2 | AC-4.1: a name that does not START with `sff-test-` is refused (row 3) | 1b `repo.startswith(P)` -> `P in repo`; W | FAILED-TO-REFUTE: 10 failed, 13 passed. Every `inner-prefix-origin` (`x-sff-test-y`) and `trailing-prefix-origin` (`repo-sff-test-`) case exits 0 and sends its GET, where exit 2 is asserted | round2-1b.txt |
| R3 | AC-1.1: a creation that is not private is refused (row 15) | 3k `if private is not True` -> `if False`; S | FAILED-TO-REFUTE: 2 failed (`private-false`, `private-null`): `DID NOT RAISE ForgeSetupError` | round2-3k.txt |
| R4 | AC-1.4: the refused creation's repository is still deleted (row 16) | 3l `created = _kept_record(...)` -> `created = None`; S | FAILED-TO-REFUTE: 2 failed. The steps end at `the creation`, where `the deletion` is expected | round2-3l.txt |
| R5 | AC-3.1: a failed listing stops the run (row 17) | 3m `raise _failure(...)` -> `return`; S | FAILED-TO-REFUTE: 1 failed, `test_a_failed_listing_stops_the_run`: `DID NOT RAISE ForgeCommandError` | round2-3m.txt |
| R6 | AC-1.4: `remove_tree` retries a refused removal (row 16) | 3n `if attempt == REMOVAL_ATTEMPTS` -> `if True`; S | FAILED-TO-REFUTE: 2 failed. On the retry test, `ForgeSuiteError` escapes `remove_tree`; on the exhaustion test, the calls are `[workspace]`, not 5 | round2-3n.txt |
| R7 | Each kill is an assertion, not a load error | `.claude/hooks/red_for_right_reason.py round2-<m>.txt`, m = 1b, 3k, 3l, 3m, 3n | FAILED-TO-REFUTE: OK five times | (this report) |
| R8 | The new tests are not vacuous | Read of the rework diff; Grep of W and S for skip, xfail, importorskip, SkipTest, pytest.exit, deselect, collect_ignore and commented-out tests or asserts | FAILED-TO-REFUTE: no hits; see the analysis below | (this report) |
| R9 | The lines behind rows 15 to 17 now run | `run_tests.py --workers 1 @<args file: --cov=test/forge --cov=src/payload/scripts --cov-report=term-missing> W S` | FAILED-TO-REFUTE: 50 passed. `ephemeral.py` lines 567, 756, 768-769, 815-816, 820-823, 837, 841-846 and 876-877, unexercised in round 1, are now covered; the remaining gaps are listed below | round2-coverage.txt |
| R10 | Restored tree green | `run_tests.py W S L B` after the five restorations | FAILED-TO-REFUTE: 70 passed | round2-restored-green.txt |

Vacuity analysis (R8). Each new test asserts what the code under test did, not what its own doubles were told:
- W, the new origins: `served_routes` serves each origin, so a wrapper that lets the origin through exits 0 with a
  routed request. The test asserts exit 2, no request, no steward call, empty stdout, and one log record naming
  `origin.shown`. R2 shows those assertions failing under the containment guard.
- S `test_a_repository_created_other_than_private_is_refused_and_deleted`: `private` is only the double's input. The
  test asserts on what `provision` did: it raised `ForgeSetupError`, its recorded steps were exactly init, remote,
  listing, creation and deletion, it sent one `repos/delete` of the answered name, the body was never entered, and
  the workspace is gone. A credential refusal before init would fail the steps assertion.
- S `test_a_failed_listing_stops_the_run`: `ForgeCommandError` and `ForgeSetupError` are sibling subclasses of
  `ForgeSuiteError`, so neither satisfies the other's `pytest.raises`. The recorded wrapper argv is pinned to the
  listing alone, and git to init and remote.
- S `remove_tree` tests: the stand-ins replace only `shutil` and `time`. The test checks that the workspace is gone or
  still exists on the real filesystem. It also checks the read-only entries seen at each attempt
  (`[[OBJECT_FILE], []]`): only `_clear_read_only` in `ephemeral.py` clears them, because the stand-in never calls
  chmod.
- `_provide` and `steps()` swallow no exception.

Remaining unexercised lines in `ephemeral.py` (R9), not counted as refutations:
- 817-819 and 824-825: the `OSError` handlers in `_clear_read_only` that log and pass over a path. D9 step 7 and AC-1.4
  state three things: clear the read-only attribute, retry a refused removal, and raise the last failure. All three
  are exercised and backed by a killed mutant (R6 and the read-only assertion). The pass-over is in no criterion.
- 250-253, 319-320, 353, 361-362, 386-387, 444, 447, 453-455, 551, 630-631, 662, 731 and 793: round 1's uncounted
  error branches, unchanged.
- 426 and 429-431 (`SubprocessGitRunner`): these run only in the forge job, as round 1 recorded.

Not re-graded here:
- Round 1's killed mutants, and its rows 1, 2 and 4 to 14 and 18, which the test-only rework does not touch.
- The whole-suite verdict for the reworked tree. No CI run exists for it, because the rework is uncommitted. It
  belongs to the CI run on the SHA that is pushed next. That run's `forge` job still needs the token permissions
  that DL-006 records.

Tree restored:
- The sha256 values of `github_wrapper.py` (eae09b31...) and `ephemeral.py` (1230e062...) equal their pre-run values.
  `git diff --quiet` exits 0 for both after every mutant.
- The sha256 values of W (5d344f79...), S (a3a45e22...) and `decision-log.md` (52c75d97...) are unchanged.
- `git status --porcelain` matches the starting status: `M` decision-log, W and S; `??` rework-1.txt, `regress/`,
  `verify/`. HEAD is 12d8df7.
- The `.coverage` file my coverage run wrote is removed, and `.hypothesis/examples` holds no file. The driver and
  argument file in `tmp/` are deleted.
- No commit, no stash (the stash list is empty), no network, no `git credential` call, and no credential read.

VERIFIED
