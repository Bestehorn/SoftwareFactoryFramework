"""Tests for scripts/run_checks.py — the security/bandit check, whatever the encoding of run_checks' stdout.

Installed from ``src/payload/test/test_run_checks.py`` to ``test/test_run_checks.py``.

What is proven: the ``security/bandit`` check lists every bandit finding and keeps bandit's verdict when
run_checks' stdout is cp1252 and bandit's report holds a character cp1252 cannot encode (U+274C), with no
``Traceback`` and no ``UnicodeEncodeError`` (AC-1, AC-2, AC-4); a clean project passes on a cp1252 and on a
UTF-8 stdout (AC-3); a UTF-8 stdout still lists the findings and fails on them (UB-3); ``bandit_argv`` still runs
bandit as ``python -m bandit`` with the console-script fallback of ``runnable`` keeping every other argument
(UB-1), and passes ``-c pyproject.toml`` exactly when that file exists (UB-2); a stale report is deleted before the
check runs and never relayed, and ``--list`` prints the bandit command whole (the change's own behaviour).

Also proven: a file-list check whose command line would exceed ``MAX_COMMAND_LINE_CHARS`` (the Windows command line
cap is 32,767 characters; one detect-secrets invocation over every tracked file crossed it with ``[WinError 206]``)
runs as several invocations, each repeating the fixed leading arguments before a consecutive, non-empty batch of the
files, every file in exactly one batch and in order, each command line within the bound; the check fails with the
first non-zero exit code of its batches and still runs every batch; it prints one ``--- RUN`` and one ``--- PASS`` or
``--- FAIL`` line; and every check whose command fits runs exactly once with its argv unchanged. These tests run no
process: ``subprocess.call`` is a recorder, ``importable`` and ``tracked_files`` are faked, and a ``subprocess.run``
fails the test. A command line is measured as ``subprocess.list2cmdline`` joins it, which is what Windows receives.

The child-process tests run ``run_check`` for ``security/bandit`` in a fresh interpreter whose stdio encoding is
set with ``PYTHONIOENCODING`` for that one subprocess, inside a scratch project under ``tmp_path`` that has no
``pyproject.toml`` — so bandit's B101 is not skipped. The in-process tests call the loaded module directly.

Run: ``python scripts/run_tests.py test/test_run_checks.py`` (needs bandit, the ``dev`` extra; no network).
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_checks.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_checks", SCRIPT)
    assert spec is not None and spec.loader is not None, f"{SCRIPT} is missing"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve postponed annotations through sys.modules
    spec.loader.exec_module(module)
    return module


run_checks = _load()

CHILD_TIMEOUT_SECONDS = 120
CP1252 = "cp1252"
UTF8 = "utf-8"
#: U+274C CROSS MARK: cp1252 has no code point for it, so a cp1252 stream cannot encode a report holding it.
#: Built from its code point so this file stays ASCII; the scratch source file holds the character itself.
CROSS_MARK = chr(0x274C)
#: A bandit B101 finding (assert used) on a line that holds CROSS_MARK itself.
BAD_SOURCE = f'def check(flag):\n    assert flag, "{CROSS_MARK} failed"\n'
#: Nothing for bandit to report.
OK_SOURCE = "def check(flag):\n    return bool(flag)\n"
FINDING_ID = "B101"
FAIL_LINE = "--- FAIL security/bandit"
PASS_LINE = "--- PASS security/bandit"
TRACEBACK = "Traceback"
ENCODE_ERROR = "UnicodeEncodeError"
BANDIT_SCRIPT_NAME = "bandit"
#: The one line of a report left by an earlier run; this run must never relay it as its own.
STALE_SENTINEL = "STALE-REPORT-SENTINEL"
#: A project-local `bandit` module that `python -m bandit` runs instead of the installed bandit (`-m` puts the
#: working directory first on sys.path). It exits zero and writes no report.
NO_REPORT_BANDIT_FILE = "bandit.py"
NO_REPORT_BANDIT_SOURCE = "import sys\nsys.exit(0)\n"
LIST_FLAG = "--list"
#: How `main --list` prefixes the bandit check's line, and the tail `listed` adds to a command it cuts short.
BANDIT_LIST_PREFIX = "  bandit: "
REPORT_ARGS = "-o reports/bandit.txt"
LIST_TRUNCATION_MARK = "more)"

#: The child's program: load run_checks from the absolute path in argv[1] the way _load does (registered in
#: sys.modules before exec_module, which the Result dataclass needs), run the bandit check, exit with its code.
DRIVER = "; ".join(
    (
        "import importlib.util, sys",
        "spec = importlib.util.spec_from_file_location('run_checks', sys.argv[1])",
        "module = importlib.util.module_from_spec(spec)",
        "sys.modules[spec.name] = module",
        "spec.loader.exec_module(module)",
        "result = module.run_check(group='security', name='bandit', spec=module.bandit_argv)",
        "sys.exit(result.returncode)",
    )
)


@dataclass(frozen=True)
class ChildRun:
    """What the child interpreter left behind: its exit code (the check's Result.returncode) and its output."""

    returncode: int
    output: str


def make_project(base: Path, source_name: str, source: str) -> Path:
    """A scratch project holding `src/<source_name>` (written as UTF-8) and no pyproject.toml."""
    project = base / "project"
    source_dir = project / "src"
    source_dir.mkdir(parents=True)
    (source_dir / source_name).write_text(source, encoding="utf-8")
    return project


def run_bandit_check(project: Path, encoding: str) -> ChildRun:
    """Run the security/bandit check in a child whose stdio is `encoding`; decode its stdout and stderr alike."""
    completed = subprocess.run(
        args=[sys.executable, "-c", DRIVER, str(SCRIPT)],
        cwd=str(project),
        env=dict(os.environ, PYTHONIOENCODING=encoding),
        capture_output=True,
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )
    output = completed.stdout.decode(encoding=encoding, errors="replace") + completed.stderr.decode(
        encoding=encoding, errors="replace"
    )
    return ChildRun(returncode=completed.returncode, output=output)


@pytest.fixture(scope="module")
def cp1252_finding_run(tmp_path_factory: pytest.TempPathFactory) -> ChildRun:
    """One bandit run over BAD_SOURCE on a cp1252 stdout, shared by the AC-1 and AC-2 tests."""
    project = make_project(base=tmp_path_factory.mktemp("cp1252-finding"), source_name="bad.py", source=BAD_SOURCE)
    return run_bandit_check(project=project, encoding=CP1252)


def test_ac1_findings_listed_on_a_cp1252_stdout(cp1252_finding_run: ChildRun) -> None:
    """AC-1, and AC-4: this is the test that is red against run_checks.py before the report relay."""
    with pytest.raises(UnicodeEncodeError):
        CROSS_MARK.encode(encoding=CP1252)  # the precondition: the report holds a character cp1252 cannot encode
    output = cp1252_finding_run.output
    assert FINDING_ID in output, f"bandit's finding {FINDING_ID} is missing from the check's output:\n{output}"
    assert TRACEBACK not in output, f"the check printed a traceback on a cp1252 stdout:\n{output}"
    assert ENCODE_ERROR not in output, f"the check raised {ENCODE_ERROR} on a cp1252 stdout:\n{output}"


def test_ac2_finding_fails_the_check(cp1252_finding_run: ChildRun) -> None:
    output = cp1252_finding_run.output
    assert cp1252_finding_run.returncode != 0, f"a bandit finding returned exit code zero:\n{output}"
    assert FAIL_LINE in output, f"{FAIL_LINE!r} is missing from the check's output:\n{output}"


@pytest.mark.parametrize("encoding", [CP1252, UTF8])
def test_ac3_clean_project_passes(tmp_path: Path, encoding: str) -> None:
    project = make_project(base=tmp_path, source_name="ok.py", source=OK_SOURCE)
    run = run_bandit_check(project=project, encoding=encoding)
    assert run.returncode == 0, f"a clean project failed the check on a {encoding} stdout:\n{run.output}"
    assert PASS_LINE in run.output, f"{PASS_LINE!r} is missing on a {encoding} stdout:\n{run.output}"
    assert TRACEBACK not in run.output, f"the check printed a traceback on a {encoding} stdout:\n{run.output}"


def test_ub3_findings_listed_and_failing_on_a_utf8_stdout(tmp_path: Path) -> None:
    project = make_project(base=tmp_path, source_name="bad.py", source=BAD_SOURCE)
    run = run_bandit_check(project=project, encoding=UTF8)
    assert FINDING_ID in run.output, f"bandit's finding {FINDING_ID} is missing on a UTF-8 stdout:\n{run.output}"
    assert run.returncode != 0, f"a bandit finding returned exit code zero on a UTF-8 stdout:\n{run.output}"


def test_ub1_bandit_runs_as_a_module_of_this_interpreter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    argv = run_checks.bandit_argv()
    assert argv[1:3] == ("-m", "bandit"), f"bandit_argv does not put `-m bandit` after the interpreter: {argv}"
    assert run_checks.runnable(argv=argv) == (argv, ""), "bandit is importable, so runnable must keep the argv"


def test_ub1_console_script_fallback_keeps_the_arguments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    fake_bandit = str(tmp_path / "bin" / BANDIT_SCRIPT_NAME)
    asked: list[str] = []

    def fake_which(cmd: str, mode: int = os.F_OK | os.X_OK, path: str | None = None) -> str | None:
        asked.append(cmd)
        return fake_bandit if cmd == BANDIT_SCRIPT_NAME else None

    monkeypatch.setattr(target=run_checks, name="importable", value=lambda module: False)
    monkeypatch.setattr(target=run_checks.shutil, name="which", value=fake_which)
    argv = run_checks.bandit_argv()
    expected = ((fake_bandit, *argv[3:]), "")
    assert run_checks.runnable(argv=argv) == expected, f"the console-script fallback dropped arguments of {argv}"
    assert asked == [BANDIT_SCRIPT_NAME], f"runnable looked up {asked}, not the `bandit` console script"


def test_ub2_config_passed_when_pyproject_is_a_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[tool.bandit]\n", encoding="utf-8")
    argv = run_checks.bandit_argv()
    assert ("-c", "pyproject.toml") in list(zip(argv, argv[1:])), f"`-c pyproject.toml` is missing: {argv}"


def test_ub2_config_omitted_without_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    argv = run_checks.bandit_argv()
    assert "-c" not in argv, f"`-c` passed with no pyproject.toml: {argv}"
    assert "pyproject.toml" not in argv, f"pyproject.toml passed when it does not exist: {argv}"


def test_chg_stale_report_deleted_before_the_check_runs(tmp_path: Path) -> None:
    """change.md, Change, the run_check bullet: a report an earlier run left behind is deleted before the command.

    The installed bandit cannot show this. Its `-o` is an `argparse.FileType("w")`, which truncates the old report
    while the arguments are parsed, even when bandit then exits for want of a target. So the project carries
    NO_REPORT_BANDIT_SOURCE, which writes no report: a report that exists after the check can only be the stale one.
    """
    project = make_project(base=tmp_path, source_name="ok.py", source=OK_SOURCE)
    (project / NO_REPORT_BANDIT_FILE).write_text(NO_REPORT_BANDIT_SOURCE, encoding="utf-8")
    stale = project / run_checks.BANDIT_REPORT
    stale.parent.mkdir(parents=True)
    stale.write_text(f"{STALE_SENTINEL}\n", encoding="utf-8")
    run = run_bandit_check(project=project, encoding=UTF8)
    assert run.returncode == 0, f"a run that reports nothing failed the check:\n{run.output}"
    assert PASS_LINE in run.output, f"{PASS_LINE!r} is missing from the check's output:\n{run.output}"
    assert STALE_SENTINEL not in run.output, f"the stale report was relayed as this run's:\n{run.output}"
    assert not stale.exists(), (
        f"{stale} exists after a run that writes no report: the stale one was not deleted before the command "
        f"(or the installed bandit ran instead of {NO_REPORT_BANDIT_FILE}):\n{run.output}"
    )


def test_chg_list_shows_the_bandit_command_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """change.md, Change, the last bullet: `--list` prints the bandit command whole, its `-o` report included.

    The project has a pyproject.toml and every BANDIT_PATHS directory, so bandit_argv is at its longest.
    """
    for directory in run_checks.BANDIT_PATHS:
        (tmp_path / directory).mkdir()
    (tmp_path / "pyproject.toml").write_text("[tool.bandit]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert run_checks.main(argv=[LIST_FLAG]) == 0, f"`run_checks {LIST_FLAG}` did not exit zero"
    listing = capsys.readouterr().out
    bandit_lines = [line for line in listing.splitlines() if line.startswith(BANDIT_LIST_PREFIX)]
    assert len(bandit_lines) == 1, f"expected one {BANDIT_LIST_PREFIX.strip()!r} line in the listing:\n{listing}"
    bandit_line = bandit_lines[0]
    assert REPORT_ARGS in bandit_line, f"{REPORT_ARGS!r} is missing from the bandit line: {bandit_line}"
    assert LIST_TRUNCATION_MARK not in bandit_line, f"--list cut the bandit command short: {bandit_line}"


#: The command line cap of Windows' CreateProcess, in characters: the limit one detect-secrets invocation over every
#: tracked file crossed (`[WinError 206] The filename or extension is too long`). A fact of the OS, not the bound.
WINDOWS_COMMAND_LINE_LIMIT = 32_767
#: The module constant every invocation's command line must stay within; the module picks its value.
BOUND_NAME = "MAX_COMMAND_LINE_CHARS"
#: The long file list's own command line spans more than this many Windows limits, so it needs several batches.
LONG_LIST_SPAN = 3
SECURITY_GROUP = "security"
DETECT_SECRETS = "detect-secrets"  # pragma: allowlist secret — the check's name, not a secret
#: What follows the interpreter in every detect-secrets invocation, before its batch of files.
DETECT_SECRETS_FIXED_ARGS = ("-m", "detect_secrets.pre_commit_hook", "--baseline", ".secrets.baseline")
SHORT_FILE_LIST = ("README.md", "pyproject.toml", "src/payload/scripts/run_checks.py")
#: The exit codes the fake answers the failing-batch test's first invocations with; every later one exits
#: LATER_FAILING_EXIT, so the check's verdict must be FIRST_FAILING_EXIT, the first non-zero code.
FIRST_FAILING_EXIT = 2
LATER_FAILING_EXIT = 5
FAILING_BATCH_EXITS = (0, FIRST_FAILING_EXIT)
#: The status lines run_check prints per check, as prefixes; `{check}` is `<group>/<name>`.
RUN_PREFIX = "--- RUN  {check}:"
PASS_PREFIX = "--- PASS {check} "
FAIL_PREFIX = "--- FAIL {check} "
RUN_TESTS_SCRIPT = Path("scripts") / "run_tests.py"
PYPROJECT = "pyproject.toml"


@dataclass
class CallRecorder:
    """Stands in for subprocess.call: records every argv and answers each invocation with its scripted exit code."""

    scripted_exits: tuple[int, ...] = ()
    later_exit: int = 0
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def exit_for(self, index: int) -> int:
        return self.scripted_exits[index] if index < len(self.scripted_exits) else self.later_exit

    def __call__(self, args: Sequence[str], **kwargs: object) -> int:
        self.calls.append(tuple(args))
        return self.exit_for(index=len(self.calls) - 1)


def refuse_subprocess(*popenargs: object, **kwargs: object) -> None:
    raise AssertionError(f"run_check started a real process: {popenargs} {kwargs}")


def isolate(monkeypatch: pytest.MonkeyPatch, project: Path, files: Sequence[str], recorder: CallRecorder) -> None:
    """Run checks in `project` with no real process: every tool importable, `files` as the tracked files, `recorder`
    as subprocess.call, and any subprocess.run a test failure."""
    monkeypatch.chdir(project)
    monkeypatch.setattr(target=run_checks, name="importable", value=lambda module: True)
    monkeypatch.setattr(target=run_checks, name="tracked_files", value=lambda: list(files))
    monkeypatch.setattr(target=run_checks.subprocess, name="run", value=refuse_subprocess)
    monkeypatch.setattr(target=run_checks.subprocess, name="call", value=recorder)


def command_line_length(argv: Sequence[str]) -> int:
    """The length of the command line Windows' CreateProcess receives for `argv` (subprocess joins it this way)."""
    return len(subprocess.list2cmdline(seq=argv))


def module_bound() -> int:
    """MAX_COMMAND_LINE_CHARS, asserted to be an int under the Windows cap."""
    bound = getattr(run_checks, BOUND_NAME, None)
    assert isinstance(bound, int) and not isinstance(bound, bool), f"run_checks.{BOUND_NAME} is {bound!r}, not an int"
    assert 0 < bound < WINDOWS_COMMAND_LINE_LIMIT, (
        f"run_checks.{BOUND_NAME} is {bound}, not under the Windows cap of {WINDOWS_COMMAND_LINE_LIMIT}"
    )
    return bound


def long_file_list() -> list[str]:
    """Tracked-file paths of varied lengths whose own command line spans more than LONG_LIST_SPAN Windows caps."""
    files: list[str] = []
    length = 0
    while length <= LONG_LIST_SPAN * WINDOWS_COMMAND_LINE_LIMIT:
        index = len(files)
        module_name = f"module_{index:05d}_{'x' * (index % 53)}.py"
        path = PurePosixPath("src", f"package_{index % 37:02d}", module_name).as_posix()
        files.append(path)
        length += len(path) + 1
    return files


def detect_secrets_spec() -> object:
    """The inventory's detect-secrets entry, as run_groups would hand it to run_check."""
    specs = [spec for group, name, spec in run_checks.CHECKS if group == SECURITY_GROUP and name == DETECT_SECRETS]
    assert len(specs) == 1, f"expected one {SECURITY_GROUP}/{DETECT_SECRETS} entry in CHECKS, found {len(specs)}"
    return specs[0]


def detect_secrets_head() -> tuple[str, ...]:
    return (run_checks.PY, *DETECT_SECRETS_FIXED_ARGS)


def status_line_counts(output: str, check: str) -> tuple[int, ...]:
    """How many `--- RUN`, `--- PASS` and `--- FAIL` lines `output` holds for `check` (`<group>/<name>`)."""
    lines = output.splitlines()
    return tuple(
        sum(1 for line in lines if line.startswith(prefix.format(check=check)))
        for prefix in (RUN_PREFIX, PASS_PREFIX, FAIL_PREFIX)
    )


def joined_batches(recorder: CallRecorder) -> list[str]:
    """Every file the invocations carried after the fixed head, in invocation order."""
    head_length = len(detect_secrets_head())
    return [path for call in recorder.calls for path in call[head_length:]]


def make_full_project(base: Path) -> None:
    """Every path an inventory check looks for, so each check takes its full, runnable form."""
    for directory in (*run_checks.LINT_PATHS, *run_checks.BANDIT_PATHS):
        (base / directory).mkdir(exist_ok=True)
    (base / run_checks.E2E_DIR).mkdir(parents=True, exist_ok=True)
    (base / run_checks.HOOK_TESTS_DIR).mkdir(parents=True, exist_ok=True)
    (base / PYPROJECT).write_text("[tool.bandit]\n", encoding="utf-8")
    (base / RUN_TESTS_SCRIPT).write_text("", encoding="utf-8")


def test_a_long_file_list_check_runs_in_batches_under_the_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A file list too long for one Windows command line runs as consecutive batches, each within the bound.

    Every invocation repeats the fixed head (interpreter, `-m detect_secrets.pre_commit_hook --baseline
    .secrets.baseline`) before a non-empty batch; the batches, joined, are the tracked files, each once, in order.
    """
    files = long_file_list()
    recorder = CallRecorder()
    isolate(monkeypatch=monkeypatch, project=tmp_path, files=files, recorder=recorder)
    result = run_checks.run_check(group=SECURITY_GROUP, name=DETECT_SECRETS, spec=detect_secrets_spec())
    output = capsys.readouterr().out
    assert recorder.calls, f"the check started no invocation ({result}):\n{output}"
    lengths = [command_line_length(argv=call) for call in recorder.calls]
    assert max(lengths) <= WINDOWS_COMMAND_LINE_LIMIT, (
        f"an invocation's command line is {max(lengths)} characters, over the Windows cap of "
        f"{WINDOWS_COMMAND_LINE_LIMIT}: {len(files)} files ran as {len(lengths)} invocation(s) of {lengths} characters"
    )
    bound = module_bound()
    assert max(lengths) <= bound, f"invocations of {lengths} characters, over run_checks.{BOUND_NAME} = {bound}"
    head = detect_secrets_head()
    heads = [call[: len(head)] for call in recorder.calls]
    assert all(call_head == head for call_head in heads), f"not every invocation starts with {head}: {set(heads)}"
    batch_sizes = [len(call) - len(head) for call in recorder.calls]
    assert all(size > 0 for size in batch_sizes), f"an invocation carries no file; files per invocation {batch_sizes}"
    joined = joined_batches(recorder=recorder)
    assert joined == files, (
        f"the batches hold {len(joined)} paths for {len(files)} tracked files: not every file once, in order"
    )
    assert result.returncode == 0, f"every batch exited 0, yet the check returned {result.returncode}"
    check = f"{SECURITY_GROUP}/{DETECT_SECRETS}"
    assert status_line_counts(output=output, check=check) == (1, 1, 0), (
        f"expected one RUN and one PASS line for {check}, no FAIL line:\n{output}"
    )


def test_a_failing_batch_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A non-zero batch fails the check with the first non-zero exit code, and every later batch still runs."""
    files = long_file_list()
    recorder = CallRecorder(scripted_exits=FAILING_BATCH_EXITS, later_exit=LATER_FAILING_EXIT)
    isolate(monkeypatch=monkeypatch, project=tmp_path, files=files, recorder=recorder)
    result = run_checks.run_check(group=SECURITY_GROUP, name=DETECT_SECRETS, spec=detect_secrets_spec())
    output = capsys.readouterr().out
    answered = [recorder.exit_for(index=index) for index in range(len(recorder.calls))]
    assert result.returncode == FIRST_FAILING_EXIT, (
        f"the check returned {result.returncode} from {len(answered)} invocation(s) answered {answered}; with the "
        f"second batch exiting {FIRST_FAILING_EXIT} and every later one {LATER_FAILING_EXIT}, the verdict is "
        f"{FIRST_FAILING_EXIT}"
    )
    joined = joined_batches(recorder=recorder)
    assert joined == files, (
        f"after a failing batch the invocations carried {len(joined)} of {len(files)} tracked files, in order: "
        f"every batch must still run"
    )
    check = f"{SECURITY_GROUP}/{DETECT_SECRETS}"
    assert status_line_counts(output=output, check=check) == (1, 0, 1), (
        f"expected one RUN and one FAIL line for {check}, no PASS line:\n{output}"
    )


OTHER_CHECKS = tuple(entry for entry in run_checks.CHECKS if entry[1] != DETECT_SECRETS)


@pytest.mark.parametrize(("group", "name", "spec"), OTHER_CHECKS, ids=[entry[1] for entry in OTHER_CHECKS])
def test_a_short_check_runs_once_unchanged(
    group: str,
    name: str,
    spec: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every other inventory check fits the bound, and runs as exactly one invocation of its own argv."""
    make_full_project(base=tmp_path)
    recorder = CallRecorder()
    isolate(monkeypatch=monkeypatch, project=tmp_path, files=SHORT_FILE_LIST, recorder=recorder)
    argv = tuple(run_checks.resolve(spec=spec))
    bound = module_bound()
    assert command_line_length(argv=argv) <= bound, f"{group}/{name} does not fit run_checks.{BOUND_NAME}: {argv}"
    result = run_checks.run_check(group=group, name=name, spec=spec)
    output = capsys.readouterr().out
    assert recorder.calls == [argv], f"{group}/{name} ran as {recorder.calls}, not once as {argv}"
    assert result.returncode == 0, f"{group}/{name} returned {result.returncode} from one invocation exiting 0"
    check = f"{group}/{name}"
    assert status_line_counts(output=output, check=check) == (1, 1, 0), (
        f"expected one RUN and one PASS line for {check}, no FAIL line:\n{output}"
    )


def test_a_short_file_list_check_runs_once_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """detect-secrets over a file list that fits the bound runs once: the fixed head, then every file in order."""
    recorder = CallRecorder()
    isolate(monkeypatch=monkeypatch, project=tmp_path, files=SHORT_FILE_LIST, recorder=recorder)
    argv = (*detect_secrets_head(), *SHORT_FILE_LIST)
    bound = module_bound()
    assert command_line_length(argv=argv) <= bound, f"the short file list does not fit run_checks.{BOUND_NAME}"
    result = run_checks.run_check(group=SECURITY_GROUP, name=DETECT_SECRETS, spec=detect_secrets_spec())
    output = capsys.readouterr().out
    assert recorder.calls == [argv], f"the short file list ran as {recorder.calls}, not once as {argv}"
    assert result.returncode == 0, f"the check returned {result.returncode} from one invocation exiting 0"
    check = f"{SECURITY_GROUP}/{DETECT_SECRETS}"
    assert status_line_counts(output=output, check=check) == (1, 1, 0), (
        f"expected one RUN and one PASS line for {check}, no FAIL line:\n{output}"
    )
