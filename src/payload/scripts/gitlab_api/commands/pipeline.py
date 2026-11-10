"""The ``pipeline`` subcommands of the GitLab wrapper (issue #13, design.md D6; UB-1)::

    pipeline status [--count N]     the N newest pipelines (default 1), as JSON
    pipeline log                    the traces of the latest pipeline's failed jobs, as text
    pipeline wait <pipeline_id> [--timeout-seconds N]   block until the pipeline is terminal: exit 0 on success, 10
                                    when it ended without success, 11 at the deadline (re-issue)

Each handler composes records of the ``verify`` family by id through ``gitlab_api.registry``: the Pipelines API's
``list-project-pipelines`` and ``retrieve-a-single-pipeline``, the Jobs API's ``list-all-jobs-by-pipeline`` and
``retrieve-a-log-file-for-a-job`` (``rest/verify.md``). "Newest" is ``order_by=id``, ``sort=desc``; ``per_page`` is the
count asked for, and only that many items are printed. ``pipeline log`` reads the failed jobs with one request of
``scope[]=failed`` (no paging, so GitLab's default page of 20 jobs) and prints, per job in the listed order, one header
line naming the job's id and name and then its trace verbatim; when no pipeline exists or none of the latest
pipeline's jobs failed it prints one line of text saying so.

``pipeline_wait`` is the skeleton's blocking wait rebuilt on the transport: it pauses with ``transport.sleep`` and reads
the time from ``transport.clock``, so a test passes a fake clock and no real time passes. It polls while the clock is
before ``clock() + timeout_seconds``, pauses ``interval_seconds`` after every poll that does not end the wait, and
prints the skeleton's one-line JSON summary: ``{id, status, web_url}`` at a terminal status, ``{id, status,
timeout_seconds}`` at the deadline, ``status`` being the last one seen or ``unknown``. Its exit codes, 10 and 11, are
distinct from the wrapper's own 1 (API error), 2 (usage) and 3 (``issue claim-check`` unclaimed), so a caller can tell
"the pipeline failed" from "the API call failed". This is the one sanctioned way for an agent to wait on CI: after the
unblocked work, in the FOREGROUND, ``--timeout-seconds 540``, re-issued while it exits 11 — never a background task,
never a ``sleep`` in a tool call (parallel-by-default.md).

Any failure raises ``GitLabAPIError``, which the entry script logs on standard error and exits 1 with.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional

from gitlab_api import registry
from gitlab_api.commands._common import (
    FIELD_ID,
    JSON_INDENT,
    LINE_END,
    PATH_PROJECT,
    add_command,
    add_group,
    print_json,
)
from gitlab_api.errors import GitLabAPIError
from gitlab_api.transport import MAX_PER_PAGE

if TYPE_CHECKING:
    from gitlab_api.commands._common import SubParsers
    from gitlab_api.transport import Transport

GROUP = "pipeline"

# The records the handlers compose (design.md D6).
OP_LIST_PIPELINES = "verify#list-project-pipelines"
OP_SHOW_PIPELINE = "verify#retrieve-a-single-pipeline"
OP_LIST_JOBS = "verify#list-all-jobs-by-pipeline"
OP_JOB_TRACE = "verify#retrieve-a-log-file-for-a-job"

# The path parameters of the pipeline and job records.
PATH_PIPELINE_ID = "pipeline_id"
PATH_JOB_ID = "job_id"

# Request and response keys only this module reads or sends (rest/verify.md "Pipelines API" and "Jobs API") and the
# `timeout_seconds` key of `pipeline wait`'s summary line at the deadline (the skeleton's).
FIELD_ORDER_BY = "order_by"
FIELD_SORT = "sort"
FIELD_PER_PAGE = "per_page"
FIELD_SCOPE = "scope"
FIELD_STATUS = "status"
FIELD_WEB_URL = "web_url"
FIELD_NAME = "name"
FIELD_TIMEOUT_SECONDS = "timeout_seconds"

# The newest pipelines first; the jobs that failed.
ORDER_BY_ID = "id"
SORT_DESCENDING = "desc"
SCOPE_FAILED = "failed"
DEFAULT_COUNT = 1
MIN_COUNT = 1

# The skeleton's verdicts. Deliberately NOT 1/2/3: 1 is this wrapper's API-error exit, 2 is argparse's usage error,
# 3 is `issue claim-check`'s "open and unclaimed".
PIPELINE_TERMINAL_STATUSES = frozenset({"success", "failed", "canceled", "skipped", "manual"})
STATUS_SUCCESS = "success"
STATUS_UNKNOWN = "unknown"
EXIT_WAIT_SUCCESS = 0
EXIT_WAIT_NOT_SUCCESS = 10
EXIT_WAIT_TIMEOUT = 11
# The contract's bounded foreground wait (the caller re-issues on 11) and the skeleton's poll interval.
DEFAULT_TIMEOUT_SECONDS = 540
DEFAULT_INTERVAL_SECONDS = 30

JOB_HEADER = "=== job {job_id} {name} ==="
NO_PIPELINE = "project {project} has no pipeline"
NO_FAILED_JOB = "pipeline {pipeline_id} ({status}) has no failed job"


# --- Reading the records' answers ---------------------------------------------------------------------------------


def _json_object(*, value: Any, operation_id: str) -> Dict[str, Any]:
    """``value`` when it is a JSON object; another answer raises ``GitLabAPIError`` naming the record."""
    if not isinstance(value, dict):
        raise GitLabAPIError(f"{operation_id} answered {type(value).__name__}, not a JSON object")
    return value


def _json_list(*, value: Any, operation_id: str) -> List[Dict[str, Any]]:
    """``value`` when it is a JSON array of objects; another answer raises ``GitLabAPIError`` naming the record."""
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise GitLabAPIError(f"{operation_id} answered {type(value).__name__}, not a JSON array of objects")
    return value


def _integer_id(*, item: Mapping[str, Any], operation_id: str) -> int:
    """A pipeline's or job's integer ``id``; an item without one raises ``GitLabAPIError`` naming the record."""
    item_id = item.get(FIELD_ID)
    if not isinstance(item_id, int) or isinstance(item_id, bool):
        raise GitLabAPIError(f"{operation_id} answered an item without an integer {FIELD_ID!r}")
    return item_id


def _newest_pipelines(*, transport: Transport, project: str, count: int) -> List[Dict[str, Any]]:
    """The ``count`` newest pipelines of the project: one ``GET /projects/:id/pipelines`` with ``order_by=id``,
    ``sort=desc`` and ``per_page=count``, of whose answer the first ``count`` items are kept."""
    values = {PATH_PROJECT: project, FIELD_ORDER_BY: ORDER_BY_ID, FIELD_SORT: SORT_DESCENDING, FIELD_PER_PAGE: count}
    value = registry.call(transport=transport, operation_id=OP_LIST_PIPELINES, values=values)
    return _json_list(value=value, operation_id=OP_LIST_PIPELINES)[:count]


def _failed_jobs(*, transport: Transport, project: str, pipeline_id: int) -> List[Dict[str, Any]]:
    """The pipeline's failed jobs: one ``GET /projects/:id/pipelines/:pipeline_id/jobs`` with ``scope[]=failed``."""
    values = {PATH_PROJECT: project, PATH_PIPELINE_ID: pipeline_id, FIELD_SCOPE: [SCOPE_FAILED]}
    value = registry.call(transport=transport, operation_id=OP_LIST_JOBS, values=values)
    return _json_list(value=value, operation_id=OP_LIST_JOBS)


