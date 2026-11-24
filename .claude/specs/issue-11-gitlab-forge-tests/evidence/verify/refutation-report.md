# Refutation report - issue #11 (tier M), VERIFY

Change: `83a1415..5b37333`. Code under test is `c389d46`; `c389d46..HEAD` adds only the CI capture and DL-009.
Captures are in this directory. W, S, G, L, H as in `design.md` Acceptance Criteria Mapping.

| Claim | Command | Result | Capture |
|---|---|---|---|
| Whole suite green on `c389d46` | `github_wrapper.py get-jobs` / `get-run 45033382186` | FAILED-TO-REFUTE: head_sha `c389d46`; verify lint, types, security, tests (hook suite included) and `forge` success. Run conclusion `failure`: `forge-gitlab` (credential step, secret unset) and `report` (`forge-gitlab job: failure`), one root cause, the F.1 prerequisite (DL-009) | full-suite.txt |
| Wave 1 (1.3, 1.4; AC-4.1-4.3, UB-3) | M1a: 1.3 and 1.4 files reverted to `83a1415`; W, H, S | FAILED-TO-REFUTE: W 45/45 red, S 29/29 red (keyword-only parameters missing), H 32 green (UB-4 guard of the old behaviour) | mutant-wave-1.txt |
| Wave 1 edge cases, UB-4 defaults | M1b: `_is_ephemeral_project` = prefix anywhere; 3 defaults of `test/forge/ephemeral.py` changed; W, H | FAILED-TO-REFUTE: 18 W red (`sff-test-x`, `Bestehorn/x-sff-test-y`, `.../sff-test-x/other`), 8 H red | mutant-wave-1.txt |
| Wave 2 (2.4, 2.5; AC-1.1, 1.2, 5.1-5.4, 6.1, 6.3) | M2: `ci.yml` reverted; `refuse_distributed_run` without `command=`, `ephemeral_full_path` without group, `CLONE_GIT_HELPER` without `username=`, GitHub credential file, `SFF_TEST_TOKEN`; wave-2 S, G, L by `-k` | FAILED-TO-REFUTE: 9/10 red, each on its own mutant. Survivor: G `test_the_default_configuration_collects_no_gitlab_forge_test`, whose behaviour the wave-5 files carry; killed by M5b | mutant-wave-2.txt |
| Wave 3 (3.3, 3.4; AC-2.1, 2.2, 3.1-3.3, 4.3, 5.3, 8.7) | M3: runner argv without marker and `PRODUCT_WRAPPER`; teardown judges the path only, deletes `id=<path>`; `is_leftover` namespace `startswith`; `write_credential.main` returns 0 on refusal | FAILED-TO-REFUTE: 8 red, every wave-3 test function red; Hypothesis found `bestehorn-sff-test-archive/sff-test-0`. 2 green params are ones the mutant still refuses | mutant-wave-3.txt |
| Wave 4 (4.3-4.5; AC-1.1, 1.3, 1.4, 2.3, 6.2, 6.3, 9.1, 9.2, UB-2) | M4a: docs reverted; any visibility accepted; no `_refuse_token_characters`; no exclude line; `.gitlab-ci.yml` seed accepted; record held before creation. M4b: deletion only on normal return; token logged at DEBUG | FAILED-TO-REFUTE: M4a 10 red, M4b 3 red (`the-body-raises`, `a-gitlab-ci-file-in-the-seed`, token test on the log record); every wave-4 test function red | mutant-wave-4.txt |
| Wave 5 (5.7, 5.8; AC-1.1, 1.4, 5.2, 7.1-7.3, 8.5, 8.6) | M5a: `python_files = forge_f*.py`; fixture without `refuse_distributed_run`; one uncalled record cut from the 5.6 docstring. M5b: conftest imports a missing module | FAILED-TO-REFUTE: M5a 4/4 G red; M5b default-collection test red (exit 4, not 5) | mutant-wave-5.txt |
| 5.9 `push_branch`, `wait_until_checked` (AC-8.2, 8.3, 8.5) | M5c: no push; first read returned undecided; S and G | PENDING F.1: 40/40 green. No default-collection test reads them, as tasks.md "Runs" declares; only the F modules call them | mutant-wave-5.txt |
| Restore | `git checkout HEAD -- <files>` after each mutant; `git diff --stat HEAD` | Empty after every restore; W+S+G+L+H 128 passed | restored-green.txt |
| No vacuous tests | Grep `skip\|skipif\|xfail\|importorskip\|pytest.exit\|collect_ignore\|deselect\|assert True` and commented asserts over W, S, G, L, `test/forge_gitlab/` | FAILED-TO-REFUTE: no match except G's own messages; green captures and restored run show 0 skipped, 0 xfailed | - |
| Red for the right reason | `.claude/hooks/red_for_right_reason.py evidence/red/wave-{1..5}.txt`; each read in full | FAILED-TO-REFUTE: all exit 0, every failure an `AssertionError`. Wave 1 fails on behaviour (exit 0, not 2). Most wave 2-5 reds are the `_load_by_path`/`_require` existence assertions tasks 2.1 prescribes; M2-M5 supply the behavioural falsification | evidence/red |
| Green captures declare their tasks | first line of `evidence/green/wave-{1..5}.txt` | FAILED-TO-REFUTE: 1.1-1.4, 2.1-2.5, 3.1-3.4, 4.1-4.5, 5.1-5.9; all exit 0 | evidence/green |
| UB-3, UB-4 tests unedited | `git diff --stat 83a1415..HEAD -- src/payload/test test`; `--name-status -- test/forge` | FAILED-TO-REFUTE: only new files, `test/forge/ephemeral.py` (D10) and L +5/-1 (one constant, the `needs` expectation extended, nothing removed). No C, A, K, V, P or H file. Under `test/forge/` only `ephemeral.py` | - |
| UB-5 no toolchain file | `config/toolchain.json` read; diff name list | FAILED-TO-REFUTE: `gitlab_wrapper.py` and `templates/ci/*` are `not_installed`, `ci.yml` is the project's own; I passed in CI | - |

