"""Tests of the GitHub wrapper's operation call, ``call <operation-id>`` (``github_api/commands/call.py``; design D2 to
D4; AC-1.1 to AC-1.7, AC-2.1 to AC-2.3; issue #32 AC-6).

Installed from ``src/payload/test/test_github_api_call.py`` to ``test/test_github_api_call.py``, beside
``scripts/github_wrapper.py`` and ``scripts/github_api/``. Every row of ``CALL_CASES`` is a golden case whose argv is
``call …``. ``github_wrapper_fixtures.run_product_case`` (loaded by path) runs it through the product entry script's
``main(argv=...)`` in the fixture project (``origin`` ``o/r``) against the fake GitHub host, and judges its exit code,
its standard output exactly, its requests other than ``GET`` (none at all for a refusal) and that every request was
routed. Each test takes the rows of its criterion (``rows_of``) and adds that criterion's own oracle:

- AC-1.2: every request in order (method, path as sent, decoded query, JSON body) and, on each, the record's
  ``X-GitHub-Api-Version`` and ``Accept``; two rows run on copies of ``issues/get`` and ``issues/list-comments`` whose
  version and media type are not the defaults, set into ``github_api.families.issues.OPERATIONS`` for the test;
- AC-1.3: the body member's JSON value, type included (``true`` is not ``1``);
- AC-1.6: the bytes of a body that is not JSON, read with ``capsysbinary``;
- AC-1.7, AC-1.1, AC-2: the log records (``fx.assert_log`` on ``caplog.records``), which the entry script's
  ``__main__`` sends to standard error. A name the caller gave is matched as ``json.dumps`` renders it (design D4).

The rows of ``MALFORMED_ARGUMENTS`` (AC-1.2, AC-1.3, design D2 "Parsing") are not in ``CALL_CASES``: each gives one
``NAME=VALUE`` with no ``=``, an empty name, or ``-F`` text that is not JSON. ``run_reading_stderr`` runs and judges
such a row as ``run_product_case`` does and returns its standard error, which must be argparse's usage message naming
the option and the name as ``json.dumps`` renders it, and must not hold the value (Security Considerations
"Command-line input").

Issue #46's rows are named ``issue-46/<criterion>/…`` and are not in ``CALL_CASES``, whose rows ``rows_of`` keys by
issue #28's criterion ids, which #46's repeat; each runs with ``run_product_case`` as a row of ``CALL_CASES`` does:

- AC-3.1: ``call repos/update`` answered ``307`` with a relative ``Location`` and then ``200`` sends its ``PATCH``
  again, once, with the same body bytes, to the resolved ``Location``, and prints the second answer.
- AC-1.1: ``--input`` on ``issues/update``, a record whose body is JSON, is refused with a log record naming the ID
  and ``--input``; ``--input`` naming a file that does not exist is argparse's usage error for ``--input``, naming the
  path as ``json.dumps`` renders it (``run_reading_stderr``). Each exits 2 with no request.
- AC-1.3: ``-f`` or ``-F`` beside ``--input`` is refused with one log record naming ``--input``, ``-f/--raw-field`` and
  ``-F/--field``, exit 2 and no request.
- AC-2.1, AC-2.2, AC-4.2: ``call repos/upload-release-asset --input`` of bytes that are not UTF-8 sends one ``POST`` of
  exactly those bytes, as ``application/octet-stream``, to the upload origin with the query ``name`` and ``label``,
  prints the ``201`` answer, and no request carries the credential to another origin.
- AC-1.2, AC-4.3: ``call markdown/render-raw --input -``, standard input a text layer over Markdown bytes holding a CR
  LF line end and the byte 0xFF, sends one ``POST`` of exactly those bytes, as ``text/plain``, to
  ``https://api.github.com/markdown/raw``, and writes the HTML answer's bytes to standard output (``capsysbinary``).

The input files are written under ``tmp_path`` before the run, so the rows that name one are built inside their test.

The fork has no ``call``, so ``CASES`` holds none of these rows and the fork parity test never runs them. No test opens
a connection.

Run: ``python scripts/run_tests.py test/test_github_api_call.py`` (no network).
"""

from __future__ import annotations

import dataclasses
import importlib
import importlib.util
import io
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Sequence, Tuple

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

REGISTRY = "registry"
TRANSPORT = "transport"
ISSUES_FAMILY = f"{fx.PACKAGE}.families.issues"
ISSUES_FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / "issues.py"
ATTRIBUTE_OPERATIONS = "OPERATIONS"

# The criteria; every row's name starts with its criterion, then ``/``.
AC_1_1 = "AC-1.1"
AC_1_2 = "AC-1.2"
AC_1_3 = "AC-1.3"
AC_1_4 = "AC-1.4"
AC_1_5 = "AC-1.5"
AC_1_6 = "AC-1.6"
AC_1_7 = "AC-1.7"
AC_2_1 = "AC-2.1"
AC_2_2 = "AC-2.2"
AC_2_3 = "AC-2.3"
NAME_SEPARATOR = "/"

CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "--raw-field"
OPTION_FIELD = "--field"
OPTION_RAW_FIELD_SHORT = "-f"
OPTION_FIELD_SHORT = "-F"
OPERATION_ID_INDEX = 1  # argv is ``call <operation-id> …``

OP_ISSUES_GET = "issues/get"
OP_ISSUES_LIST_COMMENTS = "issues/list-comments"
OP_ISSUES_LIST_FOR_REPO = "issues/list-for-repo"
OP_ISSUES_UPDATE = "issues/update"
OP_ISSUES_REMOVE_LABEL = "issues/remove-label"
OP_ISSUES_CREATE = "issues/create"
OP_PULLS_GET = "pulls/get"
OP_PULLS_MERGE = "pulls/merge"
OP_PULLS_MERGE_ASYNC = "pulls/merge-async"  # gated to ``merge-pr``: its body can merge directly (issue #32 AC-6)
OP_PULLS_UPDATE_BRANCH = "pulls/update-branch"  # on the PENDING of ``families/pulls.py``: indexed, no record
OP_NOT_IN_THE_INDEX = "issues/levitate"  # in no row of ``operations-index.md``
OP_GET_WORKFLOW_RUN = "actions/get-workflow-run"
OP_LIST_WORKFLOW_RUNS_FOR_REPO = "actions/list-workflow-runs-for-repo"
OP_DOWNLOAD_WORKFLOW_RUN_LOGS = "actions/download-workflow-run-logs"
OP_DELETE_REF = "git/delete-ref"

SUBCOMMAND_MERGE_PR = "merge-pr"
SUBCOMMAND_CREATE_ISSUE = "create-issue"
#: The end of the refusal of a gated record its subcommand sends itself (issue #32 DL-007): ``merge-pr`` sends
#: ``pulls/merge`` and ``create-issue`` sends ``issues/create``, but ``merge-pr`` never sends ``pulls/merge-async``, so
#: that refusal names ``merge-pr`` without this text.
SENDS_IT = "which sends it"

KIND_PATH = "path"
KIND_QUERY = "query"
KIND_BODY = "body"

PARAM_OWNER = "owner"
PARAM_REPO = "repo"
PARAM_ISSUE_NUMBER = "issue_number"
UNDOCUMENTED_PATH_NAME = "number"
UNDOCUMENTED_QUERY_NAME = "sort"
UNDOCUMENTED_BODY_NAME = "color"
#: The documented names of the records the refusal rows call (``families/issues.py``): the path parameters of both
#: ``issues/get`` and ``issues/update``, which document no query parameter, and the body parameters of
#: ``issues/update``, as ``rest/issues.md`` documents them.
ISSUES_PATH_PARAMETERS = (PARAM_OWNER, PARAM_REPO, PARAM_ISSUE_NUMBER)
ISSUES_UPDATE_BODY_PARAMETERS = (
    "title",
    "body",
    "assignee",
    "state",
    "state_reason",
    "duplicate_issue_id",
    "milestone",
    "labels",
    "assignees",
    "issue_field_values",
    "type",
)

HEADER_API_VERSION = "x-github-api-version"
HEADER_ACCEPT = "accept"
ACCEPT_FULL_JSON = "application/vnd.github.full+json"
#: The two records AC-1.2 runs on copies whose ``api_version`` is ``API_VERSION_NEXT`` and ``accept``
#: ``ACCEPT_FULL_JSON``: one that does not page and one that pages by ``link``.
COPIED_OPERATIONS = frozenset({OP_ISSUES_GET, OP_ISSUES_LIST_COMMENTS})
#: ``run_product_case`` reads standard error along with standard output; no row of ``CALL_CASES`` withholds a value,
#: so ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""

