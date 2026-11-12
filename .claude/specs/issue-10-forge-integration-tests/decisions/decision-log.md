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

## DL-005 — 2026-11-13T00:10:00Z — issue-work-orchestrator — phase:IMPLEMENT

**Decision:** `test/forge/conftest.py` registers the by-path-loaded `ephemeral.py` as `sys.modules["forge_ephemeral"]` (the name `test/test_forge_support.py` and `write_credential.py` use); a forge module reaches the support functions (`is_leftover`, `TEST_ORGANIZATION`) through that entry inside its test bodies.
**Driver:** D10 "loads `ephemeral.py` by path once per process (`sys.modules` holds it)" and D1's "defines one fixture" leave how a forge module reaches the helpers open; D6's `test_no_leftover_survives_the_sweep` needs `is_leftover`.
**Alternatives considered:** a second fixture returning the module (D1 names one fixture); `import ephemeral` by name (a second copy beside the by-path one).
**Evidence:** design.md D1, D10; task 3.1's `_ephemeral()` loader registers `forge_ephemeral`.
**Artifacts touched:** test/forge/conftest.py, test/forge/forge_*.py (wave 4)

## DL-006 — 2026-11-12T20:05:00Z — issue-work-orchestrator — phase:VERIFY

**Decision:** CI run 43295116103: 7 failures across 1 job (`forge`; `report` follows it) → 1 root cause, the test token lacks the permissions D6 marks "to grant"; no code change, the run waits on the operator's grant.
**Driver:** every failure is `HTTP 403 "Resource not accessible by personal access token"` on `POST /issues`, `POST /labels`, `GET`/`POST /pulls`, `GET /actions/runs`, `GET /secret-scanning/alerts`, `GET /dependabot/secrets`; the fixture created, pushed to and deleted its repository; all five `verify` legs green. <!-- pragma: allowlist secret -->
**Alternatives considered:** weakening the slice tests to accept the 403 (forbidden by `tests-must-not-fail.md`; the permissions are a documented prerequisite).
**Evidence:** evidence/regress/ci-43295116103-12d8df7.txt.
**Artifacts touched:** evidence/regress/ci-43295116103-12d8df7.txt

## DL-007 — 2026-11-12T21:00:00Z — issue-work-orchestrator — phase:VERIFY

**Decision:** Accept the verifier's REFUTED AC-1.1 AC-1.4 AC-3.1 AC-4.1 as test gaps and rework tests only: W gains a mid-name `sff-test-` origin (1b); S gains a creation answered `private: false` whose kept record is deleted (3k, 3l), a `remove_tree` whose first removal is refused (3n), and a failed leftover listing that stops the run (3m).
**Driver:** evidence/verify/refutation-report.md rows 3, 15, 16, 17 — five mutants survived the paired tests; the code under them is as designed.
**Alternatives considered:** none — a surviving mutant is a missing test, and the production code holds the designed behaviour.
**Evidence:** evidence/verify/mutant-wave-1.txt (1b), mutant-wave-3.txt (3k, 3l, 3m, 3n); coverage.txt (unexercised lines).
**Artifacts touched:** src/payload/test/test_github_wrapper_marker.py, test/test_forge_support.py; tasks.md 1.1, 3.1
