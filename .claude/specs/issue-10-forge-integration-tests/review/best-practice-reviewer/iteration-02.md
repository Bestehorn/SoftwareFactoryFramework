# Best-practice review — design iteration 02 (delta)

No documentation MCP server covers git, pytest, CPython or GitHub; sources are the official web docs (fetched
2026-11-12), the installed pytest 9.2.0 source (`_pytest/logging.py`), and local runs on git 2.53.0.windows.1 and
CPython 3.14.2.

Iteration 01 carried no A/B finding. C3 is applied (D8 Lookup: `git rev-parse --path-format=absolute
--git-common-dir`, relative-path branch gone); D1 is applied (D3 Alternatives); C1 and C2 stand as design.md Residuals.

### C1 — the Windows owner-only claim for the `mkdtemp` workspace holds only from CPython 3.12.4 / 3.13
Severity: C
Location: design.md § D8 (Writing)
Defect: docs.python.org `os.mkdir`: "On Windows, a mode of `0o700` is specifically handled to apply access control to
  the new directory such that only the current user and administrators have access", "Changed in version 3.13: Windows
  now handles a mode of `0o700`" (backported to 3.12.4, gh-118486); before it, CVE-2024-4030: a `tempfile.mkdtemp()`
  directory on Windows "would not always have permissions set to restrict reading and writing to the temporary
  directory by other users, instead usually inheriting the correct permissions from the default location".
  `pyproject.toml` declares `requires-python = ">=3.9"`, so on Windows with an older interpreter the D8 sentence "the
  owner-only protection is the `tempfile.mkdtemp` workspace's" does not hold.
Material-because: not material: the forge job runs on ubuntu (POSIX, where `0o600` and `mkdtemp`'s `0o700` both
  apply), the interpreter here is 3.14.2, and on an older one the copy gets the temporary directory's inherited access,
  just as the test credential file in the checkout gets the checkout's.
Proposed-edit: in D8 Writing replace "the owner-only protection is the `tempfile.mkdtemp` workspace's, D9: "readable,
  writable, and searchable only by the creating user ID")" with "the protection is the `tempfile.mkdtemp` workspace's,
  D9: limited to the current user and administrators from CPython 3.12.4 and 3.13 (docs.python.org `os.mkdir`:
  "Windows now handles a mode of `0o700`"), the temporary directory's inherited access before)".

CLEAN
