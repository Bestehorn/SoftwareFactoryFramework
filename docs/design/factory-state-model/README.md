# Factory state model: review set (2026-11-11)

A design for a backlog-driven software factory: every issue moves through stages; teams of maker and checker
agents loop in each stage until a deterministic finish line holds; workers on any machine and client pull work and
never wait; the human is reached only when no agent can resolve something. **Design only: nothing here is
implemented.**

## Documents

| File | What it is |
|---|---|
| [design.md](design.md) | The consolidated design: stages, flags, claims, finish lines, teams, the review-record exchange, the spec hand-off, batched delivery and revert first, close-out, human input, budgets, the dispatcher, tools and trust, what would change |
| [traceability.md](traceability.md) | The design against the keynote and the gap analysis, row by row, with the deliberate deviations |
| [decisions.md](decisions.md) | Every decision with its source: the operator's (U), the designer's reversible ones (M), the working baseline open to review (B), open items (O) |

Appendices, in [`docs/reports/factory-state-model-2026-11/`](../../reports/factory-state-model-2026-11/) (dated
records, kept as written):

| File | Content |
|---|---|
| `revert-and-batching.md` | Fast revert and batched deploys to shared AWS environments: failure taxonomy, techniques, how others batch, the two-track recommendation, hazards in today's code |
| `review-protocol.md` | The structured maker/checker exchange: standards compared (SARIF, Web Annotation, LSP, Gerrit, A2A …), the `factory-review/v1` schema with examples, transport, multi-way resolution |
| `checker-landscape.md` | Checker agents and tools per stage, with an inventory of the framework's agents and the gap list |
| `mcp-and-powers.md` | MCP servers (incl. the awslabs threat-modeling server) and Kiro powers per stage, with trust rules |
| `plugin-marketplaces.md` | Claude Code plugin marketplaces: what to adopt, imitate or skip, recurring techniques, trust rules |
| `thresholds.md` | Budgets and bounce limits derived from 600 issues on four trackers |
| `questions-data.md` | How questions to the operator spread over an issue's life, and what the late ones were |
| `discussion-log.md` | The chronological design discussion (four rounds); superseded where it differs from `decisions.md` |

**The two review targets are NOT in this repository** (it is public). The operator gives them to the target
reviewer directly:

- the keynote deck "AI-DLC in Practice: Thinking in agentic loops with Kiro" (an engineering keynote held at a
  customer, 2026-11-03), with its speaker notes;
- the gap analysis "SoftwareFactoryFramework vs. the software factory of the keynote" (2026-11-09).

## Suggested reading order

1. design.md §1–§4 (principles, starting point, stages, finish lines)
2. decisions.md
3. the rest of design.md
4. traceability.md

The appendices only where a section cites them (*R: file*).

## Review briefs

Two independent reviews are intended. Each reviewer gets this folder and the appendices, and nothing else from the
discussion.

### 1. Adversarial review of the design

Find what is wrong, missing or unenforceable. In particular:

1. **Concurrency:**
   - races between workers on different machines that share one tracker account;
   - lost updates on labels and comments;
   - a crash at every step of a transition, a claim, a revert;
   - lease expiry while work is in progress.
2. **Liveness:**
   - an issue that can stall in a stage with no worker able to move it;
   - deadlock between `blocked-by` chains;
   - livelock between REWORK and TEST-READY, or between SPEC and `needs-input`;
   - a dispatcher that never starts a needed role.
3. **Predicates:**
   - an exit condition in design §4.2 that cannot be evaluated from tracker, git and CI state;
   - one a maker can satisfy without doing the work;
   - one that blocks forever.
4. **Maker ≠ checker:** any path where an agent effectively grades its own work, incl. the arbiter and the question
   checker.
5. **Revert first:**
   - a failure mode where the restore makes things worse;
   - a wrong attribution that bounces innocent work;
   - interactions with the hazards H1–H6.
6. **Security:**
   - prompt injection through issue text, comments, review records, logs and MCP servers;
   - credential exposure;
   - the admission rule.
7. **Cost and scale:**
   - hand-off cost;
   - API rate limits;
   - comment growth on long issues;
   - checker cost per tier.
8. **Forge and client differences:** anything that works on GitHub but not GitLab, or in Claude Code but not Kiro.
9. **Claims about the existing code:** check each against the cited file and symbol (the design cites symbols, not
   line numbers).

design.md §19 lists the weaknesses the designer already sees; start there, and go further.

### 2. Review against the target

Judge the design against the keynote and the gap analysis (both provided by the operator, see above):

1. Is every loop and control of the keynote covered?
2. Is every gap-analysis row closed, partly closed with the rest named, or deliberately deviated from with a
   reason?
3. Does the design contradict anything the keynote promises an engineer could try?
4. Are the statuses in traceability.md honest?

### Finding format (both reviews)

The shape of `clients/common/docs/review-contract.md`:

- grade: A (blocking defect), B (material), C (improvement), D (note);
- the target, as a quote of the text concerned plus the file and section, never a line number;
- the reasoning with evidence;
- a proposed change, or two or three options with the recommended one first.

A reviewer who can emit the `factory-review/v1` records of design §8 may use them instead.
