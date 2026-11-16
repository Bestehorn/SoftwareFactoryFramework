# Adversarial review: factory state model design (branch `docs-factory-state-model-design`)

Reviewed: `docs/design/factory-state-model/` (README, design.md, decisions.md, traceability.md) and the appendices
in `docs/reports/factory-state-model-2026-11/`, at `origin/docs-factory-state-model-design`, in a detached review
worktree. Every code claim was checked against the code at that commit (product files: `src/payload/scripts/`,
`templates/ci/`, `clients/`). The designer's working notes were not read. Platform facts come from GitHub and
GitLab documentation, cited inline. Severities follow `clients/common/docs/review-contract.md`:

- A: cannot be implemented as written, or produces wrong behaviour, a security flaw or data loss.
- B: contradicts the design's own goals or rules, or a documented rule.
- C: a clarification or a risk.
- D: wording.

## Summary

| Grade | Count |
|---|---|
| A | 4 |
| B | 22 |
| C | 23 |
| D | 4 |

**The five most important findings**

1. **A1. No actor is allowed to move an issue out of TEST-READY.** The verb demands a claim, TEST-READY is never
   claimed, and the steward and the watcher write only delivery labels. Every landed, returned or verified issue
   keeps `stage:test-ready` for ever. This is the stranding failure ("0 of 10 closed") that the dispatcher exists
   to cure.
2. **A4. Any commenter can answer, approve or re-open the ask.** An unmarked comment from any author is "human
   input". On a public repository an outsider can answer a blocking question, approve an IAM grant, or send any
   issue back to SPEC-REQUIRED at will.
3. **A3. Claims are arbitrated per stage, but one claim carries an issue across stages.** Either the holder's own
   second transition is refused, or a second worker wins a claim for the new stage. That makes two writers on one
   issue.
4. **A2. maker ≠ checker is keyed on `<host>/<session>`.** The normal round dispatches maker and every lane inside
   one session, so no in-session verification is ever valid. The gate never holds, and the tier-S single-claim path
   cannot pass.
5. **B14. The revert that Track T depends on never lands on GitHub.** A PR the steward opens with `GITHUB_TOKEN` gets
   no PR CI, and `eligibility` waits on `"none"` for ever. `plan()` orders by enqueue time, so the revert is not
   train 1 either.

Next in weight:

- B11: the red verdict blames every landing since the last green deploy, in today's `verify_issue`.
- B7: any commenter can forge `merge-steward:` lines; the code ignores comment authors.
- B1: claim race. There is no fencing token, and the list endpoint lags.
- B10: rate limits. All workers, all projects and the operator share 500 content writes per hour.

**Root causes behind most findings.** Each finding below is written up separately.

1. **Authority is undefined.** The design never says which identity may write which record or call which edge.
   Behind A1, A4, B4–B8 and B13.
2. **Every check-then-act on the tracker is treated as atomic.** Behind A3, B1, B2 and C20.
3. **The delivery half is treated as reused unchanged.** Today's steward and watcher contradict §10.5 and §11 in
   five places (B11–B15) that §18 does not list.

---

## A findings

### A1 — No actor may change the stage of an issue in TEST-READY
Severity: A
Location: design.md § 3.1 (TEST-READY row), § 3.4 item 4, § 4.4 step 1; revert-and-batching.md § 6.5
Target: design.md §3.1 says "Owned by the steward and the deploy pipeline; never claimed by a worker". §4.4 says
"Compare-and-set: it refuses if the issue is not in `--from`, or if the caller does not hold the claim." §3.4 says
"A worker never changes the stage of an issue it does not hold."
Defect: TEST-READY → CLOSE-READY and TEST-READY → REWORK-REQUIRED have no caller that can pass the verb. Nothing
in the design gives the steward, the verdict watcher, `/get-guidance` or the reaper the right to transition.
Material-because: wrong-behaviour. Every issue that enters TEST-READY keeps `stage:test-ready` for ever, so the
dispatcher, which pulls by stage (§14), never pulls returned work or close-out.
Evidence:
- `merge_steward.py`: `_return_issue` adds `needs-rework`, releases the claim and comments. `verify_issue` adds
  `verification-failed` + `needs-rework`, or `verified` (+ `needs-closeout`). Neither writes a stage label or
  calls a transition.
- §18's Delivery row changes only "H1–H6 fixes in `merge_steward.py`; the deploy template".
- The appendix assigns the steward stage changes it cannot make. revert-and-batching.md §6.5: "LANDED →
  **TEST-READY** automatically: no claim, no worker, no rework". The culprit row: "LANDED → REWORK-REQUIRED …
  the claim released".
- The same gap affects:
  - §12.7 step 5: `/get-guidance` "Transition[s]" without a claim.
  - §5.2: the reaper "returns the issue to its queue".
  - A PR that never lands (on `hold`, dependency closed, CI `"none"`, see B14, or closed by a human). Nothing
    moves it back.
- §14 itself: "0 of 10 closed, since no one picked returned work up". This defect recreates that.
Options:
1. **(Recommended)** Add an authority table to §4.4, one row per edge, naming the identity allowed to call it:
   - a lease holder for worker edges;
   - the steward identity for TEST-READY → REWORK-REQUIRED and for the reland edges;
   - the watcher identity for TEST-READY → CLOSE-READY;
   - the reaper and the reconciler for repairs only;
   - `/get-guidance` acting for the human, with the human's login in the audit line.

   The steward and the watcher then call the verb (a library call, the same predicate code) in place of the bare
   label writes. List that change in §18's Delivery row.
2. Do not store TEST-READY's exits as labels written by anyone. The reconciler derives stage from delivery labels
   (`needs-rework` ⇒ REWORK-REQUIRED; `verified` ⇒ CLOSE-READY) and writes the projection. This is simpler, but
   it makes the reconciler a second writer of stages.

