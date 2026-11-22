"""Tests of the product GitLab wrapper's project guard under the test marker (issue #11 design D2; AC-4.1, AC-4.2,
AC-4.3, UB-1, UB-3).

The test marker is issue #10's interpreter option ``-X sff_test_marker`` (``github_wrapper.py`` ``TEST_MARKER_OPTION``),
which CPython maps to ``True`` in ``sys._xoptions``. While it is set, the entry script ``scripts/gitlab_wrapper.py``
refuses a ``config/gitlab.json`` whose ``project_id`` is not a ``<namespace>/sff-test-*`` path: exit 2, no request, no
steward, one log record naming the marker and the configured project and never the token. A config ``_load_config``
refuses still exits 1 with nothing sent. Without the marker every project is served as before.

Four tests run the entry script's ``main(argv=...)`` in-process, as ``test_gitlab_wrapper_compat.py`` does: a temporary
project whose ``config/gitlab.json`` ``gitlab_wrapper_fixtures.write_config`` writes is the working directory, a fresh
``FakeGitLab`` answers, ``install_socket_guard`` refuses every connection, the marker is set with
``monkeypatch.setitem`` on ``sys._xoptions`` or removed from it, and ``steward_delegate`` is replaced by a recorder.
The fake host answers every request a wrapper without the guard sends for these argvs, so such a wrapper is judged by
its exit code and its requests. One test runs the script by path in a child interpreter started with the option, in a
temporary project that is not this repository, with ``call plan#create-an-issue``, which ``call`` itself refuses before
any request: the child sends nothing whichever refusal comes first, and only the message tells the guard's refusal
from ``call``'s.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_wrapper_marker.py`` (no network).
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
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_FILE = HERE / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process as ``test_gitlab_wrapper_compat.load_fixtures`` loads it
    (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_FILE}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = load_fixtures()

WRAPPER_MODULE = "gitlab_wrapper_marker_under_test"
GITHUB_WRAPPER_FILE = fx.SCRIPTS_DIR / "github_wrapper.py"
GITHUB_WRAPPER_MODULE = "github_wrapper_marker_values_under_test"
STEWARD_DELEGATE = "steward_delegate"
CHILD_TIMEOUT_SECONDS = 120
CHILD_STREAM_ERRORS = "replace"

#: The test marker (design D2). Named here rather than read from the wrapper: the test pins the option the GitLab forge
#: suite passes to the interpreter.
INTERPRETER_OPTION_FLAG = "-X"
MARKER_OPTION = "sff_test_marker"
#: The names of the marker constants: the product GitLab wrapper's (design D2) and issue #10's in ``github_wrapper.py``.
GITLAB_MARKER_CONSTANT = "TEST_MARKER_OPTION"
GITLAB_PREFIX_CONSTANT = "EPHEMERAL_PROJECT_PREFIX"
GITHUB_MARKER_CONSTANT = "TEST_MARKER_OPTION"
GITHUB_PREFIX_CONSTANT = "EPHEMERAL_REPOSITORY_PREFIX"

EXIT_OK = 0
#: A config ``_load_config`` refuses: ``main`` maps its ``GitLabAPIError`` to 1, before the guard (design D2).
EXIT_CONFIG_REFUSED = 1
#: The guard's refusal, ``gitlab_wrapper.EXIT_PROJECT_REFUSED`` (design D2).
EXIT_PROJECT_REFUSED = 2
#: ``gitlab_wrapper.DELIVERY_HOST``: the ``host`` the entry script hands ``steward_delegate``.
DELIVERY_HOST = "gitlab"

# The keys of config/gitlab.json and of the answers the fake host gives.
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
FIELD_ID = "id"
FIELD_IID = "iid"
FIELD_TITLE = "title"
FIELD_PATH_WITH_NAMESPACE = "path_with_namespace"

TOKEN = "glpat-marker-guard-test"  # pragma: allowlist secret
PATH_SAFE = ""  # ``registry._segment`` percent-encodes a path value with nothing safe
METHOD_GET = "GET"
SERVED_PROJECT_NUMBER = 4321
ISSUE_IID = 1
ISSUE_TITLE = "Guarded issue"
#: ``pipeline status``'s query: the newest pipeline first, one per page (``commands/pipeline.py``
#: ``_newest_pipelines``).
NEWEST_PIPELINE_QUERY = "order_by=id&sort=desc&per_page=1"

CALL_RETRIEVE_PROJECT = ("call", "tenant-scale#retrieve-a-project")
#: A record ``call`` itself refuses before any request (``GATED_OPERATIONS``): a child interpreter running it sends
#: nothing, whether or not the guard refuses first.
CALL_GATED = ("call", "plan#create-an-issue")
ENQUEUE = ("enqueue-pr", "1")

PRODUCT_PROJECT = "Bestehorn/SoftwareFactoryFramework"
EPHEMERAL_PROJECT = "bestehorn-sff-test/sff-test-x"
CHILD_PROJECT = "1234"
#: The ``project_id`` of no ``config/gitlab.json``: the file is not written.
NO_CONFIG: Optional[Any] = None

#: AC-4.1's subcommands: a record sent through ``call``, two compatibility subcommands and two delivery verbs.
REFUSED_ARGV = (
    pytest.param(CALL_RETRIEVE_PROJECT, id="call-retrieve-a-project"),
    pytest.param(("issue", "show", str(ISSUE_IID)), id="issue-show"),
    pytest.param(("pipeline", "status"), id="pipeline-status"),
    pytest.param(ENQUEUE, id="enqueue-pr"),
    pytest.param(("wait-landed", "1"), id="wait-landed"),
)
#: AC-4.1's ``project_id`` values that are not an ``sff-test-*`` project path (design D2 ``_is_ephemeral_project``): a
#: number, a numeric text, a text without ``/``, a path whose last segment lacks the prefix, holds it only after its
#: start, or follows a segment that has it.
NON_EPHEMERAL_PROJECTS = (
    pytest.param(1234, id="numeric-id"),
    pytest.param("1234", id="numeric-text"),
    pytest.param(PRODUCT_PROJECT, id="product-project"),
    pytest.param("bestehorn-sff-test/other", id="test-group-unprefixed"),
    pytest.param("sff-test-x", id="prefix-without-namespace"),
    pytest.param("Bestehorn/x-sff-test-y", id="inner-prefix"),
    pytest.param("bestehorn-sff-test/sff-test-x/other", id="under-an-ephemeral-path"),
)
REFUSED_CONFIGS = (*NON_EPHEMERAL_PROJECTS, pytest.param(NO_CONFIG, id="no-config"))


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.install_socket_guard(monkeypatch=monkeypatch)


@dataclass
class StewardRecorder:
    """Stands in for the entry script's ``steward_delegate``: records each delivery verb, its arguments and its host,
    never the token, and answers 0, so a delivery verb nothing refuses exits 0."""

    calls: List[Tuple[str, List[str], str]] = field(default_factory=list)

    def __call__(self, *, verb: str, args: List[str], token: str, host: str) -> int:
        del token  # the delegate's token is the config's; nothing here judges it
        self.calls.append((verb, list(args), host))
        return EXIT_OK


@dataclass(frozen=True)
class Run:
    """One in-process run of the entry script: its exit code, what it wrote and the requests the fake host received."""

    exit_code: Any
    stdout: str
    stderr: str
    requests: Tuple[Any, ...]


def config_for(*, project_id: Any) -> Dict[str, Any]:
    """A ``config/gitlab.json`` that ``_load_config`` accepts, naming ``project_id`` on the fake host."""
    return {FIELD_HOSTNAME: fx.HOST, FIELD_PROJECT_ID: project_id, FIELD_TOKEN: TOKEN}


def project_url(*, project_id: Any, suffix: str = "") -> str:
    """``/projects/:id`` plus ``suffix`` under the fake host's REST base, ``:id`` as ``registry._segment`` sends it."""
    return f"{fx.REST_BASE}/projects/{quote(string=str(project_id), safe=PATH_SAFE)}{suffix}"


