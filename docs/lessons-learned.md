# Lessons Learned

Each lesson is at most five lines. A lesson older than six weeks with `Enforced-by: none`
is enforced by a test, hook or rule line, or archived to docs/archive/ by /compile-memory.
Incident narratives belong in docs/archive/incidents/<date>-<slug>.md, never here.

## 2026-11-11 — Git Bash rewrites a command argument that begins with a slas
- Date: 2026-11-11
- Lesson: Git Bash rewrites a command argument that begins with a slash into a Windows path (a leading-slash word became C:/Program Files/Git/...), so never start a CLI argument value with a slash
- Enforced-by: none
- Scope: shell arguments on Windows (memory_compile.py ledger add)
## 2026-11-11 — Take a decision-log timestamp from date -u in the same step
- Date: 2026-11-11
- Lesson: Take a decision-log timestamp from date -u in the same step that writes the entry; never type one
- Enforced-by: none
- Scope: agent-state-convention decision log

## 2026-11-11 — Run no git operation in a worktree while a delegate tests or
- Date: 2026-11-11
- Lesson: Run no git operation in a worktree while a delegate tests or mutates there; it owns the tree until its report
- Enforced-by: none
- Scope: issue-work-orchestrator worktrees

## 2026-11-12 — A delegate probing git credentials must pass -c credential.h
- Date: 2026-11-12
- Lesson: A delegate probing git credentials must pass -c credential.helper= first; without it git credential fill printed the system Git Credential Manager's real github.com token into the session
- Enforced-by: test/test_forge_support.py test_the_credential_helper_answers_git_with_the_clone_token
- Scope: forge suite, git credential helper
