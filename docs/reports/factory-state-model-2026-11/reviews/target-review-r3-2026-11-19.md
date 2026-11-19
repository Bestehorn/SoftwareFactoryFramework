# Target review, round 3: revision 3 of the factory state model against the keynote and the gap analysis (2026-11-19)

Reviewed: branch `docs-factory-state-model-design` at `5dcc08f`, read from a detached worktree:

- design.md, traceability.md, decisions.md (R34–R56), review-response.md Part 1 and README.md;
- the diff from `cec3492` for decisions.md and README.md.

Targets: the keynote deck (30 slides, text and speaker notes, extracted again in presentation order) and the gap
analysis of 2026-11-09. Both are untracked in the main checkout; neither was copied. Framing: decision U22 (the keynote
is a vision). My round-2 report is committed as
`docs/reports/factory-state-model-2026-11/reviews/target-review-r2-2026-11-16.md`. Finding shape:
`clients/common/docs/review-contract.md`.

## Summary

**Verdicts on my 20 round-2 items** (T-09, T-13, T-15, T-16, tN1–tN14, and the 2 status rows A10 and row 8):
20 verified, 0 partly, 0 not fixed, 0 disputed.

**New findings:** 1 B, 1 C, 2 D (M1–M4).

**Overall verdict: revision 3 closes every item I raised. Traceability is now honest row by row.**

- Every vision idea of the keynote has a row.
- Every gap-analysis row, section, rank and keep item is traced.
- Every difference has its reason in section C.

What is left is small:

- **M1 (B):** trust rule 5 is still stated as an absolute, but the design's own sessions break it. Teams that create
  temporary AWS resources read issue text, and the close-out reads log excerpts through the lane's findings. Only the
  close-out's deletions are scoped. The residual partly comes from my own tN1 proposal.
- **M2 (C):** A28 overstates: a docs check limited to the diff would not have caught the demo's stale URL.
- **M3 and M4 (D):** one unnamed confirmer and one role count.

OPEN ITEMS: 4

## Part 1: verdicts on my round-2 items

| Item | Verdict | Evidence in revision 3 |
|---|---|---|
| T-09 | verified | §6.1 inflow 3 and §14 pull order step 1 pull "a START issue authored by a factory login with `Origin: production`" first, before triage. The author check is there because provenance lines can be typed by anyone (§6.3) |
| T-13 | verified | §7.2 CLOSE-READY: a separately started, read-only log-scan lane; §11 item 2; row 6 and A6 name the rest |
| T-15 | verified | §3.5: TEST-READY → CLOSE-READY is "always called by the steward", which under `verification: none` applies it at its next tick; the Steward row of §4.5 names both cases |
| T-16 | verified | A27, "Checking is not the same as proving": partly aligned, rest named (mutation only for L and risk tags; no proof beyond tests) |
| tN1 | verified | §11 item 1: the close-out "reads no logs" and "may delete only resources carrying its issue's tag"; §15.1 rule 5 now says "deploy or deletion credentials". This is my recommended option, implemented as written. Its remaining gap is new finding M1 |
| tN2 | verified | A8: "aligned on coordinating through the backlog; differs on the claim medium (C12)"; C12 gives the reason and cites §5.6 |
| tN3 | verified | §13 spend line with `model=`, `writes=`, `step-seconds=`; §4.5: "Every role that runs an agent context may append spend lines"; §17 "per model (the spend lines' `model=`)" |
| tN4 | verified | §13 Calibration: only the cost, bounce and claim counters are report-only, and the review caps "stay enforced throughout"; B.4; A13's rest names it; §2 and §18 agree |
| tN5 | verified | A4: "the crew ring is partly aligned (O12)"; A14 no longer claims governance inheritance as designed and names O12 in its rest |
| tN6 | verified | A9's rest: "an empty backlog starts no search"; §19 item 12: "a search that runs when the backlog is empty" |
| tN7 | verified | §7.2 IMPLEMENTATION-READY: docs-drift tools and the docs-drift checker; A28. A28's status: M2 |
| tN8 | verified | §7.2 TEST-READY: pen-test findings "do not hold a release"; C10's source, design and reason cover it; A10 and row 9 cite C10 |
| tN9 | verified | §12.10 "Limit under U24"; R56; rows 15, 3.5 and A19 name it; §12.3 item 3 lists which forge gates exist under one account |
| tN10 | verified | §4.2: "environment" is confirmed by the steward's infra classifier or the attributor; the issue stays in REWORK-REQUIRED, `blocked-by` the incident, and the failing check is re-run when the incident closes |
| tN11 | verified | §14 (in bold), §16, the §18 Scheduling and Gates rows, and B.4 all make the A2 reversal and the supersession of `check-handoff` conditional on the dispatcher's host |
| tN12 | verified | A23: "aligned on reach; differs on the means (C8)"; C8 restated |
| tN13 | verified | A21 names P1 and P9 (slides 29 and 30); A25's rest names messaging |
| tN14 | verified | §3.6: "The claim (§5) is a git ref and works unchanged"; 3.8 restated |
| A10 (status) | verified | the design element now says "pulled before triage when a factory login filed it" |
| Row 8 (status) | verified | the same wording, with §6.1 and §14 cited |

