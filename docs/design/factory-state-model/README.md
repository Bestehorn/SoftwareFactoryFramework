# Factory state model: review set (revision 13, 2026-11-20)

A design for a backlog-driven software factory: every issue moves through stages; teams of maker and checker agents
loop in each stage until a deterministic finish line holds; workers on any machine and client pull work and never
wait; the human is reached only when no agent can resolve something. **Design only: nothing here is implemented.**

The design and its reviews so far:

- Revision 1 (11073fe, 2026-11-11) was reviewed twice, and revision 2 (cec3492) answered every finding.
- Revision 2 was re-reviewed by the same two reviewers on 2026-11-16: 21 earlier findings partly fixed, 30 new ones,
  no A.
- Revision 3 (5dcc08f) answered all of them. Its round-3 reviews left 20 items open, none of grade A.
- Revision 4 (049a047) answered those. Its round-4 reviews left 21 items open, none of grade A.
- Revision 5 (1fce726) answered those, partly by replacing mechanisms with simpler ones. Its round-5 reviews left 15
  items open, one of grade A.
- Revision 6 (8df28db) answered those. Its round-6 reviews left 8 items open, none of grade A.
- Revision 7 (b236e58) answered those. Its round-7 reviews left 4 items open (2 C, 2 D); the alignment review had none.
- Revision 8 (66c8a50) answered those. Its round-8 reviews left 2 items open (1 C, 1 D); the alignment review had none.
- Revision 9 (775d436) answered those. Its round-9 reviews left 3 items open (1 C, 2 D); the alignment review had none.
- Revision 10 (88bce8a) answered those. Its round-10 adversarial review left 2 wording items (1 C, 1 D).
- Revision 11 (b440fb7) answered those. Its round-11 adversarial review left 1 D item.
- Revision 12 (50cec91) answered it. Its round-12 adversarial review left 1 D item.
- Revision 13 answers it; review-response.md Part 0 maps it.

The reviews are kept as permanent records beside the design (decision U23).

## Documents

| File | What it is |
|---|---|
| [design.md](design.md) | The consolidated design: principles, stages, flags, delivery modes, finish lines, authority, claims, admission and triage, teams, the review-record exchange, the spec hand-off, batched delivery and revert first, close-out, human input, budgets, the dispatcher, tools, trust and identity, what would change |
| [decisions.md](decisions.md) | Every decision with its source: the operator's (U), the designer's reversible ones (M), those adopted from the reviews (R), the working baseline open to review (B), open items (O) |
| [traceability.md](traceability.md) | How the design aligns with the keynote's vision (a vision, not a specification: U22) and how it covers the gap analysis, row by row, with the deliberate differences |
| [review-response.md](review-response.md) | Every finding of every review round, with its disposition and where the design carries it: Part 0 for round 12, Parts 1 to 11 for rounds 11 to 1 |

Appendices, in [`docs/reports/factory-state-model-2026-11/`](../../reports/factory-state-model-2026-11/) (dated
records, kept as written):

