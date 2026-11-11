"""Compatibility tests of the product GitHub wrapper's entry script, ``scripts/github_wrapper.py`` (UB-1.1, UB-1.2,
UB-1.3, UB-2.1, UB-3.2).

Installed from ``src/payload/test/test_github_wrapper_compat.py`` to ``test/test_github_wrapper_compat.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every golden case of ``github_wrapper_fixtures.CASES``
(loaded by path) runs through the entry script's ``main(argv=...)`` in a temporary project, the fixture
``credentials/github-pat.txt`` and a ``.git/config`` with a GitHub ``origin``, against the fake GitHub host: standard
output is read with ``capsys``, the exit code is ``main``'s return value or its ``SystemExit``. The golden values are
the installed fork's own output; ``test/test_github_wrapper_fork_parity.py`` runs the same table against the fork in the
framework repository. The delivery verbs reach a faked ``subprocess.run`` in place of the steward, and one test runs the
script by path in a child interpreter that stops at its credential refusal. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_wrapper_compat.py`` (no network).
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator, List, Sequence, Tuple

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_PATH = HERE / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

SCRIPTS_DIR = HERE.parent / "scripts"
ENTRY_SCRIPT = SCRIPTS_DIR / "github_wrapper.py"
PACKAGE_DIR = SCRIPTS_DIR / "github_api"
WRAPPER_MODULE = "github_wrapper_under_test"
PYTHON_GLOB = "*.py"
SCRIPT_TIMEOUT_SECONDS = 120

# The delivery verbs (UB-1.2) and the steward they delegate to (src/payload/test/test_wrapper_delivery.py).
DELIVERY_CONFIG = Path("config") / "delivery.json"
FIELD_MERGE = "merge"
FIELD_HOST = "host"
MERGE_STEWARD = "steward"
HOST_GITHUB = "github"
HOST_GITLAB = "gitlab"
STEWARD_SCRIPT_SUFFIX = "scripts/merge_steward.py"
STEWARD_STDIN_OPTION = "--token-stdin"
STEWARD_REFUSED = 4  # the steward's "refused, the reason printed"; any code the wrapper must pass through unchanged
KWARG_INPUT = "input"
KWARG_ENV = "env"

# UB-2.1's static check: no read of the process environment anywhere in the entry script or the package.
ENVIRONMENT_READ = re.compile(r"\b(?:environ|getenv)\b")
TOKEN_OPTION_WORD = "token"
GET_ISSUE_1 = ("get-issue", "1")
ISSUE_1_PATH = f"{fx.ISSUES_PATH}/1"
STEWARD_DELEGATE_PARAMETERS = ["verb", "args", "token", "host"]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def load_wrapper(*, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The product entry script, freshly loaded by path as ``test_wrapper_delivery.load`` loads it."""
    return fx.load_script(path=ENTRY_SCRIPT, name=WRAPPER_MODULE, monkeypatch=monkeypatch)


def run_main(*, wrapper: ModuleType, argv: Sequence[str]) -> int:
    """The exit code of ``wrapper.main(argv=argv)``: its return value, or the code of the ``SystemExit`` it raises."""
    main = getattr(wrapper, "main", None)
    assert callable(main), f"{ENTRY_SCRIPT} defines no main"
    assert "argv" in inspect.signature(main).parameters, (
        f"{ENTRY_SCRIPT}: main takes no argv; design D6 gives the entry script main(argv=None) -> int"
    )
    try:
        result = main(argv=list(argv))
    except SystemExit as exc:
        return fx.exit_code_of(exc=exc)
    assert isinstance(result, int), f"main(argv={list(argv)}) returned {result!r}, not an exit code"
    return result


def _option_strings(*, parser: argparse.ArgumentParser) -> Iterator[Tuple[str, str]]:
    """Every option string of ``parser`` and of each of its subparsers, at any depth, with the parser's prog."""
    for action in parser._actions:
        for option in action.option_strings:
            yield parser.prog, option
        if isinstance(action, argparse._SubParsersAction):
            for subparser in action.choices.values():
                yield from _option_strings(parser=subparser)


