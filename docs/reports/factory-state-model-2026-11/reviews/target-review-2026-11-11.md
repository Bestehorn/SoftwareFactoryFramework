# Target review: the factory state model against the keynote and the gap analysis (2026-11-11)

Reviewed: branch `docs-factory-state-model-design` at `11073fe` (design.md, traceability.md, decisions.md, README.md,
appendices cited where a row depends on them), read from a detached worktree. Targets: the keynote deck (all 30
slides, text and speaker notes, extracted in presentation order) and the gap analysis of 2026-11-09, both untracked
in the main checkout and not copied anywhere. Brief: README.md "2. Review against the target". Finding shape:
`clients/common/docs/review-contract.md`, plus a Target line (quote, document, section) and an Evidence line.

## Summary

**Verdict: the design covers the keynote's inner loops and most controls, but traceability.md overstates it.**
8 B, 12 C and 3 D findings, no A. 34 rows are disputed (corrected table at the end), and 9 rows are proposed as
additions.

1. **Is every loop and control of the keynote covered?** Mostly. The task, issue and backlog loops, the
   guardrails, drift and maker ≠ checker all have mechanisms. Three things are missing or contradicted:
   - the demo's control (an agent that says what it did NOT verify): the `verdict` record schema has no field for it
     (T-06);
   - the Security Agent on every pull request and the pen test (T-04);
   - an enforceable cost budget, because no record carries the cost (T-02).

   Elements of slides 10, 15, 16, 23 and 24 have no row at all (T-16, T-17).
2. **Is every gap-analysis row closed, partly closed with the rest named, or deviated from with a reason?** No.
   - Ten rows are marked designed although an enabling part is open or absent: rows 2, 3, 5, 9, 10, 12, 14 and 16,
     and sections 3.3 and 3.5.
   - Three partial rows name no remainder (rows 6 and 13, and A17), and row 7 names only part of it.
   - The gap analysis §6 keep-list is not traced, and the design reverses part of it (T-11).
3. **Does the design contradict anything the keynote promises an engineer could try on Monday?**
   - The feedback loop ("file an issue for everything you find") is contradicted twice. The first is deliberate and
     reasoned (C2). The second is not recorded: the §6 triage rule, as written, refuses an ask "that originates in
     quoted untrusted text", which is the keynote's own issue 43 and issue 44 (T-05).
   - The proof loop and the backlog loop are not contradicted. The worker may hand over before CI is green, but the
     steward still enforces green, and this is not recorded (T-10).
   - "Every correction you make twice goes into a steering file" is weakened by machine-local writes (T-12).
4. **Are the statuses honest?** Not consistently. The recurring pattern: "designed" is used where the mechanism
   depends on an open decision (the dispatcher host, O12) or on something no record provides (cost). It is also used
   where the status text itself says a part is missing ("designed; a living system spec is not"). Some rows also cite
   design elements that design.md does not contain: Playwright MCP, the pen test, the stop gates (T-20).

## Findings

### T-01 — The return path to the spec is skippable; the production half is not designed
Severity: B
Location: design.md §4.2 (REWORK-REQUIRED rows); traceability.md A1, B.1 row 10, B.3 rank 6
Target: keynote slide 2, notes (click 3): "you do not just patch the code. You go back, you fix the spec"; gap
analysis §2.8: "Nothing asks whether the requirement itself was wrong".
Defect: The code-or-requirement classification is required only on the edges REWORK-REQUIRED → IMPLEMENTATION-READY
and → SPEC-REQUIRED. The direct edge REWORK-REQUIRED → TEST-READY needs only "a resolution record answering the
rework cause", so the most common rework path never asks the question.
Evidence:
- design.md §4.2: the REWORK → TEST-READY predicate contains no rework-analysis record.
- design.md §4.3: "After TEST-READY ... a change of mind becomes a new issue". The slide's "production shows that
  the design does not hold" case therefore arrives at START as a new issue, with no link back to the landed spec.
