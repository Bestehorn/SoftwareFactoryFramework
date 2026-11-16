# Target review, revision 2: the factory state model against the keynote and the gap analysis (2026-11-16)

Reviewed: branch `docs-factory-state-model-design` at `cec3492`, read from a detached worktree:

- design.md, decisions.md, traceability.md, review-response.md and README.md;
- the appendices where a row depends on them (README: "Where they differ from design.md, design.md wins").

Targets: the keynote deck (30 slides, text and speaker notes, extracted again in presentation order) and the gap
analysis of 2026-11-09. Both are untracked in the main checkout; neither was copied. Framing: decision U22. The keynote
is a vision, so a difference with a stated reason is not a defect, but a status must still be accurate. Finding shape:
`clients/common/docs/review-contract.md`. Previous report:
`docs/reports/factory-state-model-2026-11/reviews/target-review-2026-11-11.md`.

## Summary

**Verdicts on my 23 findings:** 19 verified, 4 partly (T-09, T-13, T-15, T-16), 0 not fixed, 0 disputed.

**My 34 corrected statuses:** 32 verified, 2 partly (A10 and row 8, both through T-09). All the rows I proposed adding
exist.

**New findings:** 1 B, 10 C, 3 D (N1–N14).

**Overall verdict: the design aligns well with the keynote's vision, and covers the gap analysis completely.**

- **Alignment.** Every central idea of the keynote has a mechanism:
  - loops inside loops, and a provable finish line per loop;
  - maker ≠ checker, now per agent context;
  - the guardrails, and drift against the spec;
  - the empty backlog, and agents that name what they did not verify.

  The differences are deliberate and reasoned (C1–C11). There is one exception: claims are git refs, not the
  keynote's comment, and section C has no row for it (N2).
- **Coverage.** Every gap-analysis row, section and recommended rank has a row. The keep-list now has a row too
  (B.4). Each item is designed, partial with the rest named, a deviation with a reason, or not designed and listed in
  §19.
- **Honesty of statuses.** Much improved. The remaining overstatements cluster in two places:
  - the dispatcher's open host (O12): A4 and A14 (N5);
  - the cost source: the spend line has no model, and the lanes have no right to write spend lines (N3, N4).
- **Monday promises** (brief question 3):
  - **The proof loop holds.** The transition now waits for green CI and the verifier, and the worker does not wait
    (T-10, verified).
  - **The feedback loop** differs by recorded reason (C2). The triage rule no longer refuses the keynote's own
    issues (T-05).
  - **The backlog loop** is partly aligned with an honest rest. N11 flags a sequencing risk to today's strong
    in-run loop.
  - **The keynote's tip to coordinate through comments** is the one difference the design makes without a recorded
    reason (N2).
- **The one new B (N1)** comes from the T-13 fix. The deploy-window log scan was put into the close-out worker, which
  also deletes AWS resources. The design's own trust rule 5 forbids that combination.

## Part 1: verdicts on the findings of 2026-11-11

