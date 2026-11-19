# Adversarial review of the factory state-model design, revision 4 (2026-11-19)

**Verdicts on the 16 open round-3 items (review-response.md Part 0):** 15 verified, 1 partly (aM5), 0 not-fixed,
0 disputed.

**New findings on revision 4's additions (P1–P15):** A 0, B 6 (P1–P6), C 8 (P7–P14), D 1 (P15).

OPEN ITEMS: 16

---

## Scope

**Subject.** Revision 4 of the factory state-model design, branch `docs-factory-state-model-design` at commit
`049a047`. Read:

- the full diff of `design.md` and `decisions.md` against revision 3 (`5dcc08f`), with the surrounding sections;
- `review-response.md` Part 0 and "What the next review should check (revision 4)".

`traceability.md` was not reviewed. The review ran in a session independent of the designer's, from a detached
worktree, read-only.

**Product code read to check the design's claims:**

- `src/payload/scripts/merge_steward.py`:
  - `Git.run` (`check=True` raises `GitError`);
  - the train push in the train builder;
  - `enqueue` and `trigger_tick`;
  - the deploy dispatch;
- `src/payload/scripts/github_wrapper.py`: `steward_delegate` (the steward runs with the wrapper's token);
- `templates/ci/github-merge-steward.yml.template`: header, triggers, tick-job permissions;
- `templates/ci/github-steward-wake.yml.template`, in full;
- `templates/ci/github-deploy.yml.template`.

**Platform facts** come from vendor documentation, the vendors' issue trackers and `docs/api-reference/`, each named
where it is used.

**Ids.** Round-3 findings are cited as `aM<n>`, the designer's naming in Part 0 (they were `M<n>` in the round-3
report).

**Operator decisions respected.**

- **U21:** equal scrutiny.
- **U24:** the agents keep posting as the operator's account. Only whether §15.2 states the residual truthfully is
  tested here.

**A disclosure.** P3 faults a mechanism that my own round-3 report proposed (aM9, the folded state in the claim
commits). P1 is a defect revision 3 already had and round 3 missed: the predicate has no fact for re-landing a
reverted PR.

---

## Summary

Revision 4 applies every round-3 edit. What it adds opens new neighbouring paths, mostly where a new rule meets code or
platform behaviour the design does not mention:

- **The revert fact has no reland.** Once a PR's landing is reverted, the closing predicate can never hold for its
  issue, not even after the rework or the steward's own reland lands (P1).
- **"Separately started" cannot be checked.** A verdict carries no proof that it came from the separately started
  session. The exits that a later worker pickup closes cannot tell it from an in-session verdict (P2).
- **The folded state is written by the maker.** The cache that spares a full re-fold is written by the releasing
  holder, and every later reader trusts it, including the separately started checkers (P3).
- **R57 cuts the steward's wake-ups.** Without "Actions: write", `enqueue-pr` can no longer dispatch the steward, and
  the template's `steward-wake` job breaks R57's own rule (P4).
- **R57 leaves workflow-file changes with no landing path.** The steward's token cannot push them, and the ruleset
  blocks the operator's token. A queued one makes every tick fail (P5).
- **On GitLab, the worker tokens can read the steward's token.** They are the operator's account, which can read the
  protected variable and change the protection (P6).

### Answers to "what the next review should check (revision 4)"

| Item | Answer |
|---|---|
| the `checker-requested` queue | starts the checkers. Their verdicts cannot be told apart from in-session ones (P2), and they read a maker-written folded state (P3) |
| the forms the recorder executes, and the re-spec edge | they execute. The edge's side effects on `ci-pending`, `checker-requested` and the open PR are not stated, and a `/stage` on TEST-READY does not dequeue (P8). `/amend` text is outside the ask's hash (P9) |
| the `/get-guidance` mark gate | session-scoped, not answer-scoped; §15.2 overstates it (aM5 partly) |
| content-keyed revert facts | no reland fact; a revert of a revert is read as a revert; the CLOSE-READY window (P1). False positives (P7) |
| the dispatched-run pin | the pin holds. A skipped or refused deploy that "concludes failure" must not count as red (P10); `return_run_details` and the API version (P15) |
| the human-flag label gate | holds for add and remove. Labels set inside create and update calls, and the production priority path (P11) |
| no worker-writable path to a write token | GitHub's workflow path is closed. Open: the steward's wake-ups (P4); workflow-file landings (P5); GitLab (P6); scripts the write-token workflows run, and other default-branch workflows (P12) |

