"""Tests of the product GitHub wrapper's origin guard under the test marker (issue #10 design D2; AC-4.1, AC-4.2,
AC-4.3, UB-1, UB-3).

The test marker is the interpreter option ``-X sff_test_marker``, which CPython maps to ``True`` in ``sys._xoptions``.
While it is set, the entry script ``scripts/github_wrapper.py`` refuses an ``origin`` whose repository name does not
start with ``sff-test-``: exit 2, no request, the refusal logged. Three tests run the entry script's ``main(argv=...)``
in-process, as ``test_github_wrapper_compat.py`` does: a temporary project (``github_wrapper_fixtures.enter_project``,
the fixtures module loaded by path), the fake GitHub host, the marker set with ``monkeypatch.setitem`` on
``sys._xoptions`` or removed from it, and ``steward_delegate`` replaced by a recorder. One test runs the script by path
in a child interpreter started with the option, in a temporary project that is not this repository. The fake host
answers every request a wrapper without the guard would send, so such a wrapper is judged by its exit code and its
requests; no test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_wrapper_marker.py`` (no network).
"""

from __future__ import annotations

import importlib.util
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Sequence, Tuple
from urllib.parse import quote

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
WRAPPER_MODULE = "github_wrapper_marker_under_test"
STEWARD_DELEGATE = "steward_delegate"
SCRIPT_TIMEOUT_SECONDS = 120

#: The test marker (design D2). Named here rather than read from the wrapper: the test pins the option the forge suite
#: passes to the interpreter.
INTERPRETER_OPTION_FLAG = "-X"
MARKER_OPTION = "sff_test_marker"
#: What the entry script's ``LOG_FORMAT`` puts before a refusal it writes to standard error.
LOG_ERROR_PREFIX = "ERROR: "

PATH_SAFE = ""  # ``registry.expand`` percent-encodes a path value with nothing safe
FIELD_FULL_NAME = "full_name"
FIELD_PRIVATE = "private"
ISSUE_NUMBER = 1
ISSUE_TITLE = "Guarded issue"

CALL_REPOS_GET = ("call", "repos/get")
#: A record ``call`` itself refuses before any request (``GATED_OPERATIONS``): a child interpreter running it sends
#: nothing, whether or not the guard refuses first.
CALL_GATED = ("call", "issues/create")


@dataclass(frozen=True)
class Origin:
    """An ``origin`` remote: its URL, the owner and repository groups ``_detect_repo`` parses from it, the
    ``owner/repo`` a refusal names, and the text besides the configured token that no log record may hold."""

    url: str
    owner: str
    repo: str
    shown: str
    withheld: Tuple[str, ...] = ()


PRODUCT_ORIGIN = Origin(
    url=f"{fx.WEB_ORIGIN}/Bestehorn/SoftwareFactoryFramework.git",
    owner="Bestehorn",
    repo="SoftwareFactoryFramework",
    shown="Bestehorn/SoftwareFactoryFramework",
)
EPHEMERAL_ORIGIN = Origin(
    url=f"{fx.WEB_ORIGIN}/bestehorn-sff-test/sff-test-x.git",
    owner="bestehorn-sff-test",
    repo="sff-test-x",
    shown="bestehorn-sff-test/sff-test-x",
)
#: An origin whose userinfo ends in ``github.com:``: the owner group ``_detect_repo`` parses is
#: ``<sentinel>@example.com``, so a refusal naming the owner as parsed would carry the userinfo; the refusal names the
#: owner after its last ``@`` (design D2 ``shown``).
USERINFO_SENTINEL = "SentinelUserinfo7c1e"  # pragma: allowlist secret
USERINFO_ORIGIN = Origin(
    url=f"{fx.WEB_ORIGIN}:{USERINFO_SENTINEL}@example.com/repo",  # pragma: allowlist secret
    owner=f"{USERINFO_SENTINEL}@example.com",
    repo="repo",
    shown="example.com/repo",
    withheld=(USERINFO_SENTINEL,),
)

