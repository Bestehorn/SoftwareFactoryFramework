---
paths:
  - "test/**/*.py"
  - "src/hooks/tests/**/*.py"
  - "src/payload/test/**/*.py"
---
# Testing Standards

1. Tests live in three suites, each beside what it tests: `src/hooks/tests/` (the hook runtime),
   `src/payload/test/` (the shipped project scripts) and `test/` (tests of the framework itself, plus
   the installed `test/test_instruction_corpus_budget.py`, which is toolchain — `project-specific.md`).
2. Coverage target: 80% minimum, 100% for critical paths.
3. A test module covers its source module (`src/hooks/tests/test_gate_filing.py` covers
   `src/hooks/gate_filing.py`). Use pytest fixtures where useful.
4. Run tests through `scripts/run_tests.py`, never `pytest` directly — it is the single definition
   of the invocation (bounded local workers, no fail-fast, complete failure list):
   - while working: `python scripts/run_tests.py src/hooks/tests/test_gate_filing.py` (the affected
     tests — fast, no coverage instrumentation)
   - coverage check: `python scripts/run_tests.py --coverage`
   - the FULL suite is CI's job, not yours: see `ci-owns-the-test-suite.md`. Do not run it locally
     to satisfy a gate.
5. Forge-facing code is integration-tested against ephemeral `sff-test-*` repositories the tests
   create and delete, never against this repository (`project-specific.md`).
