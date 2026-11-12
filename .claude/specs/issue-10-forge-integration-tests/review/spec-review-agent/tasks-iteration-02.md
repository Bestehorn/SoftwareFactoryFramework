# Tasks review, iteration 02 (delta) — spec-review-agent

## Prior findings

- B1 resolved. 1.3 now has S load `ephemeral.py` by path inside each test body through a cached helper, with
  nothing at module level, and builds the doubles of 2.1 and 3.1 and 4.2's load of `write_credential.py` the same
  way. S therefore collects in waves 1 to 4. The red runs pass `red_for_right_reason.judge`. In wave 1 S's tests
  fail in their bodies (the file is absent), in wave 2 they fail on `WrapperRunner`, and in wave 4 on
  `write_credential.py`. Each failure shows as a pytest `FAILED <file>::<test>` line, which `RIGHT_REASON_RE`
  matches, and no capture holds an `ERROR collecting` line. W and L add real assertion failures.
- B2 resolved. Wave 5 and its paragraph are deleted, and 5.1 to 5.4 are now 4.7 to 4.10 with their `Validates:`
  lists unchanged. The Wave 4 heading, the Runs paragraph, 4.3 (its "Red:" sentence deleted) and F.1 now read as
  proposed. Wave 4's red capture is S and L plus the guards. Its first line, `# tasks:`, names 4.1 to 4.3 and 4.7
  to 4.10 (`spec-phase-implement.md` RED). The L test 4.1 `test_the_forge_path_collects_every_forge_test` fails on
  an assertion until 4.4 exists. `hooklib.capture_for_task` matches whole tokens and `is_heading_id` uses a
  `<id>.` prefix, so `4.1` and `4.10` never cover each other.
- C1 resolved. 3.3 names `CHECKOUT`. No task before wave 3 needs it: 1.7's `find_test_credential` and
  `write_test_credential` take `checkout` as a parameter (D8). 4.5 and 4.6 in wave 4 can use it.
- C2 resolved. 4.6 now says that `write_credential.py` loads `ephemeral.py` by path, as D10's `conftest.py` row
  does, and calls `write_test_credential`. That works both when CI runs it as a script and when S loads it by path
  under `--import-mode=importlib`.

The delta keeps every wave's files disjoint. Wave 4's ten tasks write ten distinct paths, and wave 3 still has one
writer of `ephemeral.py`. Every TEST task in a wave is dispatched before every IMPL task, whatever the order of the
list. The test-architect's C3 is checked too. `github_wrapper_fixtures.load_script`, `enter_project` and
`FakeGitHub` exist (`src/payload/test/github_wrapper_fixtures.py`), and C's `load_wrapper` calls `fx.load_script`
on a fixtures module that C loads by path (`src/payload/test/test_github_wrapper_compat.py` `_load_fixtures`).

### C1 — 1.3's cached helper does not say it registers the module in `sys.modules`
Severity: C
Location: tasks.md § 1.3
Defect: Both of the project's by-path loaders of a dataclass module register the module in `sys.modules` before
they execute it. They reuse it when its `__file__` is the same path: P and C `_load_fixtures`, whose docstring says
"`sys.modules` holds it for its dataclasses". D10 asks the same of `conftest.py`. 1.3's "through a cached helper"
does not say so. A helper that only memoises a `module_from_spec` result therefore loads a second copy of
`ephemeral.py` alongside the one the default collection's `conftest.py` loads.
Proposed-edit: in 1.3 replace "through a cached helper," with "through a cached helper that, like P's
`_load_fixtures`, registers it in `sys.modules` before executing it and reuses it when its `__file__` is this path,".

CLEAN
