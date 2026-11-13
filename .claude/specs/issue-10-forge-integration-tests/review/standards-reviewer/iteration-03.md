# Standards review — design, iteration 03 (delta)

## Iteration-02 items

- C1 applied: D2 writes `shown` as `owner.rpartition(USERINFO_SEPARATOR)[2]`, "the idiom of `_without_userinfo`".
  Both names exist in `src/payload/scripts/github_wrapper.py` (`USERINFO_SEPARATOR = "@"`, `_without_userinfo`).
- C2 applied, in the merged wording of devops D1 (Residuals, "Nothing in this change removes ..."). Its wording is C2
  below.
- C3 applied (D8, Writing). Its version range is C1 below.
- D1 applied: the D10 `ephemeral.py` row puts the `product_wrapper()` clause in parentheses, scoped to the two
  constants.
- Scope: every hunk of the delta traces to a row or bullet of `review/review-latest.md`. `requirements.md` is not in
  the delta, and no acceptance-criterion id or requirement was added. The new L oracle for AC-4.3 and the AC-1.1
  `worker_id=worker_id` clause agree with D1 (xdist's `worker_id` fixture; `pytest-xdist` is declared in
  `pyproject.toml`) and with D10. Only `test/test_forge_support.py`, which lies outside `test/forge/`, reads
  `write_credential.main`.

### C1 — "the 2024 security releases of 3.9 to 3.11" includes releases without the fix
Severity: C
Location: design.md § D8, Writing
Defect: The new sentence says the fix is in "3.12.4 and later and the 2024 security releases of 3.9 to 3.11". Python
3.9.19 and 3.10.14 are 2024 security releases (python.org: "Release date: March 19, 2024 This is a security release
of Python 3.9"), and they do not carry gh-118486. It first ships in 3.9.20, 3.10.15 and 3.11.10 (python.org release
pages, September 2024, "gh-118486: os.mkdir() on Windows now accepts mode of 0o700 ...") and in 3.12.4 (2024-06-06
changelog). As written, a reader on 3.9.19 would believe the workspace is owner-only, and it is not (`no-guessing.md`).
Proposed-edit: replace "3.12.4 and later and the 2024 security releases of 3.9 to 3.11" with "3.9.20, 3.10.15,
3.11.10, 3.12.4 and later".

### C2 — The residual names the reaper without `--apply`, which only reports
Severity: C
Location: design.md § Residuals, "Nothing in this change removes the workspace an interrupted local run leaves ..."
Defect: The residual says "`reap_agent_temp.py --scoped-temp` empties it". The script's docstring opens "Read-only
unless --apply", and its USAGE section gives the emptying form as `--scoped-temp tmp/os-temp --apply`. The command as
named only reports. (Iteration 02's proposed edit carried the same omission.)
Proposed-edit: replace "`reap_agent_temp.py --scoped-temp` empties it" with "`reap_agent_temp.py --scoped-temp
tmp/os-temp --apply` empties it".

CLEAN