OTHER_OWNER = "x"
OTHER_REPOSITORY = "y"
OTHER_ISSUE_5_PATH = f"/repos/{OTHER_OWNER}/{OTHER_REPOSITORY}/issues/5"
COMMENTS_OF_5_PATH = f"{fx.ISSUE_5_PATH}/comments"
LABEL_WITH_A_SLASH_PATH = f"{fx.ISSUE_5_PATH}/labels/area%2Fui"
LABEL_WITH_A_SPACE_PATH = f"{fx.ISSUE_5_PATH}/labels/help%20wanted"
RUN_7_PATH = f"{fx.RUNS_PATH}/7"
TOPIC_REF_PATH = f"{fx.REPOSITORY_PATH}/git/refs/heads/topic"
QUERY_EXCLUDE_PULL_REQUESTS = "exclude_pull_requests"
QUERY_ARRAY_STATE = f"{fx.QUERY_STATE}[]"  # ``conventions.md`` "Query strings": an array parameter's spelling
FIELD_TITLE = "title"
LABEL_BUG = "bug"
LABEL_UI = "ui"
UPDATED_TITLE = "T"

# Issue #32 AC-6: a value for each body parameter ``rest/pulls.md`` "Merge a pull request asynchronously" documents,
# the strings with ``-f`` and the boolean with ``-F``. Every name is documented, so only the gate can refuse the call:
# an ungated record would send its ``PUT``, which no route answers.
FIELD_COMMIT_TITLE = "commit_title"
FIELD_MERGE_ACTION = "merge_action"
FIELD_BYPASS_RULES = "bypass_rules"
MERGE_COMMIT_MESSAGE = "Merge the wrapper rewrite"
MERGE_METHOD_SQUASH = "squash"
MERGE_ACTION_DIRECT_MERGE = "direct_merge"
MERGE_ASYNC_TEXT_MEMBERS: Tuple[Tuple[str, str], ...] = (
    (FIELD_COMMIT_TITLE, UPDATED_TITLE),
    (fx.FIELD_COMMIT_MESSAGE, MERGE_COMMIT_MESSAGE),
    (fx.FIELD_SHA, fx.HEAD_SHA),
    (fx.FIELD_MERGE_METHOD, MERGE_METHOD_SQUASH),
    (FIELD_MERGE_ACTION, MERGE_ACTION_DIRECT_MERGE),
)
MERGE_ASYNC_JSON_MEMBERS: Tuple[Tuple[str, str], ...] = ((FIELD_BYPASS_RULES, json.dumps(obj=True)),)

RUN_7 = fx.run_entry(run_id=7, outcome=(fx.RUN_COMPLETED, fx.CONCLUSION_SUCCESS))
REMAINING_LABELS = fx.label_list(names=(fx.LABEL_ENHANCEMENT,))
UPDATED_ISSUE_5 = fx.issue_entry(number=5, title=UPDATED_TITLE, labels=(LABEL_BUG,))
#: One more comment than GitHub's default page holds, so the list arrives in two pages.
COMMENTS_OVER_TWO_PAGES = fx.COMMENTS_ON_5[: fx.DEFAULT_PER_PAGE + 1]
SECOND_DEFAULT_PAGE = {fx.QUERY_PER_PAGE: [str(fx.DEFAULT_PER_PAGE)], fx.QUERY_PAGE: ["2"]}

# AC-1.4: a bare list whose next page GitHub names on another path, and a list wrapped under its item key.
PAGE_SIZE = 2
NEXT_ISSUES_PAGE_URL = f"{fx.API_ORIGIN}/repositories/1/issues?per_page={PAGE_SIZE}&page=2"
FIRST_ISSUES_PAGE = list(fx.LISTED_ENTRIES[:PAGE_SIZE])
LAST_ISSUES_PAGE = list(fx.LISTED_ENTRIES[PAGE_SIZE:])
LISTED_RUNS = fx.RUN_HISTORY[: PAGE_SIZE + 1]

# AC-1.6: bodies that are not a JSON document.
DIFF_BODY = (
    "diff --git a/README.md b/README.md\n"
    "index 1c2a3b4..5d6e7f8 100644\n"
    "--- a/README.md\n"
    "+++ b/README.md\n"
    "@@ -1 +1 @@\n"
    "-Wrapper\n"
    "+Wrapper ✓\n"
).encode(encoding="utf-8")
HTML_BODY = b'<!DOCTYPE html>\n<html lang="en"><body><h1>Wrapper rewrite</h1></body></html>\n'
NOT_UTF_8_BODY = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xd8"  # 0x89 starts no UTF-8 sequence
LOG_ARCHIVE = fx.log_archive(entries=fx.LOG_ENTRIES)
MEDIA_TYPE_DIFF = "application/vnd.github.diff; charset=utf-8"
MEDIA_TYPE_HTML = "text/html; charset=utf-8"
MEDIA_TYPE_OCTET_STREAM = "application/octet-stream"

# AC-1.3: one JSON value of each kind, given with ``--field``.
JSON_VALUES: Tuple[Tuple[str, Any], ...] = (
    ("string", "Wrapper rewrite"),
    ("number", 42),
    ("boolean", True),
    ("array", [LABEL_BUG, LABEL_UI]),
    ("object", {"level": 2, "tags": ["a", None]}),
    ("null", None),
)

# AC-1.7: GitHub's 404, logged as the error's message and then ``Details:`` with its body.
API_ERROR_MESSAGE = fx.LogExpectation(refusal=(re.escape(fx.ISSUE_6_PATH), re.escape("HTTP 404")), withheld=())
API_ERROR_DETAILS = fx.LogExpectation(
    refusal=(r"^Details: ", re.escape(f'"{fx.FIELD_MESSAGE}": "{fx.NOT_FOUND.body[fx.FIELD_MESSAGE]}"')),
    withheld=(),
)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def named(*, name: str) -> str:
    """A pattern for ``name`` as a refusal renders a name: with ``json.dumps`` (design D4)."""
    return re.escape(json.dumps(obj=name))


def named_each(*, names: Sequence[str]) -> Tuple[str, ...]:
    """One ``named`` pattern for each of ``names``."""
    return tuple(named(name=name) for name in names)


def lacking(*, text: str) -> str:
    """A pattern that matches only a message holding no ``text`` anywhere in it."""
    return rf"\A(?![\s\S]*{re.escape(text)})"


def named_with_kind(*, kind: str, name: str) -> str:
    """A pattern for the undocumented ``name`` in the list that follows ``<kind> parameter`` (or ``parameters``), as
    ``registry._check_names`` writes one (``documents no query parameter ["sort"]``); a name in another kind's list,
    or in a list of documented names, does not match."""
    return rf'\b{kind} parameters?[^"\[\]\n;]*\[?(?:"[^"]*",\s*)*{named(name=name)}'


def _refusal(*, criterion: str, slug: str, argv: Tuple[str, ...], patterns: Tuple[str, ...]) -> Any:
    """A refusal row: exit 2, nothing on standard output, no request, and one log record matching every pattern."""
    return fx.GoldenCase(
        name=f"{criterion}/exit-2/{slug}",
        argv=argv,
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(refusal=patterns, withheld=()),
    )


def _get(*, url: str, reply: Any, query: Any = None) -> Any:
    """A static route answering ``GET`` on ``url`` (and ``query``) with ``reply``."""
    return fx.StaticRouteSpec(method=fx.METHOD_GET, url=url, replies=(reply,), query=dict(query or {}))


@dataclass(frozen=True)
class SentRequest:
    """A request as AC-1.2's oracle reads it: its method, its path as sent, its decoded query, and its JSON body
    (``None``: no body)."""

    method: str
    path: str
    query: Dict[str, List[str]] = field(default_factory=dict)
    body: Any = None

    @classmethod
    def of(cls, *, request: Any) -> SentRequest:
        """``request``, a request the fake host recorded, in the oracle's form."""
        return cls(method=request.method, path=request.path, query=request.query, body=request.json())


@dataclass(frozen=True)
class SentCall:
    """An AC-1.2 row: its golden case, every request it sends in order, and whether it runs on the copies of
    ``COPIED_OPERATIONS``."""

    case: Any
    requests: Tuple[SentRequest, ...]
    on_copies: bool = False


def sent_call_name(sent: SentCall) -> str:
    """The test id of an AC-1.2 row."""
    return str(fx.case_name(case=sent.case))


