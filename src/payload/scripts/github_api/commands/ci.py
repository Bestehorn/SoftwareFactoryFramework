"""The CI subcommands of the GitHub wrapper (design D5): ``list-workflows``, ``list-runs``, ``get-run``, ``wait-run``
and ``get-logs``.

``register`` adds each subcommand with the fork's arguments — its ``_register_actions_subcommands`` and
``_register_wait_and_task_item_subcommands``, names, types and defaults as they define them, without
``--token-stdin`` (UB-1.1). Each subparser carries its handler as ``handler``, which the entry script calls as
``handler(transport=..., owner=..., repo=..., args=...)`` (D6). A handler sends the fork handler's requests on the
``actions`` family's records (``github_api/families/actions.py``) and writes the fork handler's standard output:

- ``list-workflows``: one page of ``actions/list-repo-workflows``; one ``<id> <state> <name>`` line per workflow.
- ``list-runs``: one page of ``actions/list-workflow-runs-for-repo``, or of ``actions/list-workflow-runs`` with
  ``--workflow``, with ``--limit`` sent as ``per_page`` and ``--status`` as ``status``; one
  ``<id> <status> <conclusion> <name>`` line per run.
- ``get-run``: ``actions/get-workflow-run``, echoed as indented JSON.
- ``wait-run``: the fork's poll — read the run (``actions/get-workflow-run``), return once it is ``completed``
  (exit 0 for ``success``, 10 for any other conclusion), else stop when the deadline has passed (exit 11), else sleep
  ``--interval-seconds`` and read again — each verdict a one-line JSON object. The clock and the sleep are the fork's
  module seams, ``_monotonic`` and ``_sleep``.
- ``get-logs``: ``actions/download-workflow-run-logs`` through ``Transport.download``, which follows the ``302`` to the
  storage host without the credential; each archive entry (only those whose name holds ``failed``, in any case, with
  ``--failed-only``) printed as a ``==== <name> ====`` line, then its UTF-8 text, undecodable bytes replaced, and a
  line end. The entry script has already made standard output UTF-8 (D6), as the fork's ``_configure_log_stream``.

A response that is not the JSON object a command reads, and a log download that is not a zip archive, raise
``GitHubAPIError`` (exit 1) where the fork crashed with a traceback (also exit 1). Every other refusal is the
transport's or the registry's ``GitHubAPIError``.
"""

from __future__ import annotations

import argparse
import io
import time
import zipfile
from typing import Any, Callable, Dict, List, Mapping, Optional

from github_api import registry
from github_api.commands._common import (
    FIELD_CONCLUSION,
    FIELD_NAME,
    FIELD_STATE,
    FIELD_STATUS,
    print_compact_json,
    print_json,
    print_line,
)
from github_api.errors import GitHubAPIError
from github_api.transport import Transport

#: What a subparser's ``handler`` is: called with ``transport``, ``owner``, ``repo`` and ``args``; returns ``None`` or
#: an exit code (D6).
Handler = Callable[..., Optional[int]]

OP_LIST_REPO_WORKFLOWS = "actions/list-repo-workflows"
OP_LIST_RUNS_FOR_REPO = "actions/list-workflow-runs-for-repo"
OP_LIST_WORKFLOW_RUNS = "actions/list-workflow-runs"
OP_GET_RUN = "actions/get-workflow-run"
OP_DOWNLOAD_RUN_LOGS = "actions/download-workflow-run-logs"

PATH_OWNER = "owner"
PATH_REPO = "repo"
PATH_RUN_ID = "run_id"
PATH_WORKFLOW_ID = "workflow_id"

QUERY_PER_PAGE = "per_page"
QUERY_STATUS = "status"

FIELD_ID = "id"
FIELD_HTML_URL = "html_url"
FIELD_WORKFLOWS = "workflows"
FIELD_WORKFLOW_RUNS = "workflow_runs"

# The fork's ``wait-run`` verdicts and defaults. 1 is the wrapper's API-error exit and 2 its usage or credential
# refusal, so a caller can tell "the run failed" from "the API call failed".
EXIT_OK = 0
EXIT_WAIT_NOT_SUCCESS = 10
EXIT_WAIT_TIMEOUT = 11
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_UNKNOWN = "unknown"
RUN_CONCLUSION_SUCCESS = "success"
WAIT_RUN_DEFAULT_TIMEOUT_SECONDS = 3600
WAIT_RUN_DEFAULT_INTERVAL_SECONDS = 30
KEY_RUN_ID = "run_id"
KEY_TIMEOUT_SECONDS = "timeout_seconds"

#: The clock ``wait-run`` measures its deadline with and the sleep between its reads: the fork's module seams.
_monotonic = time.monotonic
_sleep = time.sleep

LIST_RUNS_LIMIT_DEFAULT = 10
LOG_TEXT_ENCODING = "utf-8"
LOG_TEXT_ERRORS = "replace"
FAILED_ENTRY_MARKER = "failed"

CMD_LIST_WORKFLOWS = "list-workflows"
CMD_LIST_RUNS = "list-runs"
CMD_GET_RUN = "get-run"
CMD_WAIT_RUN = "wait-run"
CMD_GET_LOGS = "get-logs"

