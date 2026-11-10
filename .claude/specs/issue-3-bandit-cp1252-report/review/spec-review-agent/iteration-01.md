# spec-review-agent — iteration 01 (tier S, combined mode)

Reviewed: `change.md` (context: `prompt.md`, `decisions/decision-log.md` DL-001).

## Findings

### C1 — The child driver's load method is unspecified, and the obvious form fails before reaching the bug
Severity: C
Location: change.md § Tests (child-process harness)
Defect: "a driver that loads run_checks" does not say how. If the driver loads the script with `spec_from_file_location` but does not register it in `sys.modules`, `@dataclass class Result` raises `AttributeError` in `dataclasses._is_type` (`sys.modules.get(cls.__module__).__dict__`, on `Result`'s postponed string annotations). Every child test is then red before and after I1 for a reason that is not the bug. Evidence: `C:\Program Files\Python314\Lib\dataclasses.py` `_is_type`; the comment in `src/payload/test/test_reap_agent_temp.py` `_load`.
Material-because: risk. The AC-4 red capture would then come from a `Traceback` in the loader, and it could be told apart only because AC-2, AC-3 and UB-3 would be red too.
Proposed-edit: replace "on a driver that loads run_checks," with "on a driver that loads run_checks as `_load` does (registered in `sys.modules` before `exec_module`),".

### C2 — The UB-1 test does not exercise the console-script fallback
Severity: C
Location: change.md § Tests, UB-1
Defect: the test pins `("-m", "bandit")` at `argv[1:3]` and covers the importable branch. The clause's last part says the `CONSOLE_SCRIPTS` fallback keeps "the same remaining arguments", which now include `-f txt -o`. No test runs that path. It is protected only indirectly: `runnable` is unchanged and the argv position is pinned.
Material-because: risk. The fallback half of UB-1 has no test that can fail on its own.
Proposed-edit: append to the UB-1 test line: "; with the loaded module's `importable` monkeypatched to return False and `shutil.which` to return a fixed path, `runnable(bandit_argv())` returns `((that path, *bandit_argv()[3:]), \"\")`."

### C3 — `--list` stops printing bandit's command in full
Severity: C
Location: change.md § Change, `bandit_argv`
Defect: four more arguments push bandit's argv past `LIST_MAX_ARGS` in a tree that has `pyproject.toml`, `src/` and `scripts/` (this repository and the installed layout). `listed` then prints it cut off after `-f txt`, followed by `... (+2 more)`. That contradicts `listed`'s docstring ("every fixed command in the inventory fits and prints whole"). No test, prompt or template parses `--list` output (grep of the worktree), so nothing breaks mechanically.
Material-because: risk. `--list` hides `-o reports/bandit.txt`, and the docstring of an untouched function becomes false.
Proposed-edit: add to § Change "`LIST_MAX_ARGS` rises so that `--list` still prints the bandit command whole (`listed`'s docstring)." If the conductor counts that as scope, record it under § Residuals instead.

### C4 — `prompts.md` is absent from the spec directory
Severity: C
Location: spec directory (conductor-owned; not `change.md`)
Defect: `document-user-prompts.md` item 2 requires `prompts.md` with the chronological conversation. The directory holds `prompt.md`, `qa_log.md`, `change.md` and `decisions/` only.
Material-because: risk. This is a gap in the record only and does not affect the change's behaviour. `change.md` § User Prompts is present.
Proposed-edit: the conductor writes `prompts.md` holding the `/auto-work` invocation and issue #3's text verbatim.

### D1 — The form of the `-o` argument is left open
Severity: D
Location: change.md § Change, `bandit_argv`
Defect: `-o <BANDIT_REPORT>` does not fix the string form. On Windows, `str(Path("reports") / "bandit.txt")` is `reports\bandit.txt`, which `shlex.join` quotes in the `--- RUN` line and in `Result.command`. `tests_argv` uses the literal `reports/junit.xml`.
Proposed-edit: replace "`-f txt -o <BANDIT_REPORT>`" with "`-f txt -o BANDIT_REPORT.as_posix()`".

Lenses with no finding: intent and consistency, project standards, best practice (the `-o` file is opened `encoding="utf-8"` per bandit `cli/main.py` `main`; the stdout crash is upstream PyCQA/bandit #1040), security (no auth, IAM or secrets; the relay reads only the file `run_check` itself deletes and recreates under the gitignored `reports/`), operability (the CI `verify` job installs `.[dev]`, so bandit is present in the `tests` leg; `reports/` is already the uploaded artifact path; `E2E: not applicable` is correct for tooling per `always-test-e2e.md`).

## Coverage

All tests are example tests. No criterion quantifies over an input domain, so none needs a property-based test.

| Criterion | Test (change.md § Tests) | It fails when |
|---|---|---|
| AC-1 | child process, cp1252, `src/bad.py`: `B101` present; no `Traceback`, no `UnicodeEncodeError` | the report is not relayed, or the relay or bandit crashes on encoding (red before I1) |
| AC-2 | the same run: exit code non-zero; `--- FAIL security/bandit` | the relay masks or rewrites `Result.returncode` |
| AC-3 | child process, parametrized cp1252 and utf-8, `src/ok.py`: exit code 0; `--- PASS security/bandit`; no `Traceback` | the relay crashes on a clean report, or the return code changes |
| AC-4 | the AC-1 test, captured red by T1 against the unchanged `run_checks.py` (only AC-1 red, everything else green) | not applicable: this is the red capture itself |
| UB-1 | in process: `bandit_argv()[1:3] == ("-m", "bandit")`; `runnable(bandit_argv())` returns that argv with an empty reason | `-f`/`-o` displace `-m bandit`; the fallback is covered only indirectly (C2) |
| UB-2 | in process, `monkeypatch.chdir(tmp_path)`, with and without `pyproject.toml` | `-c pyproject.toml` is dropped or forced |
| UB-3 | child process, utf-8, `src/bad.py`: `B101` present; exit code non-zero | the relay suppresses the report on UTF-8 |

Every AC and UB maps to a test that can fail.

READY: A+B = 0. C1–C4 and D1 do not gate the loop.

CLEAN
