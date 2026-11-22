# spec-review-agent — tasks review iteration 01 (report-only)

### B1 — Three IMPL tasks of Wave 1 depend on other IMPL tasks of Wave 1
Severity: B
Location: tasks.md § Wave 1, tasks 1.9 and 1.10 (against 1.6 and 1.8)
Defect: 1.9 builds on keyword-only parameters that 1.8 adds in the same wave. It calls the reused
`refuse_distributed_run` with `command=`, binds `credential_helper_arguments(helper_key=, username=,
credential_file=)` into `CLONE_GIT_HELPER`, and calls `product_wrapper(path=, module_name=)`. Today
`test/forge/ephemeral.py` has `refuse_distributed_run(*, worker_id)`, `credential_helper_arguments(*, clone)` and
`product_wrapper()`, with none of those keywords. 1.9's `ephemeral_path` also reads the product's
`EPHEMERAL_PROJECT_PREFIX` (D4), which 1.6 adds in the same wave; `gitlab_wrapper.py` defines no such constant today.
1.10 loads the module that 1.9 writes and calls `write_test_credential(credential_file=, secret_name=)` from 1.8.
GREEN dispatches 1.6, 1.8, 1.9 and 1.10 together, so three of them call code that another task of the same dispatch is
still writing.
Material-because: unmaintainable-by-rule `.claude/specs/_workflow/phases/spec-phase-tasks.md` ("Tasks inside a wave
own DISJOINT files and depend only on earlier waves"). An implementer of 1.9 or 1.10 that runs its paired S tests before
1.8 lands gets a `TypeError` for the unknown keyword. Its nearest fixes are to edit `test/forge/ephemeral.py`, which 1.8
owns, or to stop reusing #10's functions. Either one breaks D10. Precedent #10 kept every dependency across waves:
`ephemeral_name` (2.3) read the guard constant of 1.5, and `write_credential.py` (4.6) came after `ephemeral.py` part 1
(1.7).
Proposed-edit: split Wave 1 into two waves and renumber the rest, giving five waves:
- "## Wave 1 — The project guard and the reused module's parameters": 1.1, 1.4, 1.6 and 1.8. In 1.8, replace "paired
  with 1.4's H, unedited, and with 1.2's S tests, which call the parameters" with "paired with 1.4's H, unedited", and
  set its `Validates:` to "UB-4".
- "## Wave 2 — The GitLab forge job and the credential primitives": 1.2 with ", and `write_credential.main`" deleted,
  plus 1.3, 1.5, 1.7 and 1.9. 1.3's `test_the_default_configuration_collects_no_gitlab_forge_test` stays red until
  1.9 creates `test/forge_gitlab/`.
- 1.10 moves into the wave that holds today's 2.1 to 2.3. 2.1 gains "and `test_a_missing_secret_fails_the_credential_step`
  extended: `write_credential.main`, loaded by path, logs the refusal and returns 1, and with a token writes the file
  and returns 0", and its `Validates:` gains AC-5.3, as #10's 4.2 and 4.6 did.
- Today's Waves 2 to 4 become Waves 3 to 5. In "Runs", replace "wave 4's red and green captures" with "wave 5's red and
  green captures".

### C1 — One G test of Wave 4 is green in its own red capture
Severity: C
Location: tasks.md § Wave 4, 4.1 `test_each_uncalled_form_is_named_with_its_reason` against 4.6
Defect: the G test reads the module docstring of `forge_request_forms.py`. 4.6 writes that docstring, and 4.6 is a TEST
task in the same wave, so it exists by the time of the RED capture. The other three 4.1 tests are red for the right
reason. `pytest.ini` (4.7) and `conftest.py` (4.8) do not exist yet, and `collect_only`, `configuration_problems` and
`session_fixture_problems` fail on assertions. This one test passes, though. No wave shows it failing, and stubbing
wave 4's IMPL tasks (4.7 to 4.9) does not make it fail (`spec-phase-implement.md` VERIFY). Moving the test cannot fix
this: an earlier wave's green would fail, and the docstring cannot become an IMPL task without breaking file
disjointness.
Proposed-edit: append to the "Runs" bullet: "G `test_each_uncalled_form_is_named_with_its_reason` reads the docstring
4.6 writes, so it is green in wave 4's red capture: it is the one new test that no capture shows red."

### C2 — `push_branch` and `wait_until_checked` (4.9) have no test in any capture
Severity: C
Location: tasks.md § Runs; § Wave 4, 4.9
Defect: "Runs" says that only 4.2 to 4.6 are validated by F.1 alone. 4.9 is an IMPL task, and its only callers are the
F modules 4.3, 4.4 and 4.6. Wave 4's red and green captures run G and the guards, which call neither function. Its
behaviours (`git add` by name, never `-A`; the deadline raising `ForgeCommandError` that names the last status) are
therefore proven only by F.1 against gitlab.com. This matches the design: Correctness Properties AC-8.2, AC-8.3 and
AC-8.5 are Integration only. The tasks do not say it, though.
Proposed-edit: in "Runs", replace "The GitLab forge modules (4.2 to 4.6) are declared" with "The GitLab forge modules
(4.2 to 4.6), and 4.9's `push_branch` and `wait_until_checked`, which only they call, are declared".

## Residuals

None.

Verdict: NOT-READY (A 0, B 1, C 2, D 0) — NOT-CLEAN (0 A, 1 B)