| File | Content |
|---|---|
| `reviews/adversarial-review-2026-11-11.md` | The adversarial review of revision 1: 53 findings |
| `reviews/target-review-2026-11-11.md` | The review of revision 1 against the keynote and the gap analysis: 23 findings and a corrected status table |
| `reviews/adversarial-review-r2-2026-11-16.md` | The adversarial re-review of revision 2 (cec3492): verdicts on the 53 earlier findings (36 verified, 17 partly) and 16 new findings (9 B, 6 C, 1 D) |
| `reviews/target-review-r2-2026-11-16.md` | The alignment re-review of revision 2 (cec3492): verdicts on the 23 earlier findings (19 verified, 4 partly) and 14 new findings (1 B, 10 C, 3 D) |
| `reviews/adversarial-review-r3-2026-11-19.md` | The adversarial round-3 review of revision 3 (5dcc08f): 43 of 44 earlier items verified, 15 new findings (7 B, 7 C, 1 D) |
| `reviews/target-review-r3-2026-11-19.md` | The alignment round-3 review of revision 3 (5dcc08f): all 20 earlier items verified, 4 new findings (1 B, 1 C, 2 D) |
| `reviews/adversarial-review-r4-2026-11-19.md` | The adversarial round-4 review of revision 4 (049a047): 15 of 16 earlier items verified, 15 new findings (6 B, 8 C, 1 D) |
| `reviews/target-review-r4-2026-11-19.md` | The alignment round-4 review of revision 4 (049a047): all 4 earlier items verified, 5 new findings (1 B, 3 C, 1 D) |
| `reviews/adversarial-review-r5-2026-11-19.md` | The adversarial round-5 review of revision 5 (1fce726): all 16 earlier items verified, 11 new findings (1 A, 3 B, 5 C, 2 D) |
| `reviews/target-review-r5-2026-11-19.md` | The alignment round-5 review of revision 5 (1fce726): all 5 earlier items verified, 4 new findings (2 C, 2 D) |
| `reviews/adversarial-review-r6-2026-11-19.md` | The adversarial round-6 review of revision 6 (8df28db): all 11 earlier items verified, 7 new findings (2 B, 3 C, 2 D) |
| `reviews/target-review-r6-2026-11-19.md` | The alignment round-6 review of revision 6 (8df28db): all 4 earlier items verified, 1 new finding (D) |
| `reviews/adversarial-review-r7-2026-11-19.md` | The adversarial round-7 review of revision 7 (b236e58): all 7 earlier items verified, 4 new findings (2 C, 2 D) |
| `reviews/target-review-r7-2026-11-19.md` | The alignment round-7 review of revision 7 (b236e58): the 1 earlier item verified, no new finding |
| `reviews/adversarial-review-r8-2026-11-19.md` | The adversarial round-8 review of revision 8 (66c8a50): all 4 earlier items verified, 2 new findings (1 C, 1 D) |
| `reviews/target-review-r8-2026-11-19.md` | The alignment confirmation pass on revision 8 (66c8a50): no new finding |
| `reviews/adversarial-review-r9-2026-11-19.md` | The adversarial round-9 review of revision 9 (775d436): both earlier items verified, 3 new findings (1 C, 2 D) |
| `reviews/target-review-r9-2026-11-19.md` | The alignment confirmation pass on revision 9 (775d436): no new finding |
| `reviews/adversarial-review-r10-2026-11-19.md` | The adversarial round-10 review of revision 10 (88bce8a): all 3 earlier items verified, 2 new findings (1 C, 1 D) |
| `reviews/target-review-r10-2026-11-19.md` | The alignment confirmation pass on revision 10 (88bce8a): no new finding |
| `reviews/adversarial-review-r11-2026-11-20.md` | The adversarial round-11 review of revision 11 (b440fb7): both earlier items verified, 1 new finding (D) |
| `reviews/target-review-r11-2026-11-20.md` | The alignment confirmation pass on revision 11 (b440fb7): no new finding |
| `reviews/adversarial-review-r12-2026-11-20.md` | The adversarial round-12 review of revision 12 (50cec91): the earlier item verified, 1 new finding (D) |
| `reviews/target-review-r12-2026-11-20.md` | The alignment confirmation pass on revision 12 (50cec91): no new finding |
| `revert-and-batching.md` | Fast revert and batched deploys to shared AWS environments: failure taxonomy, techniques, how others batch, the two-track recommendation, hazards in today's code |
| `review-protocol.md` | The structured maker/checker exchange: standards compared (SARIF, Web Annotation, LSP, Gerrit, A2A …), the `factory-review/v1` schema with examples, transport, multi-way resolution |
| `checker-landscape.md` | Checker agents and tools per stage, with an inventory of the framework's agents and the gap list |
| `mcp-and-powers.md` | MCP servers (incl. the awslabs threat-modeling server) and Kiro powers per stage, with trust rules |
| `plugin-marketplaces.md` | Claude Code plugin marketplaces: what to adopt, imitate or skip, recurring techniques, trust rules |
| `thresholds.md` | Budgets and bounce limits derived from 600 issues on four trackers |
| `questions-data.md` | How questions to the operator spread over an issue's life, and what the late ones were |
| `discussion-log.md` | The chronological design discussion up to revision 1; superseded where it differs from `decisions.md` |

