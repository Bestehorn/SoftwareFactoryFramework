---
description: Finish the batch and push it ONCE — integrate remote changes, commit what remains, push, then monitor the CI run to a terminal state with the wrapper's foreground blocking wait; on red, fix every failure in one pass before pushing again. Exits only when CI passes.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---
Execute the git-push workflow. Steps A–D are defined in `.claude/commands/git-commit.md`:
Read it COMPLETELY first and run them exactly as written there, including Step C's toolchain
guard and attribution rules. Steps E and F are below. Apply
`.claude/rules/no-output-shortening.md` to every command.

1. Run Step B for the current branch and, if it is not `main`, against `origin/main` too.
2. Run Steps C and D — as many commits as the work naturally divides into.
3. Run Step E (push) ONCE, when the batch is complete.
4. Run Step F (monitor CI). If CI fails, enumerate EVERY failing job and every failure inside
   it FIRST, group them by root cause, fix them ALL, then loop back to Step C and push once.
   Do not fix one failure and re-push to find the next
   (`.claude/rules/ci-owns-the-test-suite.md`).

Exit only when CI passes.

Every forge operation — runs, logs, PRs — goes through `scripts/github_wrapper.py`
(`.claude/rules/use-git-wrapper-scripts.md`); never `gh`, `curl` or a raw API call. Origin is
GitHub (`git remote get-url origin`); this project has no GitLab.

## Step E: Push (once per batch)

Push ONCE, when the batch of work is complete and self-consistent — never to find out whether
it works. Before it you owe the paired tests for what you built, green and captured, not a
local full-suite run: CI runs the suite on the pushed SHA, and that run is the verdict.

1. If `git branch --show-current` is an auto-named `claude/*` branch, rename it first to a
   descriptive `<type>-<issue-or-topic>-<short-slug>` (`git branch -m <name>`) — branch
   names describe the work (`.claude/rules/no-ai-attribution.md`).
2. `git push origin <branch>`. If rejected (non-fast-forward), go back to Step B and retry. If
   a new branch needs upstream tracking: `git push --set-upstream origin <branch>`.
3. `git push` triggers the pre-push hook (`.githooks/pre-push`): mypy, plus the FULL test
   suite if CI-OUTAGE MODE is declared (`python scripts/ci_outage_mode.py status`). Fix
   whatever it reports; NEVER `--no-verify`.

A PR title or body written in this run (`create-pr`) describes the work only: no
`Co-Authored-By: Claude`, no `🤖 Generated with Claude Code`, no AI, assistant or bot
attribution — strip any such line the tool adds.

## Step F: Monitor CI

CI is where this project's test suite runs, and it is built not to fail fast — so a red run
is the COMPLETE list of what is wrong, not the first thing wrong.

1. Find the run for the pushed commit: `python scripts/github_wrapper.py list-runs --limit 5`,
   the run whose head SHA is `git rev-parse HEAD`.
2. Do every piece of work that does not depend on the verdict FIRST (the summary draft, docs,
   the issue note). Then wait for the run to terminate, in the FOREGROUND, bounded (Bash
   `timeout` 600000):

   ```bash
   python scripts/github_wrapper.py wait-run <run_id> --timeout-seconds 540
   ```

   Exit 0: success. Exit 10: completed without success. Exit 11: timeout — re-issue the same
   command, as often as it exits 11. Exit 1: wrapper or API error — read it, fix the cause.
   Never `sleep` in a tool call or a polling loop, never a background task (it dies with the
   session's process and never wakes you), never end the turn to wait.
3. If the run failed:
   1. Retrieve the logs of EVERY non-successful job
      (`python scripts/github_wrapper.py get-logs <run_id> --failed-only`, read in full) and
      enumerate every failing test and check before changing anything.
   2. Group them by root cause and record `N failures across M jobs → K root causes`.
   3. Fix every group (consult MCP doc servers and project docs as appropriate), committing as
      you go (Steps C–D), then loop back to Step B and push ONCE (Step E), and monitor the new
      run from F.1.

   Fixing one failure and re-pushing to discover the next is forbidden
   (`ci-owns-the-test-suite.md`, `remote-ci-must-pass.md`). Never abandon a red pipeline. A
   failure that genuinely cannot be diagnosed from the logs is stated with the evidence;
   everything else is fixed first, and the extra run is a cost you chose and name. If CI
   cannot produce a run at all, follow `remote-ci-must-pass.md`'s capacity ladder
   (`python scripts/ci_outage_mode.py declare …`, `clear` the moment a real run goes green).

## Summary

End with a summary listing files committed, commit message(s), conflicts resolved,
pre-commit/pre-push fixes, CI status, the number of CI runs this took and what each surfaced
(run id, why it was pushed, failures found, root-cause groups), and the final commit hash
from `git log --oneline -1`.