---

## 1. Verdicts on the round-3 items

| Id | Verdict | Where revision 4 fixes it | Note |
|---|---|---|---|
| aN7 (rest) | verified | §3.5 "no worker-writable path to a write token": no Workflows or Actions-write on worker tokens; write-token workflows on the default branch only; branch code `contents: read`; §10.8 H7 "pushed by GitHub Actions"; §15.2 | The rule's own neighbours: P4, P5, P6, P12 |
| aM1 | verified | §3.2 `checker-requested:<lane>`; §14 lane row; §8.5 table with START exits and the recorded trade-offs; §4.1 and P4 "where §8.5 names one" | Binding a verdict to its session: P2 |
| aM2 | verified | §10.4 step 3 content-keyed `Steward-Reverts`; §4.2 the "revert outside Track T" return and the reopen; §19 item 13 | Lifecycle: P1; false positives: P7 |
| aM3 | verified | §4.2 (a) the dispatched run id and sha, or a push run's `head_sha`, and (b) job conclusions with no restore step; §10.3 restored and skipped runs conclude `failure`; §10.8 H13 | P10, P15 |
| aM4 | verified | §3.2 forms for `hold`, `priority`, `admitted`, `tamper`; §8.2 the wrapper refuses agents' label writes; §4.4 the dispatcher reverts unbacked ones; §15.2 item 1 | P11 |
| **aM5** | **partly** | §8.3 the fold checks every cited form; several forms per comment; §12.9 the `UserPromptSubmit` gate, Kiro prints the lines, the digest lists the answers | What is left: see §2 |
| aM6 | verified | §8.3 the recorder executes every form; §4.2 the re-spec edge; `/stage` on TEST-READY as a steward request; §4.3 `/amend` refused from TEST-READY on | P8, P9 |
| aM7 | verified | §6.3 `admitted {ask_hash}`; §4.3 every pickup compares | — |
| aM8 | verified | §4.2 and §14: every tick re-derives both exits | — |
| aM9 | verified | §5.1 and §8.2 the folded state in the claim commits; `since` | Trust in the cache: P3 |
| aM10 | verified | §5.1 renewal on every wrapper call and from the commit hook; L capped at 90 minutes | P13 |
| aM11 | verified | §5.1 the `pre-push` fence; §19 item 2 | — |
| aM12 | verified | §5.4 the four steps; the reconciler's recovery | Ordering window: P14 |
| aM13 | verified | §14 every row needs "no claim"; the re-fold row; `/clear-tamper`; `env-incident` "no worker queue" with the recorder executing forms on them | — |
| aM14 | verified | §3.5 and H11: setup and update check with the operator's token; the steward detects at revert time | — |
| aM15 | verified | §4.5 the watcher holds `issues: write` and sets no flags; the steward applies `blocked-by`; §8.5 REWORK row | — |

---

## 2. The remainder of aM5 (B): the `/get-guidance` mark is session-scoped, and §15.2 says "or otherwise"

- **Location:** §12.9 step 4; §8.3 "The fold checks every form a record cites"; §15.2 residual item 1 and "What limits
  it".
- **Target quote:** "The marking and label gates mean that an agent working through the wrapper can no longer
  impersonate the operator, by accident or otherwise".
