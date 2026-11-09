# Remote Repository Operations Are Not Done Until CI Passes (CRITICAL)

## Core rule

Any remote-changing operation — push, merge, rebase-and-push, PR merge — is NOT finished until the
CI pipeline for the pushed SHA reaches a successful terminal state. No CI configured at all (no
`.github/workflows/`)? Say so; the push completes the operation. Otherwise monitor to a terminal
state, however long it takes — never abandon a queued, running, or red pipeline. Status and logs
come only from the wrapper script (`use-git-wrapper-scripts.md`); declare success only with quoted
evidence: run id, terminal status, commit SHA (`no-guessing.md`).

## On failure (the debugging loop) — ONE run in, ALL fixes out

CI is built NOT to fail fast (every CI job runs `scripts/run_checks.py`, which runs every check of
its group): a red run is a COMPLETE list of what is wrong, not the first thing wrong. Your side of
that bargain:

1. **Enumerate before fixing anything.** Retrieve the full logs of EVERY non-successful job via the
   wrapper; within each, list every failing test and every failing check. Complete logs, not a tail
   (`no-output-shortening.md`). Do not start editing while still reading.
2. **Group by root cause, and write the grouping down:** `N failures across M jobs → K root causes`,
   each cause established with evidence (`no-guessing.md`).
3. **Fix EVERY group** before the next push. Commit as you go (`ci-owns-the-test-suite.md`).
4. **Verify locally what is cheap to verify**: the affected tests via `python scripts/run_tests.py`,
   or `run_checks.py --group lint` — never the full suite.
5. **Push ONCE**, then monitor the new run to a terminal state.
6. Repeat only if the new run surfaces something genuinely new.

**Fixing one failure and re-pushing to discover the next is a violation of this rule, not a work
style.** Record every run you cause, with its purpose and what it surfaced. If one failure truly
cannot be diagnosed from the logs in hand, say so with the evidence, fix everything else, and treat
the extra run as a cost you consciously choose. This loop is the ONLY exit — never abandon a red or
unfinished pipeline, and an "unrelated" failure is still on your list (`tests-must-not-fail.md`).
"It will probably pass", "the failure looks unrelated", and "I'll let CI sort it out" are all
forbidden.

## When CI CANNOT RUN AT ALL: the capacity ladder (summary)

Take the FIRST rung that applies; local execution is the LAST, never the first; an outage is never
a reason to stop (`continuous-work.md`).
- **Rung 0** — prove the refusal structurally (per-job evidence, never duration).
- **Rung 1** — an implemented CI fallback MUST be used: relocate the pipeline.
- **Rung 2** — not implemented: file, or comment on, ONE issue via issue-intake.
- **Rung 3** — declare CI-OUTAGE MODE, then run the pipeline locally, disclosed:
  `python scripts/ci_outage_mode.py declare --evidence-run <id> --issue <n> --rung <2|3>`
  (`python scripts/ci_outage_mode.py clear` when a real run goes green). `declare` hard-requires
  `--evidence-run` and `--issue`, so a rung cannot be skipped silently.

The FULL ladder procedure with its evidence obligations lives in `docs/ci-capacity-ladder.md` — read
that file THE MOMENT CI cannot run, before taking any rung. `ci-owns-the-test-suite.md` is the other
half of this rule: WHERE tests run, commit-often / push-once, and the outage marker.