ARG_RUN_ID = "run_id"
OPTION_WORKFLOW = "--workflow"
OPTION_STATUS = "--status"
OPTION_LIMIT = "--limit"
OPTION_TIMEOUT_SECONDS = "--timeout-seconds"
OPTION_INTERVAL_SECONDS = "--interval-seconds"
OPTION_FAILED_ONLY = "--failed-only"
ACTION_STORE_TRUE = "store_true"


def _repository_params(*, owner: str, repo: str) -> Dict[str, Any]:
    """The path parameters of a repository-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo}


def _run_params(*, owner: str, repo: str, run_id: int) -> Dict[str, Any]:
    """The path parameters of a run-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo, PATH_RUN_ID: run_id}


def _json_object(*, data: Any, what: str) -> Dict[str, Any]:
    """``data`` when it is a JSON object; otherwise ``GitHubAPIError`` naming ``what`` was read."""
    if not isinstance(data, dict):
        raise GitHubAPIError(message=f"Unexpected {what} payload: not a JSON object.", details=data)
    return data


def _listed(*, data: Any, item_key: str, what: str) -> List[Any]:
    """The items of one page of a wrapped list, as the fork reads them: the list under ``item_key``, none when the
    key is absent."""
    return list(_json_object(data=data, what=what).get(item_key, []))


def _workflow_line(*, workflow: Mapping[str, Any]) -> str:
    """The fork's ``list-workflows`` line of one workflow."""
    return f"{workflow[FIELD_ID]:<12} {workflow[FIELD_STATE]:<10} {workflow[FIELD_NAME]}"


def _run_line(*, run: Mapping[str, Any]) -> str:
    """The fork's ``list-runs`` line of one run; a run without a conclusion shows ``None``."""
    return f"{run[FIELD_ID]:<12} {run[FIELD_STATUS]:<12} {str(run.get(FIELD_CONCLUSION)):<12} {run[FIELD_NAME]}"


def _read_run(*, transport: Transport, owner: str, repo: str, run_id: int) -> Dict[str, Any]:
    """One fresh read of the run (``actions/get-workflow-run``)."""
    data = registry.call(
        transport=transport, operation_id=OP_GET_RUN, path_params=_run_params(owner=owner, repo=repo, run_id=run_id)
    )
    return _json_object(data=data, what=f"workflow run {run_id}")