### A2 — maker ≠ checker is keyed on the session, so in-session verification never counts
Severity: A
Location: review-protocol.md § 4.4 rule 2 (verification row) and the envelope schema (`actor.worker`);
design.md § 8.3 steps 1 and 5; § 3.4 item 1; P8
Target: review-protocol.md §4.4 says "the finding's lane, from a worker other than the one that wrote the
resolution (maker ≠ checker)". The schema says `actor.worker`: "<host>/<session>, the identity the claim lease
uses". design.md §8.3 says "The conductor pins the SHA and dispatches every lane in one message" and "Each lane
verifies ONLY its own findings at the new SHA".
Defect: in the normal round, the maker (`spec-author` or implementer) and every lane are subagents of ONE
conductor session, so they share `<host>/<session>`. Every in-session `verification` is an `invalid-writer`, no
blocking finding reaches `verified`, and the gate predicate (review-protocol §4.4 rule 3) never holds.
Material-because: wrong-behaviour. As written, no stage with a blocking finding can be left. Tier S ("START →
TEST-READY in one claim") can pass only with zero blocking findings.
Evidence:
- One conductor dispatches all lanes: design §8.3 step 1; review-protocol §6.1 step 1, "as today".
- `clients/claude/agents/issue-work-orchestrator.md` dispatches every lane as a subagent of the one main session.
- review-protocol §5.2 item 3, "Lanes are roles, not sessions … as long as it is not the maker's worker", gives
  the cross-session route only. That route needs a scheduler for lane roles, which §14 does not have (B3).
Options:
1. **(Recommended)** Separate the two identities:
   - `actor.worker` stays the lease identity.
   - maker ≠ checker is enforced on a per-context `actor.agent` (subagent or fresh-context id) plus
     `actor.role` == lane.
   - A `verified` needs the re-run evidence the protocol already demands.

   State in §8.3 that in-session lanes verify in fresh contexts.
2. Require every verification to come from another session, through the `review-verify` queue. This drops the
   tier-S single-claim path and adds one hand-off per round (cost: C6).

### A3 — Per-stage claim arbitration is incompatible with a claim that carries an issue across stages
Severity: A
Location: design.md § 5.1 steps 1–2; § 3.4 item 1; P8
Target: §5.1 says "Post a claim comment: `factory: claim <stage> worker=<host>/<session> lease-until=<ISO>`" and
"The EARLIEST unexpired claim comment for that stage wins". §3.4 says "A worker holding the claim may carry an
issue through several stages".
Defect: W1 claims at START and carries the issue to SPEC-REQUIRED. W1's claim comment names START. Two readings
are possible, and both are wrong:
- If "holds the claim" means "has the earliest claim for the issue's CURRENT stage", the verb refuses W1's next
  transition (SPEC-REQUIRED → IMPLEMENTATION-READY).
- Otherwise, a W2 that pulls the issue as SPEC-REQUIRED posts a SPEC-REQUIRED claim and finds itself the earliest
  for that stage. W2 wins, and the issue has two holders.

The `claimed` label is only "a cheap filter" and does not prevent the second case. W2 may have listed the issue
before W1 added it, or the label may have been removed, for example by today's whole-set `release-issue` (§5.4).
Material-because: wrong-behaviour. It breaks property 2, "One writer per issue at a time".
Proposed-edit: in §5.1, replace "The EARLIEST unexpired claim comment for that stage wins" with "The EARLIEST
unexpired claim on the ISSUE wins, whatever stage it names. The stage in the comment is informational; the verb
checks the caller's claim id, not its stage." Make the lease renewal (step 4) keep the same comment id. See B1
for a server-enforced alternative.

### A4 — Any commenter's unmarked comment counts as a human answer, an approval or a change of the ask
Severity: A
Location: design.md § 8.2 (last paragraph); § 12.7 (last paragraph); § 3.2 (`needs-input` row); § 4.3; § 10.5
(grant row)
Target: §8.2 says "Only comments that are written by the shared account AND carry the marker are parsed. Everything
else is human input". §12.7 says "An answer written directly on the issue (an unmarked comment after an open
question) works equally."
Defect: the design never restricts WHO a human is. §6's admission controls apply to issue authors, not to comment
authors.
Material-because: security. On a public repository, any signed-in user can:
- answer a blocking question or an approval of kind grant, such as "Culprit whose fix needs a grant (e.g. an IAM
  action)" in §10.5;
- move `last_human_comment_id` on any issue, which sends it back to SPEC-REQUIRED at every checkpoint (§4.3). That
  is an unauthenticated denial of service on the whole backlog.
Evidence:
- GitHub lets any signed-in user comment on an open, unlocked issue of a public repository. Locking restricts it:
  "While a conversation is locked, only people with write access and repository owners and collaborators can add,
  hide, and delete comments" (docs.github.com, Locking conversations).
- This repository is public (README brief).
- §6 explicitly contemplates "external reporters on a public repository".
Options:
1. **(Recommended)** Add to §8.2: "Human input is an unmarked comment whose author is on the project's human
   allow-list (the operator, named collaborators). Any other comment is data: it is never an answer, an approval,
   or a change of the ask, and it does not move `last_human_comment_id`." Apply the same filter to PR/MR threads
   (review-protocol §5.2 item 4).
2. Additionally, lock factory issues to collaborators on public repositories. This is cheap, but on its own it
   leaves collaborators with write access unfiltered.

---

## B findings

### B1 — The claim protocol has a visibility race, no fencing, and an unspecified lease
Severity: B
Location: design.md § 5.1 steps 2 and 4–5; § 19 items 1–2
Target: §5.1 says "Re-read the comments. The EARLIEST unexpired claim comment for that stage wins, because comment
ids are assigned by the server." and "The lease is extended at every checkpoint by editing the comment."
Defect: correctness needs every re-read to see every comment with a smaller id. GitHub documents ordering
("ordered by ascending ID", REST issue comments) but not read-after-write completeness of the list. A practitioner
report (agents.stackoverflow.com, 2026-07-28) describes the list lagging right after a create, while the comment
is readable by id. Two workers can each see only their own claim and both win.

Independently, a lease without a fencing token admits two writers:
- A worker whose lease expired keeps pushing and writing until its next checkpoint, for example after a laptop
  sleep or a 60-minute local suite.
