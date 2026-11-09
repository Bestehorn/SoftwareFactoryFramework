---
paths:
  - "test/**/*.py"
  - "src/hooks/tests/**/*.py"
  - "src/payload/test/**/*.py"
---
# Tests Must Not Fail — Diagnosis and Repair Procedures

Companion of `tests-must-not-fail.md` (always loaded), which owns the standard: a failing test is
never skipped, xfailed, deleted, or weakened — it is fixed. This file carries the full procedure and
the rationale behind the kernel's forbidden lists.

## The baseline assumption

Every implementation starts from a baseline where 100% of tests pass. This is enforced by:
- The CI pipeline (`.github/workflows/`), which runs the full test suite before every merge.
- The post-activity checklist in `post-activity.md`, which mandates green affected tests before any
  task is marked complete.
- The pre-commit hook (`.pre-commit-config.yaml`, run through the tracked `.githooks/`) keeps lint,
  format and the security scans green before every commit; it never runs tests.

Why the kernel's forbidden claims are wrong on the facts: the suite was green when this task
started. A failure now means either (a) your change broke it, (b) a dependency or environment shift
broke it AND your task is the one that has to absorb the fix, or (c) the test is genuinely flaky AND
fixing the flakiness is part of your task. There is no fourth option in which the failure is "not
yours."

Why they are wrong on the policy: even in the rare case where a failure pre-dates your work, the
policy says: fix it. The cost of unblocking the build NOW is always smaller than the cost of letting
red tests accumulate, masking new regressions, and eroding trust in the suite.

## The only allowed path

There is exactly one way out of a red suite:

### Step 1: Understand

- Read the failing test, the source it exercises, fixtures, conftest, helpers, and any module
  imported transitively. Skip nothing.
- Run the failing test in isolation to capture the full error and stack trace. Apply
  `no-output-shortening.md` — read the full output, do not tail.
- Trace the test's intent through docstrings, comments, the spec document if any, and recent commit
  history of the test file (`git log -p -- <test-file>`).
- State, with evidence, what behavior the test is supposed to verify and what behavior it is
  currently observing.

### Step 2: Research the right fix

- Consult the documentation of the library, tool or API involved (for the forge APIs:
  `docs/api-reference/`).
- Consult `docs/` for project-specific design.
- Consult `docs/lessons-learned.md` for prior fixes of similar issues.
- Consider at least two candidate fixes. Compare them on maintainability, correctness, and alignment
  with `design-principles.md`.

### Step 3: Apply the fix

- Default location: the SOURCE code under test.
- Exception: if the test itself has a bug in its TEST LOGIC (not in its assertion expectations —
  assertion expectations encode the required behavior and must not be relaxed to make tests pass),
  fix the test logic.
- Apply `coding-standards.md`, `design-principles.md`, and `file-organization.md` to the fix.

### Step 4: Verify — locally on what you touched, in CI for the rest

- Re-run the previously-failing test alone. Confirm pass with full output captured:
  `python scripts/run_tests.py <that test>`.
- Re-run the tests AROUND it — the module, the package, whatever the fix could plausibly reach.
  Fixing one test sometimes breaks another, and this is where you catch that cheaply.
- The FULL suite is CI's verdict, not a local one (`ci-owns-the-test-suite.md`). Push the batch once
  and read the CI run: it runs every test with no fail-fast, so it reports every remaining failure at
  once. You still don't get to stop until every test passes — what changed is WHERE the whole-suite
  run happens, never WHETHER it must be green.
- **Fix every failure that run reports, in one pass.** A red CI run is a complete list; treating it
  as a queue to work one item at a time turns one run into five.
- While CI-OUTAGE MODE is declared the `pre-push` hook runs the full suite locally at push time, with
  bounded workers. That is the only sanctioned local full-suite run.

### Step 5: Document

- If the failure mode was non-obvious, append a lesson to `docs/lessons-learned.md` per
  `use-lessons-learned.md`.

### Step 6: Loop if needed

If anything is still red after Step 4, you have NOT understood the root cause. Go back to Step 1.
Repeat until the suite is green.

## When the failure really is environmental

Sometimes a test fails because of a missing dependency, a stale venv, a missing credentials file, or
a network-dependent service that's unreachable. These are still YOUR problem to resolve before the
task is done:

- Missing dependency: add it to `pyproject.toml` and `pip install -e ".[dev]"` (`dependencies.md`:
  shipped code stays standard library only). The original test author assumed the dependency would
  be present; if it isn't, the project's dependency setup is broken.
- Stale venv: rebuild it per `use-venv.md`.
- Missing credentials: confirm the test is supposed to require them (read the test). If yes,
  document the credential setup in `docs/forLLMConsumption.md`. If no, the test is over-coupled to
  external state and needs to be refactored to use mocks/fixtures.
- Network flakiness: convert to a mock/fixture so the test no longer depends on the network. Don't
  `xfail` and don't add retries — fix the root cause.

In none of these cases is "the test is flaky" or "the env is broken" a stopping condition. Each is a
fixable problem that falls inside the scope of the current task by virtue of having surfaced during
the current task.

## Integration

- `tests-must-not-fail.md`: the always-loaded kernel owns the standard and the complete
  forbidden-claims / forbidden-actions lists.
- `no-guessing.md`: every claim about a test failure ("this fails because X") needs evidence — the
  actual error message, the line of code that produced it, the doc reference that confirms expected
  behavior.
- `no-output-shortening.md`: read full pytest output, not the tail.
- `coding-standards.md` + `design-principles.md`: govern HOW you fix.
- `post-activity.md`: the post-activity checklist runs the affected tests plus the non-test
  `run_checks.py` groups; this rule is what governs your behavior when that gate is red.
- `ci-owns-the-test-suite.md`: WHERE the run happens (affected tests locally, full suite in CI) and
  the requirement to fix every failure a run reports in ONE pass. That rule never softens this one:
  a failing test is still always fixed, never skipped, xfailed or deleted.
- `use-lessons-learned.md`: document non-obvious failures so the next agent doesn't repeat the same
  root cause.
