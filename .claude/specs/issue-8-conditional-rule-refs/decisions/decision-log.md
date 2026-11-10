# Decision Log

## DL-001 — 2026-11-10T17:05:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; a fixed `(where installed)` marker after each reference in the ten agent bodies plus install-condition notes in both setup prompts; omitting the three rules in a non-AWS project is the intended install; devops-iac-reviewer stays installed everywhere.
**Driver:** Issue #8 AC-1..AC-4 and its three open questions; setup-claude Part 5.1 "Drop the AWS/CDK deny rules and the AWS MCP allow rules for non-AWS projects" and Part 0.1 "a non-AWS project may need none" already treat AWS/MCP as conditional; devops-iac-reviewer's description says a change touching none of its areas is CLEAN in one line.
**Alternatives considered:** condition only in the prompts (installed agents still name a missing rule); per-project agent rendering (tier M, beyond the ask); dropping devops-iac-reviewer for non-infra projects (loses its CI/operability lane).
**Evidence:** prompts/setup-claude.txt Part 0.1 server-set sentence and Part 5.1 "Tailor to the project"; clients/claude/agents/devops-iac-reviewer.md description.
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-8-conditional-rule-refs/prompt.md

## DL-002 — 2026-11-10T16:23:24Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md after delta review iteration 02 (A+B = 0, no C/D).
**Driver:** review/spec-review-agent/iteration-02.md verdict READY — CLEAN.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-01.md#B1, iteration-02.md
**Supersedes:** none
**Artifacts touched:** change.md