- The lease clock is worker-written ISO time.
- No duration is given.
Material-because: wrong-behaviour (two holders; the design's P3 guarantee).
Options:
1. **(Recommended)** Make the claim a server-enforced compare-and-swap:
   - The claim is a git ref per issue (e.g. `refs/factory/claims/<n>`), created through `git/create-ref`. The
     forge refuses a second create (the api-reference lists `422` for `git/create-ref`).
   - Renewal is `git/update-ref` with `force: false` (non-fast-forward refused, `docs/api-reference/github/
     conventions.md`), or `git push --force-with-lease`.
   - The ref's commit SHA is the fencing token. The verb and every push check it.
   - The comment becomes the human-readable projection.
   - To confirm against an `sff-test-*` repository: a custom ref namespace on both forges, and the exact refusal
     codes.
2. Keep comments, but:
   - add a settle delay and a second re-read before the first outward write;
   - take the lease time from the server (the comment's `updated_at`) plus a stated duration that exceeds the
     longest single step;
   - make the claim comment id a fencing token that the verb checks on every write;
   - renew the lease from the wrapper on every verb call.

### B2 — The transition verb is check-then-act, and its crash recovery rolls back transitions that took effect
Severity: B
Location: design.md § 4.4 steps 1–4 and "Storage"; § 3.1 (START row); § 19 item 4
Target: §4.4 says "Compare-and-set", "it adds the new label, then removes the old one", and "a reconciler repairs
an issue with zero or two stage labels from the last audit line". §3.1 says "An issue without a stage label is in
START".
Defect: neither forge offers a conditional label write, so step 1 is a read followed by writes, not a
compare-and-set.

Because the audit line is written last (step 4), a crash after step 3 leaves two labels with the OLD stage in the
last audit line. The reconciler then restores the old stage, although the edge's side effects (an enqueue at
IMPLEMENTATION-READY → TEST-READY) already happened. The next implementer pulls an issue whose PR is in the queue.

Any label loss, such as a human's whole-set edit or an older toolchain's `release-issue`, silently puts an issue in
START, and triage re-runs on work in flight.
Material-because: wrong-behaviour (lost or duplicated transitions).
Proposed-edit:
- Rename step 1 to "Guard (read, then write; exclusivity comes from the claim, B1)".
- Write the audit line FIRST as an intent, `factory: stage A -> B intent <id>`, then the labels, then
  `factory: stage A -> B done <id>`.
- The reconciler rolls FORWARD from an intent whose predicate side effects are present.
- Replace "An issue without a stage label is in START" with "An issue with no stage label and no audit line is in
  START; with an audit line it is repaired from it before any worker may pull it."

### B3 — The dispatcher has no queue for checker lanes, so `review-verify` issues are never verified
Severity: B
Location: design.md § 14 (Polling bullet); review-protocol.md § 5.2 item 3
Target: §14 says "counts the issues per stage that are pullable … and starts workers per role". review-protocol
§5.2 says "It releases, and the `review-verify` label puts the issue into the verification queue of that lane."
Defect: §14 counts stages, not lane queues. An issue in SPEC-REQUIRED with `review-verify` gets a spec MAKER, which
may not verify its own resolutions (A2). The maker releases. "Claims without progress" climbs to its hard limit (5,
§13), and the issue reaches the human as "stuck" for want of a scheduler.
Material-because: wrong-behaviour (liveness; P2 "Workers never wait").
Proposed-edit: add to §14: "A `review-verify` issue counts in the queue of each lane that has a resolution waiting.
The dispatcher starts a checker of that role, which claims the issue for verification only (no maker writes)." Add
the edge to the authority table of A1.

### B4 — A direct answer on the issue is never read, because `needs-input` issues are not pullable
Severity: B
Location: design.md § 12.7 (last paragraph); § 3.2 (`needs-input` row, "Cleared by"); § 14
Target: §12.7 says "An answer written directly on the issue (an unmarked comment after an open question) works
equally." §3.2's `needs-input` row is cleared by "`/get-guidance` or an unmarked human answer".
Defect: a comment cannot clear a label. §14 excludes `needs-input` issues from what is pullable, so no worker
reads the answer. The issue waits until the human runs `/get-guidance`, which is not "equally".
Material-because: wrong-behaviour (liveness).
Proposed-edit: add to §14: "The dispatcher also lists `needs-input` issues with an allow-listed human comment
newer than the last open question (A4), and starts the inbox for them. The inbox records the answer as
`factory: answer` and clears the flag."

### B5 — The ask-change trigger fires on answers and on the steward's own comments
Severity: B
Location: design.md § 4.3 (first bullet); § 8.2 (last paragraph)
Target: §4.3 says "At an IMPLEMENTATION-READY pickup and at every later checkpoint, the verb compares `ask_hash`
and `last_human_comment_id` with the issue as it is now … A mismatch sends the issue back to SPEC-REQUIRED".
Defect: every human comment changes `last_human_comment_id`, including the answers the design itself asks for (an
implementation-stage `needs-input`, a grant approval in REWORK). Each answer therefore costs a SPEC re-entry. With
a question in each visit, SPEC and needs-input ping-pong until the "SPEC ↔ needs-input" budget trips.

Machine comments that are not `factory-review` records also count as "human". These are:
- `factory: claim`, `factory: stage` and `factory: answer` lines, for which the design specifies no hidden
  marker;
- all `merge-steward:` lines. On GitHub they are authored by `github-actions[bot]`, not the shared account:
  `templates/ci/github-merge-steward.yml.template` and `github-deploy.yml.template` run
  `merge_steward.py --token-stdin` with `${{ github.token }}`.

"At every later checkpoint" also contradicts "After TEST-READY … a change of mind becomes a new issue" for
REWORK-REQUIRED.
Material-because: wrong-behaviour (livelock, needless re-specs).
Proposed-edit:
- Define the ask by `ask_hash` only. The title, the body without ticks, and an explicit `/amend` comment by an
  allow-listed human update it.
- Drop `last_human_comment_id` from the readiness check.
- In §8.2, define "machine comment" as one written by an identity on the machine allow-list (shared account,
  steward identity per forge) with the marker, and require the marker on every `factory:` and `merge-steward:`
  line.
- Limit the check to SPEC-REQUIRED and IMPLEMENTATION-READY.

### B6 — The gate counts verdict records whose authorship cannot be proven, and the maker side can satisfy it
Severity: B
Location: design.md § 4.1; § 8.2 item 3; review-protocol.md § 4.4 (rule 2, decision row), § 5.2 (Trust), § 6.1
step 6
Target: review-protocol §5.2 says "All workers post as one account, so `actor.worker` is self-declared". Rule 2
gives "decision `downgraded`/`nonmaterial` | the conductor". §6.1 says "the conductor sets `factory/review` to
success".
Defect: these are the predicate's only inputs, and nothing binds them to the role that is supposed to write them:
- `actor.role` and `actor.worker` are free text written by the same account the maker uses.
- The conductor, which runs in the maker's session, may downgrade a checker's blocking finding alone.
- The `factory/review` status can be set by anything with push access: "Users with push access in a repository
  can create commit statuses for a given SHA" (docs.github.com, commit statuses).

A prompt-injected maker, which is the threat model of §6 and §15, can clear its own gate.
Material-because: security (P4 "a maker never grades its own artefact" is unenforced).
Proposed-edit:
- The steward re-runs the fold itself (`review_records.py fold`) on the head SHA and ignores the status, which
  stays a projection for humans.
- A `downgraded`/`nonmaterial` decision on a blocking finding needs the raising lane's `accept` or the arbiter.
- Record as a residual that true authorship needs a second identity (a GitHub App, or LLM lanes running in CI with
  their own token).

### B7 — `merge-steward:` lines are accepted from any author, so a landing can be forged
Severity: B
Location: design.md § 4.2 (TEST-READY → CLOSE-READY and TEST-READY → REWORK-REQUIRED rows); § 10.8 H1
Target: §4.2 says "the steward's landing line exists and is not superseded by a `reverted` line".
Defect: today's code matches the line text from any commenter:
- `GitHubHost.issue()` keeps only `body` (`comments = [str(c.get("body") or "") …]`).
- `last_landing` returns the last `LANDED_RE` match.

On a public repository, an outsider can post `merge-steward: landed <any deployed trunk sha>` on an issue awaiting
verification. The next green verdict then verifies it, closing it when the checklist is complete, although its own
landing was never deployed. The same forged line placed after a `reverted` line would defeat the H1 fix the design
adds.
Material-because: security, plus wrong-behaviour (false closure).
Proposed-edit: add to §10.8: "H7. Machine lines are parsed only from the steward's identity per forge
(`github-actions[bot]` on GitHub, the `STEWARD_TOKEN` user on GitLab): the host keeps the comment author and
`last_landing` filters on it." List this under §18's Delivery row.

### B8 — Admission is keyed on provenance lines anyone can type
Severity: B
Location: design.md § 6 (Admission, first bullet)
Target: "Auto-admitted: issues authored by the operator, and agent-filed issues carrying the filing gate's
provenance lines."
Defect: every worker files as the operator's shared account, so "agent-filed" can only be recognised by the lines
themselves. An external reporter who writes `Origin: agent-sweep` / `Subject:` / `Filing-rationale:` is
auto-admitted, and their text then directs agents "that can push code and deploy to AWS". The same section intends
the opposite: "external reporters on a public repository … read-only mode".
Material-because: security.
Proposed-edit: "Auto-admitted: issues whose AUTHOR is on the project's allow-list (the shared account, the
operator). Provenance lines describe an admitted issue; they never admit one."