def project_record(*, project_id: Any) -> Dict[str, Any]:
    """The project ``tenant-scale#retrieve-a-project`` answers for ``project_id``, cut to two fields."""
    return {FIELD_ID: SERVED_PROJECT_NUMBER, FIELD_PATH_WITH_NAMESPACE: str(project_id)}


def script_served_answers(*, fake: Any, project_id: Any) -> None:
    """Answers to every request the subcommands of ``REFUSED_ARGV`` send for ``project_id`` when nothing refuses them,
    so a wrapper without the guard is served and exits 0 rather than meeting an unscripted request."""
    fake.script(method=METHOD_GET, url=project_url(project_id=project_id), body=project_record(project_id=project_id))
    fake.script(
        method=METHOD_GET,
        url=project_url(project_id=project_id, suffix=f"/issues/{ISSUE_IID}"),
        body={FIELD_IID: ISSUE_IID, FIELD_TITLE: ISSUE_TITLE},
    )
    fake.script(
        method=METHOD_GET, url=project_url(project_id=project_id, suffix=f"/pipelines?{NEWEST_PIPELINE_QUERY}"), body=[]
    )


def set_marker(*, monkeypatch: pytest.MonkeyPatch, present: bool) -> None:
    """Put the test marker in ``sys._xoptions``, as ``-X sff_test_marker`` does, or take it out, until the test ends."""
    if present:
        monkeypatch.setitem(dic=sys._xoptions, name=MARKER_OPTION, value=True)
    else:
        monkeypatch.delitem(dic=sys._xoptions, name=MARKER_OPTION, raising=False)


