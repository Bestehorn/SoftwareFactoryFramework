# Decision Log

## DL-001 — 2026-11-10T15:43:18Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S; fix shape = bandit writes its txt report to a UTF-8 file (-f txt -o) that run_check relays encoding-safely.
**Driver:** Issue #3 ask is one check of one script; bandit -o opens the file with encoding utf-8 (bandit cli/main.py -o/--output FileType), so the file is console-independent; a PYTHONIOENCODING=cp1252 test can reproduce it on Linux CI.
**Alternatives considered:** -X utf8 interpreter flag (PYTHONIOENCODING overrides UTF-8 mode, so no cross-platform failing test; bypasses the runnable -m probe); another formatter (same stdout encoding problem).
**Evidence:** local reproduction 2026-11-10 (UnicodeEncodeError in bandit/formatters/text.py report, RuntimeError, FAIL security/bandit exit 1, no B101 listed).
**Supersedes:** none
**Artifacts touched:** .claude/specs/issue-3-bandit-cp1252-report/prompt.md

## DL-002 — 2026-11-10T16:00:42Z — issue-work-orchestrator — phase:DESIGN_REVIEW

**Decision:** Approve change.md after combined review iteration 01 (A+B = 0); C1-C3 and D1 applied in one pass (sys.modules load named, console-script fallback asserted, LIST_MAX_ARGS raised, as_posix report path); C4 resolved by prompts.md.
**Driver:** review/spec-review-agent/iteration-01.md verdict READY (CLEAN).
**Alternatives considered:** C3 as a residual (would leave the listed docstring false).
**Evidence:** review/spec-review-agent/iteration-01.md#C1..#D1
**Supersedes:** none
**Artifacts touched:** change.md, prompts.md
