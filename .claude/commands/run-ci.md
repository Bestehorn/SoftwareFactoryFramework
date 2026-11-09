---
description: Run every project check locally in one pass (the same command CI runs) and fix every failure.
allowed-tools: Bash, Read, Edit, Grep, Glob
---
Run the project's full check suite locally, inside the venv:

```bash
python scripts/run_checks.py
```

This is the SAME command each CI job runs (Part 7), so what you see here is what
CI will see. It does NOT stop at the first failure: it runs every check in every
group (lint, types, security, tests) and ends with a consolidated
`=== FAILED CHECKS (n) ===` block.

1. Read the COMPLETE output (no tail/head/Select-Object). The summary block at the
   end is the full list of what is wrong.
2. **Fix every listed failure in ONE pass.** Group them by root cause first — ten
   failures are usually two or three causes. Do not fix one and re-run to find the
   next; that is the habit `.claude/rules/ci-owns-the-test-suite.md` forbids, and
   it wastes as much time locally as it does in CI.
3. Never skip, disable, weaken, or delete a check to go green.
4. Re-run once when all fixes are in.
5. Report: every failure the first run listed, the root-cause grouping, what was
   fixed, and the clean final run.

A check reported as SKIPPED has NOT passed — its tool is missing from the venv.
Install it AND add it to `pyproject.toml`'s dev extra.
