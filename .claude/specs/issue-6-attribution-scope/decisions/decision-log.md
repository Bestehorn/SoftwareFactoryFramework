# Decision Log

## DL-001 — 2026-11-10T16:58:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; one scope (attribution + authored names) with a GENERAL allowance for naming an existing path, command, setting or product as the subject of the work; setup-claude restatements need no edit.
**Driver:** Issue #6 AC-1..AC-4 and its two open questions; a named list would go stale with every new path, and a commit about the Claude client's hooks names the client as subject, not as author.
**Alternatives considered:** a named list (`.claude/`, `clients/claude/`, `setup-claude`) — breaks on the next path; paths only — still forbids "setup-claude: …" style subjects.
**Evidence:** clients/claude/rules/no-ai-attribution.md opening paragraph vs. self-check; prompts/setup-kiro.txt 8.28; prompts/setup-claude.txt restatements ("no Claude/AI/bot attribution", "never an AI trailer").
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-6-attribution-scope/prompt.md

## DL-002 — 2026-11-10T16:37:32Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Fix the blanket-ban restatements in clients/claude/commands/work-issue.md, auto-work.md and both issue-work-orchestrator.md bodies in this change instead of leaving them as residuals.
**Driver:** review iteration-01 C1 and the author's residual; issue-filing-discipline branch 2 (small and clear, same root cause as the rule's contradiction).
**Alternatives considered:** residual or a new issue (would ship a rule that its own commands contradict).
**Evidence:** review/spec-review-agent/iteration-01.md#C1; iteration-02.md#C3
**Supersedes:** none
**Artifacts touched:** change.md

## DL-003 — 2026-11-10T16:37:32Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md after delta review iteration 02 (A+B = 0); C1 and C2 applied in one author pass.
**Driver:** review/spec-review-agent/iteration-02.md verdict CLEAN — READY.
**Alternatives considered:** none
**Evidence:** review/spec-review-agent/iteration-02.md#C1, #C2
**Supersedes:** none
**Artifacts touched:** change.md
