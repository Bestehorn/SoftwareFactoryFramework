# Factory state model: review set (revision 2, 2026-11-16)

A design for a backlog-driven software factory: every issue moves through stages; teams of maker and checker agents
loop in each stage until a deterministic finish line holds; workers on any machine and client pull work and never
wait; the human is reached only when no agent can resolve something. **Design only: nothing here is implemented.**

Revision 1 (11073fe, 2026-11-11) was reviewed twice. Revision 2 answers every finding of both reviews; the reviews
themselves are kept as permanent records beside it (decision U23).

Revision 2 was re-reviewed by the same two reviewers on 2026-11-16. Their open items (21 partly fixed earlier
findings, 30 new findings, no A) are not answered yet: they are the input to revision 3.

## Documents

| File | What it is |
|---|---|
| [design.md](design.md) | The consolidated design: principles, stages, flags, delivery modes, finish lines, authority, claims, admission and triage, teams, the review-record exchange, the spec hand-off, batched delivery and revert first, close-out, human input, budgets, the dispatcher, tools, trust and identity, what would change |
| [decisions.md](decisions.md) | Every decision with its source: the operator's (U), the designer's reversible ones (M), those adopted from the reviews (R), the working baseline open to review (B), open items (O) |
| [traceability.md](traceability.md) | How the design aligns with the keynote's vision (a vision, not a specification: U22) and how it covers the gap analysis, row by row, with the deliberate differences |
| [review-response.md](review-response.md) | Every finding of both reviews of revision 1, with its disposition and where revision 2 carries it |

Appendices, in [`docs/reports/factory-state-model-2026-11/`](../../reports/factory-state-model-2026-11/) (dated
records, kept as written):

| File | Content |
|---|---|
| `reviews/adversarial-review-2026-11-11.md` | The adversarial review of revision 1: 53 findings |
| `reviews/target-review-2026-11-11.md` | The review of revision 1 against the keynote and the gap analysis: 23 findings and a corrected status table |
| `reviews/adversarial-review-r2-2026-11-16.md` | The adversarial re-review of revision 2 (cec3492): verdicts on the 53 earlier findings (36 verified, 17 partly) and 16 new findings (9 B, 6 C, 1 D) |
| `reviews/target-review-r2-2026-11-16.md` | The alignment re-review of revision 2 (cec3492): verdicts on the 23 earlier findings (19 verified, 4 partly) and 14 new findings (1 B, 10 C, 3 D) |
| `revert-and-batching.md` | Fast revert and batched deploys to shared AWS environments: failure taxonomy, techniques, how others batch, the two-track recommendation, hazards in today's code |
| `review-protocol.md` | The structured maker/checker exchange: standards compared (SARIF, Web Annotation, LSP, Gerrit, A2A …), the `factory-review/v1` schema with examples, transport, multi-way resolution |
| `checker-landscape.md` | Checker agents and tools per stage, with an inventory of the framework's agents and the gap list |
| `mcp-and-powers.md` | MCP servers (incl. the awslabs threat-modeling server) and Kiro powers per stage, with trust rules |
| `plugin-marketplaces.md` | Claude Code plugin marketplaces: what to adopt, imitate or skip, recurring techniques, trust rules |
| `thresholds.md` | Budgets and bounce limits derived from 600 issues on four trackers |
| `questions-data.md` | How questions to the operator spread over an issue's life, and what the late ones were |
| `discussion-log.md` | The chronological design discussion up to revision 1; superseded where it differs from `decisions.md` |

The appendix reports describe revision 1 and are not rewritten. Where they differ from design.md, design.md wins.

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

Each reviewer gets this folder and the appendices, and nothing else from the discussion. A re-review of revision 2
starts from review-response.md, "What the next review should check", and verifies the dispositions it disputes against
design.md.

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
   - interactions with the hazards H1–H10.
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
