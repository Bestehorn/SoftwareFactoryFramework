---
description: Rebase the current branch onto the latest remote (origin/<branch>, or origin/main when it has no upstream), resolving every conflict, then run the git-commit workflow. Never pushes.
allowed-tools: Bash, Read, Edit, Grep, Glob
---
Execute the git-rebase workflow.

1. Run Step B below: fetch and rebase onto `origin/<current-branch>`; if the branch has no
   upstream, rebase onto `origin/main`.
2. Then run the git-commit workflow (Steps A, B, C, D): Read `.claude/commands/git-commit.md`
   COMPLETELY and execute it exactly as written. Its toolchain guard and its attribution rules
   (`.claude/rules/no-ai-attribution.md`) apply to every commit this run makes, and its
   pre-commit hook is never bypassed with `--no-verify`.

This command never pushes; `/git-push` does, ONCE, when the batch is complete. Apply
`.claude/rules/no-output-shortening.md` to every command.

## Step B: Integrate remote changes

`<branch>` is `git branch --show-current`. The target is `origin/<branch>`; when
`git rev-parse --abbrev-ref --symbolic-full-name @{u}` reports no upstream, the target is
`origin/main`.

`git fetch origin`. Compare the local branch with the target: `git log HEAD..<target>
--oneline`. If remote changes exist:
1. Stash local uncommitted changes if any: `git stash`.
2. `git rebase <target>`.
3. On conflict: identify with `git diff --name-only --diff-filter=U`, read both versions of
   each file, produce a merged version that preserves both intents, `git add <file>`,
   `git -c core.editor=true rebase --continue` (no editor can open here). Repeat until the
   rebase completes.
4. If the rebase becomes too tangled: `git rebase --abort`, fall back to
   `git merge <target>`.
5. Restore the stash if applicable: `git stash pop` (resolve any conflicts the same way).

## Summary

End with the git-commit summary; its remote integration details name the rebase target and
every conflict resolved.
