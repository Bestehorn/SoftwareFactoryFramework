"""The pull-request subcommands of the GitHub wrapper (design D5): ``create-pr``, ``get-pr``, ``get-pr-checks``,
``approve-pr``, ``merge-pr`` and ``delete-remote-branch``.

``register`` adds each subcommand with the fork's arguments — its ``_register_pr_subcommands``, names, types,
defaults, choices and required flags as it defines them, without ``--token-stdin`` (UB-1.1) — under argparse's default
``allow_abbrev``. Each subparser carries its handler as ``handler``, which the entry script calls as
``handler(transport=..., owner=..., repo=..., args=...)`` (D6). A handler sends the fork handler's requests on the
records of ``github_api/families/pulls.py``, ``checks.py``, ``repos.py`` and ``git.py`` through ``github_api.registry``
and writes the fork handler's standard output. The REST endpoints, one request each and none of them paged:

- ``create-pr``: ``POST /repos/{owner}/{repo}/pulls`` (``pulls/create``) with ``title`` (``--title``, else the head
  branch), ``head``, ``base`` (``--base``, default ``main``) and ``body`` (``--body`` or ``--body-file``, left out when
  empty); the created pull request echoed as indented JSON.
- ``get-pr``: ``GET /repos/{owner}/{repo}/pulls/{pull_number}`` (``pulls/get``), echoed as indented JSON.
- ``get-pr-checks``: ``pulls/get`` for the head commit, then ``GET /repos/{owner}/{repo}/commits/{ref}/check-runs``
  with ``per_page`` ``GITHUB_MAX_PER_PAGE`` (``checks/list-for-ref``, its first page only) and
  ``GET /repos/{owner}/{repo}/commits/{ref}/status`` with no query (``repos/get-combined-status-for-ref``, its first
  page only); one indented JSON summary of the head SHA, the mergeability, the combined status, each check run and each
  legacy commit status.
- ``approve-pr``: ``POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews`` (``pulls/create-review``) with ``event``
  ``APPROVE`` and the ``--body`` comment when it is not empty; the review echoed as indented JSON. GitHub forbids
  approving your own PR; on that 422 the orchestrator falls back to polling for an external approval (see
  issue-work-orchestrator).
- ``merge-pr``: ``PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge`` (``pulls/merge``) with ``merge_method``
  (``--method``, default ``merge``) and the ``--commit-message`` when it is not empty; the answer echoed as indented
  JSON. It serves ``"merge": "direct"`` projects; under the merge steward no agent merges.
- ``delete-remote-branch``: ``DELETE /repos/{owner}/{repo}/git/refs/heads/{branch}`` (``git/delete-ref``, whose
  ``ref`` is multi-segment, so a branch name keeps its ``/``); one ``Deleted remote branch: <branch>`` line.

Every error answer raises ``GitHubAPIError`` (exit 1), the own-PR approval's 422 included.
"""

from __future__ import annotations

import argparse
from typing import Any, Callable, Dict, Mapping, Optional

from github_api import registry
from github_api.commands._common import (
    FIELD_BODY,
    FIELD_CONCLUSION,
    FIELD_NAME,
    FIELD_STATE,
    FIELD_STATUS,
    FIELD_TITLE,
    add_body_arguments,
    print_json,
    print_line,
    resolve_body,
)
from github_api.transport import Transport

#: What a subparser's ``handler`` is: called with ``transport``, ``owner``, ``repo`` and ``args``; returns ``None`` or
#: an exit code (D6).
Handler = Callable[..., Optional[int]]

OP_PULLS_CREATE = "pulls/create"
OP_PULLS_GET = "pulls/get"
OP_PULLS_CREATE_REVIEW = "pulls/create-review"
OP_PULLS_MERGE = "pulls/merge"
OP_CHECKS_LIST_FOR_REF = "checks/list-for-ref"
OP_COMBINED_STATUS_FOR_REF = "repos/get-combined-status-for-ref"
OP_GIT_DELETE_REF = "git/delete-ref"

PATH_OWNER = "owner"
PATH_REPO = "repo"
PATH_PULL_NUMBER = "pull_number"
PATH_REF = "ref"

QUERY_PER_PAGE = "per_page"
GITHUB_MAX_PER_PAGE = 100  # GitHub REST caps per_page at 100 (the fork's constant)

# The fork's field names that only the pull-request commands read or write.
FIELD_HEAD = "head"
FIELD_BASE = "base"
FIELD_SHA = "sha"
FIELD_MERGEABLE = "mergeable"
FIELD_MERGEABLE_STATE = "mergeable_state"
FIELD_COMBINED_STATUS = "combined_status"
FIELD_CHECK_RUNS = "check_runs"
FIELD_STATUSES = "statuses"
FIELD_CONTEXT = "context"
FIELD_DESCRIPTION = "description"
FIELD_EVENT = "event"
FIELD_MERGE_METHOD = "merge_method"
FIELD_COMMIT_MESSAGE = "commit_message"