- No checker judges the classification (§7.2, REWORK-REQUIRED row: "only the lanes with open findings").
- Row 10's own status says the living system spec is not designed.
Material-because: gap analysis §2.8 and keynote slide 2 are not met, yet A1 says designed.
Proposed-edit:
- (Recommended) In §4.2, make the rework-analysis record a clause of EVERY exit from REWORK-REQUIRED, including
  → TEST-READY, and give it a checker (the test-architect confirms a "code" cause).
- Then set A1 and row 10 to partial, naming the rest: the production-incident path to the landed spec, and the
  living system spec.

### T-02 — Cost budgets have no measurement source
Severity: B
Location: design.md §13 (row "Cost per issue"), §17; traceability.md A13, rows 12 and 16, B.2 3.1, B.3 rank 1
Target: keynote slide 11: "Credits per user and per model, every day ... Every unattended loop gets a budget"; gap
analysis §3.1 (a): "Record tokens and wall time per run and per issue".
Defect: §13 sets USD limits per issue. §17 claims "cost per issue" from transition, claim, review, question and revert
records, but none of them carries tokens or cost.
Evidence:
- thresholds.md M7 priced cost offline: "Cost and tokens per issue, transcripts".
- It also warns that "The harness's cost record is cumulative and is not always written at the end of a session".
- With workers on several machines, no transcript holds one issue's whole cost.
Material-because: wrong-behaviour. The hard cost limit can never trip, so the budget does not limit anything. This is
the gap analysis's rank 1.
Proposed-edit:
- (Recommended) Add a machine line per claim release and checkpoint (`factory: spend tokens=<n> usd=<x> by <worker>`)
  to §5 and §17, summed by the transition verb for §13.
- Otherwise set A13, row 12 and row 16 to partial. In 3.1, mark (a) not designed (today it reads "(a) §17").

### T-03 — "Who starts the loops" is marked designed while the dispatcher's host is open
Severity: B
Location: design.md §14 ("Hosts"), §5.2; decisions.md O12; traceability.md A9, A17, rows 3, 5 and 14, B.2 3.3
Target: keynote slide 14, notes: "who runs them while you are in meetings, or asleep"; gap analysis §3.3: "Worker
sessions are always interactive sessions an operator opened".
Defect: The dispatcher is the answer to rows 3, 5, 14 and section 3.3, and it also hosts the lease reaper. But its host
is open (O12), and §14 does not design how it starts a Claude Code or Kiro worker ("the ability to start a worker").
Evidence:
- Section 3.3 says "designed" with no host caveat, and row 5 says "designed" although the reaper that replaces the
  watchdog runs inside that same unhosted dispatcher (§5.2: "A reaper (part of the dispatcher, §14)").
- Rows 3 and 14 say "designed (host open)", which per the status definitions is partial.
Material-because: gap analysis §3.3 and row 14 are not met until something runs the dispatcher.
Proposed-edit:
- (Recommended) Set rows 3, 5 and 14, section 3.3 and A9 to "partial: host and worker start not designed (O12)".
- Add the worker-start command per client to O12.
- Alternatively, decide O12 before review closes.

### T-04 — Security beyond the diff is overstated; the pen test is not in the design
Severity: B
Location: design.md §7.2 (SPEC-REQUIRED, IMPLEMENTATION-READY and TEST-READY rows), §7.3; traceability.md A10, row 9,
B.3 rank 5
Target: keynote slide 9: "Reviews every pull request against your security rules" and, in the notes, "run a
penetration test against the running application"; gap analysis §2.7 (b) "Nothing tests the deployed application"
and (c) "No system-level threat model".
Defect: Row 9 says "designed (pen testing optional)", but design.md contains no pen test. The AWS Security Agent
appears only as an optional SPEC design review for "L + auth/money", not at the PR. The threat model is per change.
Evidence:
- A grep of design.md for pen test or DAST finds nothing.
- The appendix does have a pen test: checker-landscape.md §3.2 ("auth/money: pen test (batched)") and §3.4 item 12.
- mcp-and-powers.md proposes a "Security Agent diff scan" pilot for auth/money.
- design.md §7.3 limits external agents to "optional, L or risk tags only". That deviates from "every pull request",
  and section C does not record it.
