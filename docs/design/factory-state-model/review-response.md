# Response to the reviews of revision 1 (revision 2, 2026-11-16)

Both reviews read revision 1 (11073fe) on 2026-11-11, each in a session independent of the designer's:

- [adversarial-review-2026-11-11.md](../../reports/factory-state-model-2026-11/reviews/adversarial-review-2026-11-11.md):
  53 findings (4 A, 22 B, 23 C, 4 D);
- [target-review-2026-11-11.md](../../reports/factory-state-model-2026-11/reviews/target-review-2026-11-11.md): 23
  findings (8 B, 12 C, 3 D) and a corrected status table.

Every finding is answered below with its disposition and the place in revision 2 that carries the change. A decision
id (R, M, U, O) refers to [decisions.md](decisions.md).

**Outcome.** All 76 findings are accepted:

- 70 as proposed or with a small variation;
- 4 with a different mechanism that meets the same need: B1, B7, C2 and C22;
- 1 superseded by another fix: T-10;
- 1 outside the design set: C23.

None is rejected. One finding needs the operator: A4's root cause, which identity the agents post as, is open as O13.

**Three operator decisions taken while answering** change how some findings are read:

- **U21, equal scrutiny.** The operator's input gets neither more nor less scrutiny than an agent's. Revision 2 keeps
  authorship checks only where a decision is reserved to a human, and explains why in design §12.3.
- **U22, the keynote is a vision, not a specification.** Target-review findings phrased as "not met" were applied as
  corrections of accuracy and alignment, and traceability.md now records alignment rather than compliance.
- **U23, reviews are permanent records.** Both reports are committed beside the design.

## Adversarial review

