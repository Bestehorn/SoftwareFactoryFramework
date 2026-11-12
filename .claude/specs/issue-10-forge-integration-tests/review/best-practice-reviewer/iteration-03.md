# Best-practice review — design iteration 03 (delta)

No documentation MCP server covers CPython; sources are python.org release pages and docs.python.org, fetched
2026-11-12.

Iteration-02 C1 is applied: D8 Writing now scopes the Windows protection to a CPython with the CVE-2024-4030 fix and
quotes the 3.9.20 release notes. The quote is verbatim (python.org `python-3920`, gh-118486 entry).

### C1 — "the 2024 security releases of 3.9 to 3.11" includes releases without the CVE-2024-4030 fix
Severity: C
Location: design.md § D8 (Writing)
Defect: python.org `python-3919` and `python-31014` (both 2024-03-19) say "This is a security release of Python 3.9"
  / "of Python 3.10" and carry no gh-118486 entry; the fix ships in 3.9.20 (2024-09-06), 3.10.15 and 3.11.10
  (2024-09-07), whose pages quote the gh-118486 entry, and in 3.12.4 (2024-06-06, docs.python.org 3.12 changelog,
  Security). So the version list overstates which interpreters are covered, while its governing clause ("a CPython
  with the CVE-2024-4030 fix") is right.
Material-because: not material: the forge job runs on ubuntu, where `0o600` and `mkdtemp`'s `0o700` both apply; the
  sentence only scopes a Windows note.
Proposed-edit: replace "3.12.4 and later and the 2024 security releases of 3.9 to 3.11" with "3.12.4 and later,
  and 3.9.20, 3.10.15 and 3.11.10 and later".

### D1 — "owner-only" is narrower than the documented Windows ACL
Severity: D
Location: design.md § D8 (Writing)
Defect: docs.python.org `os.mkdir`: on Windows a mode of `0o700` gives access to "only the current user and
  administrators".
Material-because: wording.
Proposed-edit: replace "owner-only on a CPython with the CVE-2024-4030 fix" with "limited to the current user and
  administrators on a CPython with the CVE-2024-4030 fix".

### D2 — the Residuals line says `reap_agent_temp.py --scoped-temp` empties the scoped temp; it reports unless `--apply`
Severity: D
Location: design.md § Residuals (interrupted local run)
Defect: `src/payload/scripts/reap_agent_temp.py` module docstring: "Read-only unless --apply"; its `--apply`
  argument: "delete; default is report only".
Material-because: wording (a Residuals note, no criterion rests on it).
Proposed-edit: replace "`reap_agent_temp.py --scoped-temp` empties it" with "`reap_agent_temp.py --scoped-temp
  tmp/os-temp --apply` empties it".

The other delta items (the `USERINFO_SEPARATOR` idiom, the `ast` checks, the Rollback's secret deletion and token
revocation) touch no external technology choice that needs a documentation check.

CLEAN