def cmd_list_workflows(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the workflows of the first page, one line each, as the fork does."""
    del args  # the fork's list-workflows takes no argument
    data = registry.call(
        transport=transport,
        operation_id=OP_LIST_REPO_WORKFLOWS,
        path_params=_repository_params(owner=owner, repo=repo),
    )
    for workflow in _listed(data=data, item_key=FIELD_WORKFLOWS, what=FIELD_WORKFLOWS):
        print_line(text=_workflow_line(workflow=workflow))


def cmd_list_runs(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the runs of ONE page, ``--limit`` sent as ``per_page``: of the repository, or of ``--workflow``."""
    query: Dict[str, Any] = {QUERY_PER_PAGE: args.limit}
    if args.status:
        query[QUERY_STATUS] = args.status
    path_params = _repository_params(owner=owner, repo=repo)
    operation_id = OP_LIST_RUNS_FOR_REPO
    if args.workflow:
        path_params[PATH_WORKFLOW_ID] = args.workflow
        operation_id = OP_LIST_WORKFLOW_RUNS
    data = registry.call(transport=transport, operation_id=operation_id, path_params=path_params, query=query)
    for run in _listed(data=data, item_key=FIELD_WORKFLOW_RUNS, what=FIELD_WORKFLOW_RUNS):
        print_line(text=_run_line(run=run))


def cmd_get_run(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the run as indented JSON."""
    data = registry.call(
        transport=transport,
        operation_id=OP_GET_RUN,
        path_params=_run_params(owner=owner, repo=repo, run_id=args.run_id),
    )
    print_json(value=data)


def cmd_wait_run(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Block until the run completes; the exit status is the verdict: 0 ``success``, 10 any other conclusion, 11 the
    timeout passed first.

    The fork's order: read the run; return when it is ``completed``; else stop when ``--timeout-seconds`` have passed
    since the start; else sleep ``--interval-seconds`` and read again. So ``--timeout-seconds 0`` reads once and never
    sleeps. Run it in the foreground with ``--timeout-seconds 540`` and re-issue it while it exits 11.
    """
    deadline = _monotonic() + args.timeout_seconds
    status = ""
    while True:
        data = _read_run(transport=transport, owner=owner, repo=repo, run_id=args.run_id)
        status = str(data.get(FIELD_STATUS) or "")
        conclusion = str(data.get(FIELD_CONCLUSION) or "")
        if status == RUN_STATUS_COMPLETED:
            print_compact_json(
                value={
                    KEY_RUN_ID: args.run_id,
                    FIELD_STATUS: status,
                    FIELD_CONCLUSION: conclusion,
                    FIELD_HTML_URL: data.get(FIELD_HTML_URL, ""),
                }
            )
            return EXIT_OK if conclusion == RUN_CONCLUSION_SUCCESS else EXIT_WAIT_NOT_SUCCESS
        if _monotonic() >= deadline:
            break
        _sleep(args.interval_seconds)  # positional: time.sleep takes its seconds positional-only
    print_compact_json(
        value={
            KEY_RUN_ID: args.run_id,
            FIELD_STATUS: status or RUN_STATUS_UNKNOWN,
            KEY_TIMEOUT_SECONDS: args.timeout_seconds,
        }
    )
    return EXIT_WAIT_TIMEOUT


def _download_logs(*, transport: Transport, owner: str, repo: str, run_id: int) -> bytes:
    """The run's log archive: the logs record's expanded path, sent with ``Transport.download``, which follows the
    ``302`` to the storage host without the credential."""
    operation = registry.lookup(operation_id=OP_DOWNLOAD_RUN_LOGS)
    path = registry.expand(operation=operation, path_params=_run_params(owner=owner, repo=repo, run_id=run_id))
    return transport.download(path=path)


def _entry_text(*, archive: zipfile.ZipFile, name: str) -> str:
    """The text of the archive entry ``name``, decoded as UTF-8 with undecodable bytes replaced; an entry that cannot
    be read gives the fork's ``(error reading <name>: <error>)`` note instead.

    The guard is the fork's per-entry ``except Exception``, kept as broad because ``ZipFile.read`` raises several
    unrelated types for a damaged entry; only the read and the decode are inside it, so no error writing the text to
    standard output is ever reported as an archive error.
    """
    try:
        return archive.read(name=name).decode(encoding=LOG_TEXT_ENCODING, errors=LOG_TEXT_ERRORS)
    except Exception as exc:  # the fork's defensive per-entry guard
        return f"(error reading {name}: {exc})"


def cmd_get_logs(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print every entry of the run's log archive — with ``--failed-only``, those whose name holds ``failed`` in any
    case — as a ``==== <name> ====`` line followed by its text."""
    blob = _download_logs(transport=transport, owner=owner, repo=repo, run_id=args.run_id)
    try:
        archive = zipfile.ZipFile(file=io.BytesIO(initial_bytes=blob))
    except zipfile.BadZipFile as error:
        raise GitHubAPIError(message=f"The logs of run {args.run_id} are not a zip archive") from error
    with archive:
        for name in archive.namelist():
            if args.failed_only and FAILED_ENTRY_MARKER not in name.lower():
                continue
            print_line(text=f"==== {name} ====")
            print_line(text=_entry_text(archive=archive, name=name))


def _add_command(
    *, subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str, help_text: str, handler: Handler
) -> argparse.ArgumentParser:
    """The subparser ``name`` with the fork's help text, carrying ``handler`` as ``handler`` (D6)."""
    parser = subparsers.add_parser(name=name, help=help_text)
    parser.set_defaults(handler=handler)
    return parser


def _register_reads(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``list-workflows``, ``list-runs``, ``get-run`` and ``get-logs``, as the fork's
    ``_register_actions_subcommands``."""
    _add_command(
        subparsers=subparsers,
        name=CMD_LIST_WORKFLOWS,
        help_text="List all GitHub Actions workflows",
        handler=cmd_list_workflows,
    )

    parser = _add_command(
        subparsers=subparsers, name=CMD_LIST_RUNS, help_text="List recent workflow runs", handler=cmd_list_runs
    )
    parser.add_argument(OPTION_WORKFLOW, help="Filter by workflow file name or ID")
    parser.add_argument(OPTION_STATUS, help="Filter by status (queued, in_progress, completed, ...)")
    parser.add_argument(OPTION_LIMIT, type=int, default=LIST_RUNS_LIMIT_DEFAULT)

    parser = _add_command(subparsers=subparsers, name=CMD_GET_RUN, help_text="Show a single run", handler=cmd_get_run)
    parser.add_argument(ARG_RUN_ID, type=int)

    parser = _add_command(
        subparsers=subparsers,
        name=CMD_GET_LOGS,
        help_text="Fetch logs for a run (zip archive, extracted)",
        handler=cmd_get_logs,
    )
    parser.add_argument(ARG_RUN_ID, type=int)
    parser.add_argument(OPTION_FAILED_ONLY, action=ACTION_STORE_TRUE)


def _register_wait(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``wait-run``, as the fork's ``_register_wait_and_task_item_subcommands``."""
    parser = _add_command(
        subparsers=subparsers,
        name=CMD_WAIT_RUN,
        help_text="BLOCK until a run completes: exit 0 success, 10 other conclusion, 11 timeout",
        handler=cmd_wait_run,
    )
    parser.add_argument(ARG_RUN_ID, type=int)
    parser.add_argument(OPTION_TIMEOUT_SECONDS, type=int, default=WAIT_RUN_DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(OPTION_INTERVAL_SECONDS, type=int, default=WAIT_RUN_DEFAULT_INTERVAL_SECONDS)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add the CI subcommands to the entry script's ``subparsers``, each carrying its handler (D6)."""
    _register_reads(subparsers=subparsers)
    _register_wait(subparsers=subparsers)
