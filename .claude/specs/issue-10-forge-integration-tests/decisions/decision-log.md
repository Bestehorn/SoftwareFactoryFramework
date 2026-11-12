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

## DL-003 — 2026-11-12T23:30:00Z — issue-work-orchestrator — phase:IMPLEMENT

**Decision:** `SubprocessGitRunner`'s identity options also pass `-c commit.gpgSign=false`, so the pull-request test's commit never asks for a signing key on a machine whose git config signs.
**Driver:** task 2.3's implementer report (D3 names only `user.name`/`user.email`); discipline C branch 2, small and clear — a constant in the identity options, no design choice.
**Alternatives considered:** leave it (the PR round trip fails on a signing machine); a design restatement (the spec is approved and the option adds no requirement).
**Evidence:** `test/test_forge_support.py` already passes `commit.gpgSign=false` to its own local commits.
**Artifacts touched:** test/forge/ephemeral.py (task 3.3)

## DL-004 — 2026-11-12T23:45:00Z — issue-work-orchestrator — phase:IMPLEMENT

**Decision:** The setup note (AC-9.1) lives in `docs/forge-suite.md`, not `credentials/README.md` (D7 restated); `docs/forLLMConsumption.md` points to it.
**Driver:** `.claude/settings.json` denies `Read(./credentials/**)` (toolchain, not editable), so no agent can read or edit a note there; task 3.2's implementer was blocked by it. AC-9.1: "Where it lives is design.md's".
**Alternatives considered:** keep `credentials/README.md` (unmaintainable by any agent; the existing file is the setup prompt's); ask the operator to relax the deny rule (a security setting stays the operator's).
**Evidence:** `.claude/settings.json` `Read(./credentials/**)`; `git ls-files credentials/` lists `README.md` and `github-pat.txt.template` (so D7's "ships no github-pat.txt.template" clause is also corrected).
**Artifacts touched:** design.md D7, D10, Correctness Properties AC-9.1; tasks.md 3.4; test/test_forge_suite_layout.py (task 3.2)
