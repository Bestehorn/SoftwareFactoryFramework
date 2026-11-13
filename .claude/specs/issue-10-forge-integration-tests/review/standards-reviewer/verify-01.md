# Standards review — VERIFY, delta pass 01 (implemented diff 590e4a9..59d5928)

### B1 — The one custom exception of the change without `details=None`
Severity: B
Location: test/test_forge_support.py § `_BodyFailure` (the provisioning tests of AC-1.4)
Defect: `_BodyFailure(Exception)` defines no `__init__` and takes no `details=None` keyword argument. Every other
custom exception in this change takes it (`ForgeSuiteError` in `test/forge/ephemeral.py`, `WorkflowReadError` in
`test/test_forge_suite_layout.py`), and so does the comparable test-local exception in `test/`
(`DocumentSyntaxError` in `test/test_github_graphql_contract.py` and `test/test_gitlab_graphql_contract.py`).
Material-because: unmaintainable-by-rule coding-standards.md: rule 5 says "Custom exceptions take a `details=None`
default kwarg", and the rule file's title says "NO EXCEPTIONS".
Proposed-edit: give the class the shape `WorkflowReadError` has, and leave the raise site
`raise _BodyFailure("the test body raised")` and the module's imports (`Any`, `Dict`, `Optional` are imported) as
they are:
```
class _BodyFailure(Exception):
    """What a test body raises, to show that the teardown runs whatever the body does (AC-1.4)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details
```

### C1 — The new lesson names a test that cannot enforce it
Severity: C
Location: docs/lessons-learned.md § "2026-11-12 — A delegate probing git credentials must pass -c credential.h"
Defect: The lesson is about how a delegate behaves ("must pass -c credential.helper= first"). Its `Enforced-by`,
`test/test_forge_support.py test_the_credential_helper_answers_git_with_the_clone_token`, only proves that the
suite's own `credential_helper_arguments` options reset a helper configured before them. Nothing stops a delegate
from running a bare `git credential fill`: no hook in `src/hooks/`, no rule in `clients/` and nothing in
`.claude/settings.json` names `credential.helper` or `credential fill`. `use-lessons-learned.md` step 4 compiles only
entries marked `Enforced-by: none`, so this entry would never be compiled into a real mechanism.
Proposed-edit: change the entry's `- Enforced-by:` value to `none`, through `scripts/memory_compile.py` if a
correction must go through the tool.

### C2 — The design's Residuals have no findings-ledger rows yet
Severity: C
Location: design.md § Residuals; docs/findings-ledger.md
Defect: The diff adds one ledger row for issue #10 (the `forge provision` row) and none for the nine bullets of
design.md § Residuals. `issue-filing-discipline.md` sends every residual that is neither fixed nor filed to a ledger
row "committed in the change they came from, before its push".
Proposed-edit: before the change's last push, the conductor adds one
`python scripts/memory_compile.py ledger add --subject ... --finding ... --evidence "issue-10 design.md Residuals" --why ...`
row for each Residual that was neither fixed nor filed.

### D1 — A literal beside its own constant
Severity: D
Location: test/test_forge_suite_layout.py § `read_workflow`, `test_the_secret_reaches_one_step`
Defect: Both read `ci.yml` with `encoding="utf-8"`, while the module defines `SOURCE_ENCODING = "utf-8"` and uses
it for every other read.
Proposed-edit: `encoding=SOURCE_ENCODING` at both sites.

## Lens items with no finding

- `coding-standards.md`. JSON fields are read through `FIELD_*` constants in `ephemeral.py`, the four `forge_*.py`
  modules and both new test files. There are no relative imports, no `print` and no `os.path` (Grep of the diff).
  Every project-defined callable takes keyword arguments. Positional calls go only to stdlib functions such as
  `ast.walk(tree)`, `re.compile(..., re.X)` and `datetime.strptime`, as `test/test_github_wrapper_coverage.py` and
  `src/payload/scripts/merge_steward.py` already do. Exception messages are passed positionally, as in 88 `raise`
  sites in `src/`. `ForgeSuiteError` (`details=None`) is the base of `ForgeSetupError`, `ForgeCommandError`,
  `ForgeTeardownRefusedError` and `ForgeSweepRefusedError`. Every class name shows its parent:
  `SubprocessWrapperRunner(WrapperRunner)`, `SubprocessGitRunner(GitRunner)`, and the test doubles
  `RecordingWrapperRunner` and `ScriptedGitRunner`.
- Line length and formatting: `ruff check` reports "All checks passed!" on the 12 changed Python files at HEAD, and
  `ruff format --check` reports "12 files already formatted". No added line is longer than 120 columns.
- `tech-stack.md`. `src/` gains only `sys._xoptions` reads. Nothing in the diff needs Python 3.10 or later: the
  built-in generics stand in annotations under `from __future__ import annotations`. `hypothesis` and `pytest-xdist`
  are in the `dev` extra of `pyproject.toml`.
- Duplication. A by-path loader in each entry point (`conftest.py`, `write_credential.py`, `test_forge_support.py`)
  is how the codebase works: `spec_from_file_location` appears in more than 100 test files. No workflow or YAML
  reader existed before, so `WorkflowReader` duplicates nothing.
- `tests-must-not-fail.md`. The diff has no `skip`, `skipif`, `xfail`, `importorskip` or `collect_ignore`; those words
  appear only in the detector `test_nothing_keeps_a_forge_test_from_running`.
- `no-environment-vars.md`. `os.getenv` appears once, in `write_credential.main`, with the step-level `env:` of
  `ci.yml`. The test sets `SFF_TEST_TOKEN` only through `monkeypatch`. No runner passes `env`.
- `use-git-wrapper-scripts.md`. The forge suite reaches GitHub only through the product wrapper subprocess and through
  git fetch and push. There is no `gh`, `curl` or `urllib` in the diff.
- `project-specific.md`. No changed path is a key of `config/toolchain.json` `files`. `ci.yml` is the project's own
  (`not_installed` `templates/ci/*`, settled at design iteration 01, C1).
- The `ci.yml` header contract: `forge` has no `needs:` and one check command, and `report` has
  `needs: [verify, forge]` and `if: always()` and fails unless `needs.forge.result` is `success`. The header now
  describes the forge job.
- `no-ai-attribution.md`. No added line and no message of `git log 590e4a9..HEAD` contains an attribution term or
  trailer. The commit subjects are imperative and describe the change.
- `file-organization.md`. The Python sits in `src/` and `test/`, and the docs in `docs/`. The forge workspace is a
  `tempfile.mkdtemp` directory (the design residual on scoped temp).

NOT-CLEAN (0 A, 1 B)