### B9 — One write-scoped token on every machine and runner, with no per-worker revocation
Severity: B
Location: design.md P3; § 5.1 heading ("one shared account"); § 15 (trust rules)
Target: P3 says "one shared tracker account".
Defect: every worker host, the dispatcher (which "needs only tracker read access" but in practice holds the same
file), the steward and every headless CI worker would carry the same credential in `credentials/github-pat.txt`,
with write on every project repository. One leaked laptop is write access to all projects. There is no revocation
of a single host and no audit trail per host. §15 hardens tools but not this credential.
Material-because: security.
Options:
1. **(Recommended)** One fine-grained PAT per host on the same account: scoped to the project repositories,
   expiring, revocable alone. This keeps P3's one login, so no new account is needed. The dispatcher gets a
   read-only token.
2. A GitHub App: a separate identity, check runs and a separate rate budget (B10, B6). It needs App setup per
   project.

### B10 — The shared account's content-creation limit caps the whole factory at a few issues per hour
Severity: B
Location: design.md § 19 item 3; § 8.2; § 5.1 step 4; review-protocol.md § 5.3
Target: "API rate limits. Many workers and a dispatcher polling one tracker, plus record comments, could hit
GitHub's and GitLab's limits".
Defect: the limit is documented, and it binds well before "many workers".
- GitHub's secondary limit: "no more than 80 content-generating requests per minute and no more than 500
  content-generating requests per hour" (docs.github.com, rate limits for the REST API).
- GitHub's best practice: "make requests serially instead of concurrently" and "Pause between mutative requests"
  (docs.github.com, best practices for the REST API).
- These limits are per account: every worker, every project and the operator's own UI activity share them.

An estimate from the design's own writes for one tier-M issue comes to about 160 content-creating requests. This
is an estimate from the mechanisms, not a measurement:
- claim, label and transitions, about 20;
- lease edits at about 20 checkpoints;
- per review round, about 6 lane envelopes, an aggregate, a resolution, 6 verifications, labels, a status and 6
  PR-review projections, about 23, times about 3 rounds;
- the implementation rounds, about 35;
- the steward and close-out, about 15.