| Id | Grade | Finding (short) | Disposition | Revision 2 |
|---|---|---|---|---|
| A1 | A | No actor may change the stage of an issue in TEST-READY | accepted (option 1) | §4.5 authority table; §3.1; §3.4 items 3–4; caller role per edge in §4.2; §18 Authority and Delivery rows (R1) |
| A2 | A | Maker ≠ checker keyed on the session, so in-session verification never counts | accepted (option 1) | §8.1 `actor.agent` + role; §4.1; §8.4 (R4) |
| A3 | A | Per-stage claims vs one claim carrying an issue across stages | accepted | §5.1: one claim per issue, the stage informational; §3.4 item 1 (R2) |
| A4 | A | Any commenter's unmarked comment counts as an answer, approval or ask change | accepted, reframed by U21 | §8.3; §12.3; §4.5 authorised-human role; lock option in §6.3. Residual under the shared account: O13 (R5) |
| B1 | B | The claim protocol has a visibility race, no fencing, an unspecified lease | accepted, different mechanism | §5.1–§5.2: the claim ref is acquired and renewed with `git push --force-with-lease`. That is a server-side compare-and-swap over the git protocol, which also spends no REST write budget, rather than `git/create-ref`. The fencing token is the ref SHA; the lease is judged by the reaper's own clock. Verification on `sff-test-*`: O14 (R2) |
| B2 | B | The verb is check-then-act, and crash recovery rolls back transitions that took effect | accepted | §4.4: guard named as such; intent first, done last; the reconciler rolls forward; the START rule (R3) |
| B3 | B | No dispatcher queue for checker lanes | accepted | §14 queue table; §5.3 verify claims (R24) |
| B4 | B | A direct answer is never read, because `needs-input` issues are not pullable | accepted | §12.7 answer recorder; §14 recorder queue (R24) |
| B5 | B | The ask-change trigger fires on answers and on the steward's own comments | accepted | §4.3: ask hash only, `/amend`, SPEC and IMPLEMENTATION only; §8.2 machine-comment definition (R7) |
| B6 | B | The gate counts verdicts whose authorship cannot be proven; the maker side can satisfy it | accepted | §8.5 downgrades; §8.6 the steward re-runs the fold; the status is a projection; the authorship residual is O13 (R23) |
| B7 | B | `merge-steward:` lines accepted from any author, so a landing can be forged | accepted, different mechanism | §10.8 H7: landings come from trunk's first-parent trailers (`Steward-PR`), with comments as projections. Author filtering is only a second layer, because a workflow on a worker's own PR branch can also post as `github-actions[bot]` (R8) |
| B8 | B | Admission keyed on provenance lines anyone can type | accepted | §6.3 admission by author (R6) |
| B9 | B | One write-scoped token everywhere, no per-worker revocation | accepted (option 1 as baseline) | §15.2 per-host fine-grained tokens without irreversible-operation permissions; option 2 is part of O13 (R33) |
| B10 | B | The shared account's content-creation limit caps the factory | accepted | §8.2 one envelope per round; claims over git (§5); PR projections off; host-wide token bucket (§15.2); identity options in O13 (R22) |
| B11 | B | The red verdict blames every landing since the last green deploy | accepted | §10.5; §10.8 H8; §2; §18 Delivery (R9) |
| B12 | B | The watcher closes verified issues itself, so CLOSE-READY never runs | accepted | §10.8 H9; §2; §11; §18 (R10) |
| B13 | B | `delivery-status` is closed and body-only, so it cannot carry escalations or be a `blocked-by` target | accepted | §12.5 `env-incident` issues per root cause; §10.4 step 6; §3.2 (R14) |
| B14 | B | Steward-opened revert PRs never get PR CI on GitHub; the revert is not train 1 | accepted | §10.4 step 3; §10.8 H10 (R11) |
| B15 | B | The H1 fix supersedes a batch-tip landing not tied to a PR | accepted | §10.8 H1: per PR, from trunk trailers; §4.2 TEST-READY → CLOSE-READY (R8) |
| B16 | B | Attribution step A3 names the wrong culprit when several landings change the failing resource | accepted | §10.4 step 2.2 (exactly one step, dependency closure); signature; refunds in §13 (R12) |
| B17 | B | The auto-restore has no guard for stateful changes and trusts an unprotected cache | accepted | §10.3 step 4 restore guard and digest check; step 5; §10.6 cache (R13, M1) |
| B18 | B | Triage sets the tier and risk tags alone | accepted | §6.4 deterministic floor, raise-only (R19) |
| B19 | B | The acceptance-test freeze can be bypassed without touching the test files | accepted | §4.2: S's tests, fixtures and configuration run over H's code; §9 (R17) |
| B20 | B | CLOSE-READY removes only resources the agents chose to record | accepted | §11 `factory-issue` tag + ledger; §4.2 (R25) |
| B21 | B | The predicates assume the steward and the watcher; other modes are not mapped | accepted | §3.5 delivery modes (R26) |
| B22 | B | Draft PRs do not exist for private repositories on GitHub Free and Pro | accepted | §9; §4.2: readiness is the `do-not-merge` label (R18) |
| C1 | C | `--allow-pending` admits any "wait" verdict | accepted | §4.2: only when pending CI is the sole unmet clause (R16) |
| C2 | C | The verifier cannot report while CI is pending | accepted, different mechanism | §4.2, §14: the worker sets `ci-pending` and releases; the verifier lane completes the transition when CI has ended. Workers still never wait (P2), and "done when CI is green" holds (R16) |
| C3 | C | The train branches are deleted at landing | accepted | §10.4 step 2.2: first-parent merges, synthesized on CI; §2 |
| C4 | C | No `--after-id` on GitHub; a machine-local cursor; the 2,500-comment cap | accepted | §8.2 paging with an id filter, the cursor in the claim ref, a continuation issue at 2,000 (R22) |
| C5 | C | GitLab notes are folded by `created_at` | accepted | §8.2 fold by id on both forges; §2 |
| C6 | C | Budgets calibrated on warm-cache sessions undercount the new flow | accepted | §13 report-only for the first 20 issues per tier (R21) |
| C7 | C | The every-issue checker list conflicts with tier S's one combined pass | accepted | §7.3: tier S keeps one combined pass; the minimum path table (R31) |
| C8 | C | The rolling learning-batch issue keeps the backlog non-empty | accepted | §11 item 3: rotation per PR, exempt from the empty backlog and from its own learning capture; traceability A5 (M5) |
| C9 | C | The split parent has no writer or close rule | accepted | §3.2 `split`; §4.2 |
| C10 | C | `blocked-by`: cycles, closed targets, GitLab tier | accepted | §3.2 |
| C11 | C | Nobody removes the lease and `claimed` on steward and watcher returns | accepted | §5.1 ONE release verb, called by the steward and the watcher too (R2) |
| C12 | C | A false negative of the question checker | accepted | §12.4 always-ask list (R29) |
| C13 | C | A read-only triage paraphrase can hide an injected ask | accepted | §6.3 verbatim body in the admission view (R6) |
| C14 | C | `spec-approved` is an effect, not a precondition | accepted | §4.2 side effect written by the verb |
| C15 | C | Log text can steer attribution | accepted | §7.2; §10.4 step 2.4: the attributor ranks only inside the suspect set; logs are data (R12) |
| C16 | C | A hand-set single stage label is taken as truth | accepted | §4.4 reconciler compares with the last done line (R3) |
| C17 | C | On Kiro, renewal "at every checkpoint" is the model's action | accepted | §5.1 renewal in the wrapper; §16 (R2) |
| C18 | C | Every deploy before the revert lands re-breaks the environment | accepted | §10.4 step 4 deploy guard (R11) |
| C19 | C | The 2.5 h replay has unstated assumptions | accepted | §10.7 assumptions listed |
| C20 | C | Group claims can livelock | accepted | §5.3 ascending order, random back-off (R2) |
| C21 | C | Counters live in comments the shared account can edit or delete | accepted | §8.2 the fold rejects edited records; §5.1 no comment deletion; §13 counters from audit lines; deletion stays a residual (§19 item 4) |
| C22 | C | The arbiter's decision has no checker | accepted, narrowed | §8.7 step 4: deterministic re-check always; only a decision that OVERRULES a security or legal finding becomes an approval, so upholding security does not add a human round (R23) |
| C23 | C | Two untracked target files in the main checkout could be published by accident | accepted; outside the design set | both paths are excluded in the main checkout's local `.git/info/exclude`; nothing committed |
| D1 | D | The delivery label list is incomplete | accepted | §2 |
| D2 | D | `delivery.md` calls the status issue open; the code keeps it closed | accepted | §2; §18 small defects |
| D3 | D | The appendix uses "LANDED" | accepted in the design; the appendix is kept as written | §10.5 uses TEST-READY; `revert-and-batching.md` is a dated record and is not rewritten |
| D4 | D | "Laundry list" is undefined | accepted | §4.2 CLOSE-READY → closed defines it |

