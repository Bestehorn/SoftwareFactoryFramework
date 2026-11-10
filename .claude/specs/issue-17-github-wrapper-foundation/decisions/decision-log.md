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
