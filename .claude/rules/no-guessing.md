# Evidence-Based Statements Only (CRITICAL)

Every claim you make to the user must be backed by verifiable evidence: log output, command output,
API response, file contents, test results. If you cannot cite evidence, do not make the claim.

## Trigger phrases that demand evidence

Before stating any of the following, verify with concrete data:
- "should work", "may work", "probably", "likely", "I think", "I believe"
- "now works", "is fixed", "will trigger", "will pick up"
- "the correct approach is" (without a doc citation)

If you catch yourself about to use one of these without evidence, stop and gather the evidence
first. State the evidence alongside the claim.

## What counts as evidence

- Command output (`scripts/run_tests.py`, ruff, `git log`, the wrapper scripts)
- API responses (CI status, the GitHub API through the wrapper)
- Log file contents (CI logs, application logs)
- Test results with explicit pass/fail counts
- Documentation quotes (for the forge APIs: `docs/api-reference/`)

## What does NOT count as evidence

- Your own reasoning without supporting data
- "Usually" / "in most cases"
- Predictions about future behavior without monitoring
- "The code looks correct" without running it

## Examples

WRONG: "The gate now works."
RIGHT: "Tests pass: `47 passed, 0 failed` from
`python scripts/run_tests.py src/hooks/tests/test_gate_filing.py`. The previously-failing test now
succeeds."

WRONG: "The pipeline should pass with this fix."
RIGHT: "Run 326 from `python scripts/github_wrapper.py get-run 326`: `in_progress`, triggered by
commit a1b2c3d, which contains the fix."

WRONG: "This approach should fix the issue."
RIGHT: "The log says `TypeError: expected str, got NoneType` at `processor.py:142`. The API
documentation (quoted) confirms the field can be null. I'll add a None check and verify it with a
unit test."

## When you violate this rule

Acknowledge it, gather the evidence, restate the claim with evidence or retract it. If the class of
error can be caught mechanically, add the check; otherwise record ONE five-line lesson in
`docs/lessons-learned.md` (`use-lessons-learned.md`). This rule carries NO violation log: an
append-only ledger inside an always-loaded file was measured growing one rule to 85,000 bytes, read
into every model call of every session.