| Id | Verdict | Evidence in revision 2, and what is left |
|---|---|---|
| T-01 | verified | §4.2 "REWORK-REQUIRED → any exit" needs a rework-analysis record, and the test-architect confirms a "code" cause; A1 and row 10 are partly aligned / partial with the rest named. New: the "environment" class has no checker and no exit (N10) |
| T-02 | verified | §13 "Where the counts come from": a spend line at each checkpoint and release, summed per issue; A13 and 3.1 (a) corrected. Completeness gaps: N3, N4 |
| T-03 | verified | A2, A9, rows 3, 5 and 14, and 3.3 are partial (O12); §14 "Host and worker start are open"; O12 names worker start and governance. Two rows still overstate: N5 |
| T-04 | verified | §7.2: the external PR review is the `external_security_review` setting, and a batched pen test sits in TEST-READY; C10; row 9 names the system threat model as the rest. New difference: N8 |
| T-05 | verified | §6.5 is restated as proposed, and A6 cites it |
| T-06 | verified | §8.1 `verdict` has a REQUIRED `notVerified`; §7.4; §11 item 4; the laundry list in §4.2. The appendix schema in review-protocol.md still lacks the field, but README makes design.md win |
| T-07 | verified | §12.10 adds sensitive PR paths to IMPLEMENTATION → TEST and REWORK → TEST; row 15 and 3.5 now agree. Under U24 the approval's authorship is not provable: N9 |
| T-08 | verified | row 2 partial; §19 item 4; O15 |
| T-09 | **partly** | See below |
| T-10 | verified (superseded) | See below |
| T-11 | verified | B.4; §16 "The stop gates must change"; §18 Gates row; A11 aligned now that the change is designed. Sequencing: N11 |
| T-12 | verified | §11 item 3: "never to machine-local memory"; A7 and row 7 name 2.5 (a)–(d) |
| T-13 | **partly** | See below |
| T-14 | verified | §16 lists 14 roles (counted) and makes the renderer a precondition; 3.4 names the growth |
| T-15 | **partly** | See below |
| T-16 | **partly** | See below |
| T-17 | verified | A23–A26, C8, C9 and C11 exist; A14, A17 and A25 name sandboxing and O11. A14 overstates inheritance: N5 |
| T-18 | verified | A19 and A20 are partly aligned; C1's reason covers questions and mob rituals |
| T-19 | verified | §6.4: a deterministic floor, raise only, re-derived at SPEC exit; the triage checker for M and L (§4.2) |
| T-20 | verified | Playwright in §9, the pen test in §7.2, the stop gates in §16 |
| T-21 | verified | §3.6, 3.8. One wording slip: N14 |
| T-22 | verified | C3 names Kiro's `/goal` and the human's use of it; C4 adds the "cannot run locally" reason |
| T-23 | verified | C2 cites slides 7, 8 and 19 and says "fix it in the open" |

**T-09 (partly).**