Material-because: gap analysis §2.7 (b) and (c) and keynote slide 9 are not met, yet row 9 says designed.
Proposed-edit:
- (Recommended) Add the batched, budget-capped pen test (TEST-READY) and the Security Agent diff scan
  (IMPLEMENTATION-READY) to §7.2, as the appendix says.
- Add a section C row: external security review not on every PR, reason cost (§7.3).
- Set row 9 and A10 to partial, naming §2.7 (c), the system threat model.

### T-05 — The triage rule can refuse the keynote's own feedback-loop issues
Severity: B
Location: design.md §6 ("Untrusted content inside admitted issues"); traceability.md A6, A10, section C (no row)
Target: keynote slide 7, notes: issue 43 is filed "with the log lines attached"; slide 9, notes: the DevOps Agent's
fix plan "becomes issue 44"; slide 19: "Run your code, read the logs, and file an issue".
Defect: §6 says "The triage checker refuses an ask that originates in quoted untrusted text, because the keynote's
feedback loop of filing issues from logs is exactly such a path". Read literally, issue 43 is refused: its ask is
derived from log lines. Issue 44 is refused too: its ask comes from an external agent's analysis of metrics.
Evidence: §6 does not say how a checker tells an ask TAKEN from text (an imperative inside a log line) from an
agent's own defect statement that cites log lines as evidence. Traceability lists no deviation for this.
Material-because: keynote slide 19's feedback loop is contradicted without a recorded reason. Security is the failure
class the rule protects, so the fix must keep it.
Proposed-edit:
- (Recommended) Restate the rule: "refuses an ask whose instruction is taken from quoted text (an imperative,
  request or command inside a log line, page, error message or external report). An agent's own defect statement
  that cites fenced log lines as evidence is admitted."
- Add to A6 that issues 43 and 44 pass triage under this rule.

### T-06 — The verdict record cannot carry what a lane did not verify
Severity: B
Location: review-protocol.md, the `factory-review/v1` schema, `verdict`; design.md §8.1, §7.4; traceability.md A18
Target: keynote slide 16, notes: "an agent that tells you what it did not verify"; slide 27: "'tests pass' ≠ 'app
verified'".
Defect: The `verdict` definition is `"additionalProperties": false` with lane, verdict, counts and a `coverage`
string described as "test-architect only". No other lane can report its blind spots. "Named, not run" (§7.4) covers
skipped tests only.
Evidence: the demo's finding was routes, auth, middleware and DB at zero coverage, which is whole-system coverage.
Diff coverage on changed lines (§7.2) would not report it.
Material-because: the keynote control is contradicted by the schema, yet A18 says designed.
Proposed-edit:
- (Recommended) Add a required `notVerified: [{scope, reason}]` (may be empty) to every `verdict`, and list it in the
  close-out summary (§11 item 4).
- Set A18 to partial until then.

### T-07 — Approval for sensitive paths has no PR-level predicate; rows 15 and 3.5 disagree
Severity: B
Location: design.md §12.8, §4.2 (IMPLEMENTATION-READY → TEST-READY); traceability.md row 15, B.2 3.5, B.3 rank 7
Target: gap analysis §3.5 proposal: `"pr_paths": ["iam/**", "auth/**"]`; keynote slide 18: "In a bank, autonomy is
a security question first".
Defect: §12.8 promises approval "for M/L specs or sensitive paths", but the only approval clause is on SPEC →
IMPLEMENTATION-READY. A PR that touches `iam/**` without the spec declaring it passes every predicate.
Evidence:
- Today's steward has only an all-or-nothing gate: `merge_steward.py` defaults `require_approval: False`, and
  `eligibility` returns "wait" when the PR is not approved. The design does not mention it.
- Row 15 says "deviation", while 3.5 says "designed by decision U17" for the same gap.
Material-because: the gap analysis §3.5 proposal is not met for PR paths, and the statuses contradict each other.
Proposed-edit:
- (Recommended) Add to the IMPLEMENTATION-READY → TEST-READY and REWORK → TEST-READY predicates: "the approval
  setting, if switched on, is satisfied for the PR's changed paths".
- Set row 15 and 3.5 alike: "designed as configurable (§12.8); default off is deviation C1".

