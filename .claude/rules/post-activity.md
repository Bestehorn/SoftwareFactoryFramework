# Post-Activity Checklist

Before marking any activity complete:

1. **Run the AFFECTED tests:** `python scripts/run_tests.py <paths or -k expr>`. Fix every failure
   (`tests-must-not-fail.md`). The FULL suite is CI's job, not this checklist's
   (`ci-owns-the-test-suite.md`): the authoritative verdict is the CI run on the pushed SHA. Do not
   run the whole suite here to feel finished. (The one exception: while CI-OUTAGE MODE is declared,
   the `pre-push` hook runs the suite for you at push time.)
2. **Run the other project checks, locally, in one pass:**
   `python scripts/run_checks.py --group lint --group types --group security`. These are the SAME
   commands CI runs, so the two cannot drift apart; the script continues past a failure and ends with
   a consolidated `=== FAILED CHECKS (n) ===` block. Read all of it (`no-output-shortening.md`).
   **Fix every failure it lists before continuing — all of them, in this pass.** Do not fix one and
   re-run to discover the next. (A plain `run_checks.py` adds the `tests` group, the full suite.)
3. **Update docs** in `docs/` for any changes. Keep `docs/forLLMConsumption.md` current and under
   its 40,000-byte cap.
4. **Flag deviations** between docs and implementation.
5. **Clean `tmp/`** — remove all files created during the task.

These duties close an activity, not the work: go on to the next step (`continuous-work.md`).