def _issue_5_read(*, name: str, on_copies: bool = False) -> SentCall:
    """``call issues/get --path issue_number=5``: one ``GET`` of issue 5, with no body."""
    return SentCall(
        case=fx.GoldenCase(
            name=f"{AC_1_2}/exit-0/{name}",
            argv=(CALL, OP_ISSUES_GET, OPTION_PATH, "issue_number=5"),
            stdout=fx.printed_json(value=fx.ISSUE_5),
            exit_code=fx.EXIT_OK,
            routes=(_get(url=fx.ISSUE_5_PATH, reply=fx.Reply(body=fx.ISSUE_5)),),
        ),
        requests=(SentRequest(method=fx.METHOD_GET, path=fx.ISSUE_5_PATH),),
        on_copies=on_copies,
    )


def _label_removal(*, name: str, label: str, path: str) -> SentCall:
    """``call issues/remove-label`` of ``label`` from issue 5: one ``DELETE`` of ``path``, the label encoded."""
    return SentCall(
        case=fx.GoldenCase(
            name=f"{AC_1_2}/exit-0/{name}",
            argv=(CALL, OP_ISSUES_REMOVE_LABEL, OPTION_PATH, "issue_number=5", OPTION_PATH, f"name={label}"),
            stdout=fx.printed_json(value=REMAINING_LABELS),
            exit_code=fx.EXIT_OK,
            routes=(fx.StaticRouteSpec(method=fx.METHOD_DELETE, url=path, replies=(fx.Reply(body=REMAINING_LABELS),)),),
            writes=(fx.NonGetRequest(method=fx.METHOD_DELETE, path=path),),
        ),
        requests=(SentRequest(method=fx.METHOD_DELETE, path=path),),
    )


def _issue_list(*, name: str, argv: Tuple[str, ...], query: Dict[str, Any], sent: Dict[str, List[str]]) -> SentCall:
    """``call issues/list-for-repo`` with ``argv``'s query: one page of the open issues, requested with ``sent``."""
    return SentCall(
        case=fx.GoldenCase(
            name=f"{AC_1_2}/exit-0/{name}",
            argv=argv,
            stdout=fx.printed_json(value=list(fx.LISTED_ENTRIES)),
            exit_code=fx.EXIT_OK,
            routes=(fx.ListRouteSpec(url=fx.ISSUES_PATH, items=fx.LISTED_ENTRIES, query=query),),
        ),
        requests=(SentRequest(method=fx.METHOD_GET, path=fx.ISSUES_PATH, query=sent),),
    )


def _sent_calls() -> Tuple[SentCall, ...]:
    """AC-1.2's rows (design § Correctness Properties)."""
    update_body = {FIELD_TITLE: UPDATED_TITLE, fx.FIELD_LABELS: [LABEL_BUG]}
    return (
        _issue_5_read(name="path-parameter-and-the-origin-repository"),
        SentCall(
            case=fx.GoldenCase(
                name=f"{AC_1_2}/exit-0/owner-and-repo-given",
                argv=(
                    CALL,
                    OP_ISSUES_GET,
                    OPTION_PATH,
                    "issue_number=5",
                    OPTION_PATH,
                    f"owner={OTHER_OWNER}",
                    OPTION_PATH,
                    f"repo={OTHER_REPOSITORY}",
                ),
                stdout=fx.printed_json(value=fx.ISSUE_5),
                exit_code=fx.EXIT_OK,
                routes=(_get(url=OTHER_ISSUE_5_PATH, reply=fx.Reply(body=fx.ISSUE_5)),),
            ),
            requests=(SentRequest(method=fx.METHOD_GET, path=OTHER_ISSUE_5_PATH),),
        ),
        _label_removal(name="path-value-with-a-slash", label="area/ui", path=LABEL_WITH_A_SLASH_PATH),
        _label_removal(name="path-value-with-a-space", label="help wanted", path=LABEL_WITH_A_SPACE_PATH),
        SentCall(
            case=fx.GoldenCase(
                name=f"{AC_1_2}/exit-0/query-parameter",
                argv=(
                    CALL,
                    OP_GET_WORKFLOW_RUN,
                    OPTION_PATH,
                    "run_id=7",
                    OPTION_QUERY,
                    f"{QUERY_EXCLUDE_PULL_REQUESTS}=true",
                ),
                stdout=fx.printed_json(value=RUN_7),
                exit_code=fx.EXIT_OK,
                routes=(_get(url=RUN_7_PATH, reply=fx.Reply(body=RUN_7), query={QUERY_EXCLUDE_PULL_REQUESTS: "true"}),),
            ),
            requests=(
                SentRequest(method=fx.METHOD_GET, path=RUN_7_PATH, query={QUERY_EXCLUDE_PULL_REQUESTS: ["true"]}),
            ),
        ),
        SentCall(
            case=fx.GoldenCase(
                name=f"{AC_1_2}/exit-0/string-and-json-body-members",
                argv=(
                    CALL,
                    OP_ISSUES_UPDATE,
                    OPTION_PATH,
                    "issue_number=5",
                    OPTION_RAW_FIELD,
                    f"{FIELD_TITLE}={UPDATED_TITLE}",
                    OPTION_FIELD,
                    f'{fx.FIELD_LABELS}=["{LABEL_BUG}"]',
                ),
                stdout=fx.printed_json(value=UPDATED_ISSUE_5),
                exit_code=fx.EXIT_OK,
                routes=(
                    fx.StaticRouteSpec(
                        method=fx.METHOD_PATCH, url=fx.ISSUE_5_PATH, replies=(fx.Reply(body=UPDATED_ISSUE_5),)
                    ),
                ),
                writes=(fx.NonGetRequest(method=fx.METHOD_PATCH, path=fx.ISSUE_5_PATH, body=update_body),),
            ),
            requests=(SentRequest(method=fx.METHOD_PATCH, path=fx.ISSUE_5_PATH, body=update_body),),
        ),
        _issue_list(
            name="query-name-given-twice",
            argv=(
                CALL,
                OP_ISSUES_LIST_FOR_REPO,
                OPTION_QUERY,
                f"{fx.QUERY_LABELS}={LABEL_BUG}",
                OPTION_QUERY,
                f"{fx.QUERY_LABELS}={LABEL_UI}",
            ),
            query={fx.QUERY_LABELS: (LABEL_BUG, LABEL_UI)},
            sent={fx.QUERY_LABELS: [LABEL_BUG, LABEL_UI]},
        ),
        _issue_list(
            name="array-query-name-sent-as-written",
            argv=(CALL, OP_ISSUES_LIST_FOR_REPO, OPTION_QUERY, f"{QUERY_ARRAY_STATE}={fx.STATE_OPEN}"),
            query={QUERY_ARRAY_STATE: fx.STATE_OPEN},
            sent={QUERY_ARRAY_STATE: [fx.STATE_OPEN]},
        ),
        _issue_5_read(name="the-record-version-and-media-type", on_copies=True),
        SentCall(
            case=fx.GoldenCase(
                name=f"{AC_1_2}/exit-0/the-record-version-and-media-type-on-every-page",
                argv=(CALL, OP_ISSUES_LIST_COMMENTS, OPTION_PATH, "issue_number=5"),
                stdout=fx.printed_json(value=list(COMMENTS_OVER_TWO_PAGES)),
                exit_code=fx.EXIT_OK,
                routes=(fx.ListRouteSpec(url=COMMENTS_OF_5_PATH, items=COMMENTS_OVER_TWO_PAGES),),
            ),
            requests=(
                SentRequest(method=fx.METHOD_GET, path=COMMENTS_OF_5_PATH),
                SentRequest(method=fx.METHOD_GET, path=COMMENTS_OF_5_PATH, query=SECOND_DEFAULT_PAGE),
            ),
            on_copies=True,
        ),
    )


SENT_CALLS = _sent_calls()


def _member_arguments(*, option: str, members: Sequence[Tuple[str, str]]) -> Tuple[str, ...]:
    """``option NAME=VALUE`` for each ``(NAME, VALUE)`` of ``members``, in order."""
    return tuple(argument for name, value in members for argument in (option, f"{name}={value}"))


