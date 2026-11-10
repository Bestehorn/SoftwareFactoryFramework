# Change — issue #3: bandit's report crashes on a cp1252 console

Tier: S. Kind: BUGFIX.

## User Prompts

- "Work this project's open-issue backlog AUTONOMOUSLY, end to end" — the `/auto-work` run that took this issue.
- Issue #3: "run_checks: bandit's report crashes on a cp1252 console instead of listing findings".

## Ask

The `security/bandit` check of `run_checks.py` must list every bandit finding, and keep bandit's verdict,
whatever the encoding of run_checks' stdout. Today `bandit_argv` leaves bandit's `txt` formatter writing to the
inherited stdout; when that stream is cp1252 and the report holds a character cp1252 cannot encode, bandit
raises `UnicodeEncodeError`, then `RuntimeError: Unable to output report using 'txt' formatter`, and the check
fails with no finding shown.

## Acceptance criteria

- AC-1 WHEN the `security/bandit` check runs AND bandit's report holds a character that the encoding of
  run_checks' stdout cannot represent, `run_check` SHALL list every bandit finding (its test id) in its output,
  with no `Traceback` and no `UnicodeEncodeError`.
- AC-2 WHEN bandit reports a finding, the `security/bandit` check SHALL fail: `run_check` SHALL return bandit's
  non-zero exit code as `Result.returncode` and print `--- FAIL security/bandit`.
- AC-3 WHEN bandit reports no finding, the `security/bandit` check SHALL pass (`Result.returncode` zero) with
  run_checks' stdout encoded as cp1252 and as UTF-8.
- AC-4 `src/payload/test/test_run_checks.py` SHALL exercise the `security/bandit` check with a cp1252 stdout
  and SHALL fail against `run_checks.py` as it is before this change.

## Unchanged behaviour

- UB-1 WHILE bandit is importable, `runnable(bandit_argv())` SHALL CONTINUE TO return the `python -m bandit`
  argv with an empty skip reason; `bandit_argv` SHALL CONTINUE TO put `-m`, `bandit` directly after the
  interpreter, so `runnable` SHALL CONTINUE TO fall back to the `CONSOLE_SCRIPTS` `bandit` script, with the same
  remaining arguments, when the module is not importable.
- UB-2 WHEN `pyproject.toml` is a file in the working directory, `bandit_argv` SHALL CONTINUE TO pass
  `-c pyproject.toml`, and SHALL CONTINUE TO omit it otherwise.
- UB-3 WHILE run_checks' stdout is UTF-8, the `security/bandit` check SHALL CONTINUE TO list bandit's findings
  and fail on them.

## Change

