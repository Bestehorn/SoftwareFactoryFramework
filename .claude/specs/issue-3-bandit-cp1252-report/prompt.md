# Prompt — issue #3: bandit's report crashes on a cp1252 console

Tier: S — one check's invocation in one shipped script (`src/payload/scripts/run_checks.py`); no new interface.

Kind: BUGFIX.

## Goal

The `security/bandit` check of `run_checks.py` must list every bandit finding, and keep bandit's verdict,
whatever the encoding of the stream it writes to. Today bandit's default `txt` formatter writes to the
inherited stdout; when that stream is cp1252 (a Windows pipe — the Bash tool of an agent session, a redirected
console) and the report holds a character cp1252 cannot encode, bandit raises `UnicodeEncodeError`, then
`RuntimeError: Unable to output report using 'txt' formatter`, and the check fails with no finding shown.

Reproduced on this host (2026-11-10, Python 3.14.2, bandit 1.9.4, stdout encoding cp1252): a scratch project
whose `src/bad.py` holds `assert flag, "❌ failed"`, checked through `run_checks.run_check` with
`run_checks.bandit_argv`, printed the two tracebacks above and `--- FAIL security/bandit (0.7s, exit 1)`, and
no `B101` finding.

## Scope (the ask)

- `src/payload/scripts/run_checks.py` — `bandit_argv`, and whatever in `run_check` must change so the report
  reaches the log on any encoding. bandit's `-o FILE` option writes the report through
  `argparse.FileType("w", encoding="utf-8")` (bandit `cli/main.py`, the `-o/--output` argument), so a report
  file is independent of the console encoding.
- A new test module `src/payload/test/test_run_checks.py` (installs at `test/test_run_checks.py`) that
  exercises the check under a cp1252 stdout (a subprocess whose `env=` sets `PYTHONIOENCODING=cp1252`, the
  per-subprocess form the existing suites use) and fails before the change.

## Out of scope

- The other checks' output encoding (ruff, mypy, pytest): no observed failure.
- Shipping a release and promoting it (the issue's third work item) — handled by the release that batches
  this run's fixes, not by this change.

## Integration points

- `run_checks.bandit_argv`, `run_checks.runnable` (the `-m` probe and the `CONSOLE_SCRIPTS` fallback, which
  must keep working — UB-1), `run_checks.run_check`, `run_checks.CHECKS`.
- `pyproject.toml` `[tool.bandit]` read through `-c pyproject.toml` (UB-2).
- `.gitignore` `/reports/` — the generated-report directory a report file may use.

## Tests

Each acceptance criterion and unchanged-behaviour clause is pinned by a test in `test_run_checks.py`.
E2E: not applicable — a check script of the development pipeline; no deployed runtime behaviour changes. CI
runs the new test in the `tests` group.
