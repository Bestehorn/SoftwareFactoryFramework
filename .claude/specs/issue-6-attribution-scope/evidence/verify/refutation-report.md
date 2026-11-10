# Refutation report - issue #6, tier S, wave 1 (T1 + I1)

Tree: worktree `issue-6`, branch `issue-6-attribution-scope`, HEAD `9454d8578b77cacc4b137d65817d404d6341a188`,
not pushed (`git branch -r --contains HEAD` prints nothing). Every run below is
`venv\Scripts\python.exe scripts/run_tests.py test/test_no_ai_attribution_rule.py` (21 items, `-n 2`).
The mutations touched the working tree only. Each file was backed up byte-for-byte to `tmp/verify-issue6/`, then
restored by copy and checked with `cmp`, and `git status --porcelain` was empty after every restore. On the
dispatcher's instruction this report is the only file written: the run results are quoted here, not kept as
separate captures.

## Results

| # | Claim | Command / mutation | Result | Capture (quoted run summary) |
|---|---|---|---|---|
| 1 | Whole suite green on the SHA | none: no CI run exists for 9454d85 (unpushed) | NOT RUN: the dispatcher assigns it to CI on the push after this verdict | - |
| M0 | T1 fails without I1 | the six I1 product files set to HEAD~1 (`git restore --source=HEAD~1`) | FAILED-TO-REFUTE | `13 failed, 8 passed` (same 13 as the red capture); after restore `21 passed` |
| M1 | AC-3/AC-4: the Kiro twin carries no blanket ban | old sentence "Never put ... into any name or message you create." re-added to the 8.28 body only | FAILED-TO-REFUTE | `2 failed, 19 passed`: ac3[kiro] (B1, B2), ac4 |
| M2 | UB-2: Claude body keeps the `claude/<adjective>-<name>` auto-name ban | that clause deleted from "Overriding the tool defaults" | FAILED-TO-REFUTE | `1 failed, 20 passed`: ub2[claude] |
| M3 | UB-2: the allowance never reaches authored names | both bodies: the domain gains "or a branch name" and the guard "the allowance never extends to a branch, worktree, tag, stash, ref or label name" is deleted | REFUTED | `21 passed` |
| M4 | UB-3: auto-work.md keeps its trailer ban | ", and never add a `Co-Authored-By` or ... trailer" deleted | FAILED-TO-REFUTE | `1 failed, 20 passed`: ub3[auto-work-command] |
| M5 | UB-3: each restatement file states the name ban | "put no Claude/AI/bot into a branch or worktree name" (both commands) and "and no branch or worktree name carries Claude/AI/assistant/bot" (both agents) deleted | REFUTED | `21 passed` |
| M6 | Vacuity of the 8 tests that pass on the red tree | kept trailer phrase deleted (Claude, Kiro), Kiro auto-name phrase deleted, B1 wording inserted after R1-R4 in setup-claude.txt | FAILED-TO-REFUTE | `7 failed, 14 passed`: ub1[claude], ub1[kiro], ub2[kiro], ub3 R1, R2, R3, R4 (ub2[claude] is M2) |
| 3 | No skip, xfail, deselection or assert-nothing test | Grep of the test source; pyproject `testpaths`/`addopts`; no `test/conftest.py` | FAILED-TO-REFUTE | only `@pytest.mark.parametrize`; `testpaths` holds `test`; `addopts = "-ra --import-mode=importlib"`; every helper asserts its slice exists; each kept agent phrase occurs once per file |
| 4 | Red for the right reason | read `evidence/red/wave-1.txt` | FAILED-TO-REFUTE | header `# tasks: T1`; 21 collected, no collection error; all 13 failures are `AssertionError` carrying the test's own K/B messages at the committed assert lines (217, 223, 229, 235, 247, 280); M0 reproduces the same 13 |
| 5 | Every changed line is exercised by a test | diff of HEAD~1..HEAD compared with the test's assertions | REFUTED UB-2, UB-3 | see Coverage |

