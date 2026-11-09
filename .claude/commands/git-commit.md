---
description: Commit the current work at a natural boundary — .gitignore compliance, integrate remote changes, refuse hand edits of toolchain files, stage and commit with a descriptive message, and loop until the pre-commit hook (lint + security) passes. Never pushes.
allowed-tools: Bash, Read, Edit, Grep, Glob
---
Execute the git-commit workflow. Run Steps A, B, C, D in order. Loop within Step D until
the pre-commit hook passes. `/git-rebase` and `/git-push` run these same steps; this file is
where they are defined. `/git-commit` itself never pushes.

**Commit often.** The pre-commit hook is lint + security only, about a second, so commit at
every natural boundary — a task finished, a test written, a refactor separated from a
behaviour change — rather than accumulating one enormous change. A readable series of small
commits is the deliverable (`.claude/rules/ci-owns-the-test-suite.md`). The full test suite
is never a precondition for a commit. Apply `.claude/rules/no-output-shortening.md` to every
command.

## Step A: .gitignore compliance

Run `git status`. For each changed/untracked file decide whether it belongs in the
repository:
- DOES NOT belong: build artifacts, compiled output, cache dirs, IDE-specific files, temp
  files, secrets, credentials, env-specific files.
- DOES belong: source, configuration files (`ruff.toml`, `.pre-commit-config.yaml`), docs,
  tests, scripts, prompts, templates, `.claude/` rules, commands, agents and hooks.

For each file that doesn't belong, add an entry to `.gitignore` (preserve existing entries).
Verify `git status` no longer lists ignored files.

## Step B: Integrate remote changes

`<branch>` is `git branch --show-current`. `git fetch origin`. Compare the local branch with
origin: `git log HEAD..origin/<branch> --oneline` (a branch with no `origin/<branch>` yet has
nothing to integrate). If remote changes exist:
1. Stash local uncommitted changes if any: `git stash`.
2. `git rebase origin/<branch>`.
3. On conflict: identify with `git diff --name-only --diff-filter=U`, read both versions of
   each file, produce a merged version that preserves both intents, `git add <file>`,
   `git -c core.editor=true rebase --continue` (no editor can open here). Repeat until the
   rebase completes.
4. If the rebase becomes too tangled: `git rebase --abort`, fall back to
   `git merge origin/<branch>`.
5. Restore the stash if applicable: `git stash pop` (resolve any conflicts the same way).

## Step C: Stage and commit

1. `git status` to review.
2. `git add <files>` for each file that should be committed.
3. **Toolchain guard.** This repository runs its own released framework. Every path under
   `files` in `config/toolchain.json` is an installed TOOLCHAIN file and is never edited by
   hand. Check `git diff --cached --name-only` against those keys. If a staged path is one of
   them and `git branch --show-current` does not match `framework-update-*` (the branch a
   framework update installs a release on), REFUSE: `git restore --staged <path>` for each,
   commit none of them, and name for each the product file to change instead — the value
   `config/toolchain.json` records for it. The change belongs in the product file; it reaches
   the installed copy only through a release and its promotion. Do not discard the hand edit —
   list it in the summary. A path the manifest does not list (`CLAUDE.md`, the ported rules,
   `scripts/api_reference/`, `test/test_layout.py`, spec artifacts) is a project file and
   commits normally. (The `toolchain-paths` gate and `test/test_toolchain_integrity.py`
   enforce the same list.)
4. `git diff --cached` — review what's about to be committed.
5. Generate a commit message:
   - subject in imperative mood, max 72 chars, describing the change
   - blank line
   - body describing changes by component or purpose

   Per `.claude/rules/no-ai-attribution.md` the message describes the work only: no
   `Co-Authored-By: Claude`, no `🤖 Generated with Claude Code`, no AI, assistant or bot
   attribution and no tool trailer of any kind. Write only your descriptive message and
   strip any such line the tool adds by default. Scan the full text for `claude`, `AI`,
   `assistant`, `bot`, `LLM`, `Anthropic`, `Copilot`, `🤖`, `Co-Authored-By`,
   `Generated with`: a hit used as attribution is a defect — restate before committing.
6. `git commit -m "<subject>" -m "<body>"`.

## Step D: Pre-commit hook handling

`git commit` triggers the pre-commit hook (`.githooks/pre-commit`): ruff lint, ruff-format,
bandit over the staged files, and a secret scan. No tests, no mypy — under two seconds.
- Exit code 0: hook passed; proceed.
- Non-zero exit: fix every reported issue. Then go back to Step B (there may be new remote
  changes), Step C (stage the fixes), Step D (commit again).
- NEVER use `--no-verify` to bypass the hook. There is nothing to save — and the secret scan
  is the one check whose miss cannot be undone after a push.

## Summary

End with a summary listing files committed, the commit message, `.gitignore` changes, remote
integration details, pre-commit fixes, and every toolchain path refused with the product
file named for it.