REVIEW_EVENT_APPROVE = "APPROVE"
BASE_DEFAULT = "main"
MERGE_METHOD_MERGE = "merge"
MERGE_METHOD_SQUASH = "squash"
MERGE_METHOD_REBASE = "rebase"
MERGE_METHODS = [MERGE_METHOD_MERGE, MERGE_METHOD_SQUASH, MERGE_METHOD_REBASE]
#: A branch's reference below ``refs/``, as ``git/delete-ref`` takes it.
BRANCH_REF_PREFIX = "heads/"
DELETED_BRANCH_LINE = "Deleted remote branch: {branch}"

CMD_CREATE_PR = "create-pr"
CMD_GET_PR = "get-pr"
CMD_GET_PR_CHECKS = "get-pr-checks"
CMD_APPROVE_PR = "approve-pr"
CMD_MERGE_PR = "merge-pr"
CMD_DELETE_REMOTE_BRANCH = "delete-remote-branch"

ARG_PR_NUMBER = "pr_number"
ARG_BRANCH = "branch"
OPTION_HEAD = "--head"
OPTION_BASE = "--base"
OPTION_TITLE = "--title"
OPTION_BODY = "--body"
OPTION_METHOD = "--method"
OPTION_COMMIT_MESSAGE = "--commit-message"


def _repository_params(*, owner: str, repo: str) -> Dict[str, Any]:
    """The path parameters of a repository-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo}


def _pull_params(*, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
    """The path parameters of a pull-request-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo, PATH_PULL_NUMBER: pull_number}


def _ref_params(*, owner: str, repo: str, ref: str) -> Dict[str, Any]:
    """The path parameters of a record addressed by a git reference (``ref`` multi-segment in each such record)."""
    return {PATH_OWNER: owner, PATH_REPO: repo, PATH_REF: ref}


