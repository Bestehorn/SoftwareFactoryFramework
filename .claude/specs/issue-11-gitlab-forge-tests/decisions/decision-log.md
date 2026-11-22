# Decision Log

## DL-001 — 2026-11-22T09:40:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M: the GitLab twin of #10 (fixture with two guarded deletion paths, product-wrapper origin guard, CI job, real-forge tests), with a design choice in each component.
**Driver:** issue #11 work item "Real-GitLab integration tests (needs a GitLab equivalent of #10)"; #10 was tier M for the same shape (its DL-001).
**Alternatives considered:** S (rejected: several components and a new guard interface); L (rejected: no new subsystem, #10's mechanisms are reused).
**Evidence:** issue #11 body, Work items; `.claude/specs/issue-10-forge-integration-tests/decisions/decision-log.md` DL-001.
**Artifacts touched:** prompt.md, qa_log.md, prompts.md

## DL-002 — 2026-11-22T09:40:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** The test group's path is the working value `bestehorn-sff-test` on gitlab.com, one constant of the suite, corrected when the operator names the group.
**Driver:** operator "Use gitlab.com"; the GitHub test organization and the operator's first GitLab group both use `bestehorn-sff-test`; a reversible constant is decided, not asked (`continuous-work.md`).
**Alternatives considered:** wait for the operator's group path before the spec (idles the run on a one-constant answer).
**Evidence:** issue #11 comments 7077139116 and 7077150394; `docs/forge-suite.md` (organization `bestehorn-sff-test`).
**Artifacts touched:** prompt.md Operator facts

## DL-003 — 2026-11-22T09:40:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** gitlab.aws.dev is rejected as the test target; gitlab.com is the operator's choice.
**Driver:** every request to gitlab.aws.dev, with `PRIVATE-TOKEN`, `Bearer` or git basic auth, returned `302` from `awselb/2.0` to `idp.federate.amazon.com` (from the operator's machine and from an outside network).
**Alternatives considered:** a GitLab started inside the CI job (no account, slower, Free features only); asking the instance's administrators (blocked on them).
**Evidence:** issue #11 comment 7077150394 (the four probes); operator answer "Use gitlab.com".
**Artifacts touched:** prompt.md Operator facts

## DL-004 — 2026-11-22T11:10:00Z — issue-work-orchestrator — phase:DESIGN

**Decision:** The project guard judges the clone config's `project_id` written as the path `<group>/sff-test-<run id>`, refusing any other value under the marker with no request (design.md D2).
**Driver:** the GitLab wrapper reads no git origin (`gitlab_wrapper.py` `_load_config`, `CONFIG_FILE`); a request-based guard breaks the fake-host tests (`FakeGitLab.serve` raises on an unscripted request).
**Alternatives considered:** a read of the configured project per invocation; a second `project_path` key.
**Evidence:** codebase research burst (wrapper map); `commands/call.py` `path_values`, `registry._segment`.
**Artifacts touched:** design.md D2

## DL-005 — 2026-11-22T11:10:00Z — issue-work-orchestrator — phase:DESIGN

**Decision:** git reads the token from `<clone>/.git/sff-forge-token` through #10's credential helper; AC-6.3 restated before the design review to allow that one clone file.
**Driver:** the clone's wrapper credential is JSON, which the helper's shell built-ins cannot parse.
**Alternatives considered:** parsing `config/gitlab.json` in the snippet; a working-tree `credentials/` file in the clone.
**Evidence:** design.md D3; `test/forge/ephemeral.py` `credential_helper_arguments`.
**Artifacts touched:** design.md D3, requirements.md AC-6.3

## DL-006 — 2026-11-22T11:10:00Z — issue-work-orchestrator — phase:DESIGN

**Decision:** A separate suite `test/forge_gitlab/` and CI job `forge-gitlab`; the teardown only marks the project (gitlab.com retains it 30 days); the sweep sends nothing for a marked project.
**Driver:** `test/test_forge_suite_layout.py` applies GitHub-only rules to every file under `test/forge/`; docs.gitlab.com/api/projects "Delete a project": `permanently_remove` "Disabled on GitLab.com and Dedicated".
**Alternatives considered:** GitLab modules inside `test/forge/`; one job for both forges; a matrix; immediate removal.
**Evidence:** lifecycle research burst (Q1); design.md D1, D5, D9.
**Supersedes:** none
**Artifacts touched:** design.md D1, D5, D9; requirements.md UB-4

## DL-007 — 2026-11-22T14:30:00Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Design approved at iteration 03 (A+B 0, TEST-READY with zero GAP); the one remaining C (name the GitLab git helper binding `CLONE_GIT_HELPER`) is applied with the tasks pass, without another panel round.
**Driver:** review/review-latest.md (iteration 03); `spec-phase-review.md` Readiness gate.
**Alternatives considered:** a fourth panel round for one C (not offered: C never gates).
**Evidence:** review/spec-review-agent/iteration-03.md C1, review/test-architect/iteration-03.md C1, review/standards-reviewer/iteration-03.md (CLEAN).
**Artifacts touched:** review/review-latest.md

## DL-008 — 2026-11-22T16:10:00Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** tasks.md approved at tasks iteration 02 (both lanes CLEAN, TEST-READY, every AC and UB in a TEST task); five waves after splitting wave 1 so no IMPL depends on an IMPL of its own wave.
**Driver:** review/spec-review-agent/tasks-iteration-01.md B1; tasks-iteration-02.md of both lanes.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/tasks-iteration-02.md (READY), review/test-architect/tasks-iteration-02.md (TEST-READY).
**Artifacts touched:** tasks.md

## DL-009 — 2026-11-22T14:40:00Z — issue-work-orchestrator — phase:VERIFY

**Decision:** CI run 45033382186: 2 failures across 2 jobs (`forge-gitlab`, `report`) → 1 root cause, the Actions secret `SFF_GITLAB_TEST_TOKEN` is unset; no code change, the real run waits on the operator's token.
**Driver:** the credential step logged "the secret SFF_GITLAB_TEST_TOKEN is unavailable to this run" (AC-5.3 as designed); `report` failed on `forge-gitlab job: failure`; all four `verify` legs and the `forge` job succeeded.
**Alternatives considered:** none (a missing secret is the operator's prerequisite, tasks.md Operator prerequisite).
**Evidence:** evidence/regress/ci-45033382186-c389d46.txt.
**Artifacts touched:** evidence/regress/ci-45033382186-c389d46.txt

## DL-010 — 2026-11-22T15:30:00Z — issue-work-orchestrator — phase:PR

**Decision:** CI run 45037920116 on ce7ea83: the same 1 root cause as DL-009 (secret `SFF_GITLAB_TEST_TOKEN` unset; `forge-gitlab` and `report` failed, every other job green); the PR waits for the operator's token, nothing to fix in code.
**Driver:** the credential step logged "the secret SFF_GITLAB_TEST_TOKEN is unavailable to this run" again.
**Alternatives considered:** merging with `forge-gitlab` red (fails `report` on `main` and every later PR; devops verify-01 C2).
**Evidence:** evidence/regress/ci-45037920116-ce7ea83.txt.
**Supersedes:** none
**Artifacts touched:** evidence/regress/ci-45037920116-ce7ea83.txt