### T-08 — "Single immutable record per issue" is marked designed, but every record is an editable comment
Severity: B
Location: design.md §4.4, §5.1, §8.2; traceability.md B.1 row 2
Target: gap analysis §2.2: "no single, immutable record per issue ... that an auditor can read"; keynote slide 18,
notes: "the evidence has to be something an auditor can read".
Defect: The audit lines and records are issue comments posted by the shared account. That account can edit or delete
them, and the claim protocol itself edits and deletes comments.
Evidence:
- §5.1 step 3: "The loser deletes its comment"; step 4: "extended ... by editing the comment".
- "Never edit" (§8.2) is a convention, not a control.
- The evidence still spans the branch (evidence report), the comments and the CI runs.
Material-because: gap analysis §2.2 (immutability) is not met, yet row 2 says designed.
Proposed-edit:
- (Recommended) Set row 2 to partial: a single readable summary exists (§11 item 4); immutability is not designed.
  Add it to §19.
- Option: put a digest of the folded records in the landing commit, or in a CI attestation.

### T-09 — Priority is subordinate to stage order, and incidents enter at START, which is pulled last
Severity: C
Location: design.md §14 (pull order), §6 inflow 3; traceability.md row 3, row 8, A10
Target: gap analysis §2.3 (b): "no product priority input ... it must follow"; keynote slide 9, notes: the DevOps
Agent "starts investigating the moment the alert fires".
Defect: §14 pulls right to left, "then priority within a queue". An `Origin: production` issue lands at START, the
last queue, so an incident fix waits behind every in-flight issue. Neither row 3 nor row 8 names this.
Proposed-edit:
- (Recommended) Add an expedite rule to §14: a `priority:critical` label, set by triage for production incidents,
  precedes the stage order.
- Or record "priority only within a queue" as a deviation (B11) with its reason.

### T-10 — The implementer may hand over before CI is green; this deviation is not recorded
Severity: C
Location: design.md §4.2 (IMPLEMENTATION-READY → TEST-READY: "PR CI green ... (or pending, see below)"); traceability
A5, section C
Target: keynote slide 7: "Done when CI is green and you can prove X meets the spec"; slide 19, notes: "you are not
done until all tests pass and CI is green".
Defect: `enqueue --allow-pending` lets the worker transition while PR CI runs. Green is then enforced by the steward:
`merge_steward.py` has `require_pr_ci: True`, and `check` accepts a "wait" verdict under `allow_pending`. A red result
returns the issue to REWORK. The finish line holds, but its owner moves from the worker to the steward (P2).
Proposed-edit: Add C8: "Task finish line checked by the steward, not the worker (P2: workers never wait); a red PR CI
returns the issue to REWORK-REQUIRED."