def _gated_cases() -> Tuple[Any, ...]:
    """AC-1.1: the records a gated compatibility subcommand sends are refused, naming that subcommand and saying that
    it sends them; issue #32 AC-6 adds ``pulls/merge-async``, called with a value for each documented body parameter,
    whose refusal names ``merge-pr`` and does not say that it sends it (DL-007)."""
    merge_async_body = (
        *_member_arguments(option=OPTION_RAW_FIELD, members=MERGE_ASYNC_TEXT_MEMBERS),
        *_member_arguments(option=OPTION_FIELD, members=MERGE_ASYNC_JSON_MEMBERS),
    )
    return (
        _refusal(
            criterion=AC_1_1,
            slug="pulls-merge-is-merge-pr",
            argv=(CALL, OP_PULLS_MERGE, OPTION_PATH, "pull_number=1"),
            patterns=(named(name=OP_PULLS_MERGE), re.escape(SUBCOMMAND_MERGE_PR), re.escape(SENDS_IT)),
        ),
        _refusal(
            criterion=AC_1_1,
            slug="pulls-merge-async-is-merge-pr",
            argv=(CALL, OP_PULLS_MERGE_ASYNC, OPTION_PATH, "pull_number=1", *merge_async_body),
            patterns=(named(name=OP_PULLS_MERGE_ASYNC), re.escape(SUBCOMMAND_MERGE_PR), lacking(text=SENDS_IT)),
        ),
        _refusal(
            criterion=AC_1_1,
            slug="issues-create-is-create-issue",
            argv=(CALL, OP_ISSUES_CREATE, OPTION_RAW_FIELD, f"{FIELD_TITLE}=T"),
            patterns=(named(name=OP_ISSUES_CREATE), re.escape(SUBCOMMAND_CREATE_ISSUE), re.escape(SENDS_IT)),
        ),
    )


def _body_member_cases() -> Tuple[Any, ...]:
    """AC-1.3: ``--field title=<JSON>`` on ``issues/update`` for one value of each JSON kind."""
    return tuple(
        fx.GoldenCase(
            name=f"{AC_1_3}/exit-0/{kind}",
            argv=(
                CALL,
                OP_ISSUES_UPDATE,
                OPTION_PATH,
                "issue_number=5",
                OPTION_FIELD,
                f"{FIELD_TITLE}={json.dumps(obj=value)}",
            ),
            stdout=fx.printed_json(value=UPDATED_ISSUE_5),
            exit_code=fx.EXIT_OK,
            routes=(
                fx.StaticRouteSpec(
                    method=fx.METHOD_PATCH, url=fx.ISSUE_5_PATH, replies=(fx.Reply(body=UPDATED_ISSUE_5),)
                ),
            ),
            writes=(fx.NonGetRequest(method=fx.METHOD_PATCH, path=fx.ISSUE_5_PATH, body={FIELD_TITLE: value}),),
        )
        for kind, value in JSON_VALUES
    )


def _list_cases() -> Tuple[Any, ...]:
    """AC-1.4: every item of every page, in page order, as one JSON array."""
    first_page = fx.Reply(body=FIRST_ISSUES_PAGE, headers={fx.HEADER_LINK: f'<{NEXT_ISSUES_PAGE_URL}>; rel="next"'})
    return (
        fx.GoldenCase(
            name=f"{AC_1_4}/exit-0/bare-list-by-the-next-target-as-given",
            argv=(CALL, OP_ISSUES_LIST_FOR_REPO, OPTION_QUERY, f"{fx.QUERY_PER_PAGE}={PAGE_SIZE}"),
            stdout=fx.printed_json(value=list(fx.LISTED_ENTRIES)),
            exit_code=fx.EXIT_OK,
            routes=(
                _get(url=fx.ISSUES_PATH, reply=first_page, query={fx.QUERY_PER_PAGE: PAGE_SIZE}),
                _get(url=NEXT_ISSUES_PAGE_URL, reply=fx.Reply(body=LAST_ISSUES_PAGE)),
            ),
        ),
        fx.GoldenCase(
            name=f"{AC_1_4}/exit-0/items-under-the-item-key",
            argv=(CALL, OP_LIST_WORKFLOW_RUNS_FOR_REPO, OPTION_QUERY, f"{fx.QUERY_PER_PAGE}={PAGE_SIZE}"),
            stdout=fx.printed_json(value=list(LISTED_RUNS)),
            exit_code=fx.EXIT_OK,
            routes=(fx.ListRouteSpec(url=fx.RUNS_PATH, items=LISTED_RUNS, item_key=fx.FIELD_WORKFLOW_RUNS),),
        ),
    )


def _json_or_empty_cases() -> Tuple[Any, ...]:
    """AC-1.5: a JSON body prints as indented JSON, an empty one as nothing."""
    return (
        fx.GoldenCase(
            name=f"{AC_1_5}/exit-0/json-body",
            argv=(CALL, OP_ISSUES_GET, OPTION_PATH, "issue_number=5"),
            stdout=fx.printed_json(value=fx.ISSUE_5),
            exit_code=fx.EXIT_OK,
            routes=(_get(url=fx.ISSUE_5_PATH, reply=fx.Reply(body=fx.ISSUE_5)),),
        ),
        fx.GoldenCase(
            name=f"{AC_1_5}/exit-0/empty-body",
            argv=(CALL, OP_DELETE_REF, OPTION_PATH, "ref=heads/topic"),
            stdout="",
            exit_code=fx.EXIT_OK,
            routes=(
                fx.StaticRouteSpec(
                    method=fx.METHOD_DELETE, url=TOPIC_REF_PATH, replies=(fx.Reply(status=fx.NO_CONTENT),)
                ),
            ),
            writes=(fx.NonGetRequest(method=fx.METHOD_DELETE, path=TOPIC_REF_PATH),),
        ),
    )


def _not_json_cases() -> Tuple[Any, ...]:
    """AC-1.6: a body that is not a JSON document reaches standard output as its bytes, unchanged."""

    def raw(*, media_type: str, body: bytes) -> Any:
        return fx.Reply(body=body, headers={fx.HEADER_CONTENT_TYPE: media_type})

    return (
        fx.GoldenCase(
            name=f"{AC_1_6}/exit-0/archive-after-a-redirect-to-storage",
            argv=(CALL, OP_DOWNLOAD_WORKFLOW_RUN_LOGS, OPTION_PATH, f"run_id={fx.RUN_ID}"),
            stdout=fx.binary_stdout(data=LOG_ARCHIVE),
            exit_code=fx.EXIT_OK,
            routes=fx.LOGS_ON_STORAGE,
        ),
        fx.GoldenCase(
            name=f"{AC_1_6}/exit-0/diff",
            argv=(CALL, OP_PULLS_GET, OPTION_PATH, "pull_number=77"),
            stdout=fx.binary_stdout(data=DIFF_BODY),
            exit_code=fx.EXIT_OK,
            routes=(_get(url=fx.PULL_77_PATH, reply=raw(media_type=MEDIA_TYPE_DIFF, body=DIFF_BODY)),),
        ),
        fx.GoldenCase(
            name=f"{AC_1_6}/exit-0/html",
            argv=(CALL, OP_ISSUES_GET, OPTION_PATH, "issue_number=5"),
            stdout=fx.binary_stdout(data=HTML_BODY),
            exit_code=fx.EXIT_OK,
            routes=(_get(url=fx.ISSUE_5_PATH, reply=raw(media_type=MEDIA_TYPE_HTML, body=HTML_BODY)),),
        ),
        fx.GoldenCase(
            name=f"{AC_1_6}/exit-0/bytes-that-are-not-utf-8",
            argv=(CALL, OP_PULLS_GET, OPTION_PATH, "pull_number=78"),
            stdout=fx.binary_stdout(data=NOT_UTF_8_BODY),
            exit_code=fx.EXIT_OK,
            routes=(_get(url=fx.PULL_78_PATH, reply=raw(media_type=MEDIA_TYPE_OCTET_STREAM, body=NOT_UTF_8_BODY)),),
        ),
    )


def _api_error_cases() -> Tuple[Any, ...]:
    """AC-1.7: GitHub's 404 exits 1, standard output empty; ``log`` is the message's record (the details' is
    ``API_ERROR_DETAILS``)."""
    return (
        fx.GoldenCase(
            name=f"{AC_1_7}/exit-1/not-found",
            argv=(CALL, OP_ISSUES_GET, OPTION_PATH, "issue_number=6"),
            stdout="",
            exit_code=fx.EXIT_API_ERROR,
            routes=(_get(url=fx.ISSUE_6_PATH, reply=fx.NOT_FOUND),),
            log=API_ERROR_MESSAGE,
        ),
    )


def _unknown_cases() -> Tuple[Any, ...]:
    """AC-2.1: an ID no record declares, pending or not in the index, is refused, naming the ID."""
    return (
        _refusal(
            criterion=AC_2_1,
            slug="pending-id",
            argv=(CALL, OP_PULLS_UPDATE_BRANCH),
            patterns=(named(name=OP_PULLS_UPDATE_BRANCH),),
        ),
        _refusal(
            criterion=AC_2_1,
            slug="id-not-in-the-index",
            argv=(CALL, OP_NOT_IN_THE_INDEX),
            patterns=(named(name=OP_NOT_IN_THE_INDEX),),
        ),
    )