- `BANDIT_REPORT = Path("reports") / "bandit.txt"`, a module constant.
- `bandit_argv` appends `-f txt -o <BANDIT_REPORT.as_posix()>` after its existing arguments (the `reports/junit.xml`
  style of `tests_argv`); `-c pyproject.toml` stays.
  bandit's `-f` default is `screen` when stdout is a TTY and `txt` otherwise, and bandit opens the `-o` file
  with `argparse.FileType("w", encoding="utf-8")` (bandit `cli/main.py` `main`: the `-f/--format` default and
  the `-o/--output` argument, read in the project venv's installed `bandit`).
- `RELAYED_REPORTS: dict[str, Path]`, a module mapping of check name to report file, holds
  `"bandit": BANDIT_REPORT`.
- `run_check`, for a check in `RELAYED_REPORTS` that is not skipped: before the command runs it creates the
  report's parent directory and deletes an existing report; after the command, when the report exists, it
  prints the report's text, read as UTF-8 with `errors="replace"`, to its own stdout through a helper that
  encodes the text with `sys.stdout`'s encoding and `errors="backslashreplace"`, flushed before the
  `--- PASS/FAIL` line. `Result.returncode` stays the command's exit code.
- `runnable`, `CONSOLE_SCRIPTS` and `CHECKS` are unchanged. `LIST_MAX_ARGS` rises to 16 so `--list` still prints
  the bandit command whole, as `listed`'s docstring says.

## Files

- `src/payload/scripts/run_checks.py` — `BANDIT_REPORT`, `RELAYED_REPORTS`, `bandit_argv`, `run_check`, the
  relay helper.
- `src/payload/test/test_run_checks.py` (new; installs at `test/test_run_checks.py`) — loads the script with
  `importlib.util.spec_from_file_location` from
  `Path(__file__).resolve().parents[1] / "scripts" / "run_checks.py"`, as
  `src/payload/test/test_reap_agent_temp.py` `_load` does.

## Tests

All example tests; no criterion quantifies over an input domain, so none is property-based.

Child-process harness (AC-1, AC-2, AC-3, UB-3): a scratch project under `tmp_path` holding either `src/bad.py`
with a bandit finding on a line that contains the character U+274C itself, written as UTF-8
(`assert flag, "❌ failed"`), or a clean `src/ok.py`; no `pyproject.toml`, so B101 is not skipped. The test
runs `sys.executable` with `cwd=` the scratch project and `env=dict(os.environ, PYTHONIOENCODING=<encoding>)` —
the per-subprocess form of `src/hooks/tests/test_dispatcher.py` `_spawn` — on a driver that loads run_checks the
way `_load` does (registered in `sys.modules` before `exec_module`, which the `Result` dataclass needs),
calls `run_check(group="security", name="bandit", spec=bandit_argv)` and exits with its `returncode`; it
asserts on the child's stdout and stderr, decoded with that encoding, and on its exit code.

- AC-1 — cp1252, `src/bad.py`: `B101` in the output; neither `Traceback` nor `UnicodeEncodeError`.
- AC-2 — the same run: exit code non-zero; `--- FAIL security/bandit` in the output.
- AC-3 — cp1252 and utf-8 (parametrized), `src/ok.py`: exit code zero; `--- PASS security/bandit` in the
  output; no `Traceback`.
- AC-4 — the AC-1 test, captured red by T1 against the unchanged `run_checks.py`.
- UB-1 — in-process: `bandit_argv()[1:3] == ("-m", "bandit")`, and `runnable(bandit_argv())` returns that
  argv with an empty reason (bandit is in the `dev` extra of `pyproject.toml`); with `importable` monkeypatched
  to `False` and `shutil.which` to a fake `bandit` path, `runnable(bandit_argv())` returns that path followed by
  `bandit_argv()[3:]` (the `-f txt -o` arguments included).
- UB-2 — in-process, `monkeypatch.chdir(tmp_path)`: `-c` followed by `pyproject.toml` in `bandit_argv()` when
  `tmp_path / "pyproject.toml"` exists; neither when it does not.
- UB-3 — utf-8, `src/bad.py`: `B101` in the output; exit code non-zero.
- E2E: not applicable — a development-pipeline check script; no deployed runtime behaviour changes. CI's
  `verify` job, `tests` leg, runs the module (`pyproject.toml` `testpaths` holds `src/payload/test`).

## Tasks

Wave 1:

- [ ] T1 TEST: the test module of §Tests; red before I1 on AC-1 — Files: `src/payload/test/test_run_checks.py`
  — Validates: AC-1, AC-2, AC-3, AC-4, UB-1, UB-2, UB-3
- [ ] I1 IMPL: §Change — Files: `src/payload/scripts/run_checks.py` — Validates: AC-1, AC-2, AC-3, UB-1,
  UB-2, UB-3

## Residuals

- Other checks' output encoding (ruff, mypy, pytest): no observed failure; nothing filed.
- Issue #3's "Ship it in a release" item: the release that batches this run's fixes, outside this change.
- Installing `test/test_run_checks.py` into a project: needs the copy steps of `prompts/setup-claude.txt`,
  `prompts/setup-kiro.txt`, `prompts/update.txt` and the `templates/README.md` table, which are outside this
  change's files.
