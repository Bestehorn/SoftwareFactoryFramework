"""Tests for scripts/run_checks.py — the security/bandit check, whatever the encoding of run_checks' stdout.

Installed from ``src/payload/test/test_run_checks.py`` to ``test/test_run_checks.py``.

What is proven: the ``security/bandit`` check lists every bandit finding and keeps bandit's verdict when
run_checks' stdout is cp1252 and bandit's report holds a character cp1252 cannot encode (U+274C), with no
``Traceback`` and no ``UnicodeEncodeError`` (AC-1, AC-2, AC-4); a clean project passes on a cp1252 and on a
UTF-8 stdout (AC-3); a UTF-8 stdout still lists the findings and fails on them (UB-3); ``bandit_argv`` still runs
bandit as ``python -m bandit`` with the console-script fallback of ``runnable`` keeping every other argument
(UB-1), and passes ``-c pyproject.toml`` exactly when that file exists (UB-2).

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
from dataclasses import dataclass
from pathlib import Path
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