- **Defect.** The gate proves less than §15.2 claims:
  1. **It is held for the whole session.** "The wrapper accepts that mark only in a session in which the human typed
     `/get-guidance`." Once the human has typed it, every later agent write in that session can carry the mark: a
     later turn about other work, or a subagent the session dispatches.
  2. **The answer text is the model's.** Within the command, the model composes the form lines "quoting the human's
     words". The mark proves that a human started the command, not that the human gave this answer.
  3. **An agent can submit the prompt.** "An agent cannot type a user prompt" is not shown. Any agent with a shell can
     start `claude -p "/get-guidance"`, whose prompt it wrote. Whether `UserPromptSubmit` fires in print mode is
     reported both ways on the vendor's tracker:
     - anthropics/claude-code #100695: a `UserPromptSubmit` hook blocked a print-mode prompt, 9 of 9 runs;
     - anthropics/claude-code #71022: per-turn hooks did not fire in `claude -p`.

     So the gate rests on undocumented behaviour, either way.

  §12.9 itself says the human authorship "is still not provable". §15.2's "or otherwise" contradicts that.
- **Material-because:** §12.3 reserved decisions and the always-ask list (§12.4); U24, the residual at its true size.
- **Evidence:** design.md §8.3, §12.9, §15.2; the two issues named above.
- **Proposed edit (recommended first):**
  1. **Scope the mark to the answer.**
     - The hook records the turn in which the human typed `/get-guidance`. The wrapper accepts the mark only during
       that turn, from the main agent, and only for issues the command listed in that turn.
     - The posted comment names the turn. The digest shows each such answer next to the question it answers.
     - §15.2 drops "or otherwise". Item 1 adds: "an agent that runs inside a `/get-guidance` turn, or starts one
       headlessly, can post a marked answer".
  2. Use the Kiro path on every client: `/get-guidance` prints the form lines and the human posts them. Only unmarked
     forms count, and the gate and its hook go away.

---

## 3. New findings

### P1 (B): the revert fact has no reland, a revert of a revert is read as a revert, and CLOSE-READY has no return

- **Location:**
  - §4.2 TEST-READY → CLOSE-READY and TEST-READY → REWORK-REQUIRED;
  - §10.4 step 3 ("The revert fact is keyed on content");
  - §10.5 rows "Culprit" and "Reverted as an ambiguous suspect";
  - §10.8 H1;
  - §4.5 Steward row.
- **Target quote:** "The predicate holds only when EVERY PR of the issue has a landing that no later revert of THAT PR
  supersedes." (§10.8 H1)
