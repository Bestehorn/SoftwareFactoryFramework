# Decision Log

## DL-001 — 2026-11-10T16:20:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; anchor `reports/` plus the root-only packaging directories (`lib/`, `lib64/`, `var/`, `downloads/`, `eggs/`, `develop-eggs/`, `parts/`, `sdist/`, `wheels/`); keep `build/`, `dist/`, venvs, `tmp/` and caches unanchored; both blocks tell a project to replace an existing slash-free form of an anchored entry.
**Driver:** Issue #2 work item "One pass over the other unanchored directory entries of PART 3; anchor those that only ever mean the root" and its two open questions; an unanchored `lib/` also matches `cdk/lib/` (TypeScript CDK source).
**Alternatives considered:** anchor every directory entry (would un-ignore a frontend's nested `build/`/`dist/` and nested venvs); anchor only `reports/` (leaves the `lib/` pitfall the issue asked to sweep for); leave existing lines alone (existing projects keep the swallowing line).
**Evidence:** gitignore(5) "If there is a separator at the beginning or middle (or both) of the pattern, then the pattern is relative to the directory level of the particular .gitignore file itself. Otherwise the pattern may also match at any level below the .gitignore level."; prompts/setup-kiro.txt PART 3 block.
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-2-anchor-gitignore-dirs/prompt.md

## DL-002 — 2026-11-10T16:06:01Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md at the tier-S cap after iteration 02 (A1: one word, "replace" -> "REPLACED"; D1: docstring note) — both applied by the orchestrator and checked against the replace sentences in change.md Files.
**Driver:** review/spec-review-agent/iteration-02.md A1 proposed edit; iteration cap 2 reached.
**Alternatives considered:** a third round (beyond the S cap; the fix is one word).
**Evidence:** review/spec-review-agent/iteration-02.md#A1, #D1
**Supersedes:** none
**Artifacts touched:** change.md