def cmd_create_pr(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Open a pull request of ``--head`` into ``--base``, titled ``--title`` or else the head branch, with the body when
    it is not empty; print the created pull request."""
    payload: Dict[str, Any] = {
        FIELD_TITLE: args.title or args.head,
        FIELD_HEAD: args.head,
        FIELD_BASE: args.base,
    }
    resolved_body = resolve_body(args=args)
    if resolved_body:
        payload[FIELD_BODY] = resolved_body
    data = registry.call(
        transport=transport,
        operation_id=OP_PULLS_CREATE,
        path_params=_repository_params(owner=owner, repo=repo),
        body=payload,
    )
    print_json(value=data)


def cmd_get_pr(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the pull request as indented JSON."""
    data = registry.call(
        transport=transport,
        operation_id=OP_PULLS_GET,
        path_params=_pull_params(owner=owner, repo=repo, pull_number=args.pr_number),
    )
    print_json(value=data)


def _check_run_summary(*, run: Mapping[str, Any]) -> Dict[str, Any]:
    """One check run as the fork's summary lists it: its name, status and conclusion."""
    return {FIELD_NAME: run[FIELD_NAME], FIELD_STATUS: run[FIELD_STATUS], FIELD_CONCLUSION: run.get(FIELD_CONCLUSION)}


def _status_summary(*, status: Mapping[str, Any]) -> Dict[str, Any]:
    """One legacy commit status as the fork's summary lists it: its context, state and description."""
    return {
        FIELD_CONTEXT: status[FIELD_CONTEXT],
        FIELD_STATE: status[FIELD_STATE],
        FIELD_DESCRIPTION: status.get(FIELD_DESCRIPTION),
    }


def cmd_get_pr_checks(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the combined CI state of the pull request's head commit: the Checks API's check runs (one page of
    ``GITHUB_MAX_PER_PAGE``) beside the legacy commit-status API's combined state and statuses, as the fork reads
    them; the orchestrator polls this to decide when CI is green."""
    pull = registry.call(
        transport=transport,
        operation_id=OP_PULLS_GET,
        path_params=_pull_params(owner=owner, repo=repo, pull_number=args.pr_number),
    )
    head_sha = pull[FIELD_HEAD][FIELD_SHA]
    ref_params = _ref_params(owner=owner, repo=repo, ref=head_sha)
    check_runs = registry.call(
        transport=transport,
        operation_id=OP_CHECKS_LIST_FOR_REF,
        path_params=ref_params,
        query={QUERY_PER_PAGE: GITHUB_MAX_PER_PAGE},
    )
    combined = registry.call(transport=transport, operation_id=OP_COMBINED_STATUS_FOR_REF, path_params=ref_params)
    summary = {
        FIELD_HEAD: head_sha,
        FIELD_MERGEABLE: pull.get(FIELD_MERGEABLE),
        FIELD_MERGEABLE_STATE: pull.get(FIELD_MERGEABLE_STATE),
        FIELD_COMBINED_STATUS: combined.get(FIELD_STATE),
        FIELD_CHECK_RUNS: [_check_run_summary(run=run) for run in check_runs.get(FIELD_CHECK_RUNS, [])],
        FIELD_STATUSES: [_status_summary(status=status) for status in combined.get(FIELD_STATUSES, [])],
    }
    print_json(value=summary)


def cmd_approve_pr(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Submit an APPROVE review on the pull request, with the ``--body`` comment when it is not empty; print the review.

    GitHub forbids approving your own PR; on that 422 the orchestrator falls back to polling for an external approval
    (see issue-work-orchestrator).
    """
    payload: Dict[str, Any] = {FIELD_EVENT: REVIEW_EVENT_APPROVE}
    if args.body:
        payload[FIELD_BODY] = args.body
    data = registry.call(
        transport=transport,
        operation_id=OP_PULLS_CREATE_REVIEW,
        path_params=_pull_params(owner=owner, repo=repo, pull_number=args.pr_number),
        body=payload,
    )
    print_json(value=data)


def cmd_merge_pr(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Merge the pull request by ``--method``, with the ``--commit-message`` when it is not empty; print the answer."""
    payload: Dict[str, Any] = {FIELD_MERGE_METHOD: args.method}
    if args.commit_message:
        payload[FIELD_COMMIT_MESSAGE] = args.commit_message
    data = registry.call(
        transport=transport,
        operation_id=OP_PULLS_MERGE,
        path_params=_pull_params(owner=owner, repo=repo, pull_number=args.pr_number),
        body=payload,
    )
    print_json(value=data)


def cmd_delete_remote_branch(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Delete the branch's reference on the remote, its ``/`` kept, and print one confirming line."""
    registry.call(
        transport=transport,
        operation_id=OP_GIT_DELETE_REF,
        path_params=_ref_params(owner=owner, repo=repo, ref=f"{BRANCH_REF_PREFIX}{args.branch}"),
    )
    print_line(text=DELETED_BRANCH_LINE.format(branch=args.branch))


def _add_command(
    *, subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str, help_text: str, handler: Handler
) -> argparse.ArgumentParser:
    """The subparser ``name`` with the fork's help text, carrying ``handler`` as ``handler`` (D6)."""
    parser = subparsers.add_parser(name=name, help=help_text)
    parser.set_defaults(handler=handler)
    return parser


def _register_lifecycle(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``create-pr``, ``get-pr`` and ``get-pr-checks``, as the fork's ``_register_pr_subcommands``."""
    parser = _add_command(
        subparsers=subparsers, name=CMD_CREATE_PR, help_text="Create a pull request", handler=cmd_create_pr
    )
    parser.add_argument(OPTION_HEAD, required=True)
    parser.add_argument(OPTION_BASE, default=BASE_DEFAULT)
    parser.add_argument(OPTION_TITLE)
    add_body_arguments(parser=parser)

    parser = _add_command(
        subparsers=subparsers, name=CMD_GET_PR, help_text="Show a single pull request", handler=cmd_get_pr
    )
    parser.add_argument(ARG_PR_NUMBER, type=int)

    parser = _add_command(
        subparsers=subparsers,
        name=CMD_GET_PR_CHECKS,
        help_text="Show combined CI check state for a PR's head commit",
        handler=cmd_get_pr_checks,
    )
    parser.add_argument(ARG_PR_NUMBER, type=int)


def _register_landing(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``approve-pr``, ``merge-pr`` and ``delete-remote-branch``, as the fork's ``_register_pr_subcommands``."""
    parser = _add_command(
        subparsers=subparsers,
        name=CMD_APPROVE_PR,
        help_text="Submit an APPROVE review on a PR",
        handler=cmd_approve_pr,
    )
    parser.add_argument(ARG_PR_NUMBER, type=int)
    parser.add_argument(OPTION_BODY, help="Optional review comment")

    parser = _add_command(
        subparsers=subparsers, name=CMD_MERGE_PR, help_text="Merge a pull request", handler=cmd_merge_pr
    )
    parser.add_argument(ARG_PR_NUMBER, type=int)
    parser.add_argument(OPTION_METHOD, default=MERGE_METHOD_MERGE, choices=MERGE_METHODS)
    parser.add_argument(OPTION_COMMIT_MESSAGE, help="Optional merge commit message")

    parser = _add_command(
        subparsers=subparsers,
        name=CMD_DELETE_REMOTE_BRANCH,
        help_text="Delete a remote branch",
        handler=cmd_delete_remote_branch,
    )
    parser.add_argument(ARG_BRANCH, help="Branch name (without refs/heads/)")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add the pull-request subcommands to the entry script's ``subparsers``, each carrying its handler (D6)."""
    _register_lifecycle(subparsers=subparsers)
    _register_landing(subparsers=subparsers)