- **Defect:**
  1. **No reland fact.**
     - Culprit: "The rework branch starts with a revert of the revert". A merged PR cannot land again, so the rework
       lands as a new PR. The culprit's first PR still has a superseded landing, and "EVERY PR of the issue" can then
       never hold. The issue strands in TEST-READY after its rework lands.
     - Ambiguous suspect: "The steward relands it itself". No trailer names that reland as a new landing of the
       suspect's PR, so its issue strands too.
  2. **A revert of a revert is read as a revert.**
     - A reland (or a rework PR that is only the revert of the revert, as when the cause turns out to be environment)
       is "exactly the inverse" of the revert's steward merge.
     - So the content key writes `Steward-Reverts: PR #<revert PR>` and calls it a revert outside Track T.
     - Where the steward's revert PR references the culprit's issue, that issue is sent back to REWORK-REQUIRED at the
       moment its fix lands. Revision 3 keyed the fact on steward-opened reverts and could not do this.
  3. **The CLOSE-READY window.**
     - The return covers TEST-READY ("TEST-READY → REWORK-REQUIRED") and closed issues ("An issue already closed when a
       revert of its PR lands is reopened"). An issue in CLOSE-READY when the revert lands gets neither.
     - CLOSE-READY → closed checks no revert, so the issue closes with its code gone: H1's failure.
     - The reopen itself (closed → REWORK-REQUIRED) is not an edge in §4.2, and the Steward row's "May call" does not
       list it.
- **Material-because:** TEST-READY → CLOSE-READY for every culprit and every ambiguous suspect, the main path of
  revert-first (§10, U20); H1 and B15.
- **Evidence:** design.md §4.2, §4.5, §10.4 step 3, §10.5, §10.8 H1.
- **Proposed edit (recommended first):**
  1. **Each PR's state is the last of its facts, and every affected stage reads it.**
     - The steward writes `Steward-Relands: PR #<k> <revert merge sha>` when it lands a PR that contains a commit
       exactly inverting a `Steward-Reverts` merge. That covers the steward's own reland and the rework's first commit.
     - A PR's state is the last of its `Steward-PR`, `Steward-Reverts` and `Steward-Relands` facts.
     - The content key excludes merges that are themselves `Steward-Reverts` merges: their inverse is a reland.
     - The predicate requires every PR of the issue to be in state landed or relanded, or to be named in a rework
       record as replaced by a later PR of the issue.
     - A revert fact returns the issue from TEST-READY, CLOSE-READY or closed. Add CLOSE-READY → REWORK-REQUIRED and
       closed → REWORK-REQUIRED (steward) to §4.2 and the Steward row, and have CLOSE-READY → closed re-check that no
       revert has landed.
  2. Count only the PRs queued in the current TEST-READY visit. `enqueue` then refuses a culprit's rework PR whose
     first commit is not the exact revert of its revert. The CLOSE-READY edge and the reopen edge of option 1 are still
     needed.

### P2 (B): a verdict carries no proof that it came from the separately started checker

- **Location:** §8.1 the `actor` fields; §8.5; §4.1; §4.2 worker edges START → SPEC-REQUIRED, START → closed,
  SPEC-REQUIRED → IMPLEMENTATION-READY and CLOSE-READY → closed; §4.5 Checker-lane row.
- **Target quote:** "Where §8.5 names a separately started checker for the exit, one of those verdicts comes from it."
- **Defect:**
  - §8.5 defines the separately started checker by how it ran: "a session the dispatcher starts, which holds a
    `verify` claim and posts its own records".
  - A record carries only `actor.worker`, `actor.agent` and `actor.role` (§8.1), all written by whoever posts it.
  - For the verifier, binding is by caller: the verifier calls IMPLEMENTATION-READY → TEST-READY itself, under its
    `verify` claim, and the verb checks its fence.
  - For every exit `checker-requested` starts, the lane only posts a verdict, and a later worker pickup calls the edge.
    The verb then counts the separately started verdict from records alone.
  - An in-session test-architect verdict with the same role, posted by the maker's conductor, looks the same.
  - So "one of them is a separately started spec checker" is satisfied by the conductor's own bytes. That is the gap
    §8.5 exists to close (aN9).
- **Material-because:** P4 and §8.5, and §4.1's checker clause for the START, SPEC and CLOSE exits.
- **Evidence:** design.md §4.1, §4.2, §4.5, §8.1, §8.5, §14.
- **Proposed edit (recommended first):**
  1. **Stamp records with the claim they were posted under.**
     - The wrapper writes into every record the caller's claim kind and fencing token (the held commit's SHA).
     - The fold counts a verdict as separately started only when that held commit is a `verify` commit of that lane in
       the claim ref's history, and the record was posted during that hold.
  2. **The lane calls the edge itself, as the verifier does.** The separately started checker evaluates the predicate
     and calls the exit under its `verify` claim, and §4.5's Checker-lane row lists those exits. This also saves the
     extra worker pickup after every requested check.

### P3 (B): the folded state is written by the releasing holder and trusted by every later reader

- **Location:** §5.1 "Both carry a tree with the folded state at the cursor"; §8.2 "Reading"; §8.5; §8.6.
- **Target quote:** "A new holder reads that state, then fetches only the comments updated since the last fold's
  time".
- **Defect:**
  - The folded state (open findings, verdicts per SHA, pending questions) is written by the release verb of the holder
    that releases, which is usually the maker.
  - Every later holder starts from it and "neither re-folds from the first record nor misses an edit". That includes
    the separately started checker and the verb that evaluates the next predicate.
  - A maker session that drops an open blocking finding from the state, by a fold bug or a conductor rewrite, hides it
    from every later reader. The finding's comment is unedited, so `tamper` never fires, and `since` never returns it
    again.
  - §8.6's steward fold before landing is "the same fold" and is not said to start from the first record. Exits before
    TEST-READY have no such check at all.
  - This re-opens, through the cache, the hole §8.5 closes for the records themselves. (The cache was my own round-3
    proposal.)