- **What was fixed.** §14 now pulls `priority:critical` first, whatever the stage.
- **What is left.** Only triage sets that label (§6.1: "Triage gives it `priority:critical`"; §3.2: set by "an
  authorised human; triage for production incidents"). A fresh incident has no label yet and sits in START, which §14
  still pulls last. So it waits behind all in-flight work until a triage worker reaches it. The delay T-09 named has
  moved from after triage to before it.
- **Proposed edit.**
  - (Recommended) In §14, pull order step 1, add: "or a START issue whose AUTHOR is the factory login and which
    carries `Origin: production`". The author check is needed because provenance lines can be typed by anyone (§6.3).
  - Alternatively, let `issue-intake-agent` set `priority:critical` at filing, as a provisional value that triage may
    lower.

**T-10 (verified, superseded).**

- **What the predicate now requires.** §4.2 IMPLEMENTATION-READY → TEST-READY requires "PR CI green on head H" and the
  adversarial verifier's report on H. While CI runs, the worker sets `ci-pending` and releases. The verifier lane
  (§14 queue "verifier": "`ci-pending` and the PR's CI run has ended") completes or refuses the transition.
- **Conclusion.** The task's finish line ("done when CI is green") is checked before TEST-READY, and no worker waits
  (P2). No deviation is left to record.
- **The remaining exception is safe.** It is `--allow-pending`, only for a re-enqueue after a rebase that changes no
  file. There the steward's `require_pr_ci: True` still enforces green.

**T-13 (partly).**

- **What was fixed.** The deploy-window log scan exists (§11 item 2; §7.2 CLOSE-READY row), and row 6 and A6 name the
  rest.
- **What is left.** It was placed in the close-out worker, which also removes AWS resources. That conflicts with §15.1
  rule 5; see N1.

**T-15 (partly).**

- **What was fixed.** §3.5 maps the delivery modes.
- **What is left.** §4.5 names only the watcher as the caller of TEST-READY → CLOSE-READY. Under `merge: steward` +
  `verification: none` no watcher runs: today the landing itself closes the issue (`clients/common/docs/delivery.md` §3
  step 5, "the landing verified and closed the issue"). The edge therefore has no caller in that mode.
- **Proposed edit.** In §4.5, the Steward row, "May call": add "TEST-READY → CLOSE-READY under `verification: none`".

**T-16 (partly).**

- **What was fixed.** The tier-S minimum path exists (§7.3, A22).
- **What is left.** The second half of T-16 has no row: the notes of slide 23, "checking is not the same as proving",
  and the advice to think about how you would prove that it works.
- **What the design does have.** Several elements align with that idea:
  - the verifier's deliberate break (§7.4);
  - verify-to-disprove (§7.4, the logic-bug lane);
  - mutation testing, for L and risk tags only (§7.2).
- **Proposed edit.** Add row A27: "Checking ≠ proving (23, notes)" → those elements. Status: partly aligned. Rest:
  mutation runs only for L and risk tags, and there is no proof beyond tests.

## Part 2: my corrected status table, row by row

"Further" names a new finding that changes the row again.

| Row | Revision 2 status | Verdict on my correction | Further |
|---|---|---|---|
| A1 | partly aligned, rest named | verified | N10 |
| A5 | aligned (task done = CI green + verifier) | verified (T-10 superseded) | — |
| A6 | partly aligned, rest named | verified | N1 (the design, not the status) |
| A7 | partly aligned, 2.5 (a)–(d) | verified | — |
| A9 | partly aligned (O12) | verified | N6 |
| A10 | partly aligned; differs C10; rest O8, system threat model | **partly**: the expedite works only after triage (T-09) | N8 |
| A11 | aligned | verified | — |
| A13 | partly aligned; rest the Kiro export | verified | N3, N4 |
| A14 | partly aligned; rest O11, sandboxing | verified | N5 |
| A15 | partly aligned; differs C4 | verified | — |
| A16 | aligned | verified | N10 |
| A17 | partly aligned, rest named | verified | — |
| A18 | aligned | verified | N7 (adjacent idea) |
| A19 | partly aligned; rest C1 | verified | N9 |
| A20 | partly aligned; rest §19 item 6 | verified | — |
| A21 | differs (C1 extended) | verified | — |
| Row 2 | partial; rest immutability | verified | — |
| Row 3 | partial; rest O12 | verified | — |
| Row 5 | partial; rest the reaper's host | verified | — |
| Row 6 | partial, rest named | verified | N1 |
| Row 7 | partial, (a)–(d) | verified | — |
| Row 8 | partial; rest O8 | **partly**: "with expedite" holds only after triage (T-09) | — |
| Row 9 | partial, rest named | verified | N8 |
| Row 10 | partial, rest named | verified | — |
| Row 12 | designed | verified | N3, N4 |
| Row 13 | partial (O11) | verified | — |
| Row 14 | partial (O12) | verified | — |
| Row 15 | designed as configurable; default off = C1 | verified | N9 |
| Row 16 | designed | verified | N3 |
| 3.1 | partial; (a) spend lines, (c) not designed | verified | N3 |
| 3.3 | partial (O12) | verified | — |
| 3.4 | partial; about 14 roles | verified | — |
| 3.5 | as row 15 | verified | N9 |
| 3.7 | not designed; steward precondition | verified | — |

Rows I proposed adding:

- my C8 is superseded by T-10;
- B.4 exists (N11);
- A22 exists (T-16 is partly fixed);
- A23–A26, C8, C9 and C11 exist (N12, N13).

## Part 3: new findings

### N1 — The close-out worker reads untrusted logs while holding credentials to delete AWS resources
Severity: B
Location: design.md §11 items 1 and 2; §7.2 CLOSE-READY row; §15.1 rule 5
Target: gap analysis §2.4, "scan the application logs"; keynote slide 19, "read the logs".
Defect: The same role does both jobs that rule 5 keeps apart:
- §11 item 1: it removes "temporary test and verification infrastructure: test users, staged uploads, probe stacks",
  which needs AWS write and delete permissions;
- §11 item 2 and §7.2: it scans "the deploy window's logs".

§15.1 rule 5 says: "No deploy credentials in a session that reads untrusted content: logs, issue text, web pages."
Material-because: security. An instruction injected into a log line reaches a session that can delete AWS resources,
which is the combination the design's own rule forbids.
Proposed-edit:
- (Recommended) Run the deploy-window scan as a read-only CLOSE-READY lane with no AWS write credentials. It emits
  finding records, which the close-out worker reads as data. Scope the close-out's AWS role to deleting resources
  tagged `factory-issue=<repo>#<n>` (tag-conditioned IAM).
- Alternatively, split close-out into a read-only report step and a clean-up step that reads no logs.

### N2 — Claims by git ref differ from the keynote's comment tip, but A8 says "aligned" and section C has no row
Severity: C
Location: traceability.md A8 and section C; design.md §5.1, §5.5
Target: keynote slide 7, notes: a worker "says so in a comment", and the speaker calls that enough to run several
workers in parallel.
Defect: §5.1 makes the claim a server-enforced ref, and a comment only "may mirror the ref for humans". §5.5 explains
why a comment claim is not enough: "Revision 1's comment protocol had the same weaknesses, plus a list endpoint that
may lag right after a create". That is a deliberate difference from an idea an engineer would try on Monday. Under U22
it needs its reason in section C, but A8 calls it "aligned, and stricter".
Proposed-edit:
- Set A8 to: "aligned on coordinating through the backlog; differs on the claim medium (C12)".
- Add C12:
  - Source says: "say so in a comment" (slide 7 notes).
  - The design says: a claim ref with compare-and-swap; a comment only mirrors it.
  - Why: two workers that read before either writes both win a comment claim, worse under one shared account across
    machines (§5.5, [B1]).

### N3 — The spend line cannot give cost per model, and the lanes may not write it
Severity: C
Location: design.md §13 "Where the counts come from", §17 ("cost per issue, per tier and per model"), §4.5 Checker
lane and Answer recorder rows; traceability A13, rows 12 and 16, 3.1
Target: keynote slide 11: "Credits per user and per model"; gap analysis §3.1 (a).
Defect:
- `factory: spend tokens=<n> usd=<x> by <worker>/<agent>` has no model field, so §17's per-model figure has no source.
- §4.5 lets a checker lane write only "finding, verification and verdict records; a verify-kind claim". The headless
  lane, verifier and recorder runs of §14 therefore add no spend line. Those cross-session runs are where §13
  ("Calibration") expects the cold-start cost.
Proposed-edit:
- Make the line `factory: spend model=<id> tokens=<n> usd=<x> by <role>/<agent>`.
- In §4.5, let every role that runs an agent context append spend lines.

### N4 — "All budgets are report-only" also suspends today's review caps
Severity: C
Location: design.md §13 "Calibration" ("For the first 20 issues per tier, all budgets are report-only") and the
table's first two rows; §7.3; traceability B.4 ("Proportionality … kept"), A13
Target: gap analysis §6 keeps "Proportionality with hard byte caps"; keynote slide 11: "Every unattended loop gets a
budget".
Defect:
- The §13 table includes "S spec review: 2 → approve with residuals" and "M / L design review: 4 / 6", which are
  today's enforced caps. Read literally, calibration suspends them, which contradicts B.4 and §7.3 ("as
  `proportionality.md` says today").
- While calibration runs, no unattended loop has an enforced cost budget, and A13 does not name that.
Proposed-edit:
- Restrict report-only to the counters calibrated from thresholds.md (cost, bounces, claims); today's review caps stay
  enforced.
- Add to A13's rest: "cost budgets are report-only for the first 20 issues per tier".

### N5 — Two rows still count on the dispatcher's open host
Severity: C
Location: traceability.md A4, A14; design.md §14 ("Host and worker start are open"); decisions.md O12
Defect:
- A4 says "otherwise aligned" for the crew ring, which is the dispatcher, while A2, A9 and A17 call the same thing
  partly aligned (O12).
- A14 lists "dispatcher-started workers inherit an interactive session's rules (§14)" as a design element. §14 itself
  says the design "still needs … the governance it inherits", which O12 lists as open.
Proposed-edit:
- A4: "differs on `/goal` (C3); the crew ring partly aligned (O12)".
- A14: delete the inheritance clause from the design element, and add "governance of dispatcher-started workers (O12)"
  to its rest.

### N6 — "An empty backlog only means something if somebody is still looking" has no row
Severity: C
Location: traceability.md A9; design.md §14 (queues), §6.1, §11 item 2
Target: keynote slide 9, notes: otherwise, the speaker says, "it just means that nobody looked".
Defect: Every search in the design is triggered by an event:
- the deploy-window scan, only where a log query exists (§11);
- production alarms (§6.1);
- an optional pen test (§7.2).

When every queue is empty, §14 starts no role. So an empty backlog starts no search. A6's rest ("no scheduled scan")
and row 11 (backlog drift, not designed) touch this, but A9 does not name it.
Proposed-edit: Add to A9's rest: "an empty backlog starts no search: no scheduled log scan (A6), no drift measurement
(row 11)".

### N7 — The demo's documentation-drift check has no stage and no row
Severity: C
Location: design.md §7.2 (no documentation checker in any stage), §11 item 3; traceability A18
Target: keynote slide 16, notes: the documentation was checked "line by line against the source"; slide 27: no drift,
and a stale URL caught.
Defect:
- No stage runs a docs-against-code checker. `doc-reviewer-agent` appears only as an agent "split when implemented"
  (§7.2, §18). The appendix's docs-drift tools (checker-landscape.md §3.4 item 14) are not adopted.
- Documentation changes reach the repository only through the learning-batch issue, after landing (§11 item 3).
- A18 covers only `notVerified`.
Proposed-edit: Add the docs-drift checker (doc-reviewer's checker half, with lychee and markdownlint) to the
IMPLEMENTATION-READY row for changes that touch documented interfaces. Trace it in a new row, or in A18.

### N8 — Pen-test findings become new issues, not a pre-release check; the difference has no reason
Severity: C
Location: design.md §7.2 TEST-READY row ("its findings enter START as issues"), §12.6; traceability A10, C10
Target: keynote slide 9, notes: before the release, the same agent can run a penetration test.
Defect: The pen test runs weekly or per batch, and its findings never hold a release or return the culprit. Its
relation to the production deploy, which §12.6 makes a standing permission, is not stated. A10 lists the pen test as
an aligned element, and C10 covers only "every PR".
Proposed-edit: Extend C10: "the pen test is batched; its findings enter START (exploitable ones as `priority:critical`)
and do not hold a release. Why: billed per task-hour and batched across PRs, so no culprit is known."

### N9 — Under the shared account, an approval's human authorship is not provable
Severity: C
Location: design.md §12.10, §12.3 item 3, §15.2 "The accepted residual"; traceability row 15, 3.5, A19
Target: gap analysis §3.5: banks expect a human to validate before construction; keynote slide 18, notes: the
evidence must be something an auditor can read.
Defect: The approval is a comment from an authorised human. Under U24 the agents post as the same login, and §15.2
says "The decision itself could still be forged". The approval setting exists for exactly the bank case, which A19
leans on, but row 15, 3.5 and A19 do not name the limit.
Proposed-edit:
- Name it in row 15, 3.5 and A19: "under U24 the approval's human authorship is not provable (§19 item 3)".
- Option: when a project switches approval on, bind it to a forge mechanism tied to the human's own credentials, as
  §12.3 item 3 already does for irreversible operations.

### N10 — The rework class "environment" has no checker and no exit
Severity: C
Location: design.md §4.2 "REWORK-REQUIRED → any exit" ("an environment cause is an `env-incident` (§12.5), not
rework"); traceability A1, A16 ("the checked rework classification")
Defect:
- Only a "code" classification is confirmed by a checker. "Environment" is the maker's own call.
- No exit is named for it: the issue's stage after the `env-incident` opens is unstated.
- So a maker can move its own culprit out of rework by declaring the cause environmental, which is the self-grading A16
  calls closed.
Proposed-edit: Have the steward's infra classifier (§10.4 step 1) or the failure attributor confirm an "environment"
class. The issue then stays in REWORK-REQUIRED, `blocked-by` the incident, and re-runs the failing check when the
incident closes; §13's refund applies.

### N11 — A2 is reversed unconditionally, while the dispatcher that makes it safe has no host
Severity: C
Location: design.md §14 introduction, §18 Scheduling row ("decision A2 reversed"); traceability B.4 row 2; O12
Target: gap analysis §6 keeps `check-handoff` and the SESSION verdict gate; gap analysis row 3: "Strong (inside a run)".
Defect: §14 says "The dispatcher is what lets this design reverse A2". §18 and B.4 nevertheless state the reversal and
the supersession of `check-handoff` without that condition. If they are implemented before O12 is decided, hand-offs
strand as measured (0 of 10 closed), and today's strong in-run backlog loop regresses.
Proposed-edit: Add to §18 Scheduling and B.4: "A2 is reversed, and `check-handoff` superseded, only once the dispatcher
runs on a host (O12). Until then a session keeps its PR until it lands."

### N12 — A23 understates: the loop reaches tracker, CI and logs, only not by MCP
Severity: D
Location: traceability.md A23
Defect: The keynote's idea is reach. The design reaches the tracker (the wrappers), CI (the forge run API) and logs
(CloudWatch, read-only, §7.2, §11). Only the means differ.
Proposed-edit: A23: "aligned on reach; differs on the means (C8)".

### N13 — Ideas of the vision that align, or are absent, have no row
Severity: D
Location: traceability.md A21, A25
Defect:
- Slide 29 ("Context persists in the repo") matches P1, and slide 30 ("Server enforces phase gates") matches P9 and the
  transition verb. Neither is traced.
- Slide 15's "messaging" is absent: the human is reached only by pull (the digest, `/get-guidance`).
Proposed-edit: Name P1 and P9 in A21. Add messaging to A25's rest, or to section C with the reason (no push channel;
§17 digest).

### N14 — The claim needs no Jira equivalent
Severity: D
Location: design.md §3.6; traceability 3.8
Defect: §3.6 says "The claim (§5) and the records (§8) use git refs and forge comments, so a Jira backend needs its own
equivalents". The claim ref lives in the git repository and is independent of the tracker. Only the records, the cursor
and the stage store need Jira equivalents.
Proposed-edit: "The records (§8) use forge comments and need Jira equivalents; the claim (§5) is a git ref and works
unchanged."

## Part 4: the revised traceability.md, row by row

- **Statuses that still overstate:**
  - A4, A14 (N5);
  - A8 (N2);
  - A10 and row 8 (T-09; N8);
  - A13, row 12 and row 16 (N3, N4);
  - A16 (N10);
  - row 15, 3.5 and A19 (N9).
- **Statuses that understate:** A23 (N12).
- **Ideas of the vision with no row:**
  - checking ≠ proving (T-16);
  - "nobody looked" (N6);
  - documentation drift (N7);
  - slides 29 and 30 (N13).
- **Differences with no section C reason:** the claim medium (N2), the pen test as a non-gate (N8).
- **Gap-analysis items with no row:** none. Every §1 row, every §2 sub-gap, every §3 section, every §5 rank and every
  §6 keep item is traced.

Accepted as written: A2, A3, A5, A6, A7, A9 (except N6), A11, A12, A15, A17, A18, A20, A21, A22, A24, A25 (except
N13), A26; rows 1–7, 9–11, 13 and 14; 3.1–3.4 and 3.6–3.8; B.3; B.4 (except N11); C1–C11. Slides 17, 25 and 26 are
context and need no row.
