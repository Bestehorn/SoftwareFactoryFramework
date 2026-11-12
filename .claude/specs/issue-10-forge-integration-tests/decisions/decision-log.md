# Decision Log

## DL-001 — 2026-11-12T16:20:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M: a session fixture, two guarded deletion paths, a wrapper origin guard and a CI job, each with a design choice, across the test tree, the product wrapper and the workflow.
**Driver:** Issue #10 body "Tier: M"; its three open questions are design choices (suite separation, the marker, the template stub).
**Alternatives considered:** S (rejected: several components and a choice of mechanism in each); L (rejected: no new subsystem, GitLab is #11).
**Evidence:** issue #10 body, Acceptance criteria (draft) and Open questions; prompt.md Scope.
**Artifacts touched:** prompt.md, qa_log.md, prompts.md

## DL-002 — 2026-11-12T19:10:00Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Fix review B1 by restating AC-6.1 to the design (the checkout that runs the suite or, for a linked worktree without the file, the repository's main working tree), not by deleting D8's fallback.
**Driver:** review/spec-review-agent/iteration-01.md B1; a linked worktree holds no git-ignored file, and every issue here is worked in one.
**Alternatives considered:** delete the fallback (the suite could never run locally from an issue worktree without copying the token into it).
**Evidence:** `git rev-parse --git-common-dir` in `.claude/worktrees/issue-10` prints the main checkout's `.git`; prompt.md operator facts (one local file).
**Artifacts touched:** requirements.md AC-6.1, review/review-latest.md
