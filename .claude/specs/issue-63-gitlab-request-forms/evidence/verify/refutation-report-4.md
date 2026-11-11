# Refutation report, round 4 (delta) - issue #63 (tier M, PR #66, head 6687d9b on 5ece525)

Scope: R3-1's residue, DL-012's test-only rework. `git diff 5ece525 6687d9b --stat -- src/payload/scripts` printed
nothing. Method: a detached worktree of 6687d9b under `tmp/verify4/`; each mutant replaced one exact text, ran G and F
(102 tests) through `scripts/run_tests.py` and restored the bytes (every restore `match=True`). No mutant survived, so
no GitLab-set run was owed. G = test_gitlab_api_container_registry.py, F = test_gitlab_api_package.py.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the head | PR run 43096840286 stuck pending since 20:34:20Z (no job, cancel HTTP 409); run 43106939480 (workflow_dispatch): head_sha 6687d9b, five jobs success, 3725 passed (+26), hooks 1053 | FAILED-TO-REFUTE | round4-full-suite.txt |
| 2 | Tree green before mutants | G and F `-v`: 102 passed, the 29 cases and the guard listed | FAILED-TO-REFUTE | round4-baseline-green.txt |
| 3 | R3-1 re-run (round 3 row 7) | `\s` -> ` \t\n\r`: 25 failed, every case but SP, HT, LF, CR | FAILED-TO-REFUTE | round4-sec-step2-vt-ff-admitted.txt |
| 4 | R3-1 re-run (round 3 row 8) | `\s` -> ` \t\n\r\f\v`: 23 failed | FAILED-TO-REFUTE | round4-sec-step2-ascii-white-space-only.txt |
| 5 | Near: ASCII `\s` | `flags=re.ASCII`: 23 failed | FAILED-TO-REFUTE | round4-sec-step2-re-ascii.txt |
| 6 | Near: Z categories | `\s` -> Zs, Zl, Zp and the six ASCII: 5 failed, exactly U+001C-U+001F, U+0085 | FAILED-TO-REFUTE | round4-sec-step2-z-categories-and-ascii.txt |
| 7 | Each character pinned | 29 mutants, `\s` less one character (`(?!\uXXXX)\s`): 29 killed, each by exactly its own case (U+0020 also F's white-space host) | FAILED-TO-REFUTE | round4-sec-step2-each-character-admitted.txt |
| 8 | Guard holds the tuple | U+3000 entry dropped: guard failed; made a second space: guard failed, 29 cases passed; U+180E added: guard and its case failed | FAILED-TO-REFUTE | round4-guard-*.txt |
| 9 | Vacuity | four hand-written params replaced by 29 generated (ids kept); markers only `parametrize`; guard asserts; nothing skipped, xfailed, deselected or relaxed; no pyproject/conftest change | FAILED-TO-REFUTE | diff |
| 10 | Red for the right reason | every kill an AssertionError (G's sent list, the guard, F's unscripted request); 0 ERROR lines | FAILED-TO-REFUTE | round4-*.txt |
| 11 | Coverage of the change | CI: G misses 49, 57-62, 179, 184, outside the hunks (11-12, 122-160, 326-331); container_registry.py 100% | FAILED-TO-REFUTE | round4-full-suite.txt |
| 12 | Restored tree green | G and F: 102 passed; mutant tree status empty | FAILED-TO-REFUTE | round4-restored-green.txt |

## Finding

R3-1 is closed. Each case's host holds its character as its only white space, so a refusal admitting any set of
white-space characters fails at least that set's cases; row 7 kills each character alone, and row 8 shows the tuple
cannot lose, duplicate or gain a character unnoticed.

## Tree

The temporary worktree is removed and pruned; tmp/ (with pytest's basetemp and the temp dir) is deleted.
`git status --porcelain` lists only `evidence/verify/round4-*` and this report. HEAD is 6687d9b. Nothing was
committed; nothing was written outside the issue-63 worktree. Run 43096840286 is unchanged (cancel refused).

Verdict: VERIFIED