### T-11 — The gap analysis's keep-list is not traced, and the design reverses part of it
Severity: C
Location: traceability.md (no section for gap analysis §6); design.md §14, §18; traceability A11 ("The client stop
gates stay")
Target: gap analysis §6 keeps "check-handoff, the SESSION verdict gate" and the Stop-gate design.
Defect: The design reverses decision A2 (§14), but today's brake refuses a loop's DONE while a queued PR has not
landed. delivery.md §3 says "the session owns its PR until it LANDS"; HANDED_OFF needs `check-handoff` exit 0. A
worker releasing at TEST-READY is refused by these gates, yet §18 lists no change to them, and A11 says they "stay".
The SESSION verdict has no stated successor for headless workers.
Proposed-edit:
- Add section B.4 mapping the gap analysis §6 items.
- Add a §18 row "Stop gates: the release vocabulary accepts a stage transition".
- Set A11 to partial until then.

### T-12 — The learning loop's remainder is named inconsistently, and close-out writes to machine-local memory
Severity: C
Location: design.md §11 item 3; traceability.md A7, row 7, B.3 rank 4
Target: keynote slide 7, notes: "the correction goes into the steering files automatically, so the next run starts
smarter"; gap analysis §2.5 (a) to (d).
Defect:
- Row 7 names only "no correction hook". A7 also names recurrence counting. Neither names §2.5 (c), the scheduled
  `/compile-memory`, or (d), the reports commissioned by hand.
- §11 has "machine-local memory ... written directly". Under P1 a worker on another machine never sees it, so the
  next run does not start smarter.
Proposed-edit: Route every close-out learning to the learning-batch issue (none to machine-local memory). Make row 7
and A7 name (a) to (d) alike.

### T-13 — Feedback from logs: the close-out's deployment findings have no source
Severity: C
Location: design.md §11 item 2, §7.2 (CLOSE-READY row); traceability.md A6, row 6
Target: gap analysis §2.4: "no step 'after the integration tests, scan the application logs'"; keynote slide 9,
notes: "Otherwise, it just means that nobody looked."
Defect: §11 promises "new issues uncovered by the deployment, even a successful one", but no CLOSE-READY checker or
tool reads deployment logs (its deterministic set is the TODO, debug-flag and ledger checks). Logs are read only to
attribute a failed smoke. Row 6 is "partial" with no remainder named.
Proposed-edit: Name the remainder in row 6 ("no log read after integration tests or a green deploy; close-out has no
log source"). Optionally, add a read-only CloudWatch query to the close-out worker.

### T-14 — Kiro parity: the design adds about 14 agent roles that each need a hand-kept Kiro twin
Severity: C
Location: design.md §7.2, §8.4, §12.3, §12.7, §16, §18; traceability.md B.2 3.4, B.3 rank 12 ("unchanged plan")
Target: gap analysis §3.4: "20 agents and 4 commands are kept twice, by hand, until the phase-2 renderer exists".
Defect: `clients/claude/agents/` has 20 agents. The design adds roles that do not exist yet: triage worker,
duplicate-confirmer, scope checker, acceptance-test author, threat-model maker and checker, logic-bug reviewer,
unnecessary-code reviewer, failure attributor, close-out worker, retro checker, question checker and arbiter, plus a
maker/checker split of 2 agents and `/get-guidance`. That grows the hand-kept twin set by about 70 %. Section 3.4
and rank 12 do not account for it.
Proposed-edit: State in §16 and §18 that the phase-2 renderer is a precondition for the new roles. Set 3.4's status
text to name the growth.

### T-15 — The design presupposes the merge steward; `merge: direct` projects are not addressed
Severity: C
Location: design.md §3.1 (TEST-READY "owned by the steward"), §10; traceability.md B.2 3.7, B.3 rank 9
Target: gap analysis §3.7: the consumer project runs "`merge: direct` + `verification: session`".
Defect: design.md never mentions `merge: direct` or `config/delivery.json`. This repository also merges directly
(CLAUDE.md "This project"). Section 3.7 is "not designed", but the design depends on rank 9's switch.
Proposed-edit: Add to 3.7: "precondition: `merge: steward` + `verification: watcher`". State in §3.1 what TEST-READY
means under `merge: direct`.

### T-16 — "A one-line fix stays a one-line fix" has no traced minimum path
Severity: C
Location: design.md §7.3 ("Every issue"), §3.4, §4.2; traceability.md A11, A20 (no row for these)
Target: keynote slide 10, notes: "If every small task gets the full ceremony, people stop using the loop"; slide 23:
"Simplest thing that works", "Open loop for a 3-step job".
Defect: A tier-S issue needs:
- a triage record with a duplicate search and a decision inventory;
- a spec with acceptance tests that fail for the right reason, a draft PR and a `spec-approved` record;
- seven every-issue checkers;
- a close-out record and summary.

No row shows that this is proportional. Slide 23's notes on checking versus proving are untraced too.
Proposed-edit: Add a row for slides 10 and 23 with a table of the tier-S minimum path (records and checkers), and
state why each is needed for S.

### T-17 — Keynote elements without a row, and deviations not recorded
Severity: C
Location: traceability.md sections A and C
Target: keynote slide 24: "MCP → the loop can reach Jira, CI and your logs", "Steering files → memory that survives
the session"; slide 15: "MCP auto-discovery", "sandbox · approval modes · audit log", webhooks; slide 16, notes:
governance "declared per agent".
Defect: None of these has a row. Three of them are deviations without a section C entry:
- §7.5: "a gate must therefore never depend on an MCP server";
- §15 rules 3 and 4: pinned servers and `--strict-mcp-config`, against auto-discovery;
- B12: polling instead of webhooks.

Sandboxing of workers, and whether dispatcher-started workers inherit central governance (slide 14: "Crew does not
get its own exceptions"), are not addressed.
Proposed-edit: Add rows for slides 15, 16 and 24, and section C rows for MCP-optional (§7.5), no auto-discovery (§15)
and polling (B12), each with its reason. Name sandboxing and governance inheritance in A14 and A17.

### T-18 — The caveat, do's-and-don'ts and AI-DLC rows claim more than the design gives
Severity: C
Location: traceability.md A19, A20, A21, C1; design.md §19.5, P1
Target: keynote slide 18, notes: "review what matters, and keep the specs readable"; slide 23: "Smallest high-signal
context", "Re-read all history each turn"; slide 28: "asks clarifying questions"; slide 29: "Mob Elaboration".
Defect:
- A19 is "designed", but its answers to comprehension debt and to "startup ≠ bank" are the default-off approval,
  which is C1.
- A20 cites diff-scoped checkers for small context, but every hand-off "re-reads issue, spec and code" (§19.5), and
  P1 makes the comment history the state.
- C1's reason covers human validation, not AI-DLC's clarifying questions, which the question checker filters
  (U12, U14), nor the mob rituals.
Proposed-edit: Set A19 and A20 to partial (pointing at C1 and §19.5). Extend C1's "Why" to cover the questions and
the mob rituals.

### T-19 — Under B2 a worker can choose its own checking depth
Severity: C
Location: design.md §3.4 ("tier S: START → TEST-READY in one claim"), §7.2 (START row), §7.3; traceability.md A11, A16
Target: keynote slide 10: "The agent that did the work does not get a vote".
Defect: One claim may triage, spec and implement, so the same worker sets the tier and risk tags that select its own
later checkers. For S and M, only "risk-tag and footprint heuristics" check them (the scope checker runs for L only).
Proposed-edit: Make the heuristic's tags binding (only a checker can remove one), or give every triage record a
checker. Set A16 to partial, naming this and T-01.

### T-20 — Traceability cites design elements that design.md does not contain
Severity: D
Location: traceability.md A15 ("Playwright MCP as a pilot"), A11 ("The client stop gates stay"), row 9 ("pen testing
optional")
Defect: A grep of design.md finds none of the three. The pen test is T-04 and the stop gates are T-11.
Proposed-edit: Add Playwright to §9, or delete it from A15.

### T-21 — Jira is "out of scope", but the state model's storage was chosen for GitHub and GitLab only
Severity: C
Location: traceability.md B.2 3.8; design.md §4.4, §5.1, §19.1
Target: keynote slide 6, notes: "something every one of you has, a Jira backlog"; gap analysis §3.8: "a
precondition for adoption there, not a feature".
Defect: The label storage and the comment-order claim tie-break (§19.1, unverified even for the two forges) are
GitHub/GitLab choices. Jira's native workflow status would be the natural stage store.
Proposed-edit: Add one sentence to §4.4 (stage = Jira workflow status), and add Jira to §19.1's comment-order check.
Restate 3.8's reason as "the wrapper is out of scope; the model maps onto Jira statuses".

### T-22 — C3 and C4 give partial reasons
Severity: D
Location: traceability.md C3, C4
Defect: C3's reason, "a command cannot set `/goal`", is a Claude Code fact. The keynote's `/goal` is Kiro's (slide 13),
and a human-driven session can still use it over the transition predicate. C4 cites U9 (no throwaway shared
environments), but what makes the LOCAL check optional is the gap analysis §2.1 reason: "not every project can run
locally".
Proposed-edit: Add to C3: "a human may still state `/goal` over the transition predicate". Add §2.1's reason to C4.

### T-23 — C2 cites one slide; the conflict appears on three
Severity: D
Location: traceability.md C2
Target: keynote slide 7, notes: "it should not quietly fix it either"; slide 8, notes: "file an issue for everything
odd they find"; slide 19.
Defect: The filing discipline's fix-first rule (a small, clear defect is fixed in the current change, and named in
the commit) also differs from slide 7's "do not fix it". C2's reason addresses only the filing volume.
Proposed-edit: Cite slides 7, 8 and 19 in C2, and add: "fixed in the open, named in the commit and report, never
quietly".

## Corrected status table (every disputed row)

| Row | traceability.md says | Corrected | Finding |
|---|---|---|---|
| A1 | designed | partial: the classification is skippable on REWORK → TEST-READY; no production path to the landed spec; no living spec | T-01 |
| A5 | designed | designed, with new deviation C8 (the steward checks green) | T-10 |
| A6 | partial | partial: no log read after tests or a green deploy; close-out has no log source; triage rule restated | T-05, T-13 |
| A7 | partial | partial: gap §2.5 (a) to (d) named; machine-local writes removed | T-12 |
| A9 | designed | partial: host open (O12) | T-03 |
| A10 | partial | partial: also no pen test, external review not per PR (deviation), no incident expedite | T-04, T-09 |
| A11 | designed | partial: the stop gates must change for hand-offs; the tier is self-selected under B2 | T-11, T-19 |
| A13 | designed | partial: no cost record; no per-user and per-model export | T-02 |
| A14 | partial | partial: also governance inheritance for dispatcher-started workers, sandboxing | T-17 |
| A15 | partial | partial: delete the Playwright citation or design it | T-20 |
| A16 | designed | partial: rework classification and tier selection lack a checker | T-01, T-19 |
| A17 | partial (nothing named) | partial: host (O12), per-agent governance (O11), MCP auto-discovery deviation | T-03, T-17 |
| A18 | designed | partial: the verdict has no not-verified field | T-06 |
| A19 | designed | partial: comprehension debt and "bank" rely on C1 | T-18 |
| A20 | designed | partial: hand-off context unbounded (§19.5) | T-18 |
| A21 | deviation | deviation: C1 reason extended | T-18 |
| Row 2 | designed | partial: comments are editable; immutability not designed | T-08 |
| Row 3 | designed (host open) | partial: host (O12); priority only within a queue | T-03, T-09 |
| Row 5 | designed | partial: the reaper runs in the unhosted dispatcher | T-03 |
| Row 6 | partial (nothing named) | partial, with the rest named | T-13 |
| Row 7 | partial: no correction hook | partial: §2.5 (a) to (d) | T-12 |
| Row 8 | partial | partial: also no expedite path | T-09 |
| Row 9 | designed (pen testing optional) | partial: no pen test in design.md; no system threat model; external review not per PR | T-04 |
| Row 10 | designed; a living system spec is not | partial | T-01 |
| Row 12 | designed | partial: no cost source | T-02 |
| Row 13 | partial (nothing named) | partial: per-agent deny by default and Kiro allowlists (O11) | T-17 |
| Row 14 | designed (host open) | partial: host and worker start (O12) | T-03 |
| Row 15 | deviation | designed as configurable once the PR-path clause exists; default off = C1 | T-07 |
| Row 16 | designed | partial: cost per issue has no source | T-02 |
| 3.1 | partial ("(a) §17") | partial: (a) not designed either | T-02 |
| 3.3 | designed | partial: host open (O12) | T-03 |
| 3.4 | partial | partial: plus about 14 new roles needing twins | T-14 |
| 3.5 | designed by decision U17 | as row 15 | T-07 |
| 3.7 | not designed | not designed; the design presupposes steward + watcher | T-15 |

Rows to ADD: C8 (T-10); B.4 for the gap analysis §6 (T-11); slides 10 and 23, the tier-S path (T-16); slides 15, 16
and 24, plus C rows for MCP-optional, no auto-discovery and polling (T-17).

Rows accepted as written: A2, A3, A4, A8, A12, rows 1, 4 and 11, 3.2, 3.6, 3.8 (reason restated in T-21), and C1 to
C7 (reasons extended by T-18, T-22 and T-23). Slide 17 (Danske Bank) and slides 25, 26 and 30 are context, not loops
or controls, and need no row.
