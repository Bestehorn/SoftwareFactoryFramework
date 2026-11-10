# Decision Log

## DL-001 — 2026-11-10T17:13:20Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M; the pending list is split per endpoint family; UB-1 adds any caller-used subcommand the docstring omits; the operation layer follows the GitHub sibling #17's structure where the forges allow.
**Driver:** Issue #13 tier line and its two open questions; AC-1 asks for a layout without a file shared across families; #17 is worked in parallel in this run.
**Alternatives considered:** one shared pending file (every part-2 family edits it); docstring-only UB-1 (could break an undocumented caller).
**Evidence:** issue #13 body; src/payload/scripts/gitlab_wrapper.py module docstring.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-10T17:59:39Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Cross-wrapper decisions X1–X5 (review/review-latest.md): stdlib-import and Hypothesis tests in framework-only test/ with sys.stdlib_module_names; exceptions in <forge>_api/errors.py with base-prefixed names; #17's forms adopted by #13 where no forge reason exists; this change edits the setup prompts' wrapper copy steps so the package ships; promotion residual restated with a ledger row; normalised origin.
**Driver:** Conflicting lane findings — #17 test-architect A1 (find_spec/sysconfig check cannot fail in a venv) vs #13 BP-A1/ST-B1/SR-B4 (sys.stdlib_module_names needs 3.10 in a shipped 3.9 suite); #13 SR-B1 (five unrecorded divergences); #13 DO-B1, #17 ST-B2 (new projects would get a wrapper whose package import fails).
**Alternatives considered:** find_spec/sysconfig check (vacuous); leaving the copy step to promotion (promotion installs only into this repository; projects would break from the next release).
**Evidence:** review/*/iteration-01.md of both specs; prompts/setup-claude.txt Part 5.3 copy step.
**Supersedes:** none
**Artifacts touched:** review/review-latest.md

## DL-003 — 2026-11-10T18:35:51Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md + design.md after design review iteration 03 (combined A+B = 0 across six lanes; test-architect TEST-READY, 24/24, 0 GAP); remaining C/D applied in one author pass without another round.
**Driver:** review/*/iteration-03.md verdicts CLEAN; spec-phase-review.md readiness gate.
**Alternatives considered:** a fourth round (not needed: gate passed).
**Evidence:** review/{spec-review-agent,test-architect,standards-reviewer,best-practice-reviewer,security-reviewer,devops-iac-reviewer}/iteration-03.md
**Supersedes:** none
**Artifacts touched:** design.md, requirements.md

## DL-004 — 2026-11-10T19:23:09Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 02 (both lanes CLEAN, A+B = 0; TEST-READY 24/24); the two remaining C/D (3.2 mutant note, 5.5 rewrap) applied by the conductor.
**Driver:** review/test-architect/tasks-iteration-02.md, review/spec-review-agent/tasks-iteration-02.md.
**Alternatives considered:** none
**Evidence:** lane files tasks-iteration-01/02.
**Supersedes:** none
**Artifacts touched:** tasks.md, design.md

## DL-005 — 2026-11-10T21:18:13Z — issue-work-orchestrator — phase:IMPLEMENT

**Decision:** Split wave 5 in two: commit 5.1, 5.3 and 5.4 now; make 5.5's setup-prompt and map edits after #17's PR lands and this branch is rebased on it, with 5.2's test committed alongside 5.5.
**Driver:** #17 (PR #26) edits the same Part 5.3, Part 6.2, shipped-Python and map lines; D2/5.5 restate only the GitLab half 'as the tree holds it when this change lands', so 5.5 written before #17 lands would be rewritten by the rebase.
**Alternatives considered:** write 5.5 now and resolve the conflict at rebase (two edits of the same sentences).
**Evidence:** tasks.md task 5.5; design.md D2 install path; evidence/green/wave-5a.txt (# tasks: 5.1 5.3 5.4).
**Supersedes:** none
**Artifacts touched:** tasks.md, evidence/green/wave-5a.txt

## DL-006 — 2026-11-10T22:53:48Z — issue-work-orchestrator — phase:IMPLEMENT

**Decision:** Absorb the run_checks.py file-list batching fix into this change (fix-first branch 1): a file-list check whose command line exceeds MAX_COMMAND_LINE_CHARS runs in batches repeating its fixed arguments.
**Driver:** run_checks.py --group security on this branch: `[WinError 206] The filename or extension is too long`, detect-secrets exit 127 — this branch's tracked files exceed CreateProcess's 32,767-character cap, so the post-activity check fails here and on every Windows session once it lands.
**Alternatives considered:** file it (rejected: small, clear, blocking); run detect-secrets in process (rejected: the runner keeps tools as subprocesses).
**Evidence:** evidence/red/run-checks-batching.txt, evidence/green/run-checks-batching.txt; product run_checks lint/types/security 5 passed, detect-secrets as 2 commands.
**Supersedes:** none
**Artifacts touched:** src/payload/scripts/run_checks.py, src/payload/test/test_run_checks.py
