# Target review, round 12 (confirmation pass): revision 12 of the factory state model (2026-11-20)

Reviewed: branch `docs-factory-state-model-design` at `50cec91`, read from a detached worktree. I read the full diff
from revision 11 (`b440fb7`) for design.md, decisions.md (R117; R116 revised) and traceability.md (header only).

Targets: the keynote deck and the gap analysis in the main checkout (untracked and excluded). Neither was copied, and
this report cites them by slide or section number only. Framing: decision U22 (the keynote is a vision). Finding shape:
`clients/common/docs/review-contract.md`. New-finding ids would be X1, …; there are none.

## Summary

OPEN ITEMS: 0

**Earlier items:** none were open after round 11.

**New findings:** none (0 A, 0 B, 0 C, 0 D).

**Verdict: every traceability row that revision 12's changes touch is still honest against design.md, the keynote and
the gap analysis.**

- Revision 12 changes only how the dispatcher keeps the steward-liveness bound (§3.5, §18; decision R117):
  - it caches the gap history of the scheduled runs it has seen;
  - it rebuilds that cache after a restart from one `event=schedule` listing of 14 days;
  - it recomputes the bound when a new scheduled run appears.
- No idea of the vision or gap-analysis item lacks a row.
- No difference lacks its reason in section C.

## The rows the changed sections touch

| Change in revision 12 | Rows that cite it | Verdict |
|---|---|---|
| §3.5: the bound from a cached gap history, rebuilt after a restart from one listing, recomputed when a new scheduled run appears | A9 and B.1 row 5 (the dispatcher's duties, host open, O12); B.2 3.3 | honest. The check stays a dispatcher duty and inherits those rows' named rest (O12); it needs no new credential |
| the same, as machine-local state | A21 ("context in the tracker and git", P1) | honest. The cache is rebuilt from the forge's run listing, so it is a cache in principle P1's sense, never the source of truth |
| §3.5: "each poll then costs one short request against the operator's shared hourly limit" | B.1 row 16 and B.2 3.6 (measurement); §15.2's write budget, which no row cites | honest. The listing is a read; the rows' claims about the records and the digest are unaffected |
| §18 Delivery row: "ran within its bound (from a cached history of its scheduled runs)" | B.3 rank 9 and B.2 3.7; C1 | honest. Nothing about the bound is an operator step, so C1's "no human-only gates" is unaffected |

Rows not touched by revision 12 keep the verdicts of rounds 7 to 11.

## New findings

None.