#: AC-4.1's subcommands: a record sent through ``call``, two compatibility subcommands and two delivery verbs, one
#: parsed (``enqueue-pr``) and one handed to the steward unparsed (``wait-landed``).
REFUSED_ARGV = (
    pytest.param(CALL_REPOS_GET, id="call-repos-get"),
    pytest.param(("get-issue", str(ISSUE_NUMBER)), id="get-issue"),
    pytest.param(("list-runs",), id="list-runs"),
    pytest.param(("enqueue-pr", "1"), id="enqueue-pr"),
    pytest.param(("wait-landed", "1"), id="wait-landed"),
)
REFUSED_ORIGINS = (
    pytest.param(PRODUCT_ORIGIN, id="product-origin"),
    pytest.param(USERINFO_ORIGIN, id="userinfo-origin"),
)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


@dataclass
class StewardRecorder:
    """Stands in for the entry script's ``steward_delegate``: records each delivery verb and its arguments, never the
    token, and answers 0, so a delivery verb nothing refuses exits 0."""

    calls: List[Tuple[str, List[str], str]] = field(default_factory=list)

    def __call__(self, *, verb: str, args: List[str], token: str, host: str) -> int:
        del token  # the delegate's token is the fixture credential; nothing here judges it
        self.calls.append((verb, list(args), host))
        return int(fx.EXIT_OK)


@dataclass(frozen=True)
class Run:
    """One in-process run of the entry script: the module it ran in, its exit code, what it wrote and the requests the
    fake host received."""

    wrapper: ModuleType
    exit_code: int
    stdout: str
    stderr: str
    requests: Tuple[Any, ...]


def repository_path(*, owner: str, repo: str) -> str:
    """``/repos/{owner}/{repo}`` as ``registry.expand`` sends it: each value percent-encoded with nothing safe."""
    return f"/repos/{quote(string=owner, safe=PATH_SAFE)}/{quote(string=repo, safe=PATH_SAFE)}"


def repository_record(*, owner: str, repo: str) -> Dict[str, Any]:
    """The repository ``repos/get`` answers for ``owner``/``repo``, cut to a few fields."""
    return {FIELD_FULL_NAME: f"{owner}/{repo}", fx.FIELD_NAME: repo, FIELD_PRIVATE: True}


def served_routes(*, origin: Origin) -> Tuple[Any, ...]:
    """Answers to every request the subcommands of ``REFUSED_ARGV`` send for ``origin`` when nothing refuses them, so a
    wrapper without the guard is served and exits 0 rather than meeting an unrouted request."""
    path = repository_path(owner=origin.owner, repo=origin.repo)
    issue = fx.issue_entry(number=ISSUE_NUMBER, title=ISSUE_TITLE)
    return (
        fx.StaticRouteSpec(
            method=fx.METHOD_GET,
            url=path,
            replies=(fx.Reply(body=repository_record(owner=origin.owner, repo=origin.repo)),),
        ),
        fx.StaticRouteSpec(method=fx.METHOD_GET, url=f"{path}/issues/{ISSUE_NUMBER}", replies=(fx.Reply(body=issue),)),
        fx.ListRouteSpec(url=f"{path}/actions/runs", items=(), item_key=fx.FIELD_WORKFLOW_RUNS),
    )


def set_marker(*, monkeypatch: pytest.MonkeyPatch, present: bool) -> None:
    """Put the test marker in ``sys._xoptions``, as ``-X sff_test_marker`` does, or take it out, until the test ends."""
    if present:
        monkeypatch.setitem(dic=sys._xoptions, name=MARKER_OPTION, value=True)
    else:
        monkeypatch.delitem(dic=sys._xoptions, name=MARKER_OPTION, raising=False)


def run_main(*, wrapper: ModuleType, argv: Sequence[str]) -> int:
    """The exit code of ``wrapper.main(argv=argv)``: its return value, or the code of the ``SystemExit`` it raises."""
    main = getattr(wrapper, "main", None)
    assert callable(main), f"{ENTRY_SCRIPT} defines no main"
    try:
        result = main(argv=list(argv))
    except SystemExit as exc:
        return int(fx.exit_code_of(exc=exc))
    assert isinstance(result, int), f"main(argv={list(argv)}) returned {result!r}, not an exit code"
    return result


