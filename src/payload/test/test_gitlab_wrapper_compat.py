"""Tests for ``scripts/gitlab_wrapper.py``, the GitLab wrapper's entry script, and the subcommands it serves.

What is pinned (issue #13, ``design.md`` D3 and D7; UB-1, UB-2): ``_load_config`` refuses, with ``GitLabAPIError``, a
missing ``config/gitlab.json``, an absent, empty or ``PASTE_`` value of ``hostname``, ``project_id`` or ``token``, a
``token`` holding any character outside ``!`` to ``~`` (the message names the key, and neither it nor ``details``
holds the value) and a ``token_type`` other than ``private``, ``bearer`` and ``job``; ``main(argv=...)`` hands a
delivery verb to ``steward_delegate`` with the rest of argv unparsed and returns the steward's exit code; the script
exits 2 on a usage error; and a fresh interpreter loads the file by path with
``importlib.util.spec_from_file_location``, which the import bootstrap keeps possible once the entry script imports
``gitlab_api`` (D3).

The ``issue`` subcommands (D6; UB-1, UB-2): ``test_a_subcommand_form`` holds one case per argv form and flag — each
pins the exact requests the fake host records (method, URL with its query, JSON body), the JSON on standard output and
the exit code; ``claim-check`` exits 0 when claimed or not open and 3 when open and unclaimed; ``issue start`` exits 1
with no PUT for a closed issue or one assigned to another user, and 1 when the re-read does not confirm the claim;
``issue reopen`` of an open issue sends no PUT; a config holding only the template's keys sends ``PRIVATE-TOKEN`` and
claims with ``in-progress``; a token in the process environment is never sent; and the script without
``config/gitlab.json`` exits 1 naming the file.

The ``pipeline``, ``label``, ``mr`` and ``delete-branch`` subcommands (D6; UB-1) are forms of ``test_a_subcommand_form``
as well: ``pipeline status`` asks for the newest pipelines first, ``per_page`` the count (default 1), and prints the
first N; ``pipeline log`` prints text — per failed job of the latest pipeline a header line naming the job's id and
name, then its trace, or one line of text when no job failed or no pipeline exists; ``label list`` and ``mr checks``
read every page; ``delete-branch`` sends the branch as one encoded path segment. ``test_pipeline_wait_exit_codes`` pins
the skeleton's verdicts — 0 success, 10 for each status it ends on without success, 11 at the deadline — through
``main``, and from ``gitlab_api.commands.pipeline.pipeline_wait`` on a ``Transport`` whose clock moves only by the
pauses its ``sleep`` records, so no real time passes.

The in-process tests write ``config/gitlab.json`` into ``tmp_path``, the working directory by ``monkeypatch.chdir``,
load the entry script by path as ``test_wrapper_delivery.load`` does and call ``main(argv=...)``; the exit code is the
return value or the ``SystemExit`` code. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test. The subprocess tests run ``sys.executable`` with ``cwd=tmp_path``.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_wrapper_compat.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import re
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
WRAPPER_FILE = SCRIPTS_DIR / "gitlab_wrapper.py"
WRAPPER_MODULE = "gitlab_wrapper_compat_under_test"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

CONFIG_DIR = "config"
CONFIG_FILE_NAME = "gitlab.json"
DELIVERY_FILE_NAME = "delivery.json"
TEXT_ENCODING = "utf-8"

# The keys of config/gitlab.json (templates/config/gitlab.json.template, design.md D7) and of config/delivery.json.
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
FIELD_TOKEN_TYPE = "token_type"
FIELD_IN_PROGRESS_LABEL = "in_progress_label"
FIELD_MERGE = "merge"
FIELD_HOST = "host"
REQUIRED_KEYS = (FIELD_HOSTNAME, FIELD_PROJECT_ID, FIELD_TOKEN)
PLACEHOLDER_MARKER = "PASTE_"

# Keys of the arguments the fake `subprocess.run` records.
SEEN_COMMAND = "command"
SEEN_INPUT = "input"

TOKEN = "glpat-wrapper-compat-test"  # pragma: allowlist secret
# Two printable halves around a refused character; neither may reach a refusal's message or details.
TOKEN_HEAD = "glpat-HeadPart"  # pragma: allowlist secret
TOKEN_TAIL = "TailPart-42"  # pragma: allowlist secret
# The characters a token may hold: `!` to `~`, printable ASCII without the space (design.md D7).
TOKEN_REFUSED_RUN = "[^!-~]+"
# Refused characters, built from their code points so this file stays ASCII.
ZERO_WIDTH_SPACE = chr(0x200B)
DELETE = chr(0x7F)
E_ACUTE = chr(0xE9)

STEWARD_SCRIPT_SUFFIX = "scripts/merge_steward.py"
STEWARD_TOKEN_FLAG = "--token-stdin"
STEWARD_EXIT_REFUSED = 4
EXIT_USAGE = 2
USAGE_PREFIX = "usage:"
TRACEBACK = "Traceback"
CHILD_TIMEOUT_SECONDS = 120

# A fresh interpreter's program: load the entry script from the absolute path in argv[1] the way
# test_wrapper_delivery.load does; nothing puts the scripts directory on sys.path but the script itself (D3).
LOAD_BY_PATH = "; ".join(
    (
        "import importlib.util, logging, sys",
        "spec = importlib.util.spec_from_file_location('gitlab_wrapper_loaded_by_path', sys.argv[1])",
        "module = importlib.util.module_from_spec(spec)",
        "spec.loader.exec_module(module)",
        "assert issubclass(module.GitLabAPIError, Exception), 'gitlab_wrapper.GitLabAPIError stays importable'",
        "assert callable(module.main), 'gitlab_wrapper.main is callable'",
        "assert not logging.getLogger().handlers, 'loading gitlab_wrapper sets up no logging'",
    )
)


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

TEMPLATE_CONFIG: Dict[str, Any] = {
    FIELD_HOSTNAME: fixtures.HOST,
    FIELD_PROJECT_ID: 1,
    FIELD_TOKEN: TOKEN,
    FIELD_IN_PROGRESS_LABEL: "in-progress",
}


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory, with an empty ``config/``."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / CONFIG_DIR).mkdir()
    return tmp_path


def load_wrapper() -> ModuleType:
    """The entry script, loaded by path afresh, as ``test_wrapper_delivery.load`` loads a wrapper."""
    spec = importlib.util.spec_from_file_location(name=WRAPPER_MODULE, location=WRAPPER_FILE)
    assert spec and spec.loader, f"{WRAPPER_FILE} is missing"
    module = importlib.util.module_from_spec(spec=spec)
    spec.loader.exec_module(module=module)
    return module


def config_with(*, changes: Optional[Mapping[str, Any]] = None, removed: Sequence[str] = ()) -> Dict[str, Any]:
    """The template's keys with ``changes`` applied and the ``removed`` keys left out."""
    config = {key: value for key, value in TEMPLATE_CONFIG.items() if key not in removed}
    config.update(changes or {})
    return config


def write_json(*, path: Path, content: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(content), encoding=TEXT_ENCODING)


def main_exit_code(*, wrapper: ModuleType, argv: Sequence[str]) -> Any:
    """``main(argv=argv)``'s exit code: its return value, or the code of the ``SystemExit`` it raised."""
    assert "argv" in inspect.signature(wrapper.main).parameters, (
        "the entry script's main takes the argument vector: main(argv=None) -> int (design.md D7)"
    )
    try:
        return wrapper.main(argv=list(argv))
    except SystemExit as exit_request:
        return exit_request.code