The appendix reports and reviews describe the revision they were written for and are not rewritten. Where they differ
from design.md, design.md wins.

**The two reference documents are NOT in this repository.** The operator gives them to a reviewer directly:

- the keynote deck "AI-DLC in Practice: Thinking in agentic loops with Kiro" (an engineering keynote held at a
  customer, 2026-11-03), with its speaker notes. It outlines a vision; it is not a specification;
- the gap analysis "SoftwareFactoryFramework vs. the software factory of the keynote" (2026-11-09).

## Suggested reading order

1. design.md §1–§5 (principles, starting point, stages, finish lines, authority, claims)
2. decisions.md
3. the rest of design.md
4. review-response.md, for what changed since revision 1
5. traceability.md

The appendices only where a section cites them (*R: file*).

## Review briefs

Each reviewer gets this folder and the appendices, and nothing else from the discussion. A re-review starts from
review-response.md, "What the next review should check (revision 13)", verifies each disposition of its own open items
in Part 0 against design.md, and reviews what revision 13 changed.

### 1. Adversarial review of the design

Find what is wrong, missing or unenforceable. In particular:

1. **Concurrency:**
   - races between workers on different machines;
   - lost updates on labels and comments;
   - a crash at every step of a transition, a claim, a revert;
   - lease expiry while work is in progress.
2. **Liveness:**
   - an issue that can stall in a stage with no role able to move it;
   - deadlock between `blocked-by` chains;
   - livelock between REWORK and TEST-READY, or between SPEC and `needs-input`;
   - a dispatcher that never starts a needed role.
3. **Predicates:**
   - an exit condition in design §4.2 that cannot be evaluated from tracker, git and CI state;
   - one a maker can satisfy without doing the work;
   - one that blocks forever;
   - an edge with no authorised caller (§4.5).
4. **Maker ≠ checker:** any path where an agent effectively grades its own work, incl. the arbiter, the question
   checker and the answer recorder.
5. **Revert first:**
   - a failure mode where the restore makes things worse;
   - a wrong attribution that bounces innocent work;
   - interactions with the hazards H1–H15.
6. **Security:**
   - prompt injection through issue text, comments, review records, logs and MCP servers;
   - credential exposure;
   - the admission rule;
   - the reserved decisions under the shared account, kept by decision U24.
7. **Cost and scale:**
   - hand-off cost;
   - API rate limits;
   - comment growth on long issues;
   - checker cost per tier.
8. **Forge and client differences:** anything that works on GitHub but not GitLab, or in Claude Code but not Kiro.
9. **Claims about the existing code:** check each against the cited file and symbol (the design cites symbols, not line
   numbers).

design.md §19 lists the weaknesses the designer already sees; start there, and go further.

### 2. Alignment with the keynote and coverage of the gap analysis

Using the keynote and the gap analysis (both provided by the operator):

1. Does the design pursue each loop and control of the keynote's vision, or say why it differs? The keynote is a
   vision, not a specification: judge alignment, not compliance.
2. Is every gap-analysis row closed, partly closed with the rest named, or deliberately deviated from with a reason?
3. Does the design contradict anything the keynote suggests an engineer could try, without saying so?
4. Are the statuses in traceability.md honest?

### Finding format (both reviews)

The shape of `clients/common/docs/review-contract.md`:

- grade: A (blocking defect), B (material), C (improvement), D (note);
- the target, as a quote of the text concerned plus the file and section, never a line number;
- the reasoning with evidence;
- a proposed change, or two or three options with the recommended one first.

A reviewer who can emit the `factory-review/v1` records of design §8 may use them instead. The report is committed
beside the design (U23).
