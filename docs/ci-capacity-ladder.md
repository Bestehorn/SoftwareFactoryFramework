# The CI Capacity Ladder — when CI cannot run at all

Referenced by `.claude/rules/remote-ci-must-pass.md` (the always-loaded kernel), whose summary
names the rungs. This file is the NORMATIVE procedure: read it THE MOMENT CI cannot produce a run,
BEFORE taking any rung. It is deliberately a project doc rather than a rule under `.claude/rules/`,
so it costs nothing until the rare session that needs it.

This ladder governs the case where the pipeline is not red but ABSENT — the account's CI
minutes/quota are exhausted, or hosted capacity is otherwise refusing work. Take the FIRST rung that
applies. Running CI locally is the LAST rung, never the first, and choosing it out of order is a
rule violation, not a shortcut.

## Rung 0 — PROVE it is a capacity refusal, structurally

Duration is NOT the signal and is forbidden as one: an unresolvable action reference fails in ~9
seconds with an empty log archive, which looks identical. Fetch the per-job listing WITH per-step
detail (`get-jobs <run-id> --steps`; the terse form cannot distinguish these) and classify EVERY
non-successful job:

| Shape | `conclusion` | runner name | labels | steps | Route |
|---|---|---|---|---|---|
| **(A) genuine code failure** — the DEFAULT for a red job that has a runner and steps | `failure` | non-empty | any | `> 0` | the debugging loop in `remote-ci-must-pass.md`. NEVER this ladder |
| **(B) refused hosted job** | `failure` | **empty** | a HOSTED label | `0` | this ladder |
| **(C) fallback job that never started** | queued or `cancelled` | **empty** | a FALLBACK-prefixed label | `0` | declare a wait budget, then triage the fallback |
| **(D) skipped by a job gate** | `skipped` | `None`/empty | a HOSTED label | `0` | evidence of NOTHING — ignore |

Two traps, both measured on a real implementation: **(D) mimics (B) byte-for-byte** and is
distinguished ONLY by `conclusion`, so classify on `conclusion` FIRST; and **(C) mimics (B)** too, so
a fallback-prefixed label must never be read as evidence about the HOSTED quota — that confusion is
how the recovery path becomes unreachable. Quote the `runner_name=… labels=… steps=N` lines
verbatim. "CI won't go green" is never the evidence.

## Rung 1 — is the CodeBuild fallback ALREADY IMPLEMENTED? Then USE it

Check, do not assume, in this order — cheapest first:

1. Does a mode variable exist? Read it through the wrapper (`get-variable`). Its presence, and its
   `updated_at`, are evidence.
2. Do the workflow files resolve `runs-on` through that variable? Parse them; a `runs-on` expression
   naming the variable is the mechanism.
3. Has the fallback ever DISPATCHED? One job, in any run, carrying a fallback-prefixed label AND a
   non-empty runner name proves the build project, the source credential and the webhook are all
   live.

**If it IS implemented, relocating the pipeline is MANDATORY and local execution is FORBIDDEN.**
Flip the mode variable to the fallback token, CONFIRM-READ it (a write helper that
probes-then-creates can fail partially, so an exit code establishes nothing), then force a fresh
`runs-on` evaluation by PUSHING a new commit to the branch. The result is a real pipeline run of the
same workflow, so it DISCHARGES the core rule in `remote-ci-must-pass.md` with no exception, no
local substitution and nothing to disclose. Confirm the relocation landed: every job must show a
fallback label WITH a non-empty runner name. A flip with no subsequent fallback-labelled assignment
is an unfinished flip, not a remedy.

Two prohibitions while relocating, because both are infrastructure-mutation capabilities rather
than retries: do NOT re-run a default-branch run and do NOT dispatch the pipeline workflow, where a
deploy job's gate is `dispatch || (push && default-branch)` — the first disjunct names NO ref, so a
dispatch deploys whatever branch it was dispatched on. Push to the branch instead; a pull-request run
leaves the deploy stage `skipped`, which is what makes a push the safe route.

The mode variable is SHARED state read by every run of every branch, so a flip relocates CI for
every concurrent worker. Take the lock, record it as a `DL-NNN` decision with the prior value, the
new value and the driving run id (`agent-state-convention.md`), and do not flip back while another
worker has fallback work in flight. Unwillingness to mutate shared state is NOT a reason to skip
this rung.

## Rung 2 — NOT implemented? FILE IT (once), via issue-intake

If Rung 1's checks show the mechanism does not exist, the durable remedy is to have it built, and
`docs/codebuild-ci-backup-mechanism.md` is what a worker needs to build it. It is installed in every
project set up with the framework, it is deliberately project-agnostic — with placeholders for every
name the project must choose, a three-phase plan where each phase ships alone, the runner-label
contract, the refusal classifier, the sizing arithmetic and a verification checklist — and its
existence means **nobody has to redesign the mechanism.** Point the issue at it rather than
restating the design or researching it afresh.

Read its §1 before filing: three of the four options it lists need no engineering at all (pay the
hosted overage, make the repository public, go all-in self-hosted), and for some projects one of
those is the right answer. The issue should name the alternatives so whoever picks it up makes a
decision rather than assuming the build.