def _undocumented_cases() -> Tuple[Any, ...]:
    """AC-2.2: an undocumented path, query or body name is refused in one record naming each such name with its kind,
    then the record's documented path, query and body parameters."""
    path_name = (OPTION_PATH, f"{UNDOCUMENTED_PATH_NAME}=5")
    query_name = (OPTION_QUERY, f"{UNDOCUMENTED_QUERY_NAME}=created")
    body_name = (OPTION_RAW_FIELD, f"{UNDOCUMENTED_BODY_NAME}=red")
    issue_5 = (OPTION_PATH, "issue_number=5")
    path_pattern = named_with_kind(kind=KIND_PATH, name=UNDOCUMENTED_PATH_NAME)
    query_pattern = named_with_kind(kind=KIND_QUERY, name=UNDOCUMENTED_QUERY_NAME)
    body_pattern = named_with_kind(kind=KIND_BODY, name=UNDOCUMENTED_BODY_NAME)
    get_documented = named_each(names=ISSUES_PATH_PARAMETERS)
    update_documented = named_each(names=(*ISSUES_PATH_PARAMETERS, *ISSUES_UPDATE_BODY_PARAMETERS))
    return (
        _refusal(
            criterion=AC_2_2,
            slug="path-name",
            argv=(CALL, OP_ISSUES_GET, *issue_5, *path_name),
            patterns=(path_pattern, *get_documented),
        ),
        _refusal(
            criterion=AC_2_2,
            slug="query-name",
            argv=(CALL, OP_ISSUES_GET, *issue_5, *query_name),
            patterns=(query_pattern, *get_documented),
        ),
        _refusal(
            criterion=AC_2_2,
            slug="body-name",
            argv=(CALL, OP_ISSUES_UPDATE, *issue_5, *body_name),
            patterns=(body_pattern, *update_documented),
        ),
        _refusal(
            criterion=AC_2_2,
            slug="one-of-each-kind-in-one-message",
            argv=(CALL, OP_ISSUES_UPDATE, *issue_5, *path_name, *query_name, *body_name),
            patterns=(path_pattern, query_pattern, body_pattern, *update_documented),
        ),
    )


def _missing_path_cases() -> Tuple[Any, ...]:
    """AC-2.3: a path parameter left without a value is refused, naming it (``issue_number``, the one ``owner`` and
    ``repo`` do not default) and the record's path parameters."""
    return (
        _refusal(
            criterion=AC_2_3,
            slug="path-parameter-without-a-value",
            argv=(CALL, OP_ISSUES_GET),
            patterns=named_each(names=ISSUES_PATH_PARAMETERS),
        ),
    )


#: Every row of this suite: a golden case whose argv is ``call …``, run with ``fx.run_product_case``.
CALL_CASES: Tuple[Any, ...] = (
    *_gated_cases(),
    *(sent.case for sent in SENT_CALLS),
    *_body_member_cases(),
    *_list_cases(),
    *_json_or_empty_cases(),
    *_not_json_cases(),
    *_api_error_cases(),
    *_unknown_cases(),
    *_undocumented_cases(),
    *_missing_path_cases(),
)


def rows_of(*, criterion: str) -> Tuple[Any, ...]:
    """The rows of ``CALL_CASES`` whose name starts with ``criterion``; none is an error at collection, never an empty
    parameter set that pytest would skip."""
    rows = tuple(case for case in CALL_CASES if case.name.split(NAME_SEPARATOR, 1)[0] == criterion)
    assert rows, f"CALL_CASES holds no row of {criterion}"
    return rows


# D2 "Parsing" (AC-1.2, AC-1.3): one malformed ``NAME=VALUE`` on ``issues/update``, whose path is otherwise complete.
USAGE_PREFIX = "usage: "
#: The option as argparse's usage error names it: its option strings joined with ``/``.
NAMED_RAW_FIELD = f"{OPTION_RAW_FIELD_SHORT}/{OPTION_RAW_FIELD}"
NAMED_FIELD = f"{OPTION_FIELD_SHORT}/{OPTION_FIELD}"
NAME_WITHOUT_A_VALUE = "noequals"
EMPTY_NAME = ""
EMPTY_NAME_QUERY_VALUE = "created"
EMPTY_NAME_MEMBER_VALUE = "secret"
#: ``-F`` text that ``json.loads`` refuses (``call.py`` refuses its constants), each with its slug.
NOT_JSON_TEXTS: Tuple[Tuple[str, str], ...] = (
    ("nan", "NaN"),
    ("infinity", "Infinity"),
    ("negative-infinity", "-Infinity"),
    ("not-json", "nope"),
)


@dataclass(frozen=True)
class MalformedArgument:
    """A row of ``MALFORMED_ARGUMENTS``: its golden case (exit 2, nothing on standard output, no request), the option
    as argparse's usage error names it, the name of the malformed argument (the text before its first ``=``, all of
    it when there is none), and each value text standard error must not hold."""

    case: Any
    option: str
    name: str
    withheld: Tuple[str, ...]


def malformed_argument_name(malformed: MalformedArgument) -> str:
    """The test id of a ``MALFORMED_ARGUMENTS`` row."""
    return str(fx.case_name(case=malformed.case))


def argument_named(*, option: str) -> str:
    """The start of argparse's usage error for ``option``: ``error: argument <option>: `` and then the message."""
    return f"error: argument {option}: "


def _malformed(
    *, criterion: str, slug: str, argument: Tuple[str, str], option: str, name: str, withheld: Tuple[str, ...]
) -> MalformedArgument:
    """``call issues/update --path issue_number=5`` and then ``argument``, which argparse refuses."""
    return MalformedArgument(
        case=fx.GoldenCase(
            name=f"{criterion}/exit-2/{slug}",
            argv=(CALL, OP_ISSUES_UPDATE, OPTION_PATH, "issue_number=5", *argument),
            stdout="",
            exit_code=fx.EXIT_REFUSED,
        ),
        option=option,
        name=name,
        withheld=withheld,
    )


def _malformed_arguments() -> Tuple[MalformedArgument, ...]:
    """D2's three usage errors: ``-F`` text that is not JSON, ``NaN`` and the infinities included (AC-1.3); a
    ``--path`` with no ``=``, and a ``--query`` and a ``-f`` with an empty name (AC-1.2)."""
    not_json = tuple(
        _malformed(
            criterion=AC_1_3,
            slug=f"field-{slug}",
            argument=(OPTION_FIELD_SHORT, f"{FIELD_TITLE}={text}"),
            option=NAMED_FIELD,
            name=FIELD_TITLE,
            withheld=(text,),
        )
        for slug, text in NOT_JSON_TEXTS
    )
    return (
        *not_json,
        _malformed(
            criterion=AC_1_2,
            slug="path-without-an-equals-sign",
            argument=(OPTION_PATH, NAME_WITHOUT_A_VALUE),
            option=OPTION_PATH,
            name=NAME_WITHOUT_A_VALUE,
            withheld=(),
        ),
        _malformed(
            criterion=AC_1_2,
            slug="query-with-an-empty-name",
            argument=(OPTION_QUERY, f"={EMPTY_NAME_QUERY_VALUE}"),
            option=OPTION_QUERY,
            name=EMPTY_NAME,
            withheld=(EMPTY_NAME_QUERY_VALUE,),
        ),
        _malformed(
            criterion=AC_1_2,
            slug="raw-field-with-an-empty-name",
            argument=(OPTION_RAW_FIELD_SHORT, f"={EMPTY_NAME_MEMBER_VALUE}"),
            option=NAMED_RAW_FIELD,
            name=EMPTY_NAME,
            withheld=(EMPTY_NAME_MEMBER_VALUE,),
        ),
    )


MALFORMED_ARGUMENTS = _malformed_arguments()