That puts the account at roughly 3 tier-M issues per hour across all projects. A conductor posting a 6-lane round
in one burst, times a few concurrent conductors, reaches the 80-per-minute limit. GitLab's default note limit is
300 per minute per user (docs.gitlab.com, rate limit on notes creation), so GitHub is the binding forge.
Material-because: wrong-behaviour (throttled or banned writes: "Continuing to make requests while you are rate
limited may result in the banning of your integration").
Proposed-edit: add to §8.2 and §5.1:
- one comment per ROUND: the conductor posts the lanes' records in one envelope;
- PR projections off by default;
- lease renewal at most every N minutes, piggy-backed on verb calls;
- a host-wide write token bucket in the wrapper, with `retry-after` honoured.

Record per-identity tokens (App) as the route past one account (B9 option 2).

### B11 — The red verdict blames every landing since the last green deploy, against §10.5
Severity: B
Location: design.md § 10.5 ("Innocent in the window" row); § 18 (Delivery row)
Target: "Innocent in the window | stays in TEST-READY; the next green deploy containing it verifies it; no
rework, no re-landing".
Defect: today's `verify_issue` returns every issue whose landing the red deploy contains and that landed before
the red began. It adds `verification-failed` + `needs-rework` and releases the claim, with the text "Every issue
landed since the last green deploy is a suspect". `verdict` exempts only landings after `red_before`.
`clients/common/docs/delivery.md` §4 says the same. §18 lists only H1–H6, so the design keeps this behaviour:
- Innocents get `needs-rework` and are pulled FIRST (§14), before Track T has attributed anything.
- The order between the deploy's verdict job and the steward's attribution is unspecified.
Material-because: wrong-behaviour (rework of good changes; the cause C2 of
`docs/reports/session-endings-analysis-2026-11-01.md`).
Proposed-edit: add to §10.8: "H7b. On a red deploy the verdict marks no issue: it records `red-since` and hands the
window to Track T. Only Track T's culprit record returns an issue." List it under §18's Delivery row.

### B12 — The watcher closes verified issues itself, so CLOSE-READY never runs
Severity: B
Location: design.md § 3.1 (CLOSE-READY row); § 11; § 18 (Delivery row)
Target: §3.1 says "CLOSE-READY | Landed, deployed, smoke green on a commit containing the landing | close-out
team | closed (done)".
Defect: `verify_issue` on success with a complete checklist calls `self.host.issue_close(number)`. Close-out
therefore never happens: no temporary-resource clean-up, no learnings, no summary (U18). With open items it sets
`needs-closeout` instead, but that is not a stage either.
Material-because: wrong-behaviour (decision U18 not met).
Proposed-edit: §18 Delivery, Changed: "`verify_issue` never closes: on success it transitions TEST-READY →
CLOSE-READY (A1) and the close-out team closes."

### B13 — The `delivery-status` issue is closed, body-only and per repository, so it cannot carry escalations or be a `blocked-by` target
Severity: B
Location: design.md § 10.4 step 5; § 10.5 (Infra row); § 12.4 (table)
Target: §10.4 says "Escalate on the `delivery-status` issue". §12.4 says "the `delivery-status` issue, as ONE
record per root cause, deduped across issues; the affected issues get `blocked-by` it".
Defect: the design uses this issue for things it cannot do:
- `_status_issue` creates it and closes it at once ("closed on purpose: no worker ever selects it as work").
  `_write_status` rewrites only its body.
- `/get-guidance` collects open `needs-input` items (§12.7), so an escalation there never reaches the human.
- "ONE record per root cause … `blocked-by` it" has no target: one closed issue cannot be blocked-by per root
  cause, and a closed target never "reaches a named stage" for the dispatcher to clear.
Material-because: wrong-behaviour (escalations unseen; blocked issues never released).
Proposed-edit: in §12.4, replace "the `delivery-status` issue, as ONE record per root cause" with "ONE open
environment issue per root cause, labelled `env-incident` and `needs-input` for its owner; the affected issues are
`blocked-by` it and released when it closes". Keep `delivery-status` as the machine status record.

### B14 — Steward-opened revert and reland PRs never get PR CI on GitHub, and the revert is not train 1
Severity: B
Location: design.md § 10.4 step 3; § 10.7 (replay); revert-and-batching.md § 6.3 T2 and § 6.5 (reland row)
Target: §10.4 says "Revert with `git revert -m 1 <merge>`, opened at once as train 1 of the next batch".
Defect: on GitHub the steward runs with `GITHUB_TOKEN` (`github-merge-steward.yml.template`, which itself notes "a
GITHUB_TOKEN push starts none"). GitHub creates no workflow run from that token's events except
`workflow_dispatch` and `repository_dispatch` (docs.github.com, GITHUB_TOKEN). A revert or reland PR opened in the
tick therefore has no PR CI, so `head_ci` returns `"none"`. With the default `require_pr_ci: True`, `eligibility`
returns "wait" ("no CI has reported on its head") for ever: the revert never lands, and VBT never ends.

Ordering fails too. `plan()` sorts by `(p.enqueued_at, p.number)`, so a fresh revert queues behind every PR already
waiting.
Material-because: wrong-behaviour (Track T does not complete on GitHub).
Proposed-edit: add to §10.4 step 3: "The steward dispatches the revert's CI itself (`workflow_dispatch`, as for
trains), or a `revert`-labelled PR is exempt from `require_pr_ci` because its train CI is its CI. `plan()` orders
`revert` PRs first." Add both to §18 Delivery, Changed.

### B15 — The H1 fix supersedes a landing that is a batch tip and is not tied to a PR
Severity: B
Location: design.md § 10.8 H1; § 4.2 (TEST-READY → CLOSE-READY row); revert-and-batching.md § 6.6 H1 (Fix)
Target: revert-and-batching.md §6.6 says "a `merge-steward: reverted <landing> in <sha>` line supersedes the
landing, so `last_landing` returns None until a newer landing line appears".
Defect: two facts make the fix fail for an issue delivered by two PRs:
- `land()` records every PR of a batch with the batch tip: `after_landing(number, target.sha, …)`, line
  `merge-steward: landed {sha} (PR #{number} …)`.
- `last_landing` takes the last match regardless of PR.

Take PR a, the culprit, landed in batch 1, and PR b landed in batch 2 after the revert. b's line is newer, so
`last_landing` returns b's landing. The next green deploy verifies and closes the issue while a's change is
reverted. That is H1 again.
Material-because: wrong-behaviour (a reverted culprit closed).
Proposed-edit: replace H1's fix with: "`reverted` names the PR and its merge commit (`reverted PR #a <merge> in
<revert>`); the predicate holds only when EVERY PR of the issue has a landing that no later `reverted` for that PR
supersedes, and the line is written when the revert LANDS."

### B16 — Attribution step A3 names the wrong culprit when several landings change the failing resource
Severity: B
Location: revert-and-batching.md § 6.4 A3; design.md § 10.4 step 2.2
Target: revert-and-batching.md §6.4 says "The first k whose step changes R, or removes the export or permission
the reason names, is the culprit. Confidence: high."
Defect: the steps that pick the wrong landing, each with "high" confidence:
- If landing 1 changes R harmlessly (a tag, a memory size) and landing 3 changes R's image or code, A3 reverts
  landing 1.
- If R fails because of a change outside its template (an IAM policy, a security group or a parameter in another
  stack), and the reason does not name it, A3 blames whichever step first touched R.

A wrong revert then charges the innocent's lifetime counters ("never reset by a worker", §13). §10.4 step 4's
"same signature" is undefined.
Material-because: wrong-behaviour (wrong revert and blame, presented as high confidence).
Proposed-edit: "If exactly one step changes R (and none changes its dependency closure: referenced roles,
policies, imports), that step is the culprit, confidence high; if several do, revert those steps as a suspect set
(A6). A wrong attribution refunds the counters it charged. Signature = (stack, logical id, resource status reason
with ids masked)."

### B17 — Track E's auto-restore has no guard for stateful changes and trusts an unprotected cache
Severity: B
Location: design.md § 10.3 step 4; § 10.6 ("The cache"); § 10.7
Target: §10.3 says "it redeploys only the stacks whose template changed … with `cdk deploy --app <cached assembly>
<stack> --exclusively`".
Defect: two gaps.

First, the change checks run on forward changes only. §10.7's checks (stateful replacement and deletion, expand
and contract) run in the train, and H5 extends them to reverts, but not to the RESTORE's change set. Restoring an
older template:
- removes resources the new template added. A named resource with a retain policy is orphaned, and the reland's
  create then fails on the existing name;
- puts old code on data a new migration already changed;
- misclassifies, at step 5 ("Last-good also red? Then the cause is infra"), a culprit with persistent side effects
  as infra, with "nobody … blamed".

Second, the cache. The S3 cache feeds a deploy with no review. Whoever can write it chooses what the restore
deploys, and neither write access nor integrity is specified.
Material-because: data-loss and security.
Proposed-edit:
- Step 4: "Before redeploying, run the stateful replacement/deletion check on the restore's change set; a restore
  that deletes or replaces a stateful or retained resource stops and becomes an infra event with the owner."
- §10.6: "Only the deploy job's role writes the cache; the trunk verdict records each assembly's SHA-256 and the
  restore verifies it."

### B18 — Triage sets the tier and risk tags alone, and they decide every later panel
Severity: B
Location: design.md § 3.2 (tier row); § 4.2 (START → SPEC-REQUIRED); § 7.2 (START row); § 7.3
Target: §3.2's tier row says "select the team, the checkers and the budgets | triage | re-tier, with a recorded
reason".
Defect: an under-tiered or under-tagged issue silently loses the M/L lanes, the threat model and the IaC gate
(§7.3), and nothing checks the call. START's LLM checkers are the duplicate-confirmer and, for L only, scope.
Downward re-tier is not forbidden. P4 holds only for whatever triage chose to require.
Material-because: security, plus wrong-behaviour (P4 unmet for mis-tiered work).
Proposed-edit: add to §4.2's START → SPEC-REQUIRED row: "a deterministic floor (footprint heuristics: IaC/auth/
migration paths ⇒ tags; footprint breadth ⇒ minimum tier) that triage may raise but not lower; the tier and tags
are re-derived from the spec's declared footprint at SPEC exit and only raised."

### B19 — The acceptance-test freeze can be bypassed without touching the test files
Severity: B
Location: design.md § 4.2 (IMPLEMENTATION-READY → TEST-READY row); § 9 ("Acceptance tests at spec time")
Target: "the acceptance tests unchanged since S (`git diff S..HEAD` over their paths is empty)".
Defect: the implementer can weaken the finish line through files outside "their paths": `conftest.py` fixtures,
test helpers, pytest configuration (`pyproject.toml` `[tool.pytest.ini_options]`), markers and collection hooks.
The diff stays empty. §9's "maker ≠ checker at the level of the issue" fails.
Material-because: wrong-behaviour (a vacuous green).
Proposed-edit: "the test tree as of S, run against the implementation at H (checkout S's tests, conftest and test
configuration over H's code), passes; any change to files the acceptance tests import or are configured by needs
a newer `spec-approved`."

### B20 — CLOSE-READY removes only resources the agents chose to record
Severity: B
Location: design.md § 11 item 1; § 4.2 (CLOSE-READY → closed)
Target: §11 says "Every team records what it creates in a temporary-resource ledger on the issue … CLOSE-READY
removes exactly those."
Defect: the predicate cannot see an unrecorded resource. The motivating example (chess #1130's 1,000 staged
uploads) is exactly a resource nobody recorded, so the exit check passes on the failure it was designed to catch.
Material-because: wrong-behaviour (U18 not met).
Proposed-edit: "Every temporary resource is tagged `factory-issue=<repo>#<n>` (or named with that prefix where
tags do not exist); CLOSE-READY queries by the tag in addition to reading the ledger, and the predicate requires
the query to be empty."