**Check for an existing issue FIRST — this filing happens at most once per project.** Search open
AND closed issues through the wrapper (`list-issues`, including a closed-state query, plus a
title/body search on the mechanism's terms). A closed one is decisive too: closed-as-done means Rung
1's checks were wrong — re-run them; closed-as-rejected means the project has DECIDED against it, so
go to Rung 3 and do not re-file. If an open issue exists, do NOT file a second one — add a comment
noting this new occurrence (the run id, the head SHA, the date) so the issue carries how often the
outage bites, then go to Rung 3.

Only if no such issue exists, file ONE through the **issue-intake** agent — never by hand, so the
intake template, the labels and the provenance are applied consistently. This filing is
pre-authorised and satisfies `issue-filing-discipline.md`: it is an OBSERVED defect (a measured,
quoted capacity refusal that blocked a real merge), the fix-first evaluation resolves to
OUT-OF-SCOPE (a multi-phase infrastructure build with IaC, a credential and new workflow files
cannot be absorbed into the issue in flight), and it is additionally a standing HUMAN-REQUEST from
the project setup. Give the issue:

- the quoted refusal evidence from Rung 0 (the shape-(B) job block, the run id, the head SHA);
- what it blocked, and how often — link previous occurrences if the ledger or earlier comments
  record them;
- BOTH document paths, naming which is normative and which is reference;
- the provenance lines the filing gate requires — `Origin:` (this rule, plus the blocked run),
  `Subject:` (CI capacity fallback), `Filing-rationale:` (OUT-OF-SCOPE + HUMAN-REQUEST, with the
  sentence above);
- the honest cost note from the guide's §1: per-run compute is roughly 2–3× hosted, so cost is NOT
  the reason to build it — a pipeline that STOPS is.

Then go to Rung 3. Filing is not a substitute for verifying the change in front of you.

## Rung 3 — run the pipeline LOCALLY, as a disclosed workaround

Reachable only when Rung 1 found no implemented mechanism AND Rung 2 has been discharged (an issue
now exists, whether you filed it or found it). It is NOT an exception to prove-before-merge — it
REPLACES remote CI with a complete local execution of the same pipeline. This is the ONE state in
which the full test suite runs locally, and even here it runs at PUSH time, never at commit time
(`ci-owns-the-test-suite.md`).

0. **DECLARE the outage** so the mechanism knows, rather than relying on you to remember:
   ```bash
   python scripts/ci_outage_mode.py declare --evidence-run <run-id> \
       --issue <n> --rung 3
   ```
   It writes a marker into the SHARED git dir, so ONE declaration covers every concurrent per-issue
   worktree in the clone — a per-worktree marker would leave sibling runs pushing unverified code.
   From that moment the `pre-push` hook runs the full suite on every push, and `declare` refuses
   without the evidence run id and the Rung 2 issue, which is how the disclosure material in step 4
   gets captured at the moment it is still in front of you instead of reconstructed later.
1. Run EVERY job group of the workflow locally, inside the venv (`use-venv.md`), reading complete
   output (`no-output-shortening.md`):
   ```bash
   python scripts/run_checks.py
   ```
   This is the SAME script each CI job runs, so the local mirror cannot structurally drift from the
   pipeline — you are not reconstructing it, you are running it. It also does not stop at the first
   failure, so one local pass gives you the whole list, exactly as a real run would. Treat any
   failure exactly as a red CI: fix every root cause in one pass, never skip.
   *If this project's CI does NOT route through `run_checks.py`, fall back to deriving the command
   list FROM the workflow file, and say so in the disclosure — a hand-derived mirror can drift and
   the reader needs to know which kind they are being shown.*
2. Any step that genuinely cannot run locally (a missing toolchain that cannot be installed, a
   credentialed deploy job) is a DISCLOSED GAP: name the step and the reason. "Best-effort" means
   you disclose the gap, never that you silently skip it.
3. Run against the SAME head SHA that is being merged.
4. Then, and only then, merge — and post a comment on the PR/issue stating: that remote CI could not
   produce a run, with the quoted shape-(B) evidence; that the fallback mechanism is not
   implemented, with the issue number from Rung 2; the head SHA; the pass result of every local job
   group; and every gap. Do not assert "quota exhaustion" unless that is what the evidence says.
5. Disclose every job of the merged run that did not execute. Once capacity returns, the normal rule
   resumes and a later run must confirm green — and **clear the marker at that moment**:
   ```bash
   python scripts/ci_outage_mode.py clear
   ```
   Clearing is not housekeeping. While it is set, every push in every worktree of this clone pays
   for a full local suite, which is the cost this whole rule set exists to avoid.

## What is NOT this ladder

- A red run WITH a runner and steps and a named failing step — shape (A), the debugging loop,
  whichever runner it ran on.
- A job `cancelled` at its timeout with no summary line, or a broken-pipe/decode error from a heavy
  library's child process. Both are measured RESOURCE-CEILING signatures whose remedy is a size or
  worker-count edit, never a merge.
- A permission error from a billing endpoint. If the token lacks the billing scope its failure is
  evidence in NEITHER direction.
- "The flip did not seem to take", "the fallback would probably have worked", "the hang was
  infrastructure, so I ran it locally." Each is a `no-guessing.md` violation wearing this ladder's
  clothes.
- Skipping Rung 1 because the check "would probably" show nothing, or skipping Rung 2 because filing
  feels like overhead. Both rungs are mandatory and both are cheap.

## Cross-references

- `no-guessing.md`: every rung determination is backed by quoted wrapper output.
- `issue-filing-discipline.md`: Rung 2's filing is pre-authorised (OUT-OF-SCOPE + HUMAN-REQUEST),
  still carries the provenance lines the filing gate checks, and is once-per-project — the duplicate
  check is mandatory.
- `agent-state-convention.md`: the mode-variable flip is a shared-state mutation — take the lock and
  record it as a `DL-NNN` decision.
- `continuous-work.md`: a capacity outage is NOT a hard blocker while a rung remains untried. Work
  down the ladder rather than stopping to ask.
- `docs/codebuild-ci-backup-mechanism.md` is what Rung 2's issue points an implementer at, so the
  mechanism never has to be redesigned per project.
- `ci-owns-the-test-suite.md`: while CI-OUTAGE MODE is declared the suite runs at PUSH time, never at
  commit time.