def run_reading_stderr(
    *, case: Any, root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> str:
    """Run ``case`` as ``fx.run_product_case`` does (the product entry script's ``main(argv=...)`` in ``case.project``
    against a fresh fake host holding ``case.routes``), judge it by ``fx.assert_outcome`` and
    ``assert_every_request_routed``, and return its standard error, which ``run_product_case`` reads and drops."""
    host = fx.enter_project(project=case.project, root=root, monkeypatch=monkeypatch, routes=case.routes)
    wrapper = fx.load_script(path=fx.PRODUCT_SCRIPT, name=fx.PRODUCT_MODULE, monkeypatch=monkeypatch)
    try:
        exit_code = wrapper.main(argv=list(case.argv))
    except SystemExit as exc:
        exit_code = fx.exit_code_of(exc=exc)
    captured = capsys.readouterr()
    fx.assert_outcome(
        case=case, outcome=fx.Outcome(stdout=captured.out, exit_code=exit_code, requests=tuple(host.requests))
    )
    host.assert_every_request_routed()
    return str(captured.err)


def _set_copies(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put copies of ``COPIED_OPERATIONS`` whose ``api_version`` is ``API_VERSION_NEXT`` and whose ``accept`` is
    ``ACCEPT_FULL_JSON`` into ``github_api.families.issues.OPERATIONS`` in place of the originals, for this test."""
    transport = fx.import_api_module(name=TRANSPORT)
    issues = importlib.import_module(name=ISSUES_FAMILY)
    loaded_from = Path(str(issues.__file__)).resolve()
    assert loaded_from == ISSUES_FAMILY_FILE.resolve(), f"{ISSUES_FAMILY} was imported from {loaded_from}"
    originals = getattr(issues, ATTRIBUTE_OPERATIONS)
    assert {record.operation_id for record in originals} >= COPIED_OPERATIONS, "a copied record is not declared"
    copies = tuple(
        dataclasses.replace(record, api_version=transport.API_VERSION_NEXT, accept=ACCEPT_FULL_JSON)
        if record.operation_id in COPIED_OPERATIONS
        else record
        for record in originals
    )
    monkeypatch.setattr(target=issues, name=ATTRIBUTE_OPERATIONS, value=copies)


def _judge_logged(
    *,
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Run ``case`` with ``fx.run_product_case`` and judge its log records by its ``log`` (``fx.assert_log``)."""
    caplog.set_level(level=logging.DEBUG)
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)
    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_1_1), ids=fx.case_name)
def test_a_gated_operation_names_its_subcommand(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-1.1, issue #32 AC-6: ``pulls/merge``, ``pulls/merge-async`` and ``issues/create`` are refused (exit 2, no
    request), and the log record names the operation ID and the compatibility subcommand to use (``merge-pr``,
    ``create-issue``); it says that the subcommand sends the record for ``pulls/merge`` and ``issues/create``, and not
    for ``pulls/merge-async``, which ``merge-pr`` never sends (issue #32 DL-007)."""
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)


@pytest.mark.parametrize(argnames="sent", argvalues=SENT_CALLS, ids=sent_call_name)
def test_an_operation_call_sends_its_record(
    sent: SentCall, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1.2: the call sends the record's method to its path as ``registry.expand`` encodes it, the given query, the
    given body members as one JSON object (no body and no ``Content-Type`` when none is given), and on every request,
    every page included, the record's ``X-GitHub-Api-Version`` and ``Accept``."""
    registry = fx.import_api_module(name=REGISTRY)
    if sent.on_copies:
        _set_copies(monkeypatch=monkeypatch)
    requests = fx.run_product_case(case=sent.case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    assert [SentRequest.of(request=request) for request in requests] == list(sent.requests)
    record = registry.lookup(operation_id=sent.case.argv[OPERATION_ID_INDEX])
    for request in requests:
        assert request.header(name=HEADER_API_VERSION) == record.api_version, f"{request.method} {request.url}"
        assert request.header(name=HEADER_ACCEPT) == record.accept, f"{request.method} {request.url}"
    for request, expected in zip(requests, sent.requests):
        if expected.body is None:
            assert request.body is None, f"{request.method} {request.url} sent a body: {request.body!r}"
            assert request.header(name=fx.HEADER_CONTENT_TYPE) is None, f"{request.method} {request.url}"


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_1_3), ids=fx.case_name)
def test_a_body_member_holds_the_given_json_value(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1.3: the member ``--field`` names holds the JSON value given, of the same JSON kind (``true`` is not ``1``,
    ``42`` is not ``"42"``)."""
    requests = fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    written = [request for request in requests if request.method == fx.METHOD_PATCH]
    assert len(written) == 1, f"{case.name}: {len(written)} PATCH requests"
    body = written[0].json()
    for name, value in case.writes[0].body.items():
        assert json.dumps(obj=body[name], sort_keys=True) == json.dumps(obj=value, sort_keys=True), name


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_1_4), ids=fx.case_name)
def test_a_list_prints_every_page_as_one_array(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1.4: a ``Paging.LINK`` record prints every item of every page, in page order, as one indented JSON array,
    each page requested by the previous one's ``rel="next"`` target as given; every request was routed."""
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_1_5), ids=fx.case_name)
def test_a_json_or_empty_body_prints_as_documented(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1.5: a ``Paging.NONE`` record's JSON body prints as ``print_json`` writes it, an empty body as nothing;
    both exit 0."""
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_1_6), ids=fx.case_name)
def test_a_body_that_is_not_json_is_written_unchanged(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """AC-1.6: an archive behind a ``302`` to a storage host, a diff, HTML and bytes that are not UTF-8 reach standard
    output as the body's bytes unchanged, and the call exits 0."""
    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsysbinary)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_1_7), ids=fx.case_name)
def test_an_api_error_exits_1_with_its_details(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-1.7: an HTTP error exits 1 with nothing on standard output; the log records hold the error's message and
    ``Details:`` with GitHub's error body, as for a compatibility subcommand."""
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)
    details = dataclasses.replace(case, log=API_ERROR_DETAILS)
    fx.assert_log(case=details, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_2_1), ids=fx.case_name)
def test_an_unknown_operation_is_refused(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.1: an ID only on a pending list, or not in the index, exits 2 with no request, and a log record names
    it."""
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_2_2), ids=fx.case_name)
def test_an_undocumented_parameter_is_refused(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.2: a path, query or body name the record does not document exits 2 with no request, and one log record
    names each such name with its kind and the record's documented path, query and body parameters."""
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)


@pytest.mark.parametrize(argnames="case", argvalues=rows_of(criterion=AC_2_3), ids=fx.case_name)
def test_a_missing_path_parameter_is_refused(
    case: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-2.3: ``call issues/get`` without ``issue_number`` exits 2 with no request, and the log record names
    ``issue_number`` and the record's path parameters ``owner``, ``repo`` and ``issue_number``."""
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)


