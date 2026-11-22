# Test architect — tasks review, iteration 02 (delta)

Delta: `tasks.md` from a4c42cd to 659363d. Wave 1 is split into Waves 1 and 2, `write_credential.py` moves to Wave 3
together with S's `write_credential.main` assertions, and the ids are renumbered. My iteration-01 C1–C3 and the spec
lane's C1 and C2 are applied.

## Findings

### C1 — 1.4's new keywords first meet a failing test one wave later, where no task owns `test/forge/ephemeral.py`
Severity: C
Location: tasks.md § Wave 1, 1.4
Defect: After the split, 1.4 is paired only with H, which is green before and after. `test/test_forge_support.py`
calls `refuse_distributed_run(worker_id=)`, `credential_helper_arguments(clone=)`, `find_test_credential(checkout=)`
and `write_test_credential(token=, checkout=)`, and it never passes a new keyword. The values other than the defaults
are first exercised by 2.1's S through 2.5:
- the refusal naming `GITLAB_FORGE_COMMAND`;
- `CLONE_GIT_HELPER`'s `git credential fill`;
- the GitLab credential file;
- the `SFF_GITLAB_TEST_TOKEN` refusal.

So if 1.4's bodies accept a keyword but ignore it, no wave-1 test fails. The defect first shows in wave 2's green run,
and no wave-2 task owns the file.
Material-because: none of the five classes. Wave 2's green run fails on it before any push, and re-dispatching 1.4
fixes it, at the cost of one more dispatch.
Proposed-edit: in 1.4, after "paired with 1.2's H, unedited" insert "; its keywords' values other than the defaults
are first exercised by 2.1's S through 2.5, so a wave-2 S failure traced to `test/forge/ephemeral.py` re-dispatches
1.4".

## Order, dependencies and red runs on the current tasks.md

- **Order.** In every wave the TEST tasks come before the IMPL tasks.
- **Disjoint files.**
  - Wave 1: W; none (the guards); the wrapper and `errors.py`; `test/forge/ephemeral.py`.
  - Wave 2: S; G; L; `ci.yml`; the GitLab `ephemeral.py`.
  - Wave 3: S; G; `ephemeral.py`; `write_credential.py`.
  - Waves 4 and 5 are unchanged apart from their ids.
- **Dependencies on earlier waves only.**
  - 2.5 uses 1.3's `EPHEMERAL_PROJECT_PREFIX` and 1.4's keywords.
  - 3.3 uses 2.5's constants and 1.3's `TEST_MARKER_OPTION`.
  - 3.4 uses 2.5's part 1 and 1.4's `write_test_credential` keywords, and nothing from 3.3.
  - The spec lane's B1 is resolved.
- **Red for the right reason, given what the earlier waves built.**
  - Wave 1: W fails on the guard that 1.3 adds.
  - Wave 2: S's five tests fail in their bodies, loading the absent `test/forge_gitlab/ephemeral.py`. G's three job
    tests and L's 2.3 expectation fail because `ci.yml` has no `forge-gitlab`. G's AC-7.1 test fails on the exit code
    while `test/forge_gitlab/` is absent.
  - Wave 3: S's five new tests fail on the attributes 3.3 adds. The extended `test_a_missing_secret_fails_the_credential_step`
    fails on the absent `write_credential.py`. G's AC-8.7 test fails because `PRODUCT_WRAPPER` is not yet in
    `SubprocessWrapperRunner`.
  - Each of these is a `FAILED` test that was collected. `red_for_right_reason.py` `judge` refuses a capture only when
    an import error and a collection error appear together.
- **`ci.yml` before `write_credential.py` breaks no guard.** `ci.yml` (2.4) names `test/forge_gitlab/write_credential.py`
  one wave before 3.4 writes it. G's and L's secret tests compare only the `run:` text, and `test/test_layout.py`
  `FRAMEWORK_PATH` matches no `test/` path.
- **Guards.** 1.2's guards join every wave's red and green runs. Each wave's runs also hold the S, G and L files that
  wave writes, and wave 5 adds S for 5.9. W runs only in wave 1, and no later wave edits `gitlab_wrapper.py` or
  `errors.py`.
- **Ids.** The cross-references were renumbered consistently: 1.2 now points to 2.3 and 2.4, 3.2 to 3.3, and Runs and
  F.1 to 5.2 to 5.6.
- **Test functions per task** match the design's mapping:
  - W: 5, in 1.1.
  - S: 16, in 2.1, 3.1 and 4.1. AC-5.3's test is split between 2.1 and 3.1, as in #10's 4.2 and 4.6.
  - G: 11, in 2.2, 3.2, 4.2 and 5.1.
  - F: 12, in 5.2 to 5.6.
  - L: 1, in 2.3.

## Coverage

| Criterion | TEST task(s) | State |
|---|---|---|
| AC-1.1 | 2.1, 4.1, 5.1, 5.2 | OK |
| AC-1.2 | 2.1 | OK |
| AC-1.3 | 4.1, 5.2, 5.3, 5.4 | OK |
| AC-1.4 | 4.1, 5.1 | OK |
| AC-2.1 | 3.1 | OK |
| AC-2.2 | 3.1 | OK |
| AC-2.3 | 4.1 | OK |
| AC-3.1 | 3.1, 5.2 | OK |
| AC-3.2 | 3.1 | OK |
| AC-3.3 | 3.1 | OK |
| AC-4.1 | 1.1 | OK |
| AC-4.2 | 1.1, 5.2, 5.3, 5.4, 5.5, 5.6 | OK |
| AC-4.3 | 1.1, 3.1, 3.2 | OK |
| AC-5.1 | 2.2 (F.1) | OK |
| AC-5.2 | 2.2, 5.1 (F.1) | OK |
| AC-5.3 | 2.1, 3.1 | OK |
| AC-5.4 | 2.2, 2.3 | OK |
| AC-6.1 | 2.1 | OK |
| AC-6.2 | 4.1 | OK |
| AC-6.3 | 2.1, 2.2, 4.1 | OK |
| AC-7.1 | 2.2 | OK |
| AC-7.2 | 5.1 | OK |
| AC-7.3 | 5.1 | OK |
| AC-8.1 | 3.2, 5.2, 5.3, 5.4, 5.5, 5.6 | OK |
| AC-8.2 | 5.3 | OK |
| AC-8.3 | 5.2, 5.4 | OK |
| AC-8.4 | 5.5 | OK |
| AC-8.5 | 5.1, 5.6 | OK |
| AC-8.6 | 5.1, 5.6 | OK |
| AC-8.7 | 3.2 | OK |
| AC-9.1 | 4.2 | OK |
| AC-9.2 | 4.2, 1.2 (B) | OK |
| UB-1 | 1.1, 1.2, 2.1, 2.2, 3.1 | OK |
| UB-2 | 4.1 | OK |
| UB-3 | 1.1, 1.2 | OK |
| UB-4 | 1.2 (H, L), 2.3 | OK |
| UB-5 | 1.2 (I) | OK |

37 OK, 0 GAP.

CLEAN — TEST-READY
