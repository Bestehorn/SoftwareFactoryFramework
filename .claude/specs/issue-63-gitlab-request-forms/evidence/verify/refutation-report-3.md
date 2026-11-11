# Refutation report, round 3 (delta) - issue #63 (tier M, PR #66, head 5ece525 on 583fbbd)

Scope: DL-011's rework (tests only) against round 2's R2-1 and R2-2. `git diff 583fbbd 5ece525 --stat --
src/payload/scripts` printed nothing; `container_registry.py`'s sha256 before each mutant equals round 2's. Method: a
detached worktree of 5ece525 under `tmp/verify3/`; each mutant replaced one exact text, ran G and F (76 tests) through
`scripts/run_tests.py` and restored the bytes (every restore `match=True`); each survivor then ran every GitLab suite
(962 tests, the rework-2.txt set). G = test_gitlab_api_container_registry.py, F = test_gitlab_api_package.py.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the head | `wait-run`/`get-run`/`get-jobs` 43093062683: head_sha 5ece525; all five jobs success; 3699 passed (+5), hook suite 1053 | FAILED-TO-REFUTE | round3-full-suite.txt |
| 2 | Tree green before mutants | G and F: 76 passed | FAILED-TO-REFUTE | round3-baseline-green.txt |
| 3 | D4 step 2: white space refused | `\s` dropped: 5 failed, G [a-space, a-tab, a-line-feed, a-carriage-return], F [image-prefix-host-with-white-space] | FAILED-TO-REFUTE | round3-sec-step2-whitespace-allowed.txt |
| 4 | R2-1 re-run | `\s` -> a space: 3 failed, G [a-tab, a-line-feed, a-carriage-return] | FAILED-TO-REFUTE | round3-sec-step2-only-space-refused.txt |
| 5 | R2-1 near: LF, CR | `\s` -> space, tab: 2 failed, G [a-line-feed, a-carriage-return] | FAILED-TO-REFUTE | round3-sec-step2-space-and-tab-refused.txt |
| 6 | R2-1 near: CR alone | `\s` -> space, tab, LF: 1 failed, G [a-carriage-return] | FAILED-TO-REFUTE | round3-sec-step2-cr-admitted.txt |
| 7 | R2-1 near: VT, FF | `\s` -> `[ \t\n\r]`: 76 passed paired, 962 passed every GitLab suite | REFUTED R3-1 | round3-sec-step2-vt-ff-admitted[-full].txt |
| 8 | R2-1 near: beyond ASCII | `\s` -> `[ \t\n\r\f\v]`: 76 passed, 962 passed | REFUTED R3-1 | round3-sec-step2-ascii-white-space-only[-full].txt |
| 9 | R2-2 re-run | any string username accepted: 1 failed, G [empty-username] | FAILED-TO-REFUTE | round3-ac53-username-empty-accepted.txt |
| 10 | R2-2 near: no job-login fallback | `""` -> `gitlab-ci-token`: 1 failed, G [empty-username] | FAILED-TO-REFUTE | round3-ac53-username-empty-job-login.txt |
| 11 | R2-2 near: `_answer_text` | `and text` dropped (every field): 1 failed, G [empty-username] | FAILED-TO-REFUTE | round3-ac53-answer-text-empty-accepted.txt |
| 12 | R2-2 near: a white-space username | D4 AC-5.3 refuses a field "absent or not a non-empty string"; `" "` is a non-empty string and `_answer_text` returns it: no refusal is claimed, so no mutant differs from D4 | FAILED-TO-REFUTE | design.md D4 |
| 13 | Vacuity | diff: 4 + 1 new params; markers only `parametrize`; both tests assert `pytest.raises` and the sent list; nothing removed or relaxed; no pyproject/conftest change; each new param failed under a mutant (rows 3-6, 9) | FAILED-TO-REFUTE | diff |
| 14 | Red for the right reason | every kill: AssertionError on the sent list, the fake host's unscripted-request AssertionError, or `DID NOT RAISE GitLabAPIError`; no collection or import error | FAILED-TO-REFUTE | round3-*.txt |
| 15 | Coverage of the change | CI: G misses 48, 56-61, 145, 150, none in the rework's hunks; container_registry.py 100% | FAILED-TO-REFUTE | round3-full-suite.txt |
| 16 | Restored tree green | G and F after every mutant: 76 passed; mutant tree `git status --porcelain` empty | FAILED-TO-REFUTE | round3-restored-green.txt |

## Refutation

- R3-1 AC-5.3 / D4 step 2 (residue of R2-1): D4 refuses a registry host holding "white space" and the code implements
  it as `\s`; the tests pin SP, HT, LF and CR alone. A mutant refusing exactly those four survives 962 tests, as does
  one refusing the six ASCII white-space characters; under them a host holding a vertical tab, a form feed or other
  white space `\s` matches passes step 2 and steps 3 and 4 are sent, where D4 raises `GitLabAPIError` before step 3.
  Rows 7 and 8 die only with a host case outside the four, or with D4 restated to the four characters pinned.

R2-2 is closed: its re-run and both near-variants are killed, and a white-space username is not a D4 claim. R2-1 is
closed for SP, HT, LF and CR; its residue is R3-1.

## Tree

The temporary worktree is removed and pruned; `tmp/` is empty, and pytest's basetemp and the temp dir were scoped
under the issue-63 tree's `tmp/` and removed. `git status --porcelain` lists only `evidence/verify/round3-*` and this
report. HEAD is 5ece525. Nothing was committed and nothing was written outside the issue-63 worktree.

Refuted: R3-1
Verdict: REFUTED