@pytest.mark.parametrize(argnames="malformed", argvalues=MALFORMED_ARGUMENTS, ids=malformed_argument_name)
def test_a_malformed_argument_is_refused_without_its_value(
    malformed: MalformedArgument, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1.2, AC-1.3 (design D2 "Parsing"): a ``NAME=VALUE`` with no ``=`` or an empty name, or ``-F`` text that
    ``json.loads`` refuses (``NaN`` and the infinities included), exits 2 with no request, and standard error is
    argparse's usage message, whose error names the option and then the name as ``json.dumps`` renders it, and holds
    no value (Security Considerations "Command-line input")."""
    name = malformed.case.name
    stderr = run_reading_stderr(case=malformed.case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    lines = stderr.splitlines()
    assert any(line.startswith(USAGE_PREFIX) for line in lines), f"{name}: standard error holds no usage: {stderr!r}"
    named_option = argument_named(option=malformed.option)
    messages = [line.split(named_option, 1)[1] for line in lines if named_option in line]
    assert messages, f"{name}: no usage error names the option {malformed.option}: {stderr!r}"
    rendered = json.dumps(obj=malformed.name)
    assert any(rendered in message for message in messages), f"{name}: no usage error names {rendered}: {messages}"
    leaking = [value for value in malformed.withheld if value in stderr]
    assert leaking == [], f"{name}: standard error holds the value {leaking}: {stderr!r}"


# ---------------------------------------------------------------------------------------------------------------------
# Issue #46 AC-3.1 — a repository update answered 307 is sent again, once, to the resolved Location
# ---------------------------------------------------------------------------------------------------------------------

ISSUE_46 = "issue-46"
ISSUE_46_AC_3_1 = "AC-3.1"
OP_REPOS_UPDATE = "repos/update"
#: ``conventions.md`` "Downloads and redirects": the ``307`` GitHub answers a ``PATCH`` of a renamed or transferred
#: repository with.
STATUS_TEMPORARY_REDIRECT = 307
MOVED_REPOSITORY_PATH = "/repositories/42"
FIELD_DESCRIPTION = "description"
FIELD_FULL_NAME = "full_name"
UPDATED_DESCRIPTION = "d"
UPDATED_REPOSITORY_BODY = {FIELD_DESCRIPTION: UPDATED_DESCRIPTION}
UPDATED_REPOSITORY = {
    fx.FIELD_ID: 42,
    FIELD_FULL_NAME: f"{fx.OWNER}/{fx.REPOSITORY}",
    FIELD_DESCRIPTION: UPDATED_DESCRIPTION,
}
REPOSITORY_UPDATE_AFTER_A_307 = fx.GoldenCase(
    name=f"{ISSUE_46}/{ISSUE_46_AC_3_1}/exit-0/repository-update-follows-its-307",
    argv=(CALL, OP_REPOS_UPDATE, OPTION_RAW_FIELD, f"{FIELD_DESCRIPTION}={UPDATED_DESCRIPTION}"),
    stdout=fx.printed_json(value=UPDATED_REPOSITORY),
    exit_code=fx.EXIT_OK,
    routes=(
        fx.StaticRouteSpec(
            method=fx.METHOD_PATCH,
            url=fx.REPOSITORY_PATH,
            replies=(fx.redirect(status=STATUS_TEMPORARY_REDIRECT, location=MOVED_REPOSITORY_PATH),),
        ),
        fx.StaticRouteSpec(
            method=fx.METHOD_PATCH, url=MOVED_REPOSITORY_PATH, replies=(fx.Reply(body=UPDATED_REPOSITORY),)
        ),
    ),
    writes=(
        fx.NonGetRequest(method=fx.METHOD_PATCH, path=fx.REPOSITORY_PATH, body=UPDATED_REPOSITORY_BODY),
        fx.NonGetRequest(method=fx.METHOD_PATCH, path=MOVED_REPOSITORY_PATH, body=UPDATED_REPOSITORY_BODY),
    ),
)


def test_a_repository_update_follows_its_307(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #46 AC-3.1: ``call repos/update --raw-field description=d``, answered ``307`` with the relative
    ``Location`` ``/repositories/42`` and then ``200``, prints the second answer's JSON and exits 0; its writes are two
    ``PATCH`` requests with the same body, the second to the ``Location`` resolved against the first one's URL."""
    requests = fx.run_product_case(
        case=REPOSITORY_UPDATE_AFTER_A_307, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )

    assert [request.method for request in requests] == [fx.METHOD_PATCH, fx.METHOD_PATCH]
    first, second = requests
    assert second.url == f"{fx.API_ORIGIN}{MOVED_REPOSITORY_PATH}"
    assert second.body == first.body, "the re-sent PATCH carries the first one's body bytes"


# ---------------------------------------------------------------------------------------------------------------------
# Issue #46 AC-1.1, AC-1.3, AC-2.1, AC-2.2, AC-4.2 — ``--input FILE``: the raw body, its refusals and the asset upload
# ---------------------------------------------------------------------------------------------------------------------

ISSUE_46_AC_1_1 = "AC-1.1"
ISSUE_46_AC_1_3 = "AC-1.3"
ISSUE_46_AC_4_2 = "AC-4.2"
OPTION_INPUT = "--input"
OP_MARKDOWN_RENDER_RAW = "markdown/render-raw"
OP_REPOS_UPLOAD_RELEASE_ASSET = "repos/upload-release-asset"
#: ``rest/releases.md`` "Upload a release asset": "Host: `https://uploads.github.com` (not `https://api.github.com`)".
UPLOAD_ORIGIN = "https://uploads.github.com"
RELEASE_3_ASSETS_PATH = f"{fx.REPOSITORY_PATH}/releases/3/assets"
QUERY_NAME = "name"
QUERY_LABEL = "label"
FIELD_LABEL = "label"
FIELD_CONTENT_TYPE = "content_type"
FIELD_SIZE = "size"
ASSET_STATE_UPLOADED = "uploaded"
ASSET_FILE = "dist.zip"
ASSET_LABEL = "Build"
#: A zip archive's local file header and then bytes no UTF-8 decoder accepts (``\xb7`` continues no sequence, ``\xff``
#: starts none), with a ``\r\n`` that a read through the text layer would translate.
ASSET_BYTES = b"PK\x03\x04\x14\x00\x00\x00\x08\x00\xb7J\r\n\xff\xfe\x00\x80"
UPLOADED_ASSET = {
    fx.FIELD_ID: 7,
    fx.FIELD_NAME: ASSET_FILE,
    FIELD_LABEL: ASSET_LABEL,
    FIELD_CONTENT_TYPE: MEDIA_TYPE_OCTET_STREAM,
    FIELD_SIZE: len(ASSET_BYTES),
    fx.FIELD_STATE: ASSET_STATE_UPLOADED,
}
#: The files ``--input`` names, each under ``tmp_path``; ``MISSING_INPUT_FILE`` is never written.
JSON_INPUT_FILE = "body.json"
MARKDOWN_INPUT_FILE = "README.md"
MISSING_INPUT_FILE = "missing.md"
#: A JSON document: ``--input`` sends no JSON body, even to a record whose body is JSON (design D1).
JSON_INPUT = json.dumps(obj={FIELD_TITLE: UPDATED_TITLE}).encode(encoding="utf-8")
MARKDOWN_INPUT = b"# Wrapper rewrite\r\n\r\nA raw body.\r\n"
#: AC-1.3: the body member beside ``--input`` on ``markdown/render-raw``, each with its slug.
BODY_MEMBERS_BESIDE_A_RAW_BODY: Tuple[Tuple[str, Tuple[str, str]], ...] = (
    ("raw-field", (OPTION_RAW_FIELD_SHORT, "text=T")),
    ("field", (OPTION_FIELD_SHORT, 'text="T"')),
)
#: AC-1.3's refusal names both inputs: ``--input`` and each body option as argparse names it.
BOTH_BODIES_NAMED = (re.escape(OPTION_INPUT), re.escape(NAMED_RAW_FIELD), re.escape(NAMED_FIELD))


@dataclass(frozen=True)
class RawBodyRefusal:
    """A row of ``RAW_BODY_REFUSALS`` (issue #46 AC-1.1): ``call <operation_id> <arguments> --input <path>``, where
    ``path`` is ``file_name`` under ``tmp_path``, holding ``content`` when ``written`` and absent otherwise. The call
    exits 2 with nothing on standard output and no request; ``log`` holds the patterns one log record must match (none:
    the log is not judged), and ``usage_error`` says whether standard error must hold argparse's usage error for
    ``--input`` naming the path as ``json.dumps`` renders it."""

    slug: str
    operation_id: str
    arguments: Tuple[str, ...]
    file_name: str
    written: bool
    content: bytes = b""
    log: Tuple[str, ...] = ()
    usage_error: bool = False


RAW_BODY_REFUSALS = (
    RawBodyRefusal(
        slug="input-for-a-json-record",
        operation_id=OP_ISSUES_UPDATE,
        arguments=(OPTION_PATH, "issue_number=5"),
        file_name=JSON_INPUT_FILE,
        written=True,
        content=JSON_INPUT,
        log=(named(name=OP_ISSUES_UPDATE), re.escape(OPTION_INPUT)),
    ),
    RawBodyRefusal(
        slug="input-file-that-does-not-exist",
        operation_id=OP_MARKDOWN_RENDER_RAW,
        arguments=(),
        file_name=MISSING_INPUT_FILE,
        written=False,
        usage_error=True,
    ),
)


def raw_body_refusal_name(refusal: RawBodyRefusal) -> str:
    """The test id of a ``RAW_BODY_REFUSALS`` row."""
    return refusal.slug


def _origin_of(*, url: str) -> Tuple[str, str, int]:
    """The origin of the absolute ``url``: its scheme, host and port (the scheme's default when it names none)."""
    endpoint = fx.Endpoint.of(url=url)
    return endpoint.scheme, endpoint.host, endpoint.port


def _asset_upload(*, asset: Path) -> Any:
    """AC-4.2's row: ``call repos/upload-release-asset`` of the file ``asset`` to release 3 of ``o/r``, named
    ``dist.zip`` and labelled ``Build``; its one write is the ``POST`` of ``ASSET_BYTES`` with that query, which the
    route on the upload origin answers with ``201`` and the asset as JSON."""
    query = {QUERY_NAME: ASSET_FILE, QUERY_LABEL: ASSET_LABEL}
    return fx.GoldenCase(
        name=f"{ISSUE_46}/{ISSUE_46_AC_4_2}/exit-0/asset-uploaded-to-its-host",
        argv=(
            CALL,
            OP_REPOS_UPLOAD_RELEASE_ASSET,
            OPTION_PATH,
            "release_id=3",
            OPTION_QUERY,
            f"{QUERY_NAME}={ASSET_FILE}",
            OPTION_QUERY,
            f"{QUERY_LABEL}={ASSET_LABEL}",
            OPTION_INPUT,
            str(asset),
        ),
        stdout=fx.printed_json(value=UPLOADED_ASSET),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.StaticRouteSpec(
                method=fx.METHOD_POST,
                url=f"{UPLOAD_ORIGIN}{RELEASE_3_ASSETS_PATH}",
                replies=(fx.Reply(status=fx.CREATED, body=UPLOADED_ASSET),),
                query=query,
            ),
        ),
        writes=(
            fx.NonGetRequest(
                method=fx.METHOD_POST, path=RELEASE_3_ASSETS_PATH, body=ASSET_BYTES, query=fx.query_of(values=query)
            ),
        ),
    )


