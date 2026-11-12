# Design review — spec-review-agent — iteration 03 (delta)

Lens: implementability and internal consistency of the delta (170b4ba to the current revision); cited symbols as
described.

## Iteration-02 items

- D1 — applied. The AC-6.2 mapping row reads "D8 `read_test_token`; D9 step 2", matching D9 step 2 and D8 "Reading".
- D2 — applied. D2 reads `owner.rpartition(USERINFO_SEPARATOR)[2]`; `github_wrapper.py` defines
  `USERINFO_SEPARATOR = "@"`, and `_without_userinfo` strips with `match.group(1).rpartition(USERINFO_SEPARATOR)[2]`.

The delta holds where I checked it. The new AC-4.3 oracle (only `ephemeral.py` names `product_wrapper`;
`PRODUCT_WRAPPER` only in `SubprocessWrapperRunner` and `product_wrapper`; no `main` attribute read in `test/forge/`)
does not conflict with D10. `conftest.py` builds the runners and calls `provision`. Nothing in D9 or D6 makes it or a
forge module name `product_wrapper` or read `.main`, and `write_credential.main` is called only from S, outside
`test/forge/`. The `worker_id=worker_id` clause of L is satisfiable: `pyproject.toml` dev extra lists `pytest-xdist`,
and `pytest.ini` `addopts` disables only `cacheprovider`. The extended AC-6.1 example matches `requirements.md` AC-6.1
and D8 "Lookup" (the checkout's own file first). `requirements.md` is unchanged, and no fix added a criterion or a
mechanism beyond the consolidated list.

## Findings

### C1 — D8's Windows sentence names the fixed CPython releases and the access set inexactly
Severity: C
Location: design.md § D8, "Writing"
Defect: "the 2024 security releases of 3.9 to 3.11" also covers 3.9.19 and 3.10.14. Both are 2024 security releases
from 19 March 2024 that do not carry the CVE-2024-4030 fix. python.org 3.9.19 lists CVE-2023-52425, CVE-2024-0450 and
CVE-2023-6597; the fix (gh-118486) shipped in 3.9.20, 3.10.15 and 3.11.10 in September 2024, and in 3.12.4. Also,
docs.python.org `os.mkdir` says a `0o700` mode on Windows gives access to "only the current user and administrators",
not to the owner alone.
Proposed-edit: replace "owner-only on a CPython with the CVE-2024-4030 fix, 3.12.4 and later and the 2024 security
releases of 3.9 to 3.11" with "limited to the current user and administrators (docs.python.org `os.mkdir`) on a
CPython with the CVE-2024-4030 fix: 3.9.20, 3.10.15, 3.11.10, 3.12.4 and later".

### D1 — The Residuals line names a reaper command that deletes nothing
Severity: D
Location: design.md § Residuals, the interrupted-local-run line
Defect: the line says "`reap_agent_temp.py --scoped-temp` empties it". The script's docstring opens "Read-only unless
--apply", and its USAGE line and `/close-session` both run `--scoped-temp tmp/os-temp --apply`.
Proposed-edit: replace "`reap_agent_temp.py --scoped-temp` empties it" with "`reap_agent_temp.py --scoped-temp
tmp/os-temp --apply` (run by `/close-session`) empties it".

CLEAN
