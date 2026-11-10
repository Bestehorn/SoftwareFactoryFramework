# Decision Log

## DL-001 — 2026-11-10T17:25:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; fix all 45 findings at the type level in one change, delete the overrides block, pin AC-1 with a pyproject test; run_checks.py keeps one mypy run.
**Driver:** Issue #7 AC-1..AC-4 and its two open questions; the baseline-free mypy run reports the same 45 errors in 10 files on linux, win32 and darwin, each an annotation or narrowing gap; a per-platform run in run_checks.py would change shipped behaviour for every project and collide with issue #3's file.
**Alternatives considered:** module-by-module PRs (10 PRs for one ask; the issue allows one change per module but not ten CI runs); per-platform mypy in run_checks.py (beyond the ask).
**Evidence:** `python -m mypy src --config-file <scratch config without the override> --platform <p>` for p in linux, win32, darwin: "Found 45 errors in 10 files (checked 55 source files)" each.
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-7-remove-mypy-baseline/prompt.md

## DL-002 — 2026-11-10T16:37:11Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md after delta review iteration 02 (A+B = 0); D1 applied by the orchestrator (the CLAUDE.md baseline sentence is corrected in this run's promotion PR).
**Driver:** review/spec-review-agent/iteration-02.md verdict READY.
**Alternatives considered:** editing CLAUDE.md here (project-specific.md lists CLAUDE.md as toolchain).
**Evidence:** review/spec-review-agent/iteration-01.md#B1, iteration-02.md#D1
**Supersedes:** none
**Artifacts touched:** change.md