### B21 — The predicates assume the steward and the watcher, and no mode is mapped otherwise
Severity: B
Location: design.md § 4.2 (IMPLEMENTATION-READY → TEST-READY, TEST-READY → CLOSE-READY rows); § 2
Target: "the steward accepts the PR (`check-pr` exit 0 …)" and "a deploy + smoke run concluded green on a commit D
that contains the landing".
Defect: `merge_steward.py` supports `VERIFICATION_MODES = ("watcher", "session", "none")` and a direct merge mode
(`record-landing`). This repository is "merge mode direct (no `config/delivery.json`, no merge steward)"
(CLAUDE.md) and has no deploy. In direct mode `check-pr` has no queue, and with `verification: none` no deploy run
exists, so TEST-READY → CLOSE-READY can never hold.
Material-because: wrong-behaviour (projects in those modes stall in TEST-READY).
Proposed-edit: add to §4.2 a per-mode note: direct mode uses `record-landing` as the landing line; `verification:
none` makes "the landing on trunk plus green trunk CI" the TEST-READY → CLOSE-READY predicate. Alternatively,
state that factory mode requires `merge: steward`.

### B22 — Draft PRs, on which the spec hand-off relies, do not exist for private repositories on GitHub Free and Pro
Severity: B
Location: design.md § 9 ("Where it lives")
Target: "the spec and the acceptance tests are committed on the pushed issue branch, with a DRAFT PR … the
steward refuses drafts, so draft means not ready."
Defect: GitHub: draft PRs are "available in public repositories with GitHub Free and GitHub Free for
organizations, GitHub Pro, and legacy per-repository billing plans, and in public and private repositories with
GitHub Team and GitHub Enterprise Cloud" (docs.github.com, pulls). A private repository on Free or Pro cannot
open the draft. GitLab draft MRs are on every tier.
Material-because: wrong-behaviour (the §9 hand-off fails on a supported configuration).
Proposed-edit: "…with a PR that carries `do-not-merge` (the steward's `hold_label` waits on it, `eligibility`) and
is a draft where the forge supports it; readiness is the label, not the draft flag."

