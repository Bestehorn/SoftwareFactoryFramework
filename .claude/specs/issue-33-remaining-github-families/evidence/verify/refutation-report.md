# Refutation report: issue #33 (tier S, one wave, 31 families)

Adversarial verification, 2026-11-11. Tree: worktree `.claude/worktrees/issue-33`, HEAD 273d86b, PR #52. Every capture
named below is in this directory and was regenerated here; prior `evidence/` was graded, not trusted. Mutants were
exact byte replacements applied and restored by a disposable harness under `tmp/` (now removed). Each restore was
checked by sha256. The paired tests ran through `scripts/run_tests.py`.

## Claims tested

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Whole suite green on the pushed SHA | `github_wrapper.py wait-run 42969041590`, `get-run`, `get-jobs`, `get-job-logs 130352951384` | FAILED-TO-REFUTE: `success`, head_sha 273d86b = worktree HEAD, 5/5 jobs success, `2830 passed`, hook suite `1053 passed`, `0 skipped` | full-suite.txt |
| AC-1 | Records carry their sections' names | M09, M10 (WI1), M17 (WI2), M21 (WI3), M29 (WI4): a body or query name dropped; N | FAILED-TO-REFUTE: 5/5 killed by N `test_every_record_matches_its_reference_section` and `test_every_record_is_sent_as_its_section_documents` | mutant-wave-1.txt |
| AC-2 | Only the two residuals pending | M04 `copilot.PENDING` emptied, M25 `markdown.PENDING` emptied, M14 / M26 an ID put back (codespaces, markdown) | FAILED-TO-REFUTE: 4/4 killed by F `test_only_the_residual_ids_are_pending` and V (`covered_or_pending`, `one_module_per_family`) | mutant-wave-1.txt |
| AC-3 | `item_key` per "items in" | M01 `automations`, M05 `secrets` (agents), M11 `codespaces`, M12 `secrets` (codespaces), M20 `configurations`, M24 `budgets` | FAILED-TO-REFUTE: 6/6 killed by F AC-3, and by F AC-4 for each one | mutant-wave-1.txt |
| AC-3 | LINK only for a `Paging:` line or a 200 array with `Link` | LINK to NONE: M03, M15, M18 (`dependency-graph/diff-range`), M23, M30, M31, M32. NONE to LINK: M02 (array, no Link), M16 and M19 (one object with Link), M22 (array, no Link) | FAILED-TO-REFUTE: 11/11 killed by F AC-3 | mutant-wave-1.txt |
| AC-4 | A paged record prints every page | the LINK to NONE and item-key mutants above | FAILED-TO-REFUTE: F AC-4 fails for each of them except M18 (see note 1) | mutant-wave-1.txt |
| AC-6 | The seven IDs are refused with exit 2, no request, ID and "no subcommand sends it" logged | M06, M07, M08, M13, M27, M34, M35: each ID removed from `GATED_OPERATIONS`. M33: the `None` message changed | FAILED-TO-REFUTE: 8/8 killed by F `test_a_branch_writing_record_is_refused` (the fake host got the request, or the log pattern found no match) | mutant-wave-1.txt |
| DL-005 | N's step 3 replaces the declared `billing/update-budget-org` | M28: `value=(*others, record))` reverted to `(*billing.OPERATIONS, record)` | FAILED-TO-REFUTE: killed: `exit 2; log ['The GitHub operation "billing/update-budget-org" is declared 2 times']` | mutant-wave-1.txt |
| W1 | The wave's tests need its implementation | the 31 modules and `commands/call.py` set to the 5cfe09f blobs; 31 F + N + V + K | FAILED-TO-REFUTE: `132 failed, 66 passed` | mutant-wave-1-revert.txt |
| MR | The merge kept call.py whole | `git diff origin/main...HEAD -- call.py`; K, repos, git, pulls suites | FAILED-TO-REFUTE: the diff against the merge base 5cfe09f is the seven `None` entries plus comment and docstring lines. 17 `GATED_OPERATIONS` entries; `GATED_NOT_SENT = {"pulls/merge-async"}`; the three forms (`use the X subcommand, which sends it`, `use the X subcommand`, `no subcommand sends it`) are present; the suites pass | green-after-restore.txt |
| VAC | No vacuous test | Grep of the 31 F and N for skip, xfail, importorskip, deselect, collect_ignore, commented tests | FAILED-TO-REFUTE: the only hits are docstrings that explain why a test is absent. Every parametrized case is a node id in the red. The AC-6 cases are 3+1+1+1+1 = 7 = AC-6. CI reports `0 skipped` | (Grep) |
| VAC-P | Families without a per-page test have no paged section | Grep for `Paging`/`Link` in the sections of classroom, codes-of-conduct, credentials, emojis, gitignore, interactions, markdown, meta, rate-limit, oidc (actions.md), agent-merge (pulls.md) | FAILED-TO-REFUTE: no `Paging:` line. The oidc lists are arrays without `Link` | (Grep) |
| RED | Red for the right reason | tally of `evidence/red/wave-1.txt` and of W1 | FAILED-TO-REFUTE: 132 failed / 13 passed, 132 `E AssertionError`, no import or collection error. W1 failed the same 132 node ids, all AssertionError: AC-4 exit 2 (no record) x63, AC-2 PENDING still holds, AC-3 declared differs from the sections, AC-6 no record x7 | mutant-wave-1-revert.txt |
| COV | Every changed line is exercised | CI coverage table of job 130352951384 | FAILED-TO-REFUTE: `call.py` 143 stmts, 0 miss. Each of the 31 changed family modules has 0 miss. N's DL-005 lines are executed (M28). Every record is covered: N's reference half checks all of them, N's call half calls each ungated one, F AC-6 calls the seven gated ones | full-suite.txt |
| SPOT | Paging and item key match the reference | 19 records read through `registry.lookup` and compared with their `Paging:` / `Responses:` lines | FAILED-TO-REFUTE: all 19 agree (agent-automations, agents, agent-tasks, copilot seats, copilot-spaces, two codespaces records, migrations, projects/get-for-org NONE, private-registries, code-security, security-advisories, billing, licenses, diff-range, hosted-compute, api-insights, oidc NONE, pull-request-stacks) | (Grep) |
| UB-5 | gitlab_wrapper.py and test_wrapper_delivery.py untouched | `git diff --name-only origin/main...HEAD`; run the delivery test | FAILED-TO-REFUTE: neither is named in the diff, and `test_wrapper_delivery.py` passes | green-after-restore.txt |

Re-confirmed green after every restore: 41 affected modules, `781 passed in 120.47s`, exit 0 (green-after-restore.txt).

## Notes (not refutations)

1. M18: `dependency-graph/diff-range` documents no `per_page`. Under `Paging.NONE` its AC-4 case therefore sends one
   request and prints the same array, so F AC-4 passes. F AC-3 (`paged == PAGED_IDS`) kills the flip.
2. origin/main moved to 3beba95 (#49, GitLab) after the CI base 5cfe09f. #49 also edits `docs/findings-ledger.md`,
   which this PR edits. Not graded: it is outside the diff.

## Tree restored

All 994 tracked files of the worktree are sha256-identical to the manifest taken before the first mutant. Every
mutant's restore line reads IDENTICAL. `git status --porcelain` lists only `evidence/verify/`. `tmp/` is removed.
HEAD is 273d86b.

Verdict: VERIFIED