def run_wrapper(
    *,
    argv: Sequence[str],
    origin: Origin,
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    steward: StewardRecorder,
) -> Run:
    """Run ``argv`` through a freshly loaded entry script's ``main`` in a project at ``root`` holding the fixture
    credential and ``origin``, against a fake host serving ``origin`` (``served_routes``); ``steward`` stands in for
    ``steward_delegate``."""
    host = fx.enter_project(
        project=fx.Project(config=fx.git_config(origin=origin.url)),
        root=root,
        monkeypatch=monkeypatch,
        routes=served_routes(origin=origin),
    )
    wrapper = fx.load_script(path=ENTRY_SCRIPT, name=WRAPPER_MODULE, monkeypatch=monkeypatch)
    monkeypatch.setattr(target=wrapper, name=STEWARD_DELEGATE, value=steward)
    exit_code = run_main(wrapper=wrapper, argv=argv)
    captured = capsys.readouterr()
    host.assert_every_request_routed()
    return Run(
        wrapper=wrapper,
        exit_code=exit_code,
        stdout=captured.out,
        stderr=captured.err,
        requests=tuple(host.requests),
    )


def outcome_of(*, run: Run) -> str:
    """``run`` described for an assertion message: its exit code, its output and the requests it sent."""
    sent = [f"{request.method} {request.url}" for request in run.requests]
    return f"exit {run.exit_code}; stdout {run.stdout!r}; stderr {run.stderr!r}; requests {sent}"


