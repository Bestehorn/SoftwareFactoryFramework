# One change blocks everyone — the chess #566 situation, and how high-velocity projects avoid it (2026-11-02)

Scope: chess's tracker, Actions runs and trunk history (read-only, through chess's own wrapper), this machine's chess
session transcripts since 2026-11-01, and a survey of how high-velocity open-source projects keep one broken change or
a red pipeline from stopping everyone (sources inline). Nothing was changed in chess or in the framework.

## 1. What happened

| When (UTC) | Event |
|---|---|
| 10-31 13:11 | Deploy dev run 612 — the LAST green dev deploy |
| 10-31 20:16 | #566 lands (37f6bef, delivery 2). Its CDK change drops two public-subnet exports of `ChessEngine-Dev` that the deployed `ChessBroker-Dev` still imports; CloudFormation refuses ("Cannot delete export … in use by ChessBroker-Dev") and rolls the engine stack back. The deploy aborts at that stack, so no later stack deploys |
| 10-31 23:02 | A session names the cause on #566 — under 3 hours after the landing |
| 11-01 09:03–09:33 | The cause is bisected; a rework is claimed (tier S, spec, reviews) |
| 11-01 16:27 | Fix PR #1544 queued; 19:38 its train is red on an unrelated collision (#1466 moved the lessons files); 21:02 it leaves the queue |
| 11-02 14:21 | The fix lands (21a3d33). 15:51: the fix deploys — and the deploy is red again, now on #1494's migration: the deploy role `chess-deploy-caller-dev` lacks `cloudformation:GetTemplate`. #1538 (Chromium install skipped after a failed step → 22 `TokenCliError`s in the sweep) rides along |
| 11-02 20:28 | Deploy dev run 646 — the 26th consecutive red dev deploy (about 50 hours) |

Measured on 2026-11-02 evening:
- **The merge queue works.** 37 PRs landed in the 50 hours — every one of them into a red environment.
- **Verification does not.** 36 open issues carry `needs-rework` and 43 `verification-failed`. 24 issues are claimed
  `in-progress` (about 20 workers across machines; 11 runs on this machine). On a sample of the 36: 15 drew a rework
  session after the red verdict, and in 7 the agent concluded in writing that the red is not theirs.
- **Chess runs the 2026-10-26 framework** (`2026.10.26-delivery-5`): its verdict watcher returns EVERY issue a red
  deploy contains as `needs-rework`, and the orchestrator takes returned work FIRST. The later rounds (red streaks,
  `wait-landed`, the SESSION verdict, contract -8) are not on chess's trunk.

## 2. Why one change blocked about twenty workers

