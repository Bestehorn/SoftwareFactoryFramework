# Tests Must Not Fail (CRITICAL)

Every task starts from a green baseline: 100% of tests pass, enforced by the CI pipeline and
`post-activity.md` (tests never gate a commit — `ci-owns-the-test-suite.md`). If the tree has failing
tests now, a previous task broke the baseline — fixing that breakage is part of starting the current
task: not optional, not deferrable, not someone else's problem.

**A failing test is NEVER skipped, xfailed, deleted, or weakened — it is FIXED.** Whether it
exercises code you touched or code you didn't, you are the agent holding the work, and the work is
not done while the suite is red. Investigate the root cause to evidence (`no-guessing.md`) and fix
it.

## Forbidden claims (the "pre-existing / out of scope" excuse)

These claims are FORBIDDEN. Each has repeatedly been used to justify shipping broken code, and each
is wrong on the facts as well as on the policy (the full rationale is in
`tests-must-not-fail-procedures.md`):

- "This test was already failing before my change."
- "This failure is pre-existing."
- "This is unrelated to my implementation."
- "This is out of scope for this task."
- "This is a flaky test."
- "This is an environment issue, not a code issue."
- "I'll fix this in a follow-up."
- "Let's track this separately."

## Forbidden actions

- `@pytest.mark.skip` / `pytest.skip()`
- `@pytest.mark.xfail`
- commenting out the test
- deleting the test
- excluding the test file from a test config (`pyproject.toml` `[tool.pytest.ini_options]`,
  `pytest.ini`, `conftest.py` collect hooks)
- adding a `pytest.mark` filter that excludes the test from the default run
- relaxing an assertion to make it pass (assertion expectations encode the required behavior)
- any other mechanism that prevents the test from executing or from failing the build when it fails

The test exists because someone designed a behavior and wrote a check for it. Unless a spec change
has explicitly removed that behavior (documented in `.claude/specs/<feature>/`), the test keeps
running and keeps enforcing it.

## The only allowed path

Understand → research → fix → verify → document → loop until green. The full diagnosis/repair
procedure — including the verification boundaries (affected tests locally, full suite in CI) and the
environmental-failure cases — is in `tests-must-not-fail-procedures.md`, which loads with
`test/**/*.py` files. Read it before working any red test.