@pytest.mark.parametrize(argnames="case", argvalues=fx.CASES, ids=fx.case_name)
def test_a_subcommand_matches_its_golden_case(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """UB-1.1: the product writes the fork's standard output, exits with the fork's code and sends the fork's requests
    other than ``GET``; a C-only case's deviation (no ``--token-stdin``, no userinfo in a refusal) holds too."""
    caplog.set_level(level=logging.DEBUG)
    host = fx.enter_project(project=case.project, root=tmp_path, monkeypatch=monkeypatch, routes=case.routes)
    exit_code = run_main(wrapper=load_wrapper(monkeypatch=monkeypatch), argv=case.argv)
    captured = capsys.readouterr()
    fx.assert_outcome(
        case=case, outcome=fx.Outcome(stdout=captured.out, exit_code=exit_code, requests=tuple(host.requests))
    )
    fx.assert_log(case=case, records=caplog.records, stderr=captured.err)
    host.assert_every_request_routed()


@dataclass
class StewardRun:
    """A faked ``subprocess.run``: records each command and keyword arguments, and answers with ``exit_code``."""

    exit_code: int
    calls: List[Tuple[List[str], Dict[str, Any]]] = field(default_factory=list)

    def __call__(self, command: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((list(command), dict(kwargs)))
        return subprocess.CompletedProcess(args=list(command), returncode=self.exit_code)


def _write_delivery_config(*, root: Path, host: str) -> None:
    target = root / DELIVERY_CONFIG
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data=json.dumps({FIELD_MERGE: MERGE_STEWARD, FIELD_HOST: host}), encoding="utf-8")


@pytest.mark.parametrize(
    argnames=("argv", "steward_verb", "steward_args"),
    argvalues=[
        pytest.param(("enqueue-pr", "77"), "enqueue", ["77"], id="enqueue-pr"),
        pytest.param(
            ("dequeue-pr", "77", "--reason", "superseded by #78"),
            "dequeue",
            ["77", "--reason", "superseded by #78"],
            id="dequeue-pr",
        ),
        pytest.param(("queue-status",), "status", [], id="queue-status"),
        pytest.param(("queue-status", "--json"), "status", ["--json"], id="queue-status-json"),
        pytest.param(
            ("wait-landed", "77", "--timeout-seconds", "540"),
            "wait-landed",
            ["77", "--timeout-seconds", "540"],
            id="wait-landed",
        ),
        pytest.param(("check-handoff", "412"), "check-handoff", ["412"], id="check-handoff"),
        pytest.param(("check-landed", "77", "78"), "check-landed", ["77", "78"], id="check-landed"),
    ],
)
def test_a_delivery_verb_delegates_to_the_steward(
    argv: Tuple[str, ...],
    steward_verb: str,
    steward_args: List[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UB-1.2: ``main`` hands the steward ``--token-stdin <steward verb> <args>`` with the file's token on standard
    input only and returns the steward's code; on a host that is not the queue's it returns ``EXIT_DELIVERY_ELSEWHERE``
    and runs nothing."""
    host = fx.enter_project(project=fx.PROJECT, root=tmp_path, monkeypatch=monkeypatch)
    _write_delivery_config(root=tmp_path, host=HOST_GITHUB)
    steward = StewardRun(exit_code=STEWARD_REFUSED)
    monkeypatch.setattr(target=subprocess, name="run", value=steward)
    wrapper = load_wrapper(monkeypatch=monkeypatch)

    assert run_main(wrapper=wrapper, argv=argv) == STEWARD_REFUSED, "the steward's exit code passes through"
    assert len(steward.calls) == 1, f"the steward ran {len(steward.calls)} times"
    command, kwargs = steward.calls[0]
    assert command[1].replace("\\", "/").endswith(STEWARD_SCRIPT_SUFFIX), command
    assert command[2:] == [STEWARD_STDIN_OPTION, steward_verb, *steward_args]
    assert fx.FIXTURE_TOKEN not in " ".join(command), "the token never reaches argv"
    assert str(kwargs.get(KWARG_INPUT, "")).startswith(fx.FIXTURE_TOKEN), "the file's token goes on standard input"
    assert KWARG_ENV not in kwargs, "nothing passes through the environment"

    steward.calls.clear()
    _write_delivery_config(root=tmp_path, host=HOST_GITLAB)
    assert run_main(wrapper=wrapper, argv=argv) == wrapper.EXIT_DELIVERY_ELSEWHERE
    assert steward.calls == [], "a host that is not the queue's never runs the steward"
    assert host.requests == [], "a delivery verb sends no API request of its own"


def test_the_script_runs_by_path(tmp_path: Path) -> None:
    """UB-1.3: run as ``python <scripts dir>/github_wrapper.py get-issue 1`` from an empty directory, the script finds
    its package beside it and reaches the credential refusal: exit 2, the credential file named on standard error."""
    completed = subprocess.run(
        args=[sys.executable, str(ENTRY_SCRIPT), *GET_ISSUE_1],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=False,
    )
    assert completed.returncode == fx.EXIT_REFUSED, (
        f"exit {completed.returncode}; stdout {completed.stdout!r}; stderr {completed.stderr!r}"
    )
    assert str(fx.CREDENTIALS_FILE) in completed.stderr, (
        f"standard error does not name {fx.CREDENTIALS_FILE}: {completed.stderr!r}"
    )
    assert completed.stdout == ""


def test_the_credential_comes_only_from_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """UB-2.1: without ``credentials/github-pat.txt`` the wrapper exits 2 and sends nothing; with it the request carries
    ``Bearer`` and the file's token; no file of the wrapper reads the environment and no option takes a token."""
    issue_1 = fx.StaticRouteSpec(method=fx.METHOD_GET, url=ISSUE_1_PATH, replies=(fx.Reply(body=fx.ISSUE_5),))
    wrapper = load_wrapper(monkeypatch=monkeypatch)

    without = fx.enter_project(
        project=fx.NO_CREDENTIAL, root=tmp_path / "without", monkeypatch=monkeypatch, routes=(issue_1,)
    )
    assert run_main(wrapper=wrapper, argv=GET_ISSUE_1) == fx.EXIT_REFUSED
    assert without.requests == [], "a request was sent without the credential file"

    host = fx.enter_project(project=fx.PROJECT, root=tmp_path / "with", monkeypatch=monkeypatch, routes=(issue_1,))
    assert run_main(wrapper=wrapper, argv=GET_ISSUE_1) == fx.EXIT_OK, capsys.readouterr().err
    sent = [request.header(name=fx.HEADER_AUTHORIZATION) for request in host.requests]
    assert sent == [f"Bearer {fx.FIXTURE_TOKEN}"]

    sources = [ENTRY_SCRIPT, *sorted(PACKAGE_DIR.rglob(PYTHON_GLOB))]
    reading = [str(path) for path in sources if ENVIRONMENT_READ.search(path.read_text(encoding="utf-8"))]
    assert reading == [], f"these files read the process environment: {reading}"

    build_parser = getattr(wrapper, "_build_parser", None)
    assert callable(build_parser), f"{ENTRY_SCRIPT} defines no _build_parser (design D6)"
    token_options = [
        f"{prog} {option}"
        for prog, option in _option_strings(parser=build_parser())
        if TOKEN_OPTION_WORD in option.lower()
    ]
    assert token_options == [], f"options that take a token: {token_options}"


def test_the_module_loads_without_credential_or_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """UB-3.2: loaded by path in a directory with neither credentials nor ``.git``, the fake host installed, the module
    raises nothing, sends nothing, sets up no logging, and exposes ``steward_delegate`` and
    ``EXIT_DELIVERY_ELSEWHERE``."""
    host = fx.enter_project(project=fx.Project(credential=None, config=None), root=tmp_path, monkeypatch=monkeypatch)
    configured: List[Dict[str, Any]] = []

    def record_configuration(**kwargs: Any) -> None:
        configured.append(kwargs)

    monkeypatch.setattr(target=logging, name="basicConfig", value=record_configuration)
    handlers = list(logging.getLogger().handlers)

    wrapper = load_wrapper(monkeypatch=monkeypatch)

    assert host.requests == [], "loading the module sent a request"
    assert configured == [], "loading the module set up logging"
    assert list(logging.getLogger().handlers) == handlers, "loading the module added a root log handler"
    assert list(inspect.signature(wrapper.steward_delegate).parameters) == STEWARD_DELEGATE_PARAMETERS
    assert isinstance(wrapper.EXIT_DELIVERY_ELSEWHERE, int)


# AC-4.1: what design D7's usage lines give the entry script's docstring for the operation call.
USAGE_CALL_TEXTS = (
    "call issues/get",
    "--path",
    "--query",
    "-f/--raw-field",
    "-F/--field",
    "JSON array",
    "indented JSON",
    "bytes unchanged",
    "exit 2",
)


def test_the_usage_names_the_operation_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-4.1: the entry script's ``__doc__`` names ``call`` with an operation ID, its options, its print forms and its
    refusal's exit code (design D7)."""
    usage = load_wrapper(monkeypatch=monkeypatch).__doc__
    assert isinstance(usage, str), f"{ENTRY_SCRIPT} has no module docstring"
    missing = [text for text in USAGE_CALL_TEXTS if text not in usage]
    assert missing == [], f"the usage of {ENTRY_SCRIPT} does not name: {missing}"


# AC-5.1: what design D6's usage lines give the entry script's docstring for the raw body input. None of these texts is
# in the docstring before D6's lines, so the test cannot pass on the earlier usage.
USAGE_RAW_BODY_TEXTS = (
    "call markdown/render-raw --input",
    "--input FILE",
    "standard input",
    "repos/upload-release-asset",
    "uploads.github.com",
    "with -f/-F",
)


def test_the_usage_names_the_raw_body_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-5.1: the entry script's ``__doc__`` names ``call`` with ``--input FILE``, its standard-input form, the two
    records it sends, the upload host, and its refusal beside ``-f/-F`` (design D6)."""
    usage = load_wrapper(monkeypatch=monkeypatch).__doc__
    assert isinstance(usage, str), f"{ENTRY_SCRIPT} has no module docstring"
    missing = [text for text in USAGE_RAW_BODY_TEXTS if text not in usage]
    assert missing == [], f"the usage of {ENTRY_SCRIPT} does not name: {missing}"
