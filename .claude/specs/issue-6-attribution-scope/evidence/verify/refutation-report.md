# Refutation report - issue #6, tier S, wave 1 (T1 + I1)

Worktree `issue-6`, branch `issue-6-attribution-scope`. Every run is `venv\Scripts\python.exe scripts/run_tests.py
test/test_no_ai_attribution_rule.py` (`-n 2`). Mutations touched the working tree only: each file was backed up
byte-for-byte to `tmp/`, restored by copy and checked with `cmp`, and `git status --porcelain` was empty after every
restore. On the dispatcher's instruction the run results are quoted here, not kept as separate captures.

## Round 1 (HEAD 9454d85, 21 tests)

| # | Claim | Mutation | Result | Run |
|---|---|---|---|---|
| 1 | Whole suite green | none: unpushed, no CI run | NOT RUN: CI runs it on the push | - |
| M0 | T1 fails without I1 | six I1 files at HEAD~1 | FAILED-TO-REFUTE | `13 failed, 8 passed` |
| M1 | AC-3/AC-4: no blanket ban in the Kiro body | old B1 sentence re-added to 8.28 | FAILED-TO-REFUTE | `2 failed`: ac3[kiro], ac4 |
| M2 | UB-2: Claude auto-name ban kept | `claude/<adjective>-<name>` clause deleted | FAILED-TO-REFUTE | `1 failed`: ub2[claude] |
| M3 | UB-2: allowance never reaches authored names | both bodies: domain gains "or a branch name", guard deleted | REFUTED | `21 passed` |
| M4 | UB-3: auto-work trailer ban kept | its trailer clause deleted | FAILED-TO-REFUTE | `1 failed` |
| M5 | UB-3: restatement name ban kept | name clause deleted in the 4 files | REFUTED | `21 passed` |
| M6 | 8 tests green on the red tree are not vacuous | kept phrases deleted, B1 after R1-R4 | FAILED-TO-REFUTE | `7 failed, 14 passed` |
| 3 | no skip/xfail/deselect/assert-nothing | Grep of test and pyproject | FAILED-TO-REFUTE | only `parametrize` |
| 4 | red for the right reason | `evidence/red/wave-1.txt` | FAILED-TO-REFUTE | 13 `AssertionError`s, no load error |
| 5 | changed lines exercised | diff against the assertions | REFUTED UB-2, UB-3 | M3, M5 |

S1 (served M3): neither self-check exemption sentence stated a domain, so a branch name that names a product read as
permitted, and only the unpinned paragraph-2 guard closed that. S2: no loophole for trailers or sign-offs (UB-1).
Gaps named: a domain-and-guard check, a restatement name-clause check, both S1 sentences scoped to messages.
Round-1 verdict: REFUTED UB-2 UB-3.

## Re-verification

HEAD `1c5fc8c`, 29 tests. Delta `git diff 9454d85..HEAD`: 8 new tests (allowance domain and guard x2, self-check
limit x2, restatement name clause x4); the self-check sentence of both bodies now ends "in a commit message, PR/MR
text or issue text"; `evidence/red/wave-1-reopen.txt`; `evidence/green/wave-1.txt`. Backups: `tmp/verify-issue6-r2/`.

| # | Claim | Mutation | Result | Run |
|---|---|---|---|---|
| 1 | Whole suite green on 1c5fc8c | none: `git branch -r --contains HEAD` prints nothing, so no CI run exists | NOT RUN: CI runs it on the push | - |
| B | Clean tree green | none | baseline | `29 passed` |
| M3 | UB-2: allowance never reaches authored names | round-1 M3 re-applied to both bodies | FAILED-TO-REFUTE | `2 failed, 27 passed`: ub2_allowance[claude], [kiro], each reporting both "does not name its message domain ... right before K3" and "lost the guard" |
| M5 | UB-3: restatement name clause kept | round-1 M5 re-applied to the 4 files | FAILED-TO-REFUTE | `4 failed, 25 passed`: name_clause[work-issue-command], [auto-work-command], [claude-orchestrator], [kiro-orchestrator] |
| M7 | UB-2: Claude self-check exemption limited to messages | "in a commit message, PR/MR text or issue text" deleted from the Claude self-check only | FAILED-TO-REFUTE | `1 failed, 28 passed`: self_check[claude] only |
| M7k | Same, Kiro | the same deletion in the 8.28 self-check only | FAILED-TO-REFUTE | `1 failed, 28 passed`: self_check[kiro] only |
| 3 | No vacuous new test | read the 8 new tests | FAILED-TO-REFUTE | only `parametrize` marks; `_ub2_allowance_problems` asserts K3 is found, `_ub2_self_check_allowance_problems` asserts an exempting clause exists; each new test failed under M3, M5, M7 or M7k; pyproject is not in the delta |
| 4 | Reopened red is red for the right reason | `evidence/red/wave-1-reopen.txt` | FAILED-TO-REFUTE | `# tasks: T1`, 29 collected, no collection error; 2 `AssertionError`s at line 344 carrying the test's own message, which M7 and M7k reproduce verbatim. The other 6 new tests pin text committed in 9454d85, so they pass on that tree, and M3 and M5 kill them |
| 5 | Changed lines exercised | delta against the assertions | FAILED-TO-REFUTE | the only product edits in the delta are the two self-check sentences, and M7 and M7k exercise them |
| M8 | Probe, not graded | Claude self-check limit widened in place: "issue text, or in a branch name, is not." (run together with M7k) | survives: self_check[claude] passed | see below |

M8 is neither a revert nor a stub. The limit stays and an exception is added beside it, so it falls outside step 2's
"a test that passes without its behaviour". Every unanchored pin in this file accepts an appended qualifier in the
same way: `_missing` and the guard check are substring tests. The body domain check rejects this widening only
because it anchors the domain directly before K3. The writer of record can give the self-check test the same
strength by anchoring the domain to the clause end ("... issue text is not" / "... issue text stays"). M8 is not a
refutation.

Security lens on both current bodies:
- Authored names. The opening paragraph bans the listed words in "names you author" (K4, pinned). The paragraph-2
  allowance is scoped to messages and closed by the guard, now pinned (M3). Both self-checks call a hit "in one of the
  names you author" a defect, and each exemption now covers messages only (M7, M7k). The Kiro branch bullet keeps
  `never any name containing "claude"/"ai"/"bot"`. The `.claude/` and `.kiro/` exemptions cover only the fixed config
  directory ("not a name you author" / "not names you choose"). No sentence reads as permitting a listed word in a
  branch, worktree, tag, stash, ref or label name.
- Disguised attribution. The allowance applies only to a path, command, setting or product named "as the subject of
  the work", and a trailer, a "generated with" line or a sign-off names the producer instead. Both bodies keep the
  explicit bans (`Co-Authored-By`, `Generated with`, "filed by" / "fixed by <agent>") and the sentence that the
  producer "must not appear in it". Neither exemption overrides the preceding "attribution of work to a tool ... is a
  defect" / "remove it". No loophole found.

Round 1 also noted that the general attribution clause in each restatement file, with its allowance parenthetical, is
unpinned. That still holds. Deleting the clause removes no UB-3 behaviour: the pinned trailer and name clauses still
state attribution and names, and the B1/B2/B4/B5 absence checks still hold. As in round 1, it is not graded.

Restoration: all six files were restored from `tmp/verify-issue6-r2/` and match their backups under `cmp`;
`git status --porcelain` and `git diff HEAD --stat` were empty; the final run gave `29 passed`; `tmp/verify-issue6-r2/`
is deleted. The only change left in the worktree is this report.

VERIFIED