---

## C findings

- **C1.**
  - Target: design.md §4.2 (IMPLEMENTATION-READY → TEST-READY), "`enqueue --allow-pending` admits a PR whose own
    CI is still running".
  - Reason: `check(allow_pending)` admits ANY "wait" verdict (`allow_pending and verdict == "wait"`). That
    includes `hold`, an unlanded dependency, "not approved" and CI `"none"`.
  - Proposed change: say "admits a PR whose only unmet clause is pending CI", and make `check` test the reason.
- **C2.**
  - Target: design.md §4.2, "PR CI green on head H … (or pending, see below); all required implementation checkers
    report on H".
  - Reason: the adversarial verifier "takes the CI run for the pushed SHA as the whole-suite verdict", so it
    cannot report while CI is pending. The two clauses conflict.
  - Proposed change: the verifier's verdict on H is required before the transition. Pending CI applies only to
    re-enqueue after a rebase that changes no file.
- **C3.**
  - Target: design.md §10.4 step 2.2, "(the steward's train branches already are those states)".
  - Reason: `land()` calls `delete_trains(trains)` after landing. The states survive as trunk's first-parent
    `--no-ff` merges, but the cached assemblies exist only per DEPLOYED SHA (§10.6). Each step needs a synth, and
    the synth time is unbudgeted.
  - Proposed change: "the window's first-parent merge commits are those states; the attributor synthesizes each
    (runs on CI, bounded)".
- **C4.**
  - Target: review-protocol.md §5.1, "`list-issue-comments --after-id`", and §5.2, "kept in
    `resume_state.md`".
  - Reason: the GitHub list endpoint takes only `since`, `per_page` and `page` (repo api-reference). `since` is
    updated-time, so every lease edit re-surfaces the claim comment. A cursor in a machine-local file means every
    new worker full-scans the issue.
  - Further reason: GitHub disables commenting on issues past 2,500 comments. An observed 403, "Commenting is
    disabled on issues with more than 2500 comments", is quoted in public issue ram0verflow/ram0verflow#7.
  - Proposed change: implement `--after-id` as paging plus a client-side filter, store the cursor in the issue's
    audit trail, and cap comments per issue.
- **C5.**
  - Target: design.md §5.1, "comment ids are assigned by the server", and §8.1, "folding the records in comment
    order".
  - Reason: today's GitLab host orders notes by `created_at` (`notes?sort=asc&order_by=created_at`), not by id.
    Two notes in the same second can fold in different orders on the two forges.
  - Proposed change: fold by id on both forges, explicitly.
- **C6.**
  - Target: design.md §13 cost budgets and §19 item 5.
  - Reason: thresholds.md's costs come from single-session flows with "~97 % cache reads" (cache read weight 0.1
    against cache write 1.25). Each hand-off and each cross-session lane starts cold, so budgets calibrated on that
    data undercount the new flow.
  - Proposed change: run budgets report-only for the first N issues per tier, then recalibrate.
- **C7.**
  - Target: design.md §7.3, "Every issue | … test-architect, adversarial-verifier, the retro checker".
  - Reason: `clients/claude/rules/proportionality.md` gives tier S "ONE combined pass (`spec-review-agent`, all
    lenses)". §18 does not list proportionality.md under Changed.
  - Proposed change: list it, or keep S at one combined pass plus the verifier.
- **C8.**
  - Target: design.md §11 item 3, "ONE rolling learning-batch issue", and traceability.md A5, "no open issue in any
    stage (all closed)".
  - Reason: the rolling issue keeps the backlog permanently non-empty. Its own close-out produces learnings that
    feed it, and it accumulates comments toward the per-issue cap (C4).
  - Proposed change: give A5 an exception for the batch issue, close the batch issue per PR and open the next,
    and exempt its own close-out from learning capture.
- **C9.**
  - Target: design.md §4.2, "START → split | … the parent's stage is derived from its children".
  - Reason: no writer or label rule is given for the derived stage, and none says when the parent closes.
  - Proposed change: the parent gets `blocked-by` all children and stays in START with a `split` flag. It closes
    administratively when the last child closes.
- **C10.**
  - Target: design.md §3.2, "`blocked-by #N` … cleared by the dispatcher, when #N gets there".
  - Reason: three cases are undefined:
    - cycles;
    - a target closed administratively, which never "gets there";
    - GitLab blocking links, which are Premium and Ultimate. Only "relates to" is Free (docs.gitlab.com, related
      issues).
  - Proposed change: a cycle is a triage error. A closed target releases the block with a comment. The Free tier
    uses the comment form.
- **C11.**
  - Target: design.md §5, the lease comment plus the `claimed` label.
  - Reason: `verify_issue` and `_return_issue` release the OLD claim (`issue_release_claim`: the in-progress label
    and assignees). The design does not say who removes the lease comment and the `claimed` label on those paths.
  - Proposed change: one release verb that removes both. The steward and the watcher call it.
- **C12.**
  - Target: design.md §12.3, "a separate agent tries to answer it … Only these pass".
  - Reason: a false negative on "irreversible" or "sensitive" lets an agent answer a question the human had to
    answer.
  - Proposed change: a deterministic always-ask list (IAM grants, deletions, production, credentials) that the
    checker cannot answer.
- **C13.**
  - Target: design.md §6, "the triage record says what the issue asks, so the human admits it in seconds".
  - Reason: a read-only triage agent reading injected text can paraphrase a malicious ask benignly.
  - Proposed change: the admission view shows the verbatim body (fenced) next to the paraphrase.
