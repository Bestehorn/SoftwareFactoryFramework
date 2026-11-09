---
description: Run coverage analysis and add tests until the configured threshold is met.
allowed-tools: Bash, Read, Edit, Grep, Glob
---
Analyze and improve test coverage:
1. `python scripts/run_tests.py --coverage` (inside the venv; bounded workers).
2. Read the threshold from `COVERAGE_THRESHOLD` in `scripts/run_tests.py` — it lives
   there, NOT in `[tool.pytest.ini_options]`, deliberately: coverage flags in
   `addopts` would make every targeted run pay for instrumentation and fail a
   whole-project threshold (Part 4).
3. Identify uncovered files and lines, prioritizing critical paths.
4. Add tests until the threshold is met (use hypothesis where property-based testing
   fits). While writing them, run just those tests — `python scripts/run_tests.py
   <path>`, no coverage, fast — and re-run with `--coverage` only to check progress.
5. Report initial vs final coverage, tests added, and any remaining gaps with
   justification.
