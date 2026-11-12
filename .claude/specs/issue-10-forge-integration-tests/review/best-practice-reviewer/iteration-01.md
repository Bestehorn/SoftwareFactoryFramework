# Best-practice review — design iteration 01

No documentation MCP server covers pytest, CPython, git or GitHub; sources are the official web docs (fetched
2026-11-12), the installed pytest 9.2.0 / pytest-xdist source, and local runs on git 2.53.0.windows.1 and CPython 3.14.2.

### C1 — `report` keeps `if: always()`, which GitHub's expressions reference advises against for a job that fetches sources
Severity: C
Location: design.md § D5 (`report`)
Defect: docs.github.com "Expressions" `always()`: "Avoid using `always` for any task that could suffer from a critical
  failure, for example: getting sources, otherwise the workflow may hang until it times out. If you want to run a job or
  step regardless of its success or failure, use the recommended alternative: `if: ${{ !cancelled() }}`". The `report`
  job checks out under `always()`. The condition is the existing job's, and the `ci.yml` header contract ("a report job
  that always runs and decides") and AC-5.4 ("whatever their results") match it as written.
Material-because: not material to this change; switching changes what the existing `report` job does on a cancelled run.
Proposed-edit: none in this change; one line under design.md `## Residuals`: "`report`'s `if: always()` against GitHub's
  recommended `if: ${{ !cancelled() }}` (docs.github.com Expressions, `always`): a workflow-wide choice outside issue #10."

### C2 — the new job pins actions that declare the deprecated Node 20 runtime
Severity: C
Location: design.md § D5 (`forge`: `actions/checkout@v4`, `actions/setup-python@v5`)
Defect: GitHub changelog 2025-09-19 "Deprecation of Node 20 on GitHub Actions runners"
  (github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/) deprecates the Node 20 action
  runtime that these majors declare; the runner now runs them on Node 24 with a deprecation warning. The new job reuses
  the pins `verify` and `report` already carry, which keeps the workflow uniform.
Material-because: not material: the actions still run, and moving every pin is a workflow-wide change.
Proposed-edit: none in this change; one line under design.md `## Residuals`: "The workflow's action pins
  (`checkout@v4`, `setup-python@v5`, `upload-artifact@v4`, `download-artifact@v4`) declare the deprecated Node 20
  runtime (GitHub changelog 2025-09-19); moving them is outside issue #10."

### C3 — git can print the common directory as an absolute path, which removes D8's relative-path branch
Severity: C
Location: design.md § D8 (Lookup)
Defect: git-scm.com/docs/git-rev-parse `--path-format`: "If specified as absolute, the paths printed by those options
  will be absolute and canonical", and `--git-common-dir` is one of those options. Measured: run in the main working tree,
  `git rev-parse --git-common-dir` prints `.git`, and `git rev-parse --path-format=absolute --git-common-dir` prints
  `D:/Code Workspace/CodingProjectSetupPrompt/.git`. D8's "relative to `checkout` when it prints a relative path" is then
  a path-joining branch that one documented option makes unnecessary.
Material-because: clarification only; the design as written is correct.
Proposed-edit: in D8 Lookup replace "the parent of `git rev-parse --git-common-dir` run in `checkout` (relative to
  `checkout` when it prints a relative path)" with "the parent of `git rev-parse --path-format=absolute
  --git-common-dir` run in `checkout`".

### D1 — D3's reason for rejecting a helper that reads the test credential file does not hold for git
Severity: D
Location: design.md § D3 (Alternatives, `git clone` with the helper reading the test credential file)
Defect: Measured: `read -r` in Git for Windows' `sh` keeps a trailing CR (`printf 'abc\r\n' | sh -c 'read -r t; ...'`
  gives `a b c \r`). But git's credential reader drops a CR before the line end: a helper that prints `password=abc\r`
  gets `password=abc` back from `git credential fill`. So "may end in CRLF, which `read` keeps" is not why that file
  cannot feed git. The chosen design stands on its own.
Material-because: wording of a rejected alternative's rationale.
Proposed-edit: replace "(that file is the operator's text and may end in CRLF, which `read` keeps; the clone's file
  holds the token as `_one_token` strips it)" with "(that file is the operator's text; the clone's file holds exactly the
  token `_one_token` accepted from it)".

CLEAN
