# Decision Log

## DL-001 — 2026-11-11T00:10:50Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier M; follow #28's design for the call mechanism, restating only GitLab differences; AC-4 covers the `/<route-prefix>/...` package-manager keys and the `Status: Experiment` capabilities rather than excluding them.
**Driver:** issue #41 Tier line and Open questions; the operator's #11/#15 request for 'the complete set of API features for both repo hosts'; parity with #28 (cross-wrapper precedent X1–X5 of #17/#13).
**Alternatives considered:** exclude protocol routes and experiments by rule (rejected: narrows the operator's 'complete set'; reversible later).
**Evidence:** issue #41 and #15 bodies; .claude/specs/issue-13-gitlab-wrapper-foundation/design.md Residuals.
**Supersedes:** none
**Artifacts touched:** prompt.md, qa_log.md

## DL-002 — 2026-11-11T00:27:57Z — issue-work-orchestrator — phase:REQUIREMENTS

**Decision:** Accept requirements.md as written, incl. Requirement 6's coverage of the 'Only in GraphQL' table (a capability pending set the coverage test reads) and AC-5.3's removed-key / moved-id checks, both for parity with #28.
**Driver:** issue #41 AC-4 ('covered … by a rule the coverage test applies'); #28 requirements AC-5.3.
**Alternatives considered:** keep part 1's REST-only coverage test (rejected: AC-4 needs the test to apply the rule to GraphQL-only capabilities).
**Evidence:** requirements.md Requirement 5, Requirement 6.
**Supersedes:** none
**Artifacts touched:** requirements.md

## DL-003 — 2026-11-11T02:48:41Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve design.md after iteration 04, the tier-M cap (test-architect CLEAN, TEST-READY 27/27; spec-review READY; the other four lanes CLEAN since iteration 02); the iteration-04 C items applied in one author pass without a further round.
**Driver:** review/<lane>/iteration-04.md and iteration-02/03 verdicts; review/review-latest.md Y1–Y5, Z1–Z3.
**Alternatives considered:** none
**Evidence:** review/review-latest.md; design.md 59,063 bytes, Residuals 10 lines.
**Supersedes:** none
**Artifacts touched:** design.md, review/review-latest.md

## DL-004 — 2026-11-11T03:26:25Z — issue-work-orchestrator — phase:TASKS_REVIEW

**Decision:** Approve tasks.md after tasks iteration 01 (both lanes CLEAN/READY, TEST-READY 27/27); the C/D items applied in one pass (three N helper tests named green-by-design with their verifier mutant; wave 4 runs test_layout.py).
**Driver:** review/test-architect/tasks-iteration-01.md, review/spec-review-agent/tasks-iteration-01.md.
**Alternatives considered:** none
**Evidence:** tasks.md (14,887 bytes).
**Supersedes:** none
**Artifacts touched:** tasks.md