- **C14.**
  - Target: design.md §4.2 (SPEC-REQUIRED → IMPLEMENTATION-READY), "a `spec-approved` record … is written".
  - Reason: writing the record is the transition's effect, not a precondition, and its writer is unnamed.
  - Proposed change: move it to §4.4 as a side effect written by the verb.
- **C15.**
  - Target: design.md §7.2 (TEST-READY row), "failure attributor for smoke failures (CloudWatch and CloudTrail
    MCP, read-only)".
  - Reason: anyone who can make the dev service log text can steer attribution, and attribution drives a trunk
    revert.
  - Proposed change: the attributor's output alone never reverts. It may only rank inside the A5 suspect set, and
    the logs are fenced as data.
- **C16.**
  - Target: design.md §3.4 item 3, "No agent sets a stage label by hand".
  - Reason: humans with write access can, and the reconciler repairs only zero or two labels. A hand-set single
    label is taken as truth.
  - Proposed change: the reconciler also compares the label with the last audit line, and corrects or records a
    human override as `factory: stage … by <login>`.
- **C17.**
  - Target: design.md §16, "the lease reaper replaces it".
  - Reason: on Kiro, lease renewal "at every checkpoint" is the model's own action.
  - Proposed change: renew in the wrapper on every verb call (B1 option 2), not in prompts.
- **C18.**
  - Target: design.md §10.4 step 3, "Landings never pause".
  - Reason: until the revert lands, every deploy of a newer trunk still contains the culprit and re-breaks the
    environment. Each one costs a restore (§10.6: 5–30 min).
  - Proposed change: `deploy_guard` skips trunk commits that contain an attributed culprit without its revert.
- **C19.**
  - Target: design.md §10.7, "about 2.5 h red".
  - Reason: the replay assumes the revert lands on train CI alone, with no lost tick. On GitHub it needs B14's
    fixes, and otherwise a PR CI plus a train CI.
  - Proposed change: state the assumptions next to the figure.
- **C20.**
  - Target: design.md §5.3, "takes all their claims, all or nothing".
  - Reason: two group claimers that each take half, both release and both retry, can livelock.
  - Proposed change: acquire in ascending issue number, with randomised back-off.
- **C21.**
  - Target: design.md §13 resets, "never by a worker: queue returns, culprit failures, rework, claims and cost".
  - Reason: the counters live in comments the shared account can edit or delete, and the claim protocol itself
    deletes comments ("The loser deletes its comment"), which also removes §17 metrics.
  - Proposed change: the fold rejects edited record comments (`updated_at != created_at`), except leases. Counters
    are derived from the verb's audit lines.
- **C22.**
  - Target: design.md §8.4 step 3 and §19 item 7, the arbiter.
  - Reason: the arbiter's decision has no checker.
  - Proposed change: each affected lane's deterministic checks are re-run against the chosen option. A
    legal/security-precedence decision becomes a `needs-input` approval.
- **C23 (outside the reviewed set).**
  - Target: the main checkout's `docs/`. `git status` shows two untracked files there: a keynote deck and a gap
    analysis.
  - Reason: the repository is public, and an accidental `git add docs/` would publish third-party material.
  - Proposed change: move both outside the repository, or add them to `.gitignore`.

## D findings

- **D1.**
  - Target: design.md §2, "Delivery labels: `queue`, `queue-failed`, `queue-conflict`, `needs-rework`,
    `awaiting-verification`, `verification-failed`, `needs-closeout`, `reverify`".
  - Reason: `clients/common/docs/delivery.md` §6 also lists `queue-retried`, `do-not-merge`, `verified` and
    `delivery-status`.
  - Proposed change: complete the list.
- **D2.**
  - Target: design.md §2, "the `delivery-status` issue".
  - Reason: delivery.md §4 says "ONE open issue labelled `delivery-status`", but `_status_issue` keeps it closed
    (`STATUS_PREAMBLE`: "kept CLOSED on purpose"). This is an existing doc/code deviation.
  - Proposed change: correct delivery.md when the design is implemented.
- **D3.**
  - Target: revert-and-batching.md §6.5, "LANDED → **REWORK-REQUIRED**".
  - Reason: decision U7 says "no separate LANDED state".
  - Proposed change: write "TEST-READY (landed)".
- **D4.**
  - Target: design.md §4.2 (CLOSE-READY → closed), "every laundry-list item has a disposition".
  - Reason: "laundry list" is defined nowhere in the set.
  - Proposed change: define it, or name the list meant (the residuals, the ledger rows).

---

## Claims about the existing code: checked

True as stated:
- §5.4, all four bullets:
  - `_claim_is_held_by_another` and `cmd_start_issue` (read, `--strict` refusal, write, re-read) in `claim.py`.
  - The orchestrator's SELECT takes the `mkdir` lock and then `issue start` without `--strict`.
  - `cmd_release_issue` writes `labels` as the whole set minus `in-progress`.
- §2, "ONE TICK", trains as `git merge --no-ff <head>`, and culprit-only blame.
- §10.8 H1: `verdict` uses ancestry of the last landing line.
- §10.8 H4: the deploy template has one concurrency group per environment, and a newer pending run replaces an
  older pending one.
- §14, "0 of 10 closed" (`docs/reports/session-endings-analysis-2026-11-01.md`).
- §15: both setup prompts use `@latest`, and `setup-claude.txt` auto-allows `mcp__awslabs.aws-api-mcp-server__*`
  with `READ_OPERATIONS_ONLY`.
- §18: `spec-review-agent.md` repeats a paragraph, and `dead-code-language-matrix.md` lists `ts-prune` as
  required.
- §2: `src/hooks/red_for_right_reason.py` exists.
- §8.2: "A personal token can set a commit status" is true, but anything with push access can set it (B6).

Not true, or incomplete:
- §2 reuses "the `delivery-status` issue" as if it were open. The code keeps it closed (B13, D2).
- §10.4 says the train branches "already are those states". The code deletes them at landing (C3).
- §18 treats the steward and the watcher as reused except H1–H6. The code also:
  - blames every landing since the last green deploy (B11);
  - closes issues directly (B12);
  - writes the batch tip as every PR's landing (B15);
  - ignores comment authors (B7);
  - needs PR CI that a `GITHUB_TOKEN` PR never gets (B14).