- **Material-because:** §4.1's "no blocking finding is open"; P4 and §8.5.
- **Evidence:** design.md §5.1, §8.2, §8.5, §8.6.
- **Proposed edit (recommended first):**
  1. **The cache is an optimisation for pickups only.**
     - The verb re-folds from the first record whenever it evaluates an exit predicate.
     - The separately started checkers re-fold from the first record too. They are started rarely, so the cost is
       bounded.
     - An ordinary pickup may start from the cache.
     - §8.6 says the steward's fold before landing starts from the first record.
  2. Keep the cache everywhere, but store with it a digest of the record ids and bodies it folded. Every reader then
     re-reads that id set, a full fetch without the fold, and compares the digest.

### P4 (B): R57 cuts both event-driven steward wake-ups

- **Location:** §3.5 "Both: no worker-writable path to a write token"; §15.2 bullet "The worker tokens also lack
  'Workflows' and 'Actions: write'"; R57.
- **Target quote:** "the worker tokens lack 'Actions: write', so no worker dispatches a workflow, including the
  steward's".
- **Defect:**
  1. **The enqueue wake-up.**
     - `merge_steward.py` `enqueue` ends with `trigger_tick`, a `POST /actions/workflows/{steward}/dispatches`.
     - It runs with the wrapper's token: `steward_delegate` hands "this wrapper's own token" to the steward. That is the
       worker's token, and dispatching a workflow needs "Actions: write".
     - Under R57 every enqueue's tick trigger therefore fails. The code then says "the scheduled tick will pick the PR
       up".
  2. **The train wake-up.**
     - `github-steward-wake.yml.template` is a job with `permissions: actions: write` that runs on train refs
       (`startsWith(github.ref_name, 'steward/train-')`), not on the default branch.
     - That breaks R57's "every factory workflow that holds a write token runs only on the default branch". Applying
       the rule removes the job.
  3. **What is left.** The template header calls the schedule "only the safety net, and a weak one: GitHub delays and
     drops scheduled runs (8 of about 86 in 43 hours, same project)". Under R57 it becomes the only wake-up, both for an
     enqueue and for a finished train.