@pytest.mark.parametrize(argnames="refusal", argvalues=RAW_BODY_REFUSALS, ids=raw_body_refusal_name)
def test_a_raw_body_the_call_cannot_send_is_refused(
    refusal: RawBodyRefusal,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #46 AC-1.1 (design D1): ``--input`` on ``issues/update``, a record whose body is JSON, is refused, a JSON
    document included, and a log record names the ID as ``json.dumps`` renders it and ``--input``; ``--input`` naming
    a file that does not exist is argparse's usage error, whose ``argument --input:`` message names the path as
    ``json.dumps`` renders it. Each exits 2 with nothing on standard output and no request."""
    caplog.set_level(level=logging.DEBUG)
    path = tmp_path / refusal.file_name
    if refusal.written:
        path.write_bytes(data=refusal.content)
    case = fx.GoldenCase(
        name=f"{ISSUE_46}/{ISSUE_46_AC_1_1}/exit-2/{refusal.slug}",
        argv=(CALL, refusal.operation_id, *refusal.arguments, OPTION_INPUT, str(path)),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(refusal=refusal.log, withheld=()) if refusal.log else None,
    )
    stderr = run_reading_stderr(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=stderr)
    if refusal.usage_error:
        named_option = argument_named(option=OPTION_INPUT)
        messages = [line.split(named_option, 1)[1] for line in stderr.splitlines() if named_option in line]
        assert messages, f"{case.name}: no usage error names the option {OPTION_INPUT}: {stderr!r}"
        rendered = json.dumps(obj=str(path))
        assert any(rendered in message for message in messages), (
            f"{case.name}: no usage error names the path {rendered}: {messages}"
        )


@pytest.mark.parametrize(
    argnames=("slug", "member"),
    argvalues=BODY_MEMBERS_BESIDE_A_RAW_BODY,
    ids=[slug for slug, _ in BODY_MEMBERS_BESIDE_A_RAW_BODY],
)
def test_a_raw_body_with_body_members_is_refused(
    slug: str,
    member: Tuple[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #46 AC-1.3 (design D1 step 1): ``-f text=T`` or ``-F text="T"`` beside ``--input`` of a file under
    ``tmp_path`` on ``markdown/render-raw`` exits 2 with nothing on standard output and no request, and one log record
    names ``--input``, ``-f/--raw-field`` and ``-F/--field``."""
    path = tmp_path / MARKDOWN_INPUT_FILE
    path.write_bytes(data=MARKDOWN_INPUT)
    case = fx.GoldenCase(
        name=f"{ISSUE_46}/{ISSUE_46_AC_1_3}/exit-2/{slug}-beside-input",
        argv=(CALL, OP_MARKDOWN_RENDER_RAW, *member, OPTION_INPUT, str(path)),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(refusal=BOTH_BODIES_NAMED, withheld=()),
    )
    _judge_logged(case=case, tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys, caplog=caplog)


def test_an_asset_is_uploaded_to_its_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #46 AC-2.1, AC-2.2, AC-4.2: ``call repos/upload-release-asset --path release_id=3 --query name=dist.zip
    --query label=Build --input <a file of bytes that are not UTF-8>`` exits 0 and prints the ``201`` answer as JSON.
    Its one request is the ``POST`` of exactly the file's bytes to the expanded path, with the query ``name`` and
    ``label``, on the origin of ``https://uploads.github.com``, with ``content-type`` ``application/octet-stream`` and
    the credential; no request carries the credential to any other origin."""
    asset = tmp_path / ASSET_FILE
    asset.write_bytes(data=ASSET_BYTES)
    requests = fx.run_product_case(
        case=_asset_upload(asset=asset), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys
    )

    upload_origin = _origin_of(url=UPLOAD_ORIGIN)
    credentialed_elsewhere = [
        f"{request.method} {request.url}"
        for request in requests
        if request.header(name=fx.HEADER_AUTHORIZATION) is not None and _origin_of(url=request.url) != upload_origin
    ]
    assert credentialed_elsewhere == [], f"the credential reached another origin: {credentialed_elsewhere}"
    assert len(requests) == 1, f"{len(requests)} requests: {[request.url for request in requests]}"
    upload = requests[0]
    assert _origin_of(url=upload.url) == upload_origin, f"the upload went to {upload.url}"
    assert upload.header(name=fx.HEADER_CONTENT_TYPE) == MEDIA_TYPE_OCTET_STREAM
    authorization = upload.header(name=fx.HEADER_AUTHORIZATION)
    assert authorization is not None and fx.FIXTURE_TOKEN in authorization, "the upload carries no credential"
    assert upload.body == ASSET_BYTES, "the upload's body is not the file's bytes"


# ---------------------------------------------------------------------------------------------------------------------
# Issue #46 AC-1.2, AC-4.3 — ``--input -``: a raw Markdown document read from standard input and rendered
# ---------------------------------------------------------------------------------------------------------------------

ISSUE_46_AC_4_3 = "AC-4.3"
#: The ``--input`` text that reads the raw body from standard input, as ``gh api`` spells it.
INPUT_FROM_STDIN = "-"
#: ``rest/markdown.md`` "Render a Markdown document in raw mode": ``POST /markdown/raw``, its request body
#: ``text/plain``, its ``200`` ``text/html``.
MARKDOWN_RAW_PATH = "/markdown/raw"
MEDIA_TYPE_TEXT_PLAIN = "text/plain"
#: The ``sys`` attribute the test replaces with a text layer over the document, and that layer's encoding: strict
#: UTF-8, which fails on ``\xff``.
ATTRIBUTE_STDIN = "stdin"
STDIN_ENCODING = "utf-8"
#: A Markdown document with ``\r\n`` line ends, which a read through the text layer would translate to ``\n``, and the
#: byte ``\xff``, which no UTF-8 decoder accepts.
RAW_MARKDOWN = b"# Wrapper rewrite\r\n\r\nA raw body \xff in raw mode.\r\n"
RENDERED_RAW_MARKDOWN = b"<h1>Wrapper rewrite</h1>\n<p>A raw body in raw mode.</p>\n"
RAW_MARKDOWN_RENDERED = fx.GoldenCase(
    name=f"{ISSUE_46}/{ISSUE_46_AC_4_3}/exit-0/raw-markdown-from-standard-input-rendered",
    argv=(CALL, OP_MARKDOWN_RENDER_RAW, OPTION_INPUT, INPUT_FROM_STDIN),
    stdout=fx.binary_stdout(data=RENDERED_RAW_MARKDOWN),
    exit_code=fx.EXIT_OK,
    routes=(
        fx.StaticRouteSpec(
            method=fx.METHOD_POST,
            url=MARKDOWN_RAW_PATH,
            replies=(fx.Reply(body=RENDERED_RAW_MARKDOWN, headers={fx.HEADER_CONTENT_TYPE: MEDIA_TYPE_HTML}),),
        ),
    ),
    writes=(fx.NonGetRequest(method=fx.METHOD_POST, path=MARKDOWN_RAW_PATH, body=RAW_MARKDOWN),),
)


def test_a_raw_markdown_document_is_rendered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    """Issue #46 AC-1.2, AC-4.3: ``call markdown/render-raw --input -``, standard input a text layer over Markdown
    bytes holding a CR LF line end and the byte 0xFF, exits 0 and writes the HTML answer's bytes to standard output
    unchanged. Its one request is the ``POST`` to ``https://api.github.com/markdown/raw`` with ``content-type``
    ``text/plain`` and a body equal to those bytes, read from standard input's binary buffer, not through the text
    layer, which would translate the line end or fail to decode the byte."""
    stdin = io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=RAW_MARKDOWN), encoding=STDIN_ENCODING)
    monkeypatch.setattr(target=sys, name=ATTRIBUTE_STDIN, value=stdin)
    requests = fx.run_product_case(
        case=RAW_MARKDOWN_RENDERED, root=tmp_path, monkeypatch=monkeypatch, capsys=capsysbinary
    )

    assert len(requests) == 1, f"{len(requests)} requests: {[request.url for request in requests]}"
    rendering = requests[0]
    assert rendering.method == fx.METHOD_POST, f"the rendering was a {rendering.method}"
    assert rendering.url == f"{fx.API_ORIGIN}{MARKDOWN_RAW_PATH}", f"the rendering went to {rendering.url}"
    assert rendering.header(name=fx.HEADER_CONTENT_TYPE) == MEDIA_TYPE_TEXT_PLAIN
    assert rendering.body == RAW_MARKDOWN, f"the body sent is not the Markdown bytes: {rendering.body!r}"
