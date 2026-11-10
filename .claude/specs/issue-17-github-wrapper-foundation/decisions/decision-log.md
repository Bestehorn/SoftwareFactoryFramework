# Decision Log

## DL-001 — 2026-11-10T17:13:20Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M; the delivery verbs wait-landed/check-handoff/check-landed keep the skeleton's DELIVERY_VERBS behaviour under UB-1; default API version stays 2022-11-28 (2026-03-10 selectable); the pending list is split per operation family.
**Driver:** Issue #17 tier line and its three open questions; clients/ call the three delivery verbs; the skeleton and the fork both send 2022-11-28 today; AC-1 asks for a layout where part-2 families avoid a shared file.
**Alternatives considered:** fork-only UB-1 (would break the steward verbs callers use); default 2026-03-10 (a caller-visible change in part 1); one shared pending file (every part-2 family edits it).
**Evidence:** clients/ wrapper invocations (wait-landed, check-handoff, check-landed); src/payload/scripts/github_wrapper.py `_api_request`, `DELIVERY_VERBS`.
**Supersedes:** none
**Artifacts touched:** prompt.md

## DL-002 — 2026-11-10T17:59:39Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Cross-wrapper decisions X1–X5 (review/review-latest.md): stdlib-import and Hypothesis tests in framework-only test/ with sys.stdlib_module_names; exceptions in <forge>_api/errors.py with base-prefixed names; #17's forms adopted by #13 where no forge reason exists; this change edits the setup prompts' wrapper copy steps so the package ships; promotion residual restated with a ledger row; normalised origin.
**Driver:** Conflicting lane findings — #17 test-architect A1 (find_spec/sysconfig check cannot fail in a venv) vs #13 BP-A1/ST-B1/SR-B4 (sys.stdlib_module_names needs 3.10 in a shipped 3.9 suite); #13 SR-B1 (five unrecorded divergences); #13 DO-B1, #17 ST-B2 (new projects would get a wrapper whose package import fails).
**Alternatives considered:** find_spec/sysconfig check (vacuous); leaving the copy step to promotion (promotion installs only into this repository; projects would break from the next release).
**Evidence:** review/*/iteration-01.md of both specs; prompts/setup-claude.txt Part 5.3 copy step.
**Supersedes:** none
**Artifacts touched:** review/review-latest.md

## DL-003 — 2026-11-10T18:39:55Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve requirements.md + design.md after design review iteration 04 (iteration 03: five lanes CLEAN, test-architect A1/B1 fixed; iteration 04: test-architect TEST-READY 24/24 0 GAP, combined delta check CLEAN); one conductor restatement routed from #13 (D8 keeps the shared sentence's GitLab half).
**Driver:** review/test-architect/iteration-04.md, review/spec-review-agent/iteration-04.md; tier M cap 4 reached with A+B = 0.
**Alternatives considered:** none
**Evidence:** review/*/iteration-0{1..4}.md; review/iteration-03-conductor.md
**Supersedes:** none
**Artifacts touched:** design.md, requirements.md

## DL-004 — 2026-11-10T19:06:38Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks review iteration 01 (both lanes CLEAN, A+B = 0; test-architect TEST-READY 24/24); C/D applied in one author pass (fork parity moved to wave 4, wave-5 run line extended, F.1 restated).
**Driver:** review/spec-review-agent/tasks-iteration-01.md, review/test-architect/tasks-iteration-01.md.
**Alternatives considered:** spec-review C2's separate task 4.2 (would depend on a same-wave sibling).
**Evidence:** tasks.md coverage table; lane files.
**Supersedes:** none
**Artifacts touched:** tasks.md

## DL-005 — 2026-11-10T21:47:36Z — issue-work-orchestrator — phase:VERIFY

**Decision:** Accept the verifier's REFUTED R1 R2 R3 as test gaps and reopen the TEST side only: R1 pins the Part 5.3 / Part 6.2 copy instruction itself, R2 adds golden rows for list-issues --limit <= 0 and a non-UTF-8 credential file, R3 adds the non-integer rate-limit header case; then one push and a delta re-verification.
**Driver:** evidence/verify/refutation-report.md R1 (copy-step mutant survives), R2/R3 (lines never run).
**Alternatives considered:** record R2/R3 as residuals (rejected: small, clear, test-only).
**Evidence:** evidence/verify/refutation-report.md; CI run 42903402594 success on 95fc3b8.
**Supersedes:** none
**Artifacts touched:** test/test_setup_prompts_github_wrapper.py, src/payload/test/github_wrapper_fixtures.py, src/payload/test/test_github_api_transport.py

## DL-006 — 2026-11-10T21:47:36Z — issue-work-orchestrator — phase:PR

**Decision:** Defer the work item 'Real-forge test on the #10 fixture' to #10 and close #17 on merge with the deferral recorded on the issue.
**Driver:** #10 owns the sff-test-* fixture and waits on the operator's create/delete token; requirements Residuals name the real-forge E2E as #10's.
**Alternatives considered:** keep #17 open until #10 lands (an issue held open by another issue's blocker).
**Evidence:** issue #17 comment of the implementation note; tasks.md F.1.
**Supersedes:** none
**Artifacts touched:** issue #17 comment