def _trace(*, transport: Transport, project: str, job_id: int) -> str:
    """The job's log, ``GET /projects/:id/jobs/:job_id/trace``: its text; an empty log is ``""``."""
    values = {PATH_PROJECT: project, PATH_JOB_ID: job_id}
    value = registry.call(transport=transport, operation_id=OP_JOB_TRACE, values=values)
    if value is None:
        return ""
    return value if isinstance(value, str) else json.dumps(obj=value, indent=JSON_INDENT)


# --- Text output --------------------------------------------------------------------------------------------------


def _write_line(*, text: str) -> None:
    """One line of text on standard output, the result of a subcommand that prints text."""
    sys.stdout.write(text + LINE_END)


def _write_trace(*, job_id: int, name: str, trace: str) -> None:
    """One job's block: its header line, then its trace verbatim, ending with a line end."""
    _write_line(text=JOB_HEADER.format(job_id=job_id, name=name))
    if trace:
        sys.stdout.write(trace if trace.endswith(LINE_END) else trace + LINE_END)


def _write_summary(*, value: Mapping[str, Any]) -> None:
    """``pipeline wait``'s summary: one line of JSON, as the skeleton printed it."""
    _write_line(text=json.dumps(obj=dict(value)))


# --- The blocking wait --------------------------------------------------------------------------------------------


def _poll(*, transport: Transport, project: str, pipeline_id: int) -> Dict[str, Any]:
    """One ``GET /projects/:id/pipelines/:pipeline_id``: the pipeline."""
    values = {PATH_PROJECT: project, PATH_PIPELINE_ID: pipeline_id}
    value = registry.call(transport=transport, operation_id=OP_SHOW_PIPELINE, values=values)
    return _json_object(value=value, operation_id=OP_SHOW_PIPELINE)