def capture_steward(*, monkeypatch: pytest.MonkeyPatch, code: int) -> Dict[str, Any]:
    """Replace ``subprocess.run`` so the steward is not executed; the returned dict fills with what it was given."""
    seen: Dict[str, Any] = {}

    def fake_run(command: List[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen[SEEN_COMMAND] = list(command)
        seen.update(kwargs)
        return subprocess.CompletedProcess(args=command, returncode=code)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return seen


def run_child(*, args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run ``args`` in a child process from ``cwd`` and decode its output as UTF-8 (D7 reconfigures both streams)."""
    return subprocess.run(
        args=list(args),
        cwd=str(cwd),
        capture_output=True,
        encoding=TEXT_ENCODING,
        errors="replace",
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )


def printable_pieces(*, value: str) -> List[str]:
    """The runs of ``value`` a token may hold; a refusal that echoed the value would echo one of them."""
    return [piece for piece in re.split(pattern=TOKEN_REFUSED_RUN, string=value) if piece]


def refusal_cases() -> List[Any]:
    """One case per refusal rule of ``_load_config`` (design.md D7): the config written (``None``: no file), the
    text the message names (``None``: not pinned), the value nothing reported may contain (``None``: not pinned)."""
    cases = [pytest.param(None, str(Path(CONFIG_DIR) / CONFIG_FILE_NAME), None, id="file-missing")]
    for key in REQUIRED_KEYS:
        placeholder = f"{PLACEHOLDER_MARKER}YOUR_{key.upper()}_HERE"
        cases.append(pytest.param(config_with(removed=(key,)), key, None, id=f"{key}-absent"))
        cases.append(pytest.param(config_with(changes={key: ""}), key, None, id=f"{key}-empty"))
        cases.append(pytest.param(config_with(changes={key: placeholder}), key, None, id=f"{key}-placeholder"))
    refused_tokens = [
        ("token-trailing-newline", f"{TOKEN}\n"),
        ("token-zero-width-space", f"{TOKEN_HEAD}{ZERO_WIDTH_SPACE}{TOKEN_TAIL}"),
        ("token-space", f"{TOKEN_HEAD} {TOKEN_TAIL}"),  # U+0020, just below `!`
        ("token-delete", f"{TOKEN_HEAD}{DELETE}{TOKEN_TAIL}"),  # U+007F, just above `~`
        ("token-non-ascii", f"{TOKEN_HEAD}{E_ACUTE}{TOKEN_TAIL}"),
    ]
    for case, token in refused_tokens:
        cases.append(pytest.param(config_with(changes={FIELD_TOKEN: token}), FIELD_TOKEN, token, id=case))
    cases.append(pytest.param(config_with(changes={FIELD_TOKEN_TYPE: "oauth"}), None, None, id="token_type-unknown"))
    return cases


@pytest.mark.parametrize(("config", "named", "hidden"), refusal_cases())
def test_load_config_refusals(
    config: Optional[Dict[str, Any]], named: Optional[str], hidden: Optional[str], project: Path
) -> None:
    if config is not None:
        write_json(path=project / CONFIG_DIR / CONFIG_FILE_NAME, content=config)
    wrapper = load_wrapper()
    with pytest.raises(wrapper.GitLabAPIError) as refusal:
        wrapper._load_config()
    message = str(refusal.value)
    if named is not None:
        assert named in message, f"the refusal names {named!r}: {message!r}"
    if hidden is not None:
        details = refusal.value.details
        reported = message if details is None else f"{message}\n{details}"
        for piece in printable_pieces(value=hidden):
            assert piece not in reported, "a refused token is named by its key, never echoed (design.md D7)"


@pytest.mark.parametrize(
    ("verb", "args", "steward_verb"),
    [
        pytest.param("dequeue-pr", ["77", "--reason", "x"], "dequeue", id="dequeue-pr"),
        pytest.param("enqueue-pr", ["77"], "enqueue", id="enqueue-pr"),
        pytest.param("queue-status", ["--json"], "status", id="queue-status"),
        pytest.param("wait-landed", ["77", "--timeout-seconds", "540"], "wait-landed", id="wait-landed"),
        pytest.param("check-handoff", ["412"], "check-handoff", id="check-handoff"),
        pytest.param("check-landed", ["77", "78"], "check-landed", id="check-landed"),
    ],
)
def test_delivery_verb_through_main(
    verb: str,
    args: List[str],
    steward_verb: str,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_gitlab: Any,
) -> None:
    write_json(path=project / CONFIG_DIR / CONFIG_FILE_NAME, content=TEMPLATE_CONFIG)
    write_json(path=project / CONFIG_DIR / DELIVERY_FILE_NAME, content={FIELD_MERGE: "steward", FIELD_HOST: "gitlab"})
    seen = capture_steward(monkeypatch=monkeypatch, code=STEWARD_EXIT_REFUSED)
    wrapper = load_wrapper()
    assert main_exit_code(wrapper=wrapper, argv=[verb, *args]) == STEWARD_EXIT_REFUSED, (
        "main returns the steward's exit code unchanged"
    )
    command = seen.get(SEEN_COMMAND)
    assert command is not None, f"main({[verb, *args]}) did not run the merge steward"
    assert command[1].replace("\\", "/").endswith(STEWARD_SCRIPT_SUFFIX)
    assert command[2:] == [STEWARD_TOKEN_FLAG, steward_verb, *args], "the rest of argv reaches the steward unparsed"
    assert TOKEN not in " ".join(command), "the token never reaches argv"
    assert str(seen.get(SEEN_INPUT, "")).startswith(TOKEN), "the token of config/gitlab.json goes on stdin"
    assert fake_gitlab.requests == [], "a delivery verb sends no GitLab request of its own"


@pytest.mark.parametrize(
    "argv",
    [pytest.param([], id="no-subcommand"), pytest.param(["no-such-command"], id="unknown-subcommand")],
)
def test_script_usage_error_exits_2(argv: List[str], tmp_path: Path) -> None:
    # No config/gitlab.json: main parses before it loads the config (design.md D7), so a usage error is reported as
    # one whatever the config, and the child has no host it could reach.
    completed = run_child(args=[sys.executable, str(WRAPPER_FILE), *argv], cwd=tmp_path)
    assert completed.returncode == EXIT_USAGE, (
        f"a usage error exits {EXIT_USAGE} through argparse, got {completed.returncode}; stderr:\n{completed.stderr}"
    )
    assert USAGE_PREFIX in completed.stderr, f"argparse prints the usage on stderr:\n{completed.stderr}"
    assert TRACEBACK not in completed.stderr, f"a usage error is not a crash:\n{completed.stderr}"


def test_script_loads_by_path(tmp_path: Path) -> None:
    # `-I`: neither the working directory, the program's directory nor PYTHONPATH reaches sys.path, so only the
    # entry script's own bootstrap can make `gitlab_api` importable (design.md D3).
    completed = run_child(args=[sys.executable, "-I", "-c", LOAD_BY_PATH, str(WRAPPER_FILE)], cwd=tmp_path)
    assert completed.returncode == 0, (
        f"a fresh interpreter loads {WRAPPER_FILE} by path; exit {completed.returncode}, stderr:\n{completed.stderr}"
    )


# --- The subcommands (design.md D6; UB-1, UB-2) ---------------------------------------------------------------------

# This repository's config template (templates/config/gitlab.json.template; UB-2).
TEMPLATE_FILE = Path(__file__).resolve().parents[3] / "templates" / "config" / "gitlab.json.template"

REST_BASE = fixtures.REST_BASE
PROJECT_ID = TEMPLATE_CONFIG[FIELD_PROJECT_ID]
# The page size the transport adds to an offset-paged list: conventions.md "Offset-based" maximum (design.md D4).
PER_PAGE = "per_page=100"
HEADER_NEXT_PAGE = "x-next-page"
HEADER_CONTENT_TYPE = "Content-Type"
CONTENT_TYPE_JSON = "application/json"
# The three credential headers (design.md D4 "Credentials"); a request carries exactly one of them.
HEADER_PRIVATE_TOKEN = "PRIVATE-TOKEN"
HEADER_AUTHORIZATION = "Authorization"
HEADER_JOB_TOKEN = "JOB-TOKEN"

METHOD_GET = "GET"
METHOD_POST = "POST"
METHOD_PUT = "PUT"
METHOD_DELETE = "DELETE"
EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_CLAIM_UNCLAIMED = 3
# `pipeline wait`'s verdicts, the skeleton's EXIT_WAIT_NOT_SUCCESS and EXIT_WAIT_TIMEOUT (design.md D6).
EXIT_WAIT_NOT_SUCCESS = 10
EXIT_WAIT_TIMEOUT = 11

# Request and response keys: rest/plan.md "Issues API" and "Notes API", rest/software-supply-chain-security.md "Users
# API", and `issue claim-check`'s own output (design.md D6).
FIELD_ID = "id"
FIELD_IID = "iid"
FIELD_TITLE = "title"
FIELD_DESCRIPTION = "description"
FIELD_STATE = "state"
FIELD_LABELS = "labels"
FIELD_ASSIGNEE = "assignee"
FIELD_ASSIGNEES = "assignees"
FIELD_USERNAME = "username"
FIELD_UPDATED_AT = "updated_at"
FIELD_BODY = "body"
FIELD_NOTEABLE_IID = "noteable_iid"
FIELD_MESSAGE = "message"
FIELD_ADD_LABELS = "add_labels"
FIELD_REMOVE_LABELS = "remove_labels"
FIELD_ASSIGNEE_IDS = "assignee_ids"
FIELD_STATE_EVENT = "state_event"
FIELD_CLAIMED = "claimed"

STATE_OPENED = "opened"
STATE_CLOSED = "closed"
EVENT_CLOSE = "close"
EVENT_REOPEN = "reopen"
# `assignee_ids: [0]` unassigns everyone (rest/plan.md "Update an issue").
UNASSIGN_ID = 0

IN_PROGRESS = "in-progress"  # TEMPLATE_CONFIG's in_progress_label and the default (design.md D7)
CONFIGURED_LABEL = "claimed-by-a-worker"
OTHER_LABEL = "needs-triage"
IID = 7
SECOND_IID = 8
ISSUE_TITLE = "Fix the parser"
ISSUE_DESCRIPTION = "Steps to reproduce: run the parser on an empty file."
NOTE_ID = 501
NOTE_BODY = "Claimed; working on it."
UPDATED_BEFORE = "2026-11-10T08:00:00.000Z"
UPDATED_AFTER = "2026-11-10T08:05:00.000Z"
UNKNOWN_USERNAME = "nobody-by-this-name"

# The token's owner (`GET /user`), another user, and the user `--user` names (`GET /users?username=...`).
ME: Dict[str, Any] = {FIELD_ID: 42, FIELD_USERNAME: "maintainer"}
OTHER_USER: Dict[str, Any] = {FIELD_ID: 99, FIELD_USERNAME: "someone-else"}
NAMED_USER: Dict[str, Any] = {FIELD_ID: 77, FIELD_USERNAME: "alice"}

# Variables GitLab clients read a token from (glab, python-gitlab, GitLab CI/CD); the wrapper reads none of them.
ENVIRONMENT_TOKENS: Dict[str, str] = {
    "GITLAB_TOKEN": "glpat-environment-gitlab-token",  # pragma: allowlist secret
    "GITLAB_PRIVATE_TOKEN": "glpat-environment-private-token",  # pragma: allowlist secret
    "GITLAB_ACCESS_TOKEN": "glpat-environment-access-token",  # pragma: allowlist secret
    "PRIVATE_TOKEN": "glpat-environment-bare-private-token",  # pragma: allowlist secret
    "CI_JOB_TOKEN": "glcbt-environment-job-token",  # pragma: allowlist secret
}

# Template values for the template's `PASTE_` placeholders (UB-2).
TEMPLATE_FILLED: Dict[str, Any] = {FIELD_PROJECT_ID: 4242, FIELD_TOKEN: TOKEN}


class Exchange(NamedTuple):
    """One request a subcommand must send, and the fake host's answer to it."""

    method: str
    url: str
    sent: Any = None  # the JSON body the request carries; None: no body
    status: int = 200
    headers: Tuple[Tuple[str, str], ...] = ()
    answer: Any = None  # the response body, sent as JSON


class FormCase(NamedTuple):
    """One argv form: the requests it sends with their answers, the JSON on standard output, the exit code."""

    argv: Tuple[str, ...]
    exchanges: Tuple[Exchange, ...]
    printed: Any  # the JSON value printed on standard output; None: nothing is printed
    exit_code: int = EXIT_OK
    config_changes: Tuple[Tuple[str, Any], ...] = ()  # applied to TEMPLATE_CONFIG for this case


def issues_url(*, base: str = REST_BASE, project: Any = PROJECT_ID) -> str:
    return f"{base}/projects/{project}/issues"


def issue_url(*, base: str = REST_BASE, project: Any = PROJECT_ID, iid: int = IID) -> str:
    return f"{issues_url(base=base, project=project)}/{iid}"


def user_url(*, base: str = REST_BASE) -> str:
    return f"{base}/user"


def users_url(*, username: str) -> str:
    return f"{REST_BASE}/users?username={username}"


def with_query(*, url: str, pairs: Sequence[str]) -> str:
    """``url`` with the already-encoded ``pairs`` as its query, in the order given."""
    return f"{url}?{'&'.join(pairs)}"


def issue_record(
    *,
    iid: int = IID,
    state: str = STATE_OPENED,
    labels: Sequence[str] = (),
    assignees: Sequence[Mapping[str, Any]] = (),
    updated_at: str = UPDATED_BEFORE,
) -> Dict[str, Any]:
    """An issue as ``GET /projects/:id/issues/:issue_iid`` returns it, with the fields the subcommands read."""
    people = [dict(person) for person in assignees]
    return {
        FIELD_ID: 9000 + iid,
        FIELD_IID: iid,
        FIELD_TITLE: ISSUE_TITLE,
        FIELD_STATE: state,
        FIELD_LABELS: list(labels),
        FIELD_ASSIGNEES: people,
        FIELD_ASSIGNEE: people[0] if people else None,
        FIELD_UPDATED_AT: updated_at,
    }


def form(
    *,
    case_id: str,
    argv: Sequence[str],
    exchanges: Sequence[Exchange],
    printed: Any,
    exit_code: int = EXIT_OK,
    config_changes: Optional[Mapping[str, Any]] = None,
) -> Any:
    case = FormCase(
        argv=tuple(argv),
        exchanges=tuple(exchanges),
        printed=printed,
        exit_code=exit_code,
        config_changes=tuple((config_changes or {}).items()),
    )
    return pytest.param(case, id=case_id)


def start_exchanges(
    *, base: str = REST_BASE, project: Any = PROJECT_ID, label: str = IN_PROGRESS
) -> Tuple[Tuple[Exchange, ...], Dict[str, Any]]:
    """``issue start 7`` that takes: read the issue, resolve the token's user, ONE claim PUT, re-read (design.md D6);
    and the re-read issue, which is what the subcommand prints."""
    url = issue_url(base=base, project=project)
    before = issue_record(labels=(OTHER_LABEL,))
    claimed = issue_record(labels=(OTHER_LABEL, label), assignees=(ME,))
    verified = issue_record(labels=(OTHER_LABEL, label), assignees=(ME,), updated_at=UPDATED_AFTER)
    exchanges = (
        Exchange(method=METHOD_GET, url=url, answer=before),
        Exchange(method=METHOD_GET, url=user_url(base=base), answer=ME),
        Exchange(
            method=METHOD_PUT,
            url=url,
            sent={FIELD_ADD_LABELS: label, FIELD_ASSIGNEE_IDS: [ME[FIELD_ID]]},
            answer=claimed,
        ),
        Exchange(method=METHOD_GET, url=url, answer=verified),
    )
    return exchanges, verified


def issue_list_cases() -> List[Any]:
    """``issue list`` and each of its flags alone: every page (offset paging, design.md D4 ``pages``)."""
    first = issue_record(iid=IID)
    second = issue_record(iid=SECOND_IID, labels=(OTHER_LABEL,))
    cases = [
        form(
            case_id="issue-list",
            argv=("issue", "list"),
            exchanges=(
                Exchange(
                    method=METHOD_GET,
                    url=with_query(url=issues_url(), pairs=(PER_PAGE,)),
                    headers=((HEADER_NEXT_PAGE, "2"),),
                    answer=[first],
                ),
                Exchange(
                    method=METHOD_GET,
                    url=with_query(url=issues_url(), pairs=(PER_PAGE, "page=2")),
                    headers=((HEADER_NEXT_PAGE, ""),),
                    answer=[second],
                ),
            ),
            printed=[first, second],
        )
    ]
    # One flag at a time, so the query's order is the flag's pair and then the transport's page size.
    flags = [
        ("issue-list-state", ("--state", STATE_OPENED), "state=opened"),
        ("issue-list-assignee-any", ("--assignee", "*"), "assignee_id=Any"),
        ("issue-list-assignee-none", ("--assignee", "none"), "assignee_id=None"),
        ("issue-list-assignee-username", ("--assignee", NAMED_USER[FIELD_USERNAME]), "assignee_username[]=alice"),
        ("issue-list-labels", ("--labels", IN_PROGRESS), "labels=in-progress"),
    ]
    for case_id, flag, pair in flags:
        cases.append(
            form(
                case_id=case_id,
                argv=("issue", "list", *flag),
                exchanges=(
                    Exchange(
                        method=METHOD_GET, url=with_query(url=issues_url(), pairs=(pair, PER_PAGE)), answer=[first]
                    ),
                ),
                printed=[first],
            )
        )
    return cases


def issue_create_cases() -> List[Any]:
    """``issue show``, ``issue create`` with each optional flag, ``issue comment``."""
    shown = issue_record(labels=(OTHER_LABEL,), assignees=(OTHER_USER,))
    created = issue_record()
    note = {FIELD_ID: NOTE_ID, FIELD_BODY: NOTE_BODY, FIELD_NOTEABLE_IID: IID}
    creates = [
        ("issue-create", (), {}),
        ("issue-create-description", ("--description", ISSUE_DESCRIPTION), {FIELD_DESCRIPTION: ISSUE_DESCRIPTION}),
        ("issue-create-labels", ("--labels", OTHER_LABEL), {FIELD_LABELS: OTHER_LABEL}),
    ]
    cases = [
        form(
            case_id="issue-show",
            argv=("issue", "show", str(IID)),
            exchanges=(Exchange(method=METHOD_GET, url=issue_url(), answer=shown),),
            printed=shown,
        )
    ]
    for case_id, flag, extra in creates:
        cases.append(
            form(
                case_id=case_id,
                argv=("issue", "create", "--title", ISSUE_TITLE, *flag),
                exchanges=(
                    Exchange(
                        method=METHOD_POST, url=issues_url(), sent={FIELD_TITLE: ISSUE_TITLE, **extra}, answer=created
                    ),
                ),
                printed=created,
            )
        )
    cases.append(
        form(
            case_id="issue-comment",
            argv=("issue", "comment", str(IID), "--body", NOTE_BODY),
            exchanges=(
                Exchange(method=METHOD_POST, url=f"{issue_url()}/notes", sent={FIELD_BODY: NOTE_BODY}, answer=note),
            ),
            printed=note,
        )
    )
    return cases


def issue_claim_cases() -> List[Any]:
    """``issue start`` (the default and a configured label), ``issue release``, ``label-add``, ``label-remove``."""
    exchanges, verified = start_exchanges()
    configured_exchanges, configured_verified = start_exchanges(label=CONFIGURED_LABEL)
    released = issue_record(labels=(OTHER_LABEL,))
    labelled = issue_record(labels=(OTHER_LABEL, IN_PROGRESS))
    return [
        form(case_id="issue-start", argv=("issue", "start", str(IID)), exchanges=exchanges, printed=verified),
        form(
            case_id="issue-start-configured-label",
            argv=("issue", "start", str(IID)),
            exchanges=configured_exchanges,
            printed=configured_verified,
            config_changes={FIELD_IN_PROGRESS_LABEL: CONFIGURED_LABEL},
        ),
        form(
            case_id="issue-release",
            argv=("issue", "release", str(IID)),
            exchanges=(
                Exchange(
                    method=METHOD_PUT,
                    url=issue_url(),
                    sent={FIELD_REMOVE_LABELS: IN_PROGRESS, FIELD_ASSIGNEE_IDS: [UNASSIGN_ID]},
                    answer=released,
                ),
            ),
            printed=released,
        ),
        form(
            case_id="issue-label-add",
            argv=("issue", "label-add", str(IID), "--labels", IN_PROGRESS),
            exchanges=(
                Exchange(method=METHOD_PUT, url=issue_url(), sent={FIELD_ADD_LABELS: IN_PROGRESS}, answer=labelled),
            ),
            printed=labelled,
        ),
        form(
            case_id="issue-label-remove",
            argv=("issue", "label-remove", str(IID), "--labels", IN_PROGRESS),
            exchanges=(
                Exchange(method=METHOD_PUT, url=issue_url(), sent={FIELD_REMOVE_LABELS: IN_PROGRESS}, answer=released),
            ),
            printed=released,
        ),
    ]


def issue_assign_cases() -> List[Any]:
    """``issue assign`` with ``--me``, ``--user U`` (and a username no user has), ``--unassign``."""
    mine = issue_record(assignees=(ME,))
    theirs = issue_record(assignees=(NAMED_USER,))
    nobody = issue_record()
    return [
        form(
            case_id="issue-assign-me",
            argv=("issue", "assign", str(IID), "--me"),
            exchanges=(
                Exchange(method=METHOD_GET, url=user_url(), answer=ME),
                Exchange(method=METHOD_PUT, url=issue_url(), sent={FIELD_ASSIGNEE_IDS: [ME[FIELD_ID]]}, answer=mine),
            ),
            printed=mine,
        ),
        form(
            case_id="issue-assign-user",
            argv=("issue", "assign", str(IID), "--user", NAMED_USER[FIELD_USERNAME]),
            exchanges=(
                Exchange(method=METHOD_GET, url=users_url(username=NAMED_USER[FIELD_USERNAME]), answer=[NAMED_USER]),
                Exchange(
                    method=METHOD_PUT, url=issue_url(), sent={FIELD_ASSIGNEE_IDS: [NAMED_USER[FIELD_ID]]}, answer=theirs
                ),
            ),
            printed=theirs,
        ),
        form(
            case_id="issue-assign-user-unknown",
            argv=("issue", "assign", str(IID), "--user", UNKNOWN_USERNAME),
            exchanges=(Exchange(method=METHOD_GET, url=users_url(username=UNKNOWN_USERNAME), answer=[]),),
            printed=None,
            exit_code=EXIT_API_ERROR,
        ),
        form(
            case_id="issue-assign-unassign",
            argv=("issue", "assign", str(IID), "--unassign"),
            exchanges=(
                Exchange(method=METHOD_PUT, url=issue_url(), sent={FIELD_ASSIGNEE_IDS: [UNASSIGN_ID]}, answer=nobody),
            ),
            printed=nobody,
        ),
    ]


def issue_state_cases() -> List[Any]:
    """``issue close``; ``issue reopen`` of a closed issue (an open one: ``test_issue_reopen_of_open_issue``)."""
    closed = issue_record(state=STATE_CLOSED)
    reopened = issue_record(updated_at=UPDATED_AFTER)
    return [
        form(
            case_id="issue-close",
            argv=("issue", "close", str(IID)),
            exchanges=(
                Exchange(method=METHOD_PUT, url=issue_url(), sent={FIELD_STATE_EVENT: EVENT_CLOSE}, answer=closed),
            ),
            printed=closed,
        ),
        form(
            case_id="issue-reopen",
            argv=("issue", "reopen", str(IID)),
            exchanges=(
                Exchange(method=METHOD_GET, url=issue_url(), answer=closed),
                Exchange(method=METHOD_PUT, url=issue_url(), sent={FIELD_STATE_EVENT: EVENT_REOPEN}, answer=reopened),
            ),
            printed=reopened,
        ),
    ]


# --- The pipeline, label, mr and delete-branch subcommands (design.md D6; UB-1) ----------------------------------

# Request and response keys: rest/verify.md "Pipelines API" and "Jobs API", rest/plan.md "Project labels API",
# rest/ai-coding.md "Merge requests API" and "Merge request approvals API"; the keys of `pipeline wait`'s summary line
# (the skeleton's) and of `delete-branch`'s output (design.md D6).
FIELD_STATUS = "status"
FIELD_REF = "ref"
FIELD_WEB_URL = "web_url"
FIELD_NAME = "name"
FIELD_STAGE = "stage"
FIELD_COLOR = "color"
FIELD_SOURCE_BRANCH = "source_branch"
FIELD_TARGET_BRANCH = "target_branch"
FIELD_REMOVE_SOURCE_BRANCH = "remove_source_branch"
FIELD_SHOULD_REMOVE_SOURCE_BRANCH = "should_remove_source_branch"
FIELD_MERGE_STATUS = "merge_status"
FIELD_APPROVED = "approved"
FIELD_APPROVED_BY = "approved_by"
FIELD_USER = "user"
FIELD_BRANCH = "branch"
FIELD_DELETED = "deleted"
FIELD_TIMEOUT_SECONDS = "timeout_seconds"

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_RUNNING = "running"
# The statuses `pipeline wait` ends on without success: the skeleton's PIPELINE_TERMINAL_STATUSES less `success`.
NOT_SUCCESS_STATUSES = (STATUS_FAILED, "canceled", "skipped", "manual")
# The status `pipeline wait`'s summary line names when no poll was answered (the skeleton's).
STATUS_UNKNOWN = "unknown"
STATE_MERGED = "merged"
MERGE_STATUS_MERGEABLE = "can_be_merged"

# `pipeline status` and `pipeline log` ask for the newest pipelines first (design.md D6); `pipeline log` asks for one
# pipeline's failed jobs, `scope` sent as an array (rest/verify.md "List all jobs by pipeline"); a list read to its end
# asks for page 2 by page 1's `x-next-page` (design.md D4 `pages`).
NEWEST_FIRST = ("order_by=id", "sort=desc")
FAILED_JOBS = "scope[]=failed"
SECOND_PAGE = "page=2"
CONTENT_TYPE_TEXT = "text/plain; charset=utf-8"

PIPELINE_ID = 1201
OLDER_PIPELINE_ID = 1200
OLDEST_PIPELINE_ID = 1199
JOB_ID = 3001
SECOND_JOB_ID = 3002
JOB_NAME = "unit-tests"
SECOND_JOB_NAME = "lint"
JOB_TRACE = (
    "Running with gitlab-runner 17.5.0\n"
    "$ python scripts/run_tests.py\n"
    "FAILED test/test_parser.py::test_empty_file - AssertionError\n"
)
# A blank line inside a trace is part of it.
SECOND_JOB_TRACE = "$ ruff check .\n\nE501 Line too long (121 > 120)\n"
LABEL_ID = 601
LABEL_COLOR = "#d9534f"
NEW_LABEL = "blocked"
LABEL_DESCRIPTION = "Waiting on another issue."
MR_IID = 21
MR_TITLE = "Fix the parser on an empty file"
SOURCE_BRANCH = "feature/issue-13-parser"
# SOURCE_BRANCH as ONE path segment, `/` written %2F (conventions.md "URL-encoding path parameters", design.md D5).
BRANCH_SEGMENT = "feature%2Fissue-13-parser"
TARGET_BRANCH = "main"
# conventions.md "Responses": `201` with the new resource for creates, `204` for deletes without a body. A refused
# approval is an error status, here 401 with GitLab's `message` body shape (conventions.md "Body shapes").
CREATED = 201
NO_CONTENT = 204
UNAUTHORIZED = 401
REFUSED_APPROVAL = {FIELD_MESSAGE: "401 Unauthorized"}

# `pipeline wait` through `main` waits the contract's bounded foreground wait. `pipeline_wait` on the fake clock gets a
# deadline three poll intervals after the start: its polls at 0, 15 and 30 seconds are answered, and its third pause
# brings the clock to the deadline, where the skeleton stops polling (it polls while the clock is BEFORE the deadline).
WAIT_TIMEOUT_SECONDS = 540
DIRECT_TIMEOUT_SECONDS = 45
POLL_INTERVAL_SECONDS = 15
POLLS_BEFORE_DEADLINE = DIRECT_TIMEOUT_SECONDS // POLL_INTERVAL_SECONDS
CLOCK_START_SECONDS = 1000.0
TOKEN_TYPE_PRIVATE = "private"  # a token_type value, not a secret
PIPELINE_COMMANDS_FILE = SCRIPTS_DIR / "gitlab_api" / "commands" / "pipeline.py"
PIPELINE_COMMANDS_MODULE = "gitlab_api.commands.pipeline"
TRANSPORT_MODULE = "gitlab_api.transport"


def project_url(*, path: str) -> str:
    """``path`` under the configured project's ``/projects/:id``."""
    return f"{REST_BASE}/projects/{PROJECT_ID}{path}"


def newest_pipelines_url(*, count: int) -> str:
    """``GET /projects/:id/pipelines`` for the ``count`` newest pipelines (design.md D6 ``pipeline status``)."""
    return with_query(url=project_url(path="/pipelines"), pairs=(*NEWEST_FIRST, f"per_page={count}"))


def pipeline_url() -> str:
    return project_url(path=f"/pipelines/{PIPELINE_ID}")


def merge_request_url(*, suffix: str = "") -> str:
    return project_url(path=f"/merge_requests/{MR_IID}{suffix}")


def web_url(*, kind: str, item_id: int) -> str:
    """The web page of one of the project's pipelines, jobs or merge requests."""
    return f"https://{fixtures.HOST}/group/project/-/{kind}/{item_id}"


def pipeline_record(*, pipeline_id: int = PIPELINE_ID, status: str = STATUS_FAILED) -> Dict[str, Any]:
    """A pipeline as the Pipelines API lists and returns it, with the fields the subcommands read."""
    return {
        FIELD_ID: pipeline_id,
        FIELD_STATUS: status,
        FIELD_REF: TARGET_BRANCH,
        FIELD_WEB_URL: web_url(kind="pipelines", item_id=pipeline_id),
    }


def job_record(*, job_id: int, name: str) -> Dict[str, Any]:
    """A failed job as ``GET /projects/:id/pipelines/:pipeline_id/jobs`` lists it."""
    return {
        FIELD_ID: job_id,
        FIELD_NAME: name,
        FIELD_STAGE: "test",
        FIELD_STATUS: STATUS_FAILED,
        FIELD_WEB_URL: web_url(kind="jobs", item_id=job_id),
    }


def label_record(*, label_id: int, name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """A project label as the Project labels API lists and returns it."""
    return {FIELD_ID: label_id, FIELD_NAME: name, FIELD_COLOR: LABEL_COLOR, FIELD_DESCRIPTION: description}


def merge_request_record(*, state: str = STATE_OPENED) -> Dict[str, Any]:
    """A merge request as the Merge requests API returns it, with the fields its callers read."""
    return {
        FIELD_ID: 7000 + MR_IID,
        FIELD_IID: MR_IID,
        FIELD_TITLE: MR_TITLE,
        FIELD_STATE: state,
        FIELD_SOURCE_BRANCH: SOURCE_BRANCH,
        FIELD_TARGET_BRANCH: TARGET_BRANCH,
        FIELD_MERGE_STATUS: MERGE_STATUS_MERGEABLE,
        FIELD_WEB_URL: web_url(kind="merge_requests", item_id=MR_IID),
    }


def two_pages(*, url: str, first: List[Any], second: List[Any]) -> Tuple[Exchange, Exchange]:
    """A list read to its end by offset paging: the transport's page size, then ``page=2`` named by page 1's
    ``x-next-page``, which page 2 sends empty (design.md D4 ``pages``)."""
    return (
        Exchange(
            method=METHOD_GET,
            url=with_query(url=url, pairs=(PER_PAGE,)),
            headers=((HEADER_NEXT_PAGE, "2"),),
            answer=first,
        ),
        Exchange(
            method=METHOD_GET,
            url=with_query(url=url, pairs=(PER_PAGE, SECOND_PAGE)),
            headers=((HEADER_NEXT_PAGE, ""),),
            answer=second,
        ),
    )


def text_line_at(*, lines: Sequence[str], start: int) -> int:
    """The index of the first line from ``start`` on that is not blank; ``len(lines)`` when there is none."""
    return next((index for index in range(start, len(lines)) if lines[index].strip()), len(lines))


class TextOutput(ABC):
    """Standard output that is text, not JSON: ``check`` asserts what design.md D6 states of it."""

    @abstractmethod
    def check(self, *, out: str) -> None:
        """Assert that ``out``, the whole of standard output, is this output."""


@dataclass(frozen=True)
class JobTracesOutput(TextOutput):
    """``pipeline log`` with failed jobs (design.md D6): per job, in the order the jobs were listed, one header line
    naming the job's ``id`` and ``name``, then the job's trace line for line; blank lines may separate the blocks, and
    nothing else is printed."""

    jobs: Tuple[Tuple[int, str, str], ...]  # (id, name, trace) of each failed job

    def check(self, *, out: str) -> None:
        lines = out.splitlines()
        cursor = 0
        for job_id, name, trace in self.jobs:
            cursor = text_line_at(lines=lines, start=cursor)
            assert cursor < len(lines), f"no header line for job {job_id} ({name}); standard output:\n{out}"
            header = lines[cursor]
            assert str(job_id) in header and name in header, (
                f"job {job_id}'s header line names its id and its name {name!r}: {header!r}; standard output:\n{out}"
            )
            expected = trace.splitlines()
            shown = lines[cursor + 1 : cursor + 1 + len(expected)]
            assert shown == expected, f"job {job_id}'s trace follows its header line verbatim; standard output:\n{out}"
            cursor += 1 + len(expected)
        assert text_line_at(lines=lines, start=cursor) == len(lines), f"nothing follows the last trace:\n{out}"


@dataclass(frozen=True)
class OneLineOutput(TextOutput):
    """``pipeline log`` when no job failed or no pipeline exists (design.md D6): one line of text, not JSON."""

    def check(self, *, out: str) -> None:
        lines = [line for line in out.splitlines() if line.strip()]
        assert len(lines) == 1, f"one line on standard output, got {len(lines)}:\n{out}"
        assert isinstance(printed_value(out=out), str), f"a line of text, not a JSON value:\n{out}"


def pipeline_status_cases() -> List[Any]:
    """``pipeline status``: the newest pipeline; with ``--count 2`` the first two items of the page."""
    newest = pipeline_record(pipeline_id=PIPELINE_ID)
    older = pipeline_record(pipeline_id=OLDER_PIPELINE_ID, status=STATUS_SUCCESS)
    oldest = pipeline_record(pipeline_id=OLDEST_PIPELINE_ID, status=STATUS_SUCCESS)
    return [
        form(
            case_id="pipeline-status",
            argv=("pipeline", "status"),
            exchanges=(Exchange(method=METHOD_GET, url=newest_pipelines_url(count=1), answer=[newest]),),
            printed=[newest],
        ),
        form(
            case_id="pipeline-status-count",
            argv=("pipeline", "status", "--count", "2"),
            # A page holding more than asked for: only the first N items are printed (design.md D6).
            exchanges=(Exchange(method=METHOD_GET, url=newest_pipelines_url(count=2), answer=[newest, older, oldest]),),
            printed=[newest, older],
        ),
    ]


def pipeline_log_cases() -> List[Any]:
    """``pipeline log``: the latest pipeline, as ``pipeline status`` reads it; its failed jobs; each one's trace. One
    line when no job failed (the pipeline still runs) and when no pipeline exists, which reads no jobs."""
    latest = newest_pipelines_url(count=1)
    failed_jobs = with_query(url=f"{pipeline_url()}/jobs", pairs=(FAILED_JOBS,))
    traces = ((JOB_ID, JOB_NAME, JOB_TRACE), (SECOND_JOB_ID, SECOND_JOB_NAME, SECOND_JOB_TRACE))
    trace_exchanges = tuple(
        Exchange(
            method=METHOD_GET,
            url=project_url(path=f"/jobs/{job_id}/trace"),
            headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_TEXT),),
            answer=trace,
        )
        for job_id, _, trace in traces
    )
    jobs = [job_record(job_id=job_id, name=name) for job_id, name, _ in traces]
    return [
        form(
            case_id="pipeline-log",
            argv=("pipeline", "log"),
            exchanges=(
                Exchange(method=METHOD_GET, url=latest, answer=[pipeline_record(status=STATUS_FAILED)]),
                Exchange(method=METHOD_GET, url=failed_jobs, answer=jobs),
                *trace_exchanges,
            ),
            printed=JobTracesOutput(jobs=traces),
        ),
        form(
            case_id="pipeline-log-none-failed",
            argv=("pipeline", "log"),
            exchanges=(
                Exchange(method=METHOD_GET, url=latest, answer=[pipeline_record(status=STATUS_RUNNING)]),
                Exchange(method=METHOD_GET, url=failed_jobs, answer=[]),
            ),
            printed=OneLineOutput(),
        ),
        form(
            case_id="pipeline-log-no-pipeline",
            argv=("pipeline", "log"),
            exchanges=(Exchange(method=METHOD_GET, url=latest, answer=[]),),
            printed=OneLineOutput(),
        ),
    ]


def label_cases() -> List[Any]:
    """``label list`` (every page) and ``label create`` without and with ``--description``."""
    labels_url = project_url(path="/labels")
    listed = [label_record(label_id=LABEL_ID, name=IN_PROGRESS)]
    more = [label_record(label_id=LABEL_ID + 1, name=OTHER_LABEL)]
    cases = [
        form(
            case_id="label-list",
            argv=("label", "list"),
            exchanges=two_pages(url=labels_url, first=listed, second=more),
            printed=[*listed, *more],
        )
    ]
    creates = [
        ("label-create", (), {}),
        ("label-create-description", ("--description", LABEL_DESCRIPTION), {FIELD_DESCRIPTION: LABEL_DESCRIPTION}),
    ]
    for case_id, flag, extra in creates:
        created = label_record(label_id=LABEL_ID + 2, name=NEW_LABEL, description=extra.get(FIELD_DESCRIPTION))
        cases.append(
            form(
                case_id=case_id,
                argv=("label", "create", "--name", NEW_LABEL, "--color", LABEL_COLOR, *flag),
                exchanges=(
                    Exchange(
                        method=METHOD_POST,
                        url=labels_url,
                        sent={FIELD_NAME: NEW_LABEL, FIELD_COLOR: LABEL_COLOR, **extra},
                        status=CREATED,
                        answer=created,
                    ),
                ),
                printed=created,
            )
        )
    return cases


def mr_cases() -> List[Any]:
    """``mr create``, ``mr get``, ``mr checks`` (every page), ``mr approve`` and a refused one, ``mr merge``."""
    opened = merge_request_record()
    merged = merge_request_record(state=STATE_MERGED)
    approval = {
        FIELD_ID: opened[FIELD_ID],
        FIELD_IID: MR_IID,
        FIELD_APPROVED: True,
        FIELD_APPROVED_BY: [{FIELD_USER: ME}],
    }
    checked = [pipeline_record(pipeline_id=PIPELINE_ID)]
    rechecked = [pipeline_record(pipeline_id=OLDER_PIPELINE_ID, status=STATUS_SUCCESS)]
    created = {
        FIELD_SOURCE_BRANCH: SOURCE_BRANCH,
        FIELD_TARGET_BRANCH: TARGET_BRANCH,
        FIELD_TITLE: MR_TITLE,
        FIELD_REMOVE_SOURCE_BRANCH: True,
    }
    return [
        form(
            case_id="mr-create",
            argv=("mr", "create", "--source", SOURCE_BRANCH, "--target", TARGET_BRANCH, "--title", MR_TITLE),
            exchanges=(
                Exchange(
                    method=METHOD_POST,
                    url=project_url(path="/merge_requests"),
                    sent=created,
                    status=CREATED,
                    answer=opened,
                ),
            ),
            printed=opened,
        ),
        form(
            case_id="mr-get",
            argv=("mr", "get", str(MR_IID)),
            exchanges=(Exchange(method=METHOD_GET, url=merge_request_url(), answer=opened),),
            printed=opened,
        ),
        form(
            case_id="mr-checks",
            argv=("mr", "checks", str(MR_IID)),
            exchanges=two_pages(url=merge_request_url(suffix="/pipelines"), first=checked, second=rechecked),
            printed=[*checked, *rechecked],
        ),
        form(
            case_id="mr-approve",
            argv=("mr", "approve", str(MR_IID)),
            exchanges=(Exchange(method=METHOD_POST, url=merge_request_url(suffix="/approve"), answer=approval),),
            printed=approval,
        ),
        # A refused approval (the own-MR caveat of commands/mr.py) is a GitLabAPIError: exit 1, nothing printed.
        form(
            case_id="mr-approve-refused",
            argv=("mr", "approve", str(MR_IID)),
            exchanges=(
                Exchange(
                    method=METHOD_POST,
                    url=merge_request_url(suffix="/approve"),
                    status=UNAUTHORIZED,
                    answer=REFUSED_APPROVAL,
                ),
            ),
            printed=None,
            exit_code=EXIT_API_ERROR,
        ),
        form(
            case_id="mr-merge",
            argv=("mr", "merge", str(MR_IID)),
            exchanges=(
                Exchange(
                    method=METHOD_PUT,
                    url=merge_request_url(suffix="/merge"),
                    sent={FIELD_SHOULD_REMOVE_SOURCE_BRANCH: True},
                    answer=merged,
                ),
            ),
            printed=merged,
        ),
    ]


def branch_cases() -> List[Any]:
    """``delete-branch <branch>``: the branch as ONE encoded segment; a delete answers ``204`` without a body
    (conventions.md "Responses")."""
    return [
        form(
            case_id="delete-branch",
            argv=("delete-branch", SOURCE_BRANCH),
            exchanges=(
                Exchange(
                    method=METHOD_DELETE,
                    url=project_url(path=f"/repository/branches/{BRANCH_SEGMENT}"),
                    status=NO_CONTENT,
                ),
            ),
            printed={FIELD_BRANCH: SOURCE_BRANCH, FIELD_DELETED: True},
        )
    ]


def subcommand_cases() -> List[Any]:
    """One case per argv form and flag of design.md D6."""
    return [
        *issue_list_cases(),
        *issue_create_cases(),
        *issue_claim_cases(),
        *issue_assign_cases(),
        *issue_state_cases(),
        *pipeline_status_cases(),
        *pipeline_log_cases(),
        *label_cases(),
        *mr_cases(),
        *branch_cases(),
    ]


def claim_check_cases() -> List[Any]:
    """``issue claim-check``: 0 claimed by the label or an assignee, 0 not open, 3 open and unclaimed, 1 an API error,
    2 a usage error (design.md "Correctness Properties", UB-1)."""
    states = [
        ("label", issue_record(labels=(OTHER_LABEL, IN_PROGRESS)), True, EXIT_OK),
        ("assignee", issue_record(labels=(OTHER_LABEL,), assignees=(OTHER_USER,)), True, EXIT_OK),
        ("closed", issue_record(state=STATE_CLOSED), False, EXIT_OK),
        ("open-unclaimed", issue_record(labels=(OTHER_LABEL,)), False, EXIT_CLAIM_UNCLAIMED),
    ]
    cases = [
        form(
            case_id=case_id,
            argv=("issue", "claim-check", str(IID)),
            exchanges=(Exchange(method=METHOD_GET, url=issue_url(), answer=issue),),
            printed={FIELD_IID: IID, FIELD_STATE: issue[FIELD_STATE], FIELD_CLAIMED: claimed},
            exit_code=exit_code,
        )
        for case_id, issue, claimed, exit_code in states
    ]
    cases.append(
        form(
            case_id="not-found",
            argv=("issue", "claim-check", str(IID)),
            exchanges=(
                Exchange(method=METHOD_GET, url=issue_url(), status=404, answer={FIELD_MESSAGE: "404 Issue Not Found"}),
            ),
            printed=None,
            exit_code=EXIT_API_ERROR,
        )
    )
    cases.append(
        form(case_id="no-iid", argv=("issue", "claim-check"), exchanges=(), printed=None, exit_code=EXIT_USAGE)
    )
    return cases


def sent_body(*, request: Any) -> Any:
    """A recorded request's body: decoded JSON under ``Content-Type: application/json``, else its text."""
    if request.body is None:
        return None
    content_type = str(request.header(name=HEADER_CONTENT_TYPE) or "").split(";")[0].strip()
    text = request.body.decode(TEXT_ENCODING, errors="replace")
    return json.loads(text) if content_type == CONTENT_TYPE_JSON else text


def recorded(*, fake: Any) -> List[Tuple[str, str, Any]]:
    """``(method, URL, body)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url, sent_body(request=request)) for request in fake.requests]


def expected_requests(*, exchanges: Sequence[Exchange]) -> List[Tuple[str, str, Any]]:
    return [(exchange.method, exchange.url, exchange.sent) for exchange in exchanges]


def printed_value(*, out: str) -> Any:
    """Standard output as the JSON value it holds; ``None`` when nothing was printed, the text when it is not JSON."""
    if not out.strip():
        return None
    try:
        return json.loads(out)
    except ValueError:
        return out


def script_exchanges(*, fake: Any, exchanges: Sequence[Exchange]) -> None:
    for exchange in exchanges:
        fake.script(
            method=exchange.method,
            url=exchange.url,
            status=exchange.status,
            headers=exchange.headers,
            body=exchange.answer,
        )


def check_form(
    *, case: FormCase, config: Mapping[str, Any], project: Path, fake: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run ``case`` through ``main`` with ``config`` as config/gitlab.json; assert its exit code, its exact requests and
    its standard output, in that order. A ``TextOutput`` checks the text; any other ``printed`` is the JSON value."""
    write_json(path=project / CONFIG_DIR / CONFIG_FILE_NAME, content=config)
    script_exchanges(fake=fake, exchanges=case.exchanges)
    code = main_exit_code(wrapper=load_wrapper(), argv=case.argv)
    captured = capsys.readouterr()
    assert code == case.exit_code, (
        f"main({list(case.argv)}) exits {case.exit_code}, got {code}; stderr:\n{captured.err}"
    )
    assert recorded(fake=fake) == expected_requests(exchanges=case.exchanges), (
        "the recorded requests: method, URL with its query, JSON body (design.md D6)"
    )
    if isinstance(case.printed, TextOutput):
        case.printed.check(out=captured.out)
    else:
        assert printed_value(out=captured.out) == case.printed, f"standard output:\n{captured.out}"


@pytest.mark.parametrize("case", subcommand_cases())
def test_a_subcommand_form(case: FormCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]) -> None:
    check_form(
        case=case,
        config=config_with(changes=dict(case.config_changes)),
        project=project,
        fake=fake_gitlab,
        capsys=capsys,
    )


@pytest.mark.parametrize("case", claim_check_cases())
def test_claim_check_exit_codes(
    case: FormCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    check_form(case=case, config=TEMPLATE_CONFIG, project=project, fake=fake_gitlab, capsys=capsys)


class FakeClock:
    """The ``clock`` and ``sleep`` of a ``Transport``: the clock moves only by the pauses ``sleep`` records, so a wait
    ends at this clock's deadline and no real time passes. ``sleep`` takes ``seconds`` positionally, as
    ``time.sleep`` does."""

    def __init__(self, *, start: float) -> None:
        self.now = start
        self.sleeps: List[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float, /) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def refuse_real_sleep(seconds: float) -> None:
    raise AssertionError(f"time.sleep({seconds!r}): pipeline wait pauses through transport.sleep (design.md D6)")


class WaitCase(NamedTuple):
    """One verdict of ``pipeline wait``: ``via_main`` runs it through ``main``; ``pipeline_wait`` on the fake clock has
    its polls answered with ``polled``, pauses ``sleeps``, prints ``printed`` and returns ``exit_code``."""

    via_main: FormCase
    polled: Tuple[str, ...]
    sleeps: Tuple[float, ...]
    printed: Dict[str, Any]
    exit_code: int


def pipeline_wait_cases() -> List[Any]:
    """The skeleton's verdicts and summary line: 0 on ``success``, 10 on each status that ends without success, 11 at
    the deadline. Through ``main`` with ``--timeout-seconds 0`` no poll is sent and the summary names ``unknown``."""
    cases: List[Any] = []
    endings = [(STATUS_SUCCESS, EXIT_OK), *((status, EXIT_WAIT_NOT_SUCCESS) for status in NOT_SUCCESS_STATUSES)]
    for status, exit_code in endings:
        ended = pipeline_record(status=status)
        summary = {FIELD_ID: PIPELINE_ID, FIELD_STATUS: status, FIELD_WEB_URL: ended[FIELD_WEB_URL]}
        via_main = FormCase(
            argv=("pipeline", "wait", str(PIPELINE_ID), "--timeout-seconds", str(WAIT_TIMEOUT_SECONDS)),
            exchanges=(Exchange(method=METHOD_GET, url=pipeline_url(), answer=ended),),
            printed=summary,
            exit_code=exit_code,
        )
        case = WaitCase(
            via_main=via_main,
            polled=(STATUS_RUNNING, status),
            sleeps=(POLL_INTERVAL_SECONDS,),
            printed=summary,
            exit_code=exit_code,
        )
        cases.append(pytest.param(case, id=f"{status}-exits-{exit_code}"))
    timed_out = WaitCase(
        via_main=FormCase(
            argv=("pipeline", "wait", str(PIPELINE_ID), "--timeout-seconds", "0"),
            exchanges=(),
            printed={FIELD_ID: PIPELINE_ID, FIELD_STATUS: STATUS_UNKNOWN, FIELD_TIMEOUT_SECONDS: 0},
            exit_code=EXIT_WAIT_TIMEOUT,
        ),
        polled=(STATUS_RUNNING,) * POLLS_BEFORE_DEADLINE,
        sleeps=(POLL_INTERVAL_SECONDS,) * POLLS_BEFORE_DEADLINE,
        printed={FIELD_ID: PIPELINE_ID, FIELD_STATUS: STATUS_RUNNING, FIELD_TIMEOUT_SECONDS: DIRECT_TIMEOUT_SECONDS},
        exit_code=EXIT_WAIT_TIMEOUT,
    )
    cases.append(pytest.param(timed_out, id=f"timeout-exits-{EXIT_WAIT_TIMEOUT}"))
    return cases


def pipeline_commands() -> ModuleType:
    """``gitlab_api.commands.pipeline``, imported inside the test, so a module not written yet fails on an assertion."""
    assert PIPELINE_COMMANDS_FILE.is_file(), f"{PIPELINE_COMMANDS_FILE} is missing (design.md D6)"
    return importlib.import_module(name=PIPELINE_COMMANDS_MODULE)


@pytest.mark.parametrize("case", pipeline_wait_cases())
def test_pipeline_wait_exit_codes(
    case: WaitCase,
    project: Path,
    fake_gitlab: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(time, "sleep", refuse_real_sleep)
    check_form(case=case.via_main, config=TEMPLATE_CONFIG, project=project, fake=fake_gitlab, capsys=capsys)
    # The same verdict from pipeline_wait itself, polling through a Transport whose clock moves only when it sleeps.
    pipeline_wait = pipeline_commands().pipeline_wait
    fake_time = FakeClock(start=CLOCK_START_SECONDS)
    transport = importlib.import_module(name=TRANSPORT_MODULE).Transport(
        host=fixtures.HOST,
        token=TOKEN,
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=fake_time.sleep,
        clock=fake_time.clock,
    )
    for status in case.polled:
        fake_gitlab.script(method=METHOD_GET, url=pipeline_url(), body=pipeline_record(status=status))
    sent_before = len(fake_gitlab.requests)
    code = pipeline_wait(
        transport=transport,
        project=str(PROJECT_ID),
        pipeline_id=PIPELINE_ID,
        timeout_seconds=DIRECT_TIMEOUT_SECONDS,
        interval_seconds=POLL_INTERVAL_SECONDS,
    )
    captured = capsys.readouterr()
    assert code == case.exit_code, f"pipeline_wait returns {case.exit_code}, got {code}; stderr:\n{captured.err}"
    assert recorded(fake=fake_gitlab)[sent_before:] == [(METHOD_GET, pipeline_url(), None)] * len(case.polled), (
        "one GET of the pipeline per poll, polled while the transport's clock is before the deadline"
    )
    assert fake_time.sleeps == list(case.sleeps), "a poll that does not end the wait is followed by one transport.sleep"
    assert printed_value(out=captured.out) == case.printed, f"the skeleton's summary line:\n{captured.out}"


class StartRefusal(NamedTuple):
    """An ``issue start`` that must exit 1: the first read, the re-read after the claim (``None``: no claim may be
    sent) and the text the logged refusal names (the observed labels, design.md D6)."""

    before: Dict[str, Any]
    reread: Optional[Dict[str, Any]]
    observed: Tuple[str, ...]


@pytest.mark.parametrize(
    "refusal",
    [
        pytest.param(
            StartRefusal(before=issue_record(state=STATE_CLOSED), reread=None, observed=()),
            id="closed",
        ),
        pytest.param(
            StartRefusal(before=issue_record(assignees=(OTHER_USER,)), reread=None, observed=()),
            id="assigned-to-another-user",
        ),
        pytest.param(
            StartRefusal(
                before=issue_record(labels=(OTHER_LABEL,)),
                reread=issue_record(labels=(OTHER_LABEL,), assignees=(ME,)),
                observed=(OTHER_LABEL,),
            ),
            id="re-read-lacks-the-label",
        ),
        pytest.param(
            StartRefusal(
                before=issue_record(labels=(OTHER_LABEL,)),
                reread=issue_record(labels=(OTHER_LABEL, IN_PROGRESS)),
                observed=(OTHER_LABEL,),
            ),
            id="re-read-lacks-the-assignee",
        ),
    ],
)
def test_issue_start_refusals(
    refusal: StartRefusal,
    project: Path,
    fake_gitlab: Any,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    write_json(path=project / CONFIG_DIR / CONFIG_FILE_NAME, content=TEMPLATE_CONFIG)
    fake_gitlab.script(method=METHOD_GET, url=issue_url(), body=refusal.before)
    # Served whenever the handler resolves the token's user; not every refusal needs it.
    fake_gitlab.script(method=METHOD_GET, url=user_url(), body=ME)
    claim = {FIELD_ADD_LABELS: IN_PROGRESS, FIELD_ASSIGNEE_IDS: [ME[FIELD_ID]]}
    if refusal.reread is not None:
        fake_gitlab.script(method=METHOD_PUT, url=issue_url(), body=refusal.reread)
        fake_gitlab.script(method=METHOD_GET, url=issue_url(), body=refusal.reread)
    code = main_exit_code(wrapper=load_wrapper(), argv=["issue", "start", str(IID)])
    captured = capsys.readouterr()
    assert code == EXIT_API_ERROR, f"a refused or unconfirmed claim exits 1, got {code}; stderr:\n{captured.err}"
    puts = [
        (request.url, sent_body(request=request)) for request in fake_gitlab.requests if request.method == METHOD_PUT
    ]
    expected_puts = [] if refusal.reread is None else [(issue_url(), claim)]
    assert puts == expected_puts, "a closed or foreign-assigned issue gets no PUT; otherwise exactly ONE claim PUT"
    assert captured.out == "", "a refusal is a diagnostic on standard error, never a result on standard output"
    for text in refusal.observed:
        assert text in caplog.text, f"the logged refusal names the observed labels ({text!r}):\n{caplog.text}"


def test_issue_reopen_of_open_issue(project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]) -> None:
    opened = issue_record(labels=(OTHER_LABEL,))
    case = FormCase(
        argv=("issue", "reopen", str(IID)),
        exchanges=(Exchange(method=METHOD_GET, url=issue_url(), answer=opened),),
        printed=opened,
    )
    check_form(case=case, config=TEMPLATE_CONFIG, project=project, fake=fake_gitlab, capsys=capsys)


def template_config(*, removed: Sequence[str]) -> Dict[str, Any]:
    """templates/config/gitlab.json.template with its `PASTE_` placeholders filled and the ``removed`` keys left out."""
    template = json.loads(TEMPLATE_FILE.read_text(encoding=TEXT_ENCODING))
    assert FIELD_TOKEN_TYPE not in template, "the template leaves token_type out, so `private` is the default (UB-2)"
    filled = {
        key: TEMPLATE_FILLED[key] if str(value).startswith(PLACEHOLDER_MARKER) else value
        for key, value in template.items()
        if key not in removed
    }
    assert not any(str(value).startswith(PLACEHOLDER_MARKER) for value in filled.values()), filled
    return filled


@pytest.mark.parametrize(
    "removed",
    [pytest.param((), id="template-keys"), pytest.param((FIELD_IN_PROGRESS_LABEL,), id="in_progress_label-omitted")],
)
def test_template_config_sends_private_token(
    removed: Tuple[str, ...], project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    config = template_config(removed=removed)
    base = f"https://{config[FIELD_HOSTNAME]}/api/v4"
    exchanges, verified = start_exchanges(base=base, project=TEMPLATE_FILLED[FIELD_PROJECT_ID], label=IN_PROGRESS)
    case = FormCase(argv=("issue", "start", str(IID)), exchanges=exchanges, printed=verified)
    check_form(case=case, config=config, project=project, fake=fake_gitlab, capsys=capsys)
    for request in fake_gitlab.requests:
        sent_headers = (
            request.header(name=HEADER_PRIVATE_TOKEN),
            request.header(name=HEADER_AUTHORIZATION),
            request.header(name=HEADER_JOB_TOKEN),
        )
        assert sent_headers == (TOKEN, None, None), (
            f"{request.method} {request.url} carries the token as PRIVATE-TOKEN and no other credential header"
        )


@pytest.mark.parametrize(
    ("config", "exit_code"),
    [
        pytest.param(TEMPLATE_CONFIG, EXIT_OK, id="config-token"),
        pytest.param(config_with(removed=(FIELD_TOKEN,)), EXIT_API_ERROR, id="no-config-token"),
    ],
)
def test_environment_token_ignored(
    config: Dict[str, Any],
    exit_code: int,
    project: Path,
    fake_gitlab: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name, value in ENVIRONMENT_TOKENS.items():
        monkeypatch.setenv(name=name, value=value)
    shown = issue_record()
    exchanges = (Exchange(method=METHOD_GET, url=issue_url(), answer=shown),) if exit_code == EXIT_OK else ()
    case = FormCase(
        argv=("issue", "show", str(IID)),
        exchanges=exchanges,
        printed=shown if exit_code == EXIT_OK else None,
        exit_code=exit_code,
    )
    check_form(case=case, config=config, project=project, fake=fake_gitlab, capsys=capsys)
    for request in fake_gitlab.requests:
        assert request.header(name=HEADER_PRIVATE_TOKEN) == TOKEN, "the token comes from config/gitlab.json only"
        sent_text = " ".join(
            [request.url, *request.headers.values(), (request.body or b"").decode(TEXT_ENCODING, errors="replace")]
        )
        for name, value in ENVIRONMENT_TOKENS.items():
            assert value not in sent_text, f"the value of {name} reached {request.method} {request.url}"


def test_script_without_config_exits_1(tmp_path: Path) -> None:
    completed = run_child(args=[sys.executable, str(WRAPPER_FILE), "issue", "show", str(IID)], cwd=tmp_path)
    config_file = str(Path(CONFIG_DIR) / CONFIG_FILE_NAME)
    assert completed.returncode == EXIT_API_ERROR, (
        f"a missing {config_file} exits {EXIT_API_ERROR}, got {completed.returncode}; stderr:\n{completed.stderr}"
    )
    assert config_file in completed.stderr, f"the refusal names {config_file}:\n{completed.stderr}"
    assert TRACEBACK not in completed.stderr, f"a missing config is a refusal, not a crash:\n{completed.stderr}"
