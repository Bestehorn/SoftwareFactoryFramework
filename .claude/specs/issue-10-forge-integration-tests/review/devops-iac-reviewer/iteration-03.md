# DevOps / IaC review — issue #10 design, iteration 03 (delta)

## Iteration-02 items

- D1 (interrupted-run residual) — applied. Residuals now reads "Nothing in this change removes the workspace an
  interrupted local run leaves in the temporary directory", and adds the scoped-temp clause (standards C2). The
  clause carries one wording slip, D1 below.

## Delta checked, no defect found

- Rollback (security C1): deleting `SFF_TEST_TOKEN` and revoking the token is a teardown step on a revert, not a
  test, so `always-test-e2e.md` is not engaged. The forge job stays an automated CI job with no human step. No
  infrastructure is touched outside version control: this repository has no CDK and the secret is a forge setting.
- AC-1.1's `worker_id=worker_id` and AC-4.3's `ast` oracle change no job, trigger or `needs:`. AC-5.1 to AC-5.4
  are unchanged.
- D8 Windows clause: the local venv is CPython 3.14.2 (`venv/pyvenv.cfg` `version`), which has the CVE-2024-4030
  fix, so the owner-only workspace holds on this host. The python.org 3.9.20 page (Sept. 6, 2024) quotes the
  design's sentence.

### D1 — The residual names the reaper without `--apply`, which only reports
Severity: D
Location: design.md § Residuals (interrupted local run)
Defect: `reap_agent_temp.py --scoped-temp` on its own deletes nothing. The module docstring opens "Read-only unless
--apply", and `main` declares `--apply` "delete; default is report only". The command that empties the scoped temp
is `/close-session`'s `python scripts/reap_agent_temp.py --scoped-temp tmp/os-temp --apply --budget-minutes 9`
(close-session.md, OS temp residue step).
Proposed-edit: replace "`reap_agent_temp.py --scoped-temp` empties it" with "`/close-session`'s
`reap_agent_temp.py --scoped-temp tmp/os-temp --apply` empties it".

### D2 — "the 2024 security releases of 3.9 to 3.11" includes releases without the fix
Severity: D
Location: design.md § D8 Writing (Windows clause)
Defect: Two 2024 security releases predate the fix. Python 3.9.19 and 3.10.14 are each "a security release",
both released March 19, 2024 (python.org release pages). The fix (gh-118486) first ships in 3.9.20 (Sept. 6, 2024), 3.10.15 and
3.11.10 (Sept. 7, 2024). As written, the version range is wrong for 3.9.19 and 3.10.14.
Proposed-edit: replace "3.12.4 and later and the 2024 security releases of 3.9 to 3.11" with "3.12.4, 3.11.10,
3.10.15, 3.9.20 or later".

CLEAN
