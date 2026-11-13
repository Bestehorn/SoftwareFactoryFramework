# Security review — design iteration 03, delta (lane: security-reviewer)

## Iteration-02 item

- C1 applied. design.md § Operability (Rollback) now reads, verbatim as proposed: "the secret and the token stay only
  while the suite is to return; otherwise the operator deletes the secret `SFF_TEST_TOKEN` and revokes the token."

## Delta checked for new risk

- D2 `shown`: `owner.rpartition(USERINFO_SEPARATOR)[2]`. `USERINFO_SEPARATOR = "@"` in
  `src/payload/scripts/github_wrapper.py`, and `_without_userinfo` uses the same `rpartition(USERINFO_SEPARATOR)[2]`.
  This is the iteration-02 text with the literal replaced by its constant, so the refusal still names no userinfo.
- AC-4.3 L: the tightened `ast` oracle can be implemented as D9/D10 write the fixture. `conftest.py` names the runner
  classes, not `PRODUCT_WRAPPER` or `product_wrapper`, and its by-path loader reads `loader`/`exec_module`, not
  `main`. The oracle now also rules out an in-process `main` call that would carry no marker.
- AC-6.1: a worktree's own file comes first, and the fallback still reads only `github-sff-testing-pat.txt`. The
  backlog token's path is not reachable.
- Residuals, interrupted local run: accurate. `.claude/hooks/gate_scoped_temp.py` (`scoped-temp-init`) points the
  session's temp at `<tree>/tmp/os-temp`. `reap_agent_temp.py` docstring tier 1: under `--scoped-temp` "its CONTENTS
  are removed wholesale". The leftover clone credential lies under the gitignored `tmp/`.
- D8 Windows sentence: the quote matches the python.org 3.9.20 release page. This repository's venv is CPython 3.14.2
  (`venv/pyvenv.cfg`), so local runs get the owner-only directory. The version range is imprecise; see C1.

### C1 — The CVE-2024-4030 version range names releases that lack the fix
Severity: C
Location: design.md § D8 (Writing)
Defect: "the 2024 security releases of 3.9 to 3.11" takes in 3.9.19 (python.org: released March 19, 2024, "a security
bugfix release"). Its notes carry no CVE-2024-4030 / `os.mkdir` 0o700 entry. The fix landed in 3.9.20, 3.10.15 and
3.11.10 (September 2024) and in 3.12.4.
Proposed-edit: replace "3.12.4 and later and the 2024 security releases of 3.9 to 3.11" with "3.9.20, 3.10.15,
3.11.10, 3.12.4 or any later release (3.13 and later carry it)".

## Residuals

None new.

CLEAN