## Target review

| Id | Grade | Finding (short) | Disposition | Revision 2 |
|---|---|---|---|---|
| T-01 | B | The return path to the spec is skippable | accepted | §4.2 a rework analysis on every exit, confirmed by the test-architect; traceability A1, row 10 partial (R15) |
| T-02 | B | Cost budgets have no measurement source | accepted | §13 spend lines; §17; traceability A13, rows 12, 16, 3.1 (R21) |
| T-03 | B | "Who starts the loops" marked designed while the host is open | accepted | traceability A2, A9, rows 3, 5, 14, 3.3 partial; O12 extended with worker start and governance; §14 |
| T-04 | B | Security beyond the diff overstated; no pen test | accepted | §7.2 optional external PR review (setting) and batched pen test; traceability C10; row 9 partial (R27) |
| T-05 | B | The triage rule can refuse the keynote's own feedback-loop issues | accepted | §6.5 rule restated (R30) |
| T-06 | B | The verdict cannot carry what a lane did not verify | accepted | §8.1 required `notVerified`; §7.4; §11 summary (R20) |
| T-07 | B | Approval for sensitive paths has no PR-level predicate | accepted | §12.10; §4.2; traceability row 15 and 3.5 aligned (R28) |
| T-08 | B | "Single immutable record" marked designed, but records are editable comments | accepted | traceability row 2 partial; §19 item 4; O15 |
| T-09 | C | Incidents enter at START, which is pulled last | accepted | §6.1, §14 `priority:critical` first (R24) |
| T-10 | C | The implementer may hand over before CI is green | superseded | the C2 fix makes the transition wait for green CI and the verifier, without the worker waiting, so there is no deviation to record (R16) |
| T-11 | C | The keep-list is not traced; the stop gates must change | accepted | traceability B.4; §16; §18 Gates row (R32) |
| T-12 | C | The learning loop's remainder named inconsistently; machine-local writes | accepted | §11 item 3: no machine-local memory; traceability A7, row 7 name 2.5 (a)–(d) (M5) |
| T-13 | C | Close-out's deployment findings have no source | accepted | §11 item 2 and §7.2: the deploy-window log scan where the project provides a query; traceability A6, row 6 name the rest |
| T-14 | C | About 14 new roles need hand-kept Kiro twins | accepted | §16 renderer precondition; traceability 3.4 (R32) |
| T-15 | C | The design presupposes the steward | accepted | §3.5; traceability 3.7 (R26) |
| T-16 | C | No traced minimum path for a one-line fix | accepted | §7.3 tier-S table; traceability A22 (R31) |
| T-17 | C | Keynote ideas without a row; differences not recorded | accepted | traceability A23–A26, C8, C9, C11; §14 governance inheritance |
| T-18 | C | The caveat, do's-and-don'ts and AI-DLC rows claim too much | accepted | traceability A19, A20 partly aligned; C1 reason extended |
| T-19 | C | Under B2 a worker can choose its own checking depth | accepted | §6.4 (same fix as B18) (R19) |
| T-20 | D | Traceability cites elements design.md lacks | accepted | Playwright in §9; the pen test in §7.2; the stop gates in §16 |
| T-21 | C | Jira is out of scope, but storage was chosen for GitHub and GitLab only | accepted | §3.6; traceability 3.8 |
| T-22 | D | C3 and C4 give partial reasons | accepted | traceability C3, C4 |
| T-23 | D | C2 cites one slide | accepted | traceability C2 |

## What the next review should check

1. Whether the claim ref (§5) holds up: the custom ref namespace, the atomicity of `--force-with-lease` on both forges
   (O14), and the fencing window (§19 item 2).
2. Whether the authority table (§4.5) leaves any edge or record without a writer, or gives one to two roles.
3. Whether the queues of §14 make every flag combination pullable by someone, with no issue stranded.
4. Whether U21's equal scrutiny and §12.3's reserved decisions are consistent everywhere `needs-input`, approvals and
   admission appear.