def run_wrapper(
    *,
    argv: Sequence[str],
    project_id: Optional[Any],
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    steward: StewardRecorder,
) -> Run:
    """Run ``argv`` through a freshly loaded entry script's ``main`` with ``root`` as the working directory, holding a
    ``config/gitlab.json`` naming ``project_id`` (none for ``NO_CONFIG``), against a fresh fake host answering
    ``script_served_answers``; ``steward`` stands in for ``steward_delegate``."""
    root.mkdir(parents=True, exist_ok=True)
    if project_id is not NO_CONFIG:
        fx.write_config(root=root, config=config_for(project_id=project_id))
    monkeypatch.chdir(path=root)
    fake = fx.FakeGitLab().install(monkeypatch=monkeypatch)
    if project_id is not NO_CONFIG:
        script_served_answers(fake=fake, project_id=project_id)
    wrapper = fx.load_wrapper(module_name=WRAPPER_MODULE)
    monkeypatch.setattr(target=wrapper, name=STEWARD_DELEGATE, value=steward)
    exit_code = fx.run_main(wrapper=wrapper, argv=argv)
    captured = capsys.readouterr()
    return Run(exit_code=exit_code, stdout=captured.out, stderr=captured.err, requests=tuple(fake.requests))


def outcome_of(*, run: Run) -> str:
    """``run`` described for an assertion message: its exit code, its output and the requests it sent."""
    sent = [f"{request.method} {request.url}" for request in run.requests]
    return f"exit {run.exit_code}; stdout {run.stdout!r}; stderr {run.stderr!r}; requests {sent}"