## Part 2: traceability.md, row by row

I checked every row against design.md and both targets. Statuses that are honest as written:

- **Section A:** A2–A27 except A28, and A1 apart from the wording in M3.
- **B.1:** rows 1–16.
- **B.2:** 3.1–3.8, apart from the count in M4 (3.4).
- **B.3:** ranks 1–12.
- **B.4:** all six keep items.
- **Section C:** C1–C12.

Vision ideas without a row: none that is a loop or a control. These have no row, and I raise no finding on them:

- slide 13's passing mention of `/loop`;
- slide 16's parallel fan-out mechanics, which §8.4 has;
- the context slides 17, 25 and 26.

Gap-analysis items without a row: none. Every §1 row, §2 sub-gap, §3 section, §5 rank and §6 keep item is traced.

Differences without a reason in section C: none.

## Part 3: new findings

### M1 — Trust rule 5 is still absolute, but sessions in the design hold AWS write credentials while reading untrusted text
Severity: B
Location: design.md §15.1 rule 5; §11 item 1 ("Deletion credentials and untrusted log text never meet in one
session") and item 2; §8.1 (finding evidence); §18 Setup row
Target: gap analysis §2.4 and keynote slide 19 (read the logs, file what you find), the loop that made rule 5
necessary.
Defect: Rule 5 says: "No deploy or deletion credentials in a session that reads untrusted content: logs, issue text,
web pages." The design has sessions that break it:
- **Teams that create temporary AWS resources.** §11 item 1 says "Each team also records" the "test users, staged
  uploads, probe stacks" it creates. Creating them needs AWS write credentials, and every team reads issue text. Only
  the close-out's permissions are scoped: §18 Setup lists "tag-conditioned delete permissions for the close-out", and
  nothing for creation.
- **The close-out itself.** It reads the log-scan lane's finding records "as data" (§11 item 2). A finding carries
  "evidence (command, exit code, excerpt, commit)" (§8.1), so log excerpts do reach the session that deletes.
  It also reads the issue's own text (the ledger, the laundry list).

So §11's sentence "never meet in one session" is not accurate. What actually bounds the close-out is its tag-scoped
role. The bound is the one I proposed in tN1, and my proposal did not cover the excerpts either.
Material-because: security. The design's own rule is contradicted by the design's own sessions, and the teams that
create resources have no scope at all.
Proposed-edit:
- (Recommended) Restate rule 5 as a bound: "A session that reads untrusted content (logs, issue text, web pages,
  finding excerpts) holds AWS write credentials only when they are tag-conditioned to its own issue's temporary
  resources (`factory-issue=<repo>#<n>`)."
- In the §18 Setup row, extend "tag-conditioned delete permissions for the close-out" to "tag-conditioned create and
  delete permissions for every team that makes temporary resources".
- In §11 item 1, replace "never meet in one session" with "meet only under credentials scoped to the issue's own
  tagged resources".
- Alternative: let only a non-reading provisioning step create temporary AWS resources, never an agent session.

### M2 — A28 says "aligned", but a diff-scoped docs check would not find the demo's stale URL
Severity: C
Location: traceability.md A28; design.md §7.2 IMPLEMENTATION-READY ("when the change touches a documented interface")
Target: keynote slide 16, notes: the documentation was checked "line by line against the source", and a URL from an
old version was found.
Defect: The demo's catch was drift that already existed. The design's docs-drift checker runs only when a change
touches a documented interface, so it finds drift a change introduces, not drift in untouched documentation. §19 item
12 already records that no search runs on its own ("a search that runs when the backlog is empty").
Proposed-edit: Set A28 to "partly aligned. Rest: drift in documentation no change touches is found only when a change
touches it (§19 item 12)."

### M3 — The rework class "requirement" has no named confirmer
Severity: D
Location: design.md §4.2 "REWORK-REQUIRED → any exit"; traceability.md A1 ("each confirmed by a checker other than
the maker")
Defect: §4.2 names the confirmer for "code" (the test-architect) and for "environment" (the infra classifier or the
attributor), but none for "requirement". In effect the spec checkers confirm it when they re-approve the amended
criteria: the IMPLEMENTATION-READY → TEST-READY predicate needs a newer `spec-approved` for changed acceptance tests,
and only SPEC-REQUIRED → IMPLEMENTATION-READY writes one. The text does not say so.
Proposed-edit: Add to §4.2: "a 'requirement' cause is confirmed by the spec checkers when they re-approve the amended
criteria (tier S: the in-session combined pass, §8.5)".

### M4 — The new-role count does not match the list
Severity: D
Location: design.md §16 ("about 15 agent roles", "about 75 %"); traceability.md 3.4 ("about 15 new roles")
Defect: §16 lists 16 roles (counted). One of them, the docs-drift checker, is "the checker half of
`doc-reviewer-agent`" (§7.2), so it is also counted in "the split of two agents into maker and checker".
Proposed-edit: Drop the docs-drift checker from the list, since the split covers it, and keep "15 new roles". Or say
"16" and "80 %" (16 of 20 agents).
