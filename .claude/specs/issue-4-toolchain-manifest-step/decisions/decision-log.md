# Decision Log

## DL-001 — 2026-11-10T17:15:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; a committed repository tool `scripts/toolchain_manifest.py` derives `files` from the release tree by the install layout minus `not_installed`, carries `deviations`/`not_installed`, and is reached from update.txt step 7 through a generic one-sentence manifest step plus the map's pointer; five unreasoned release sources get `not_installed` reasons.
**Driver:** Issue #4 AC-1..AC-4 and both open questions; only this repository keeps a toolchain manifest, so a full product step would burden every project; deriving from the release (not manifest+delta) makes added and removed files visible mechanically; `git ls-tree -r --name-only v2026.11.09` lists `clients/claude/README.md`, `templates/README.md`, `templates/docs/README.md`, `src/hooks/ruff.toml`, `templates/pre-commit-config.yaml.template` under installable trees with neither a `files` nor a `not_installed` entry.
**Alternatives considered:** a prompt-only manifest paragraph in update.txt (not reproducible, no AC-4 test); manifest-plus-delta derivation (a re-run against the same release proves nothing; added files invisible); naming the tool in CLAUDE.md "This project" (CLAUDE.md is toolchain per project-specific.md).
**Evidence:** prompts/update.txt `## Task` step 7; config/toolchain.json; test/test_toolchain_integrity.py; git ls-tree of v2026.11.09.
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-4-toolchain-manifest-step/prompt.md

## DL-002 — 2026-11-10T16:38:55Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md at the tier-S cap after iteration 02: B1 (tests read release_tag/installed from the committed manifest instead of naming v2026.11.09) applied and re-verified by the author against v2026.11.10; D1 cuts applied; prompt.md restated by the orchestrator.
**Driver:** review/spec-review-agent/iteration-02.md#B1; origin/main promoted v2026.11.10 (f13cf20) during the review.
**Alternatives considered:** a third round (beyond the S cap; the fix is a restatement).
**Evidence:** review/spec-review-agent/iteration-02.md#B1, #D1; git ls-tree -r -z --name-only refs/tags/v2026.11.10 comparison (author report)
**Supersedes:** none
**Artifacts touched:** change.md, prompt.md
