# Standards review — design, iteration 02 (delta)

## Iteration-01 findings

- B1 resolved. `design.md` now names only `ForgeTeardownRefusedError` and `ForgeSweepRefusedError`: D9 "The teardown
  guard" and "The sweep", the D10 `ephemeral.py` row, and Correctness Properties AC-2.2 and AC-3.1/AC-3.2. Neither
  `requirements.md` nor `design.md` still holds an unprefixed name.
- C1 applied (the first paragraph of D5; the promotion-only wording became a Residual). C2 applied (Overview, "One
  deviation"). C3 applied (the D10 `ephemeral.py` row; its wording is D1 below). C4 applied (D1 Alternatives). C5
  applied (the D10 map row). D1 applied (`RepositoryRecord.of(item=<item>)`).
- Scope: every changed region traces to a row or a bullet of `review/review-latest.md`. No acceptance-criterion id
  and no requirement was added. AC-6.1 is restated, not widened by a new criterion (DL-002).

### C1 — The refusal strips the owner with a literal where the wrapper already has a constant and an idiom
Severity: C
Location: design.md § D2, `_refuse_unless_ephemeral`
Defect: The delta writes `shown` as `owner.rpartition("@")[2]`. `src/payload/scripts/github_wrapper.py` already
defines `USERINFO_SEPARATOR = "@"` and strips userinfo with exactly this idiom in `_without_userinfo`
(`match.group(1).rpartition(USERINFO_SEPARATOR)[2]`). That module names each of its separators as a constant
(`MODULE_SEPARATOR`, `PRIVATE_MODULE_PREFIX`). Implemented as written, the design adds a second spelling of the same
value next to the constant (`design-principles.md` rule 2).
Proposed-edit: replace "`owner.rpartition("@")[2]`" with "`owner.rpartition(USERINFO_SEPARATOR)[2]`, the idiom of
`_without_userinfo`".

### C2 — The residual about the leftover workspace overlooks the scoped temp directory
Severity: C
Location: design.md § Residuals, "Nothing removes the workspace an interrupted local run leaves in the temporary
directory"
Defect: The residual is true only for a run outside a scoped session:
- `tempfile.gettempdir()` checks `TMPDIR` first (docs.python.org `library/tempfile.html`).
- This project's `.claude/settings.local.json` points `TMPDIR`, `TEMP` and `TMP` at `tmp/os-temp`
  (`no-environment-vars.md` CLARIFICATION 2), so in a session `mkdtemp` places the workspace there.
- `scripts/reap_agent_temp.py --scoped-temp` removes the whole contents of that directory (its docstring, "THE
  OWNERSHIP RULE", tier 1), and `post-activity.md` step 5 cleans `tmp/`.
Proposed-edit: replace the residual with "An interrupted local run outside a scoped temp directory
(`no-environment-vars.md` CLARIFICATION 2) leaves its workspace in the shared temporary directory, where nothing
removes it; in a scoped session the workspace lies under `tmp/os-temp`, which `reap_agent_temp.py --scoped-temp`
empties."

### C3 — The Windows owner-only claim holds only on an interpreter with the CVE-2024-4030 fix
Severity: C (borders on the security lens)
Location: design.md § D8, Writing
Defect: The delta relies on the owner-only `tempfile.mkdtemp` workspace to protect the clone's credential file on
Windows. On Windows, `mkdtemp` restricts access only since gh-118486 (CVE-2024-4030): the Python 3.11.10 release notes
say "os.mkdir() on Windows now accepts mode of 0o700 to restrict the new directory to the current user", and
`os.mkdir` says "Changed in version 3.13: Windows now handles a mode of 0o700". `tech-stack.md` keeps the code on
Python 3.9+, and on a Windows interpreter without the fix the workspace takes its parent directory's ACL. This
machine's venv (`venv/pyvenv.cfg`, 3.14.2) has the fix, and the forge job runs on a POSIX runner.
Proposed-edit: after "the owner-only protection is the `tempfile.mkdtemp` workspace's", insert "on a CPython that
carries the CVE-2024-4030 fix (gh-118486)".

### D1 — The clause inserted into the `ephemeral.py` row also captures the items after it
Severity: D
Location: design.md § D10, the `test/forge/ephemeral.py` row
Defect: After the C3 insertion, the row reads "which it reads from `product_wrapper()` as it reads `_one_token` and
`PLACEHOLDER`, the commit identity and a subprocess timeout", which says the commit identity and the timeout also come
from `product_wrapper()`.
Proposed-edit: "new: the constants D3 to D9 name (except `TEST_MARKER_OPTION` and `EPHEMERAL_REPOSITORY_PREFIX`,
which it reads from `product_wrapper()`, as it reads `_one_token` and `PLACEHOLDER`), the commit identity and a
subprocess timeout; ..."

CLEAN