- **Material-because:** the event-driven tick design of `github-merge-steward.yml.template` ("The ticks are
  EVENT-driven, and every event is a DISPATCH"). Landing latency, the dominant wait in the measured build span, would
  fall back to a dropped-and-delayed schedule.
- **Evidence:**
  - `merge_steward.py` `enqueue`, `trigger_tick`;
  - `github_wrapper.py` `steward_delegate`;
  - `github-merge-steward.yml.template`, header;
  - `github-steward-wake.yml.template`;
  - design.md §3.5, §15.2.
- **Proposed edit (recommended first):**
  1. **Wake the steward through `repository_dispatch`.**
     - The steward workflow adds `repository_dispatch` with one event type. That event always runs the default branch's
       copy.
     - Creating it needs "Contents: write", which the worker tokens already hold (the repository-dispatch action's
       documentation lists "contents: read & write" for a fine-grained token).
     - The steward ignores the payload.
     - R57 is restated: "no write-token workflow runs a ref a worker can write, and no `repository_dispatch` payload is
       trusted".
     - The `steward-wake` job may keep `actions: write` on train refs. It runs only inline steps from a workflow file
       no worker can change, and R57 lists it as the exception.
  2. Keep R57 as written and accept schedule-only ticks. Then record the latency cost in §19, and drop the replay
     assumption "no steward tick is lost" from §10.7.

### P5 (B): a workflow-file change has no landing path, and a queued one makes every tick fail

- **Location:** §3.5 "a change to a workflow file is landed with the operator's own token, as a reserved decision";
  §3.5 "a trunk ruleset that blocks updates by anyone but GitHub Actions"; §10.8.
- **Target quote:** "a change to a workflow file is landed with the operator's own token, as a reserved decision."
- **Defect:**
  1. **The steward cannot push one.**
     - The `GITHUB_TOKEN` cannot be given the right to create or update a workflow file. The push is refused with
       "refusing to allow a GitHub App to create or update workflow … without `workflows` permission".
     - The `permissions` key has no entry for it. Sources: Stack Overflow 66643917 and 68940030; the `permissions`
       key list in GitHub's workflow syntax.
  2. **The operator cannot push one either.** The ruleset blocks every actor except GitHub Actions, and the design
     names no bypass for the operator. Under U24 a bypass for the operator's user would also cover the worker tokens,
     which are the same account (to confirm with O14).
  3. **A queued one freezes the steward.**
     - The train builder pushes all trains in one `git push` through `Git.run`, which raises `GitError` on a non-zero
       exit (`check=True`).
     - A queued PR that changes a workflow file fails that push on every tick, and the PRs behind it do not land.
     - Framework promotions (`prompts/update.txt`) change workflow templates, so this is a routine case, not a rare
       one.
- **Material-because:**
  - liveness of the whole queue;
  - R57's own premise that workflow changes have a path;
  - P5 (workers never wait: a frozen queue makes every session wait).
- **Evidence:** `merge_steward.py` `Git.run` and the train push; design.md §3.5; the sources above.
- **Proposed edit (recommended first):**
  1. **Give workflow changes their own path, and keep them out of trains.**
     - `eligibility` refuses a PR that changes `.github/workflows/` with a named reason, and sets `needs-input` of kind
       approval on its issue.
     - The operator lands it with a credential no worker host holds that the ruleset names as a bypass: a write deploy
       key kept on the operator's machine. Whether rulesets accept a deploy key as bypass actor goes into O14.
     - The activity check accepts that key's pushes and records them.
     - §10.8 gains the hazard "a queued workflow change fails every train push".
  2. The operator lands workflow changes by switching the ruleset off for the push with their own token (which has
     Administration) and on again. The steward's activity check reports that push as an expected non-Actions push from
     the setup record. `eligibility` still refuses such PRs.

### P6 (B): on GitLab the worker tokens can read the steward's token and change the protection

- **Location:** §3.5 GitLab bullet; §15.2 "What limits it" (the delivery side); §12.3 item 3.
- **Target quote:** "The steward's token is a protected, masked CI variable, so pipelines on unprotected branches never
  receive it."
- **Defect:**
  - Protection from pipelines is not protection from the API.
  - Under U24 the worker tokens are the operator's account, which owns or maintains the project.
  - §12.3 item 3 itself says that before GitLab 19.2 "the `api` scope is full access". The worker tokens need `api` to
    write notes and labels.
  - GitLab's project-level CI/CD variables API (`GET /projects/:id/variables`) returns each variable's `value`. The
    documented example shows `"masked": true` with its value. The API offers `masked_and_hidden` as a separate setting.
  - So a worker token can read `STEWARD_TOKEN` and push trunk as the steward's bot user. With the same scope it can
    change the protected-branch rules themselves.
  - §15.2's "closed against worker tokens and worker-written workflows" does not hold on GitLab as specified.
- **Material-because:** aN7's failure class (a worker token reaching trunk) and B7, on the second forge; U24, the
  residual at its true size.
- **Evidence:** design.md §3.5, §12.3 item 3, §15.2; GitLab Docs, "Project-level CI/CD variables API"
  (`masked_and_hidden`; the list example returning values).
- **Proposed edit (recommended first):**
  1. **State the GitLab precondition, and use what the platform offers.**
     - The steward's variable is masked and hidden.
     - The worker tokens are fine-grained (GitLab 19.2 or later) without Maintainer-level settings, protected-branch
       or variable permissions.
     - Before 19.2, §15.2 and §19 item 4 say that on GitLab the delivery side is not closed against a worker token.
  2. A separate bot account for the workers on GitLab only. That reopens U24 for one forge, so it is the operator's
     call.

### P7 (C): the content key can match a legitimate later change, or several merges

- **Location:** §10.4 step 3; §4.2 "An issue already closed when a revert of its PR lands is reopened".
- **Defect:** an exact inverse is common for small changes: a flag toggled back, a version pin restored, a line
  removed again. A later issue's legitimate PR that matches an old merge reopens a long-closed issue as a culprit. A
  diff can also invert several merges with identical diffs, and the design does not say which is reverted.
- **Proposed edit:**
  - match only a merge whose change is still the newest change to those lines;
  - match only within a window (for example since that issue's close, bounded by days);
  - and, outside Track T, only when the PR declares `Reverts: PR #<k>` and the content check confirms it.
  - Otherwise the steward records a candidate on the old issue, without reopening it.

### P8 (C): the re-spec edge and the `/stage` request leave flags and PRs behind

- **Location:** §4.2 re-spec edge; §8.3 `/stage` row; §4.3 first bullet header.
- **Defect:**
  1. The edge says nothing about `ci-pending`, `checker-requested`, `review-open`/`review-verify` or the open PR.
     - Re-spec at `ci-pending` leaves the flag set. Worker queues exclude it, and the verifier is then refused, because
       the issue is no longer in IMPLEMENTATION-READY.
  2. A `/stage` on TEST-READY becomes a steward request applied "at its next tick" as a return. The design does not say
     the steward first dequeues the issue's PRs, so it can land the PR the human asked to stop.
  3. §4.3's header still says "checked in SPEC-REQUIRED and IMPLEMENTATION-READY only". Its sub-bullets now include
     REWORK-REQUIRED, so an edit above the marker during rework is never detected at pickup.
- **Proposed edit:**
  - the re-spec edge clears those flags, sets `do-not-merge` on the PR (or closes it), and records which;
  - a `/stage` request dequeues the issue's PRs before the return;
  - §4.3's header lists REWORK-REQUIRED.

### P9 (C): `/amend` text is not part of the ask

- **Location:** §4.3 "The ask is the title plus the body ABOVE a machine-owned marker line"; §8.3 `/amend`; §4.3
  "Agents write only below the marker … The wrapper refuses an agent's edit above it".
- **Defect:**
  - `/amend <text>` "changes the ask", but the ask is the title plus the body above the marker, and the recorder, an
    agent path, may not write above the marker.
  - So the amendment is never part of the ask or its hash. In START and SPEC-REQUIRED, where "the change simply
    becomes the ask", nothing records it as such.
  - `spec-approved {ask_hash}` and the close-out's "what was asked" omit it.
- **Proposed edit:** define the ask as title + body above the marker + every executed `/amend`, in comment order, and
  hash that.

### P10 (C): a skipped or refused deploy that "concludes failure" must not count as red

- **Location:** §10.3 "A restored run concludes `failure` explicitly … So does a deploy the guard of §10.4 step 4
  skipped"; §10.5; §10.4 step 5.
- **Defect:**
  - §10.5 records `red-since` for "a red deploy or smoke verdict".
  - §10.4 step 5 reads a red with the same signature as a wrong attribution, and reverts the next suspect.
  - A guard skip now concludes `failure`, while the deploy template's header says a refused dispatch "is not a failed
    deploy, and must not return the issues it happens to contain".
  - The design does not separate them, so a skip during a pending revert can read as a second red and revert an
    innocent suspect.
- **Proposed edit:**
  - the pinned verdict has four outcomes: green, red, restored, skipped or refused (read from the job and step
    conclusions);
  - Track T and `red-since` read only red and restored.

### P11 (C): gaps in the label gate's coverage

- **Location:** §3.2 "Human-owned flags"; §8.2; §6.1 item 3.
- **Defect:**
  1. The gate is stated for "an agent's add or remove". Labels can also be set inside `issues/create` and replaced
     whole by the `labels` field of `issues/update`, through the wrapper's `call`.
  2. The `priority:critical` exception ("triage may set `priority:critical` only on an `Origin: production` issue a
     factory login filed") is met by any agent's filing under U24. Every agent files as the factory login, and anyone
     can type the provenance line. So any spawned issue can be expedited past the queue.
- **Proposed edit:**
  - the gate covers create and update payloads;
  - the production expedite requires a record the intake writes from the alarm itself (alarm ARN and state, read-only
    verified by the dispatcher), not the provenance line.

### P12 (C): what a write-token workflow runs is worker-changeable, and other workflows share the exemption

- **Location:** §3.5 "Both: no worker-writable path to a write token"; §10.8 H7 "Given the previous point, that can
  only be the steward".
- **Defect:**
  1. **The scripts and local actions those workflows run are not reserved.**
     - The steward and deploy workflows run `scripts/merge_steward.py`, the deploy scripts, and local actions under
       `.github/actions/`, all from the default branch.
     - A worker changes these through an ordinary PR, which needs no Workflows permission. Only workflow files are made
       a reserved decision.
  2. **Other workflows are exempt too.**
     - Any other default-branch workflow with `contents: write` (a release or version-bump workflow) is exempt from the
       ruleset as well.
     - So "can only be the steward" holds only if no such workflow exists, and setup does not check for one.
  3. **"Declares `contents: read`" is not the same as "holds no write scope".** A branch-code workflow with
     `pull-requests: write` can post as `github-actions[bot]`, which §4.5 now says it cannot.
  4. **`repository_dispatch` needs only "Contents: write"**, which the worker tokens hold. So "no worker dispatches a
     workflow" is false for that event. It runs default-branch code with a worker-chosen payload.
- **Proposed edit:**
  - the reserved-path list covers every file a write-token workflow executes, checked by `eligibility` the same way as
    P5's workflow rule;
  - setup lists every default-branch workflow with `contents: write` and refuses factory mode unless it is the
    steward's;
  - branch-code workflows hold `contents: read` and nothing else;
  - no write-token workflow trusts a `repository_dispatch` payload.

### P13 (C): renewal from the commit hook and long local runs

- **Location:** §5.1 "Renew"; `ci-owns-the-test-suite.md` (the `pre-commit` boundary costs "< 2 s").
- **Defect:**
  - A ref push from the commit hook adds a network round trip to every commit, and fails when offline. The design does
    not say whether a failed renewal blocks the commit.
  - Long local runs (mutation testing on tier L, a suite waiting for a host-wide slot) make no wrapper call and no
    commit. They exceed the 90-minute cap, and the reaper frees a live claim.
- **Proposed edit:**
  - the commit hook renews best-effort and asynchronously, never failing the commit;
  - `scripts/run_tests.py` and `suite_semaphore.py run` renew while they run or wait, as wrapper-side tools.

### P14 (C): the continuation writes the stage before the claim exists

- **Location:** §5.4 steps 2–3.
- **Defect:**
  - Step 2 puts the stage label on the new issue before step 3 creates its claim ref. In between, the issue is
    pullable ("no claim": the ref is absent).
  - A worker can acquire it with an empty expectation and start without the cursor or the folded state. Step 3's
    atomic push then fails.
- **Proposed edit:** create the new issue's claim ref (held) and free the old one in the atomic push first, then write
  the label and the `continued from` line, then close the old issue.

### P15 (D): `return_run_details` depends on the API version

- **Location:** §10.4 step 3 "dispatched with `return_run_details`"; §4.2 (a).
- **Defect:**
  - `docs/api-reference/github/rest/actions.md`, `actions/create-workflow-dispatch`, says that from API version
    `2026-03-10` (`change_workflow_dispatch_response_status`) the 204 response and the body parameter
    `return_run_details` are removed. In that version the 200 response is the only one.
  - The code and templates send `X-GitHub-Api-Version: 2022-11-28`.
- **Proposed edit:** "the run id from the dispatch response (`return_run_details: true` under `2022-11-28`; always
  returned from `2026-03-10`)".