@pytest.mark.parametrize(argnames="origin", argvalues=REFUSED_ORIGINS)
@pytest.mark.parametrize(argnames="argv", argvalues=REFUSED_ARGV)
def test_the_marker_refuses_an_origin_without_the_prefix(
    argv: Tuple[str, ...],
    origin: Origin,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-4.1 (design D2): while the marker is set and the ``origin`` names no ``sff-test-*`` repository, ``call``, a
    compatibility subcommand and a delivery verb alike exit 2 (``EXIT_REFUSED``), send no request, run no steward and
    print nothing. Exactly one log record names the marker and the origin's ``owner/repo`` (an owner group holding
    userinfo is named after its last ``@``), and no record and nothing on standard error holds the configured token or
    that userinfo."""
    caplog.set_level(level=logging.DEBUG)
    set_marker(monkeypatch=monkeypatch, present=True)
    steward = StewardRecorder()

    run = run_wrapper(argv=argv, origin=origin, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys, steward=steward)

    assert run.exit_code == run.wrapper.EXIT_REFUSED, outcome_of(run=run)
    assert run.requests == (), f"a refusal sent requests: {outcome_of(run=run)}"
    assert steward.calls == [], f"the steward ran: {steward.calls}"
    assert run.stdout == "", outcome_of(run=run)
    messages = [record.getMessage() for record in caplog.records]
    naming = [message for message in messages if MARKER_OPTION in message and origin.shown in message]
    assert len(naming) == 1, f"no single log record names {MARKER_OPTION} and {origin.shown}: {messages}"
    formatter = logging.Formatter()
    rendered = [formatter.format(record=record) for record in caplog.records]
    for withheld in (fx.FIXTURE_TOKEN, *origin.withheld):
        leaking = [text for text in rendered if withheld in text]
        assert leaking == [], f"a log record holds the withheld {withheld!r}: {leaking}"
        assert withheld not in run.stderr, f"standard error holds the withheld {withheld!r}: {run.stderr!r}"


def test_the_interpreter_option_reaches_the_entry_script(tmp_path: Path) -> None:
    """AC-4.1, AC-4.3 (design D2): run as ``python -X sff_test_marker <scripts dir>/github_wrapper.py`` in a temporary
    project, not this repository, whose ``origin`` is a non-ephemeral repository and whose credential file holds a
    dummy token, the script exits 2, prints nothing, and writes one ``ERROR:`` line naming the marker and the origin's
    ``owner/repo``, and not the token, to standard error. The argv is ``call issues/create``, which ``call`` itself
    refuses before any request, so the child reaches no network whichever refusal comes first; only the message tells
    the guard's refusal from ``call``'s."""
    fx.Project(config=fx.git_config(origin=PRODUCT_ORIGIN.url)).build(root=tmp_path)

    completed = subprocess.run(
        args=[sys.executable, INTERPRETER_OPTION_FLAG, MARKER_OPTION, str(ENTRY_SCRIPT), *CALL_GATED],
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=False,
    )

    outcome = f"exit {completed.returncode}; stdout {completed.stdout!r}; stderr {completed.stderr!r}"
    assert completed.returncode == fx.EXIT_REFUSED, outcome
    refusals = [
        line
        for line in completed.stderr.splitlines()
        if line.startswith(LOG_ERROR_PREFIX) and MARKER_OPTION in line and PRODUCT_ORIGIN.shown in line
    ]
    assert len(refusals) == 1, f"standard error holds no single refusal naming {MARKER_OPTION}: {outcome}"
    assert fx.FIXTURE_TOKEN not in completed.stderr, outcome
    assert completed.stdout == "", outcome


def test_the_marker_lets_an_ephemeral_origin_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4.2 (design D2): with the origin ``bestehorn-sff-test/sff-test-x``, ``call repos/get`` under the marker sends
    the same requests, prints the same output and exits as it does without the marker, and is served (exit 0). The
    same marker then refuses the non-ephemeral origin in this process, so the comparison was made with a marker the
    wrapper reads."""
    set_marker(monkeypatch=monkeypatch, present=False)
    without = run_wrapper(
        argv=CALL_REPOS_GET,
        origin=EPHEMERAL_ORIGIN,
        root=tmp_path / "without",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )
    set_marker(monkeypatch=monkeypatch, present=True)
    marked = run_wrapper(
        argv=CALL_REPOS_GET,
        origin=EPHEMERAL_ORIGIN,
        root=tmp_path / "with",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )

    assert without.exit_code == without.wrapper.EXIT_OK, outcome_of(run=without)
    served = [request.path for request in without.requests]
    assert served == [repository_path(owner=EPHEMERAL_ORIGIN.owner, repo=EPHEMERAL_ORIGIN.repo)], outcome_of(
        run=without
    )
    assert marked.exit_code == without.exit_code, outcome_of(run=marked)
    assert marked.stdout == without.stdout, outcome_of(run=marked)
    assert marked.requests == without.requests, outcome_of(run=marked)

    control = run_wrapper(
        argv=CALL_REPOS_GET,
        origin=PRODUCT_ORIGIN,
        root=tmp_path / "control",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )
    assert control.exit_code == control.wrapper.EXIT_REFUSED, f"the marker was not read: {outcome_of(run=control)}"
    assert control.requests == (), outcome_of(run=control)


def test_without_the_marker_every_origin_is_served(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """UB-3, AC-4.3 (design D2): without the marker, the origin ``Bestehorn/SoftwareFactoryFramework``, which the
    marker refuses, is served as before this change: ``call repos/get`` exits 0, sends its one request and prints the
    repository record."""
    set_marker(monkeypatch=monkeypatch, present=False)

    run = run_wrapper(
        argv=CALL_REPOS_GET,
        origin=PRODUCT_ORIGIN,
        root=tmp_path,
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )

    assert run.exit_code == run.wrapper.EXIT_OK, outcome_of(run=run)
    sent = [(request.method, request.path) for request in run.requests]
    assert sent == [(fx.METHOD_GET, repository_path(owner=PRODUCT_ORIGIN.owner, repo=PRODUCT_ORIGIN.repo))]
    assert json.loads(s=run.stdout) == repository_record(owner=PRODUCT_ORIGIN.owner, repo=PRODUCT_ORIGIN.repo)