def load_github_wrapper(*, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """``src/payload/scripts/github_wrapper.py`` loaded by path afresh, as ``github_wrapper_fixtures.load_script`` loads
    it: in ``sys.modules`` until the test ends, since ``dataclasses`` reads the module of a class it processes there."""
    spec = importlib.util.spec_from_file_location(name=GITHUB_WRAPPER_MODULE, location=GITHUB_WRAPPER_FILE)
    assert spec is not None and spec.loader is not None, f"cannot load {GITHUB_WRAPPER_FILE}"
    module = importlib.util.module_from_spec(spec=spec)
    monkeypatch.setitem(dic=sys.modules, name=GITHUB_WRAPPER_MODULE, value=module)
    spec.loader.exec_module(module=module)
    return module


@pytest.mark.parametrize(argnames="project_id", argvalues=REFUSED_CONFIGS)
@pytest.mark.parametrize(argnames="argv", argvalues=REFUSED_ARGV)
def test_the_marker_refuses_a_project_without_the_prefix(
    argv: Tuple[str, ...],
    project_id: Optional[Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-4.1 (design D2): while the marker is set and ``project_id`` is not an ``sff-test-*`` project path, ``call``,
    a compatibility subcommand and a delivery verb alike exit 2, send no request, run no steward and print nothing;
    exactly one log record names the marker and the configured project, and no record and nothing on standard error
    holds the configured token. With the marker and no ``config/gitlab.json``, each exits 1 with nothing sent, as it
    does without the marker: ``_load_config`` refuses before the guard."""
    caplog.set_level(level=logging.DEBUG)
    set_marker(monkeypatch=monkeypatch, present=True)
    steward = StewardRecorder()

    run = run_wrapper(
        argv=argv, project_id=project_id, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys, steward=steward
    )

    expected_exit = EXIT_CONFIG_REFUSED if project_id is NO_CONFIG else EXIT_PROJECT_REFUSED
    assert run.exit_code == expected_exit, outcome_of(run=run)
    assert run.requests == (), f"a refusal sent requests: {outcome_of(run=run)}"
    assert steward.calls == [], f"the steward ran: {steward.calls}"
    assert run.stdout == "", outcome_of(run=run)
    messages = [record.getMessage() for record in caplog.records]
    if project_id is not NO_CONFIG:
        shown = str(project_id)
        naming = [message for message in messages if MARKER_OPTION in message and shown in message]
        assert len(naming) == 1, f"no single log record names {MARKER_OPTION} and the project {shown}: {messages}"
    formatter = logging.Formatter()
    leaking = [text for text in (formatter.format(record=record) for record in caplog.records) if TOKEN in text]
    assert leaking == [], f"a log record holds the configured token: {leaking}"
    assert TOKEN not in run.stderr, f"standard error holds the configured token: {run.stderr!r}"


def test_the_interpreter_option_reaches_the_entry_script(tmp_path: Path) -> None:
    """AC-4.1, AC-4.3 (design D2): run as ``python -X sff_test_marker <scripts dir>/gitlab_wrapper.py`` in a temporary
    project, not this repository, whose ``config/gitlab.json`` ``_load_config`` accepts with ``project_id`` ``"1234"``,
    the script exits 2, prints nothing, and writes one line naming the marker and the configured project, and not the
    token, to standard error. The argv is ``call plan#create-an-issue``, which ``call`` itself refuses before any
    request, so the child reaches no network whichever refusal comes first; only the message tells the guard's refusal
    from ``call``'s."""
    fx.write_config(root=tmp_path, config=config_for(project_id=CHILD_PROJECT))

    completed = subprocess.run(
        args=[sys.executable, INTERPRETER_OPTION_FLAG, MARKER_OPTION, str(fx.WRAPPER_FILE), *CALL_GATED],
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        encoding=fx.TEXT_ENCODING,
        errors=CHILD_STREAM_ERRORS,
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )

    outcome = f"exit {completed.returncode}; stdout {completed.stdout!r}; stderr {completed.stderr!r}"
    assert completed.returncode == EXIT_PROJECT_REFUSED, outcome
    refusals = [line for line in completed.stderr.splitlines() if MARKER_OPTION in line and CHILD_PROJECT in line]
    assert len(refusals) == 1, f"standard error holds no single refusal naming {MARKER_OPTION}: {outcome}"
    assert TOKEN not in completed.stderr, outcome
    assert completed.stdout == "", outcome


def test_the_marker_lets_an_ephemeral_project_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4.2 (design D2): with ``project_id`` ``bestehorn-sff-test/sff-test-x``,
    ``call tenant-scale#retrieve-a-project`` under the marker sends the same requests, prints the same output and exits
    as it does without the marker, and is served (exit 0); ``enqueue-pr 1`` reaches the steward recorder once with the
    same arguments with and without the marker. The same marker then refuses the product project in this process, so
    the comparison was made with a marker the wrapper reads."""
    set_marker(monkeypatch=monkeypatch, present=False)
    without = run_wrapper(
        argv=CALL_RETRIEVE_PROJECT,
        project_id=EPHEMERAL_PROJECT,
        root=tmp_path / "without",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )
    without_steward = StewardRecorder()
    without_enqueue = run_wrapper(
        argv=ENQUEUE,
        project_id=EPHEMERAL_PROJECT,
        root=tmp_path / "without-enqueue",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=without_steward,
    )
    set_marker(monkeypatch=monkeypatch, present=True)
    marked_steward = StewardRecorder()
    marked = run_wrapper(
        argv=CALL_RETRIEVE_PROJECT,
        project_id=EPHEMERAL_PROJECT,
        root=tmp_path / "with",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )
    marked_enqueue = run_wrapper(
        argv=ENQUEUE,
        project_id=EPHEMERAL_PROJECT,
        root=tmp_path / "with-enqueue",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=marked_steward,
    )

    assert without.exit_code == EXIT_OK, outcome_of(run=without)
    served = [(request.method, request.url) for request in without.requests]
    assert served == [(METHOD_GET, project_url(project_id=EPHEMERAL_PROJECT))], outcome_of(run=without)
    assert json.loads(s=without.stdout) == project_record(project_id=EPHEMERAL_PROJECT), outcome_of(run=without)
    assert marked.exit_code == without.exit_code, outcome_of(run=marked)
    assert marked.stdout == without.stdout, outcome_of(run=marked)
    assert marked.requests == without.requests, outcome_of(run=marked)

    enqueued = [(ENQUEUE[0], list(ENQUEUE[1:]), DELIVERY_HOST)]
    assert without_steward.calls == enqueued, outcome_of(run=without_enqueue)
    assert marked_steward.calls == without_steward.calls, outcome_of(run=marked_enqueue)
    assert marked_enqueue.exit_code == without_enqueue.exit_code == EXIT_OK, outcome_of(run=marked_enqueue)
    assert marked_enqueue.requests == without_enqueue.requests == (), outcome_of(run=marked_enqueue)

    control = run_wrapper(
        argv=CALL_RETRIEVE_PROJECT,
        project_id=PRODUCT_PROJECT,
        root=tmp_path / "control",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )
    assert control.exit_code == EXIT_PROJECT_REFUSED, f"the marker was not read: {outcome_of(run=control)}"
    assert control.requests == (), outcome_of(run=control)


def test_the_marker_values_are_issue_10s(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-4.3 (design D2): the product GitLab wrapper's ``TEST_MARKER_OPTION`` and ``EPHEMERAL_PROJECT_PREFIX`` equal
    ``github_wrapper.py``'s ``TEST_MARKER_OPTION`` and ``EPHEMERAL_REPOSITORY_PREFIX``, and the marker is the option
    these tests and the GitLab forge suite pass to the interpreter."""
    gitlab = fx.load_wrapper(module_name=WRAPPER_MODULE)
    github = load_github_wrapper(monkeypatch=monkeypatch)

    issue_10s = (getattr(github, GITHUB_MARKER_CONSTANT, None), getattr(github, GITHUB_PREFIX_CONSTANT, None))
    assert issue_10s[0] == MARKER_OPTION, f"{GITHUB_WRAPPER_FILE} {GITHUB_MARKER_CONSTANT} is {issue_10s[0]!r}"
    gitlab_values = (getattr(gitlab, GITLAB_MARKER_CONSTANT, None), getattr(gitlab, GITLAB_PREFIX_CONSTANT, None))
    assert gitlab_values == issue_10s, (
        f"{fx.WRAPPER_FILE} ({GITLAB_MARKER_CONSTANT}, {GITLAB_PREFIX_CONSTANT}) is {gitlab_values!r}, "
        f"{GITHUB_WRAPPER_FILE} ({GITHUB_MARKER_CONSTANT}, {GITHUB_PREFIX_CONSTANT}) is {issue_10s!r}"
    )


@pytest.mark.parametrize(argnames="project_id", argvalues=NON_EPHEMERAL_PROJECTS)
def test_without_the_marker_every_project_is_served(
    project_id: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """UB-3, AC-4.3 (design D2): without the marker, each ``project_id`` AC-4.1's guard refuses is served as before this
    change: ``call tenant-scale#retrieve-a-project`` exits 0, sends its one request and prints the project record. The
    same project is then refused under the marker in this process, so the project served is one the guard judges."""
    set_marker(monkeypatch=monkeypatch, present=False)

    run = run_wrapper(
        argv=CALL_RETRIEVE_PROJECT,
        project_id=project_id,
        root=tmp_path / "without",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )

    assert run.exit_code == EXIT_OK, outcome_of(run=run)
    sent = [(request.method, request.url) for request in run.requests]
    assert sent == [(METHOD_GET, project_url(project_id=project_id))], outcome_of(run=run)
    assert json.loads(s=run.stdout) == project_record(project_id=project_id), outcome_of(run=run)

    set_marker(monkeypatch=monkeypatch, present=True)
    control = run_wrapper(
        argv=CALL_RETRIEVE_PROJECT,
        project_id=project_id,
        root=tmp_path / "with",
        monkeypatch=monkeypatch,
        capsys=capsys,
        steward=StewardRecorder(),
    )
    assert control.exit_code == EXIT_PROJECT_REFUSED, f"the marker was not read: {outcome_of(run=control)}"
    assert control.requests == (), outcome_of(run=control)