Every one of the 21 tests failed under at least one mutant (M0, M2, M6), so no test is vacuous. The surviving
mutants show text that no test pins.

## Semantics lens

S1, a loophole in UB-2 (it serves the M3 refutation). The last sentence of the Claude self-check reads "A hit inside
a path, command, setting or product named as the subject of the work is not."; the Kiro self-check reads "...; a
path, command, setting or product named as the subject of the work stays." Neither sentence states its domain, and
the self-check governs branch and worktree creation too ("before creating any commit/PR/issue/comment/branch/worktree").
So a branch `fix-issue-12-setup-claude-restatement`, which names a product file as its subject, reads as permitted,
against the preceding "or is in one of the names you author, is a defect". The guard clause in paragraph 2 is the
only text that closes this, and M3 shows no test pins that clause. Under the old text the name ban in the self-check
was unconditional ("Any hit used as attribution or in a name is a defect").

S2, no loophole for trailers or sign-offs (UB-1). The opening paragraph explicitly bans `Co-Authored-By: Claude`,
`Generated with Claude Code`, "no tool trailer of any kind" and "filed by <agent>" sign-offs, and the allowance
applies only to a path or product named as "the subject of the work". A trailer names the producer, not the subject.
The Kiro bullets keep `Co-Authored-By`, "Generated with" and "fixed by <agent>". The tool auto-name is not a "name
you author", but "Overriding the tool defaults" (Claude) and "NEVER an auto-generated `<tool>/<adjective>-<name>`"
(Kiro) cover it, and M2 and M6 pin both.

S3, observation, not graded (the wording is AC-1's, and the spec's prose is outside this report's scope): "The rule has
one scope: attribution of work to a tool in commit messages, PR/MR titles and bodies, and issue text" names three
channels. Attribution inside a committed file (a source header, a doc, a tag annotation) is covered only by the bold
"anywhere".

S4, observation: the restatements' allowance drops "existing" ("naming a path ... is fine"), and the two commands also
drop "command, setting". The wording differs from the rule but opens no path to attribution.

## Coverage of the change

These new lines are unexercised: a test still passes after each was deleted or widened.
- Both bodies: the allowance's domain ("In commit messages (subject line included), PR/MR titles and bodies, and issue
  text,") and its guard ("the allowance never extends to a branch, worktree, tag, stash, ref or label name").
  change.md, section Files, assigns both to UB-2. M3 stays green. Refutes UB-2.
- The four restatement files: the name clause (M5 stays green), and the general clause "attribute no work to a tool" /
  "or any other attribution of the work to a tool" with its allowance parenthetical. The test checks only two things
  in these files: B1, B2, B4 and B5 are absent, and the kept trailer phrase is present
  (`test_ub3_restatement_file_states_attribution_and_names_only`). Refutes UB-3, whose Files entry requires "no listed
  word in a branch or worktree name".
- Both self-check final sentences and the example commit subject are also unexercised, but deleting them removes no
  required behaviour; S1 is the defect in the self-check sentence.
- A Grep across `clients/`, `prompts/`, `templates/` and `src/` for the B1, B3, B4 and B5 wordings finds no match: no
  blanket-ban restatement remains outside the diff.

Gaps the writer of record must close (the verifier fixes nothing):
- A check that each body's allowance sentence states its message domain and keeps the "never extends to a branch,
  worktree, tag, stash, ref or label name" guard.
- A check that each restatement file keeps its branch/worktree name clause.
- S1's two sentences scoped to messages.

## Tree restoration

Every mutation was restored from `tmp/verify-issue6/`, and `cmp` matched for all seven files. `git diff HEAD --stat`
and `git status --porcelain` were empty before this report was written. A final run on the restored tree gave
`21 passed`. `tmp/verify-issue6/` is deleted and tmp/ holds no files. The only change left in the worktree is this
file.

REFUTED UB-2 UB-3