| # | Cause | Effect here |
|---|---|---|
| R1 | **No revert in steward mode.** The framework knows only a forward fix (a full tier-S cycle: spec, review panel, CI, queue). "Revert" appears only in the old direct-merge session flow | The culprit was known within 3 h; the trunk stayed broken ~44 h more while its fix went through the whole pipeline and bounced once on an unrelated collision |
| R2 | **Blame-all verdicts** (chess's -5 watcher) + **returned work first** | Every one of 37 good landings was bounced; the fleet's top priority became reworking changes that were not broken — 7 sessions proved "not ours" in writing |
| R3 | **Serial masking.** The deploy stops at the first failing stack | #1494's own defect stayed hidden until #566's fix let the deploy reach it — red cause after red cause, each found only after the previous one was fixed |
| R4 | **No owner for the environment, no "infra" class.** A missing IAM permission on the deploy role is an environment fault, handled like a change failure | Nobody owns "dev is red"; every worker whose issue is covered investigates it independently |
| R5 | **Pre-merge cannot see deploy breakage.** Train CI runs the tests; CloudFormation's export rules, IAM grants and migration steps only fail at the real deploy | #566's train and #1494's train were green; both broke the deploy |
| R6 | **Even the newer framework only half-solves it.** Contract -8 (B2 red streaks) stops blaming issues that land AFTER the red began, but still blames everything in the first red window, never reverts, never escalates, and tells nobody | Rolled out alone, it would end the rework churn but leave dev red until someone happens to fix it |

## 3. What high-velocity projects do

1. **Keep the trunk green before the merge** — the Not Rocket Science Rule: test the exact merge, land only green
   (bors, Zuul's speculative dependent pipelines, GitHub merge queue, GitLab merge trains). A failing change is
   dropped and the changes behind it are re-tested without it. *Chess has this (the steward).*
   https://graydon2.dreamwidth.org/1597.html · https://zuul-ci.org/docs/zuul/latest/gating.html ·
   https://docs.gitlab.com/ci/pipelines/merge_trains/
2. **Revert first, on a clock, by a designated owner or bot.** ChromiumOS is "a revert-first project"; Skia "revert
   first and ask questions later"; LLVM prefers "revert to green", and anyone may revert a change a few hours old;
   Mozilla sheriffs back out about 5 minutes after pinging an unresponsive author; Google TAP auto-reverts when it is
   confident of the culprit; Chromium reverts a perf regression not fixed within a business day. The author relands
   the fix later. https://www.chromium.org/chromium-os/developer-library/guides/testing/breakages-and-flakes ·
   https://skia.org/docs/dev/gardening/ · https://llvm.org/docs/DeveloperPolicy.html ·
   https://wiki.mozilla.org/Sheriffing/How_To/Backouts · https://abseil.io/resources/swe-book/html/ch23.html
3. **Blame only what fails WITH the change and passes WITHOUT it.** Chromium's CQ retries a failing test, then runs it
   on tip without the change; only "fails with, passes without" fails the change. Google's culprit finder keeps a
   probability that there is no culprit at all, so flakes do not cause wrong reverts.
   https://github.com/chromium/chromium/blob/main/docs/infra/cq.md · https://research.google/pubs/pub52048/
4. **Infrastructure failures are not change failures.** Mozilla closes the tree with an `infra` reason and backs
   nobody out; Zuul retries setup-phase failures; GitLab retries only `runner_system_failure`-type errors; Chromium
   routes infrastructure to "troopers". https://wiki.mozilla.org/Sheriffing/Deciding_To_Close_A_Tree ·
   https://zuul-ci.org/docs/zuul/latest/config/job.html · https://docs.gitlab.com/ci/yaml/
5. **Deploy is decoupled from merge.** Deploy the last known good (Chromium LKGR, Google's "green head"); verify
   bystanders later instead of failing them (TAP post-submit, LLVM buildbots); throttle merges when too much is
   undeployed (Shopify Shipit merges only with "no lock, no failing CI, no backlog"); ship dormant code behind flags
   and switch a broken feature off instead of reverting (Meta). https://github.com/Shopify/shipit-engine ·
   https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/ ·
   https://martinfowler.com/articles/feature-toggles.html
6. **One owner for red, and a fixes-only lane.** Build cops, gardeners, sheriffs and release-signal teams own red
   "regardless of who broke it"; while the tree is closed only fixes and reverts land (Chromium `No-Tree-Checks`,
   Rust's priority-scoped `treeclosed`); escalation clocks run from minutes (Mozilla) to days (kernel regressions).
   https://github.com/chromium/chromium/blob/main/docs/gardener.md · https://forge.rust-lang.org/release/rollups.html
7. **Non-gating tiers for what is not reliable.** Kubernetes demotes jobs that miss its release-blocking bar to
   "informing" and quarantines flakes with an owner and a deadline; Mozilla's Tier-2 failures never cause a backout.
   https://github.com/kubernetes/sig-release/blob/master/release-blocking-jobs.md ·
   https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/flaky-tests.md

## 4. Options

**For the framework** (each maps to a cause and to a practice above):

- **F1 — Revert first, by the steward, on a clock (R1; practice 2).** When a deploy turns red after a green one,
  the culprit window is the landings between the two. The steward (the trunk's one owner) opens a REVERT of the
  culprit's landing — the window's suspect whose changed files the failing stack or job touches, or the whole window
  when that is ambiguous — and lands it through the queue on a fixes-only lane; the culprit's author relands with the
  fix. A clock bounds the forward-fix option (e.g. revert unless a fix is queued within 60 minutes). *Trade-off:* a
  revert of an innocent PR when attribution is wrong costs a reland, never a broken trunk.
- **F2 — Blame only the culprit (R2, R6; practice 3).** Ship B2 (red streaks) and extend it: during a red streak
  only the attributed culprit is returned as `needs-rework`; every other covered issue stays `awaiting-verification`
  ("verify at the next green deploy"), and "returned work first" applies only to culprit returns.
- **F3 — The environment's health is a state with an owner (R4; practices 4, 6).** The `delivery-status` issue
  carries `dev: open | closed (deploy-red: <culprit or infra>, since <t>)`; a closed environment pauses landings
  except fixes and reverts (or throttles them: at most N undeployed landings), names the owner, and escalates to the
  operator after a clock with a one-line NEEDS YOU. Infrastructure failures (credentials, IAM, quota, throttling)
  are classified and retried, never blamed on a change.
- **F4 — Make the deploy stop masking (R3).** Report every stack's result instead of stopping the plan at the first
  failure where the stacks are independent, so two defects surface in one deploy rather than one per day; attribute
  per stack.
- **F5 — Catch deploy-breaking changes before the merge (R5; practice 1).** A pre-merge "deploy safety" job in the
  train: `cdk diff` against the deployed stacks, CloudFormation export/import compatibility (the check #566's fix
  added, made general), IAM permissions simulated for the actions a migration step calls, and an expand–contract rule
  for cross-stack changes (keep an export until its last consumer has deployed). Optionally a short-lived preview
  environment for infrastructure PRs only.
- **F6 — Optional, larger: decouple further (practice 5).** Deploy only the last green train result, and gate issue
  closure on per-issue checks rather than on the whole environment's smoke.

**For chess now** (operator decisions — none taken):

- **C-a — Restore green fastest:** revert #1494's landing (its migration is the current red; #566's fix already
  deployed in run 642), or grant `cloudformation:GetTemplate` to `chess-deploy-caller-dev`. Either should let the
  next deploy reach every stack; the puzzles Replay check belongs to the same migration (unverified that nothing else
  is red behind it — the current deploy stops early).
- **C-b — Stop the churn:** roll out contract -8 (red streaks, landing-owned sessions, the SESSION verdict), and
  return the bystanders: the 36 `needs-rework` issues whose landing predates nothing they caused go back to
  `awaiting-verification`.

## 5. Recommendation

Framework: **F1 + F2 + F3 + F5**, then F4. F1 and F3 are what every surveyed project has and chess lacks — one owner
who reverts to green on a clock — and they bound a red environment to about an hour instead of days; F2 keeps that
hour from bouncing everyone else; F5 removes the class of change that broke chess twice (an infrastructure change
whose tests pass and whose deploy fails). Chess: **C-a** today, then **C-b** with the framework update.