## Coverage of the change (static, from S read in full)

S runs every behaviour of `ephemeral.py` parts 1-3 and `write_credential.py`. Some defensive branches run in no
test: the runner's `OSError`/`SubprocessError` branch, the error branches of `_created_at`, `ProjectRecord.of`,
`_listed_records` and `_created_record`, non-zero exits of `list_group_projects` and `read_test_group`, the
`full_path`/`id` refusal in `read_test_group`, `_run_git`'s failure, `read_test_token`'s `OSError` branch,
`fetch_seed`'s revision count, and `_already_handled` for an exit other than 1. None of these is an AC of
`requirements.md` or a Correctness Property of `design.md`, so they refute no criterion. `pytest-cov` could not be
used: `run_tests.py` parses `--cov=<path>` as `--coverage` (exit 2, "argument --coverage: ignored explicit argument").

## The real-gitlab.com modules: static judgement, runtime pending F.1

The `forge-gitlab` job stopped at its credential step, so no `test/forge_gitlab/forge_*.py` test has run anywhere.
The runtime verdict of AC-8.1-8.6 and the F halves of AC-1.1, 1.3, 3.1 and 4.2 waits on F.1. Read statically:

- Wiring: every test takes `ephemeral_project`. The wrapper runs through `SubprocessWrapperRunner` (marker set, clone
  as working directory). No module names a project with `--path id=` (G reach-only green). Only `ephemeral.py` imports
  `subprocess`.
- Oracles: values the fixture or the test made (run id, full path, seed SHA, `git rev-parse <seed>:README.md`, fresh
  `uuid4` titles, branches, pushed SHAs) or values GitLab documents (`opened`, `closed`, `merged`, `mergeable`, `OPEN`,
  `Issue`, `answered 404`, `[]`). No oracle is read back through the code under test, except F:fixture's listing,
  which goes through S-proven `list_group_projects`.
- Kill power: M5c's mutants would fail F (`mr create` of an unpushed branch exits 1; `mergeable` asserted after the
  wait).
- CI runtime already shows AC-5.3 (step log names `SFF_GITLAB_TEST_TOKEN`, exit 1), AC-5.4 (`report` exit 1 on
  `forge-gitlab job: failure`) and AC-5.1 (the job started with no `needs:`).

## Observations (not refutations)

- H pins the refusal of `refuse_distributed_run` only to `--workers 1` (`SINGLE_WORKER_OPTION`), so the new
  `command=` default is pinned to that substring. Before the change the message was pinned the same way.
- `mutant-wave-4.txt` holds the synthetic token `test-<uuid hex>` that M4b's leak mutant logged (S `_new_token`). It
  is not a credential.

Tree restored: every mutation undone with `git checkout HEAD`. `git diff --stat HEAD` is empty, and the only
untracked path is this directory.
Scope: every default-collection claim of waves 1-5 survived. The F modules' runtime verdict is F.1's.

VERIFIED
