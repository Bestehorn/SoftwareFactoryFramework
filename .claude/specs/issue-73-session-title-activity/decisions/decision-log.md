# Decision Log

## DL-001 — 2026-11-26T14:10:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** Tier S, not the M the intake proposed.
**Driver:** The ask changes natural-language assets and one structural test; no shipped code, no new interface
(`proportionality.md`: a message or doc change however many files it touches; smaller tier when in doubt).
**Alternatives considered:** M (intake: "two agents, eleven commands and the main session, with a format to choose").
**Evidence:** issue #73 body, `## Where` and `## Work items`.
**Artifacts touched:** change.md, prompt.md

## DL-002 — 2026-11-26T14:10:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** The issue's three open questions are reversible and decided here: separator ` · ` with a fixed activity
list per kind of session and the subject first; the interactive session learns the rule from one CLAUDE.md fleet
line pointing to the on-demand doc; Kiro keeps its skip, since an operator-typed `/sessions rename` is no tool an
agent can call.
**Driver:** issue #73 `## Open questions`; `continuous-work.md` (reversible decisions are decided, not asked).
**Alternatives considered:** a new always-loaded rule file (costs every agent of every session the corpus bytes for a
desktop-only norm); asking the operator.
**Evidence:** `test/test_instruction_corpus_budget.py` `CORPUS_CAP_BYTES`; kirodotdev/Kiro#7836, #5471 (issue body).
**Artifacts touched:** change.md, clients/claude/docs/session-title.md

## DL-003 — 2026-11-26T14:10:00Z — issue-work-orchestrator — phase:CLASSIFY

**Decision:** The delivery.md §4 refusal row rides along in this PR as a fix in passing, not a filing.
**Driver:** `issue-filing-discipline.md` branch 2 (small and clear, one table row, no design choice).
**Evidence:** `clients/common/docs/delivery.md` §4 has no row for a `deploy-guard` refusal since PR #70.
**Artifacts touched:** clients/common/docs/delivery.md

## DL-004 — 2026-11-26T14:40:00Z — issue-work-orchestrator — phase:CHANGE_REVIEW

**Decision:** Approve the spec as reviewed after iteration 2, its one B and one C applied as proposed, without a third
round.
**Driver:** `proportionality.md` tier S review cap of 2 iterations; both fixes restate test text and add no criterion.
**Evidence:** review/spec-review-agent/iteration-02.md#B1, #C1; review/review-latest.md.
**Artifacts touched:** change.md, review/review-latest.md