def pipeline_wait(
    *,
    transport: Transport,
    project: str,
    pipeline_id: int,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
) -> int:
    """Block until the pipeline is terminal or the deadline, ``transport.clock()`` + ``timeout_seconds``, is reached.

    It polls while ``transport.clock()`` is before the deadline and calls ``transport.sleep(interval_seconds)`` after
    every poll whose status is not in ``PIPELINE_TERMINAL_STATUSES``; a timeout of 0 sends no request. Returns
    ``EXIT_WAIT_SUCCESS`` (0) on ``success``, ``EXIT_WAIT_NOT_SUCCESS`` (10) on another terminal status and
    ``EXIT_WAIT_TIMEOUT`` (11) at the deadline, after printing the skeleton's summary line."""
    deadline = transport.clock() + timeout_seconds
    status = ""
    while transport.clock() < deadline:
        pipeline = _poll(transport=transport, project=project, pipeline_id=pipeline_id)
        status = str(pipeline.get(FIELD_STATUS) or "")
        if status in PIPELINE_TERMINAL_STATUSES:
            web_url = pipeline.get(FIELD_WEB_URL, "")
            _write_summary(value={FIELD_ID: pipeline_id, FIELD_STATUS: status, FIELD_WEB_URL: web_url})
            return EXIT_WAIT_SUCCESS if status == STATUS_SUCCESS else EXIT_WAIT_NOT_SUCCESS
        transport.sleep(interval_seconds)
    _write_summary(
        value={FIELD_ID: pipeline_id, FIELD_STATUS: status or STATUS_UNKNOWN, FIELD_TIMEOUT_SECONDS: timeout_seconds}
    )
    return EXIT_WAIT_TIMEOUT


# --- The handlers (design.md D6) ----------------------------------------------------------------------------------


def status_pipelines(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``pipeline status [--count N]``: the N newest pipelines, as a JSON list."""
    print_json(value=_newest_pipelines(transport=transport, project=project, count=args.count))


def log_pipeline(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``pipeline log``: per failed job of the latest pipeline a header line and its trace; one line of text when no
    pipeline exists (no jobs are read) or no job of the latest pipeline failed."""
    latest = _newest_pipelines(transport=transport, project=project, count=1)
    if not latest:
        _write_line(text=NO_PIPELINE.format(project=project))
        return
    pipeline_id = _integer_id(item=latest[0], operation_id=OP_LIST_PIPELINES)
    jobs = _failed_jobs(transport=transport, project=project, pipeline_id=pipeline_id)
    if not jobs:
        status = latest[0].get(FIELD_STATUS) or STATUS_UNKNOWN
        _write_line(text=NO_FAILED_JOB.format(pipeline_id=pipeline_id, status=status))
        return
    for index, job in enumerate(jobs):
        job_id = _integer_id(item=job, operation_id=OP_LIST_JOBS)
        if index:
            _write_line(text="")
        _write_trace(
            job_id=job_id,
            name=str(job.get(FIELD_NAME) or ""),
            trace=_trace(transport=transport, project=project, job_id=job_id),
        )


def wait_pipeline(
    *, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace
) -> Optional[int]:
    """``pipeline wait <pipeline_id> [--timeout-seconds N]``: ``pipeline_wait``'s exit code."""
    return pipeline_wait(
        transport=transport, project=project, pipeline_id=args.pipeline_id, timeout_seconds=args.timeout_seconds
    )


# --- The argv group -----------------------------------------------------------------------------------------------


def _count(text: str) -> int:
    """``--count``: an integer from ``MIN_COUNT`` to ``MAX_PER_PAGE``, the most one page holds (conventions.md
    "Offset-based"); another value is a usage error (exit 2). argparse passes the text positionally."""
    try:
        count = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
    if not MIN_COUNT <= count <= MAX_PER_PAGE:
        raise argparse.ArgumentTypeError(f"{count} is not from {MIN_COUNT} to {MAX_PER_PAGE}")
    return count


def register(subparsers: SubParsers) -> None:
    """Add the ``pipeline`` group and its subcommands to the entry script's top-level ``subparsers``."""
    group = add_group(subparsers=subparsers, name=GROUP, help_text="GitLab CI/CD pipelines: read, log and wait on them")
    status = add_command(
        subparsers=group, name="status", handler=status_pipelines, help_text="print the newest pipelines"
    )
    status.add_argument(
        "--count",
        type=_count,
        default=DEFAULT_COUNT,
        help=f"how many (default {DEFAULT_COUNT}, at most {MAX_PER_PAGE})",
    )
    add_command(
        subparsers=group,
        name="log",
        handler=log_pipeline,
        help_text="print the traces of the latest pipeline's failed jobs",
    )
    wait = add_command(
        subparsers=group,
        name="wait",
        handler=wait_pipeline,
        help_text="block until the pipeline is terminal: exit 0 success, 10 not success, 11 timeout (re-issue)",
    )
    wait.add_argument("pipeline_id", type=int, help="the pipeline's id")
    wait.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"the bounded wait (default {DEFAULT_TIMEOUT_SECONDS}); re-issue while it exits {EXIT_WAIT_TIMEOUT}",
    )
