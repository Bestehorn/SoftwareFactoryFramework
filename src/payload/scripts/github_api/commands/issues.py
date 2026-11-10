"""The issues subcommands of the GitHub wrapper (design D5): ``list-issues``, ``get-issue``, ``get-issue-comments``,
``comment-issue``, ``create-issue``, ``update-issue``, ``reopen-issue`` and ``checklist``.

``register`` adds each subcommand with the fork's arguments — its ``_register_issue_subcommands`` and
``_register_wait_and_task_item_subcommands``, names, types, defaults, choices, required flags and the ``checklist``
group as they define them, without ``--token-stdin`` (UB-1.1) — under argparse's default ``allow_abbrev``, so
``list-issues --label`` resolves to ``--labels``. Each subparser carries its handler as ``handler``, which the entry
script calls as ``handler(transport=..., owner=..., repo=..., args=...)`` (D6). A handler sends the fork handler's
requests on the ``issues`` family's records (``github_api/families/issues.py``) through ``github_api.registry`` and
writes the fork handler's standard output:

- ``list-issues``: pages of ``issues/list-for-repo`` with ``per_page`` ``GITHUB_MAX_PER_PAGE``, followed by ``link``;
  pull requests left out and not counted; stops at ``--limit``; one ``#<number> <state> <title>`` line per issue.
- ``get-issue``: ``issues/get``; ``get-issue-comments``: every page of ``issues/list-comments``, as one JSON list.
- ``comment-issue``, ``create-issue``, ``update-issue``: ``issues/create-comment``, ``issues/create``,
  ``issues/update``, the response echoed as indented JSON.
- ``reopen-issue``: ``issues/get``; unless the issue is open, ``issues/update`` and a verifying ``issues/get``.
  ``checklist``: ``issues/get``; for ``--tick``/``--untick``, ``issues/update`` and a verifying ``issues/get``. Each
  prints a one-line JSON verdict.

The one deviation, invisible on standard output (D5): the two lists follow ``link`` instead of the fork's ``page=``
loop and short-page stop, giving the same items in the same order. Every refusal raises ``GitHubAPIError`` (exit 1).
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from github_api import registry
from github_api.commands._common import (
    FIELD_BODY,
    FIELD_LABELS,
    FIELD_NUMBER,
    FIELD_STATE,
    FIELD_TITLE,
    add_body_arguments,
    print_compact_json,
    print_json,
    print_line,
    resolve_body,
)
from github_api.errors import GitHubAPIError
from github_api.transport import Transport

#: What a subparser's ``handler`` is: called with ``transport``, ``owner``, ``repo`` and ``args``; returns ``None`` or
#: an exit code (D6).
Handler = Callable[..., Optional[int]]

OP_LIST_FOR_REPO = "issues/list-for-repo"
OP_GET = "issues/get"
OP_LIST_COMMENTS = "issues/list-comments"
OP_CREATE_COMMENT = "issues/create-comment"
OP_CREATE = "issues/create"
OP_UPDATE = "issues/update"

PATH_OWNER = "owner"
PATH_REPO = "repo"
PATH_ISSUE_NUMBER = "issue_number"

QUERY_STATE = "state"
QUERY_LABELS = "labels"
QUERY_ASSIGNEE = "assignee"
QUERY_PER_PAGE = "per_page"
GITHUB_MAX_PER_PAGE = 100  # GitHub REST caps per_page at 100 (the fork's constant)

FIELD_PULL_REQUEST = "pull_request"
ISSUE_STATE_OPEN = "open"
ISSUE_STATE_CLOSED = "closed"
ISSUE_STATE_ALL = "all"
LIST_STATES = [ISSUE_STATE_OPEN, ISSUE_STATE_CLOSED, ISSUE_STATE_ALL]
UPDATE_STATES = [ISSUE_STATE_OPEN, ISSUE_STATE_CLOSED]
LIST_LIMIT_DEFAULT = 30
LABEL_SEPARATOR = ","

KEY_ISSUE = "issue"
KEY_ITEM = "item"
KEY_CHANGED = "changed"
KEY_TICKED = "ticked"
KEY_TOTAL = "total"
KEY_UNTICKED = "unticked"

#: A task-list line (the fork's ``CHECKLIST_ITEM_RE``); a line ending is not part of a match.
CHECKLIST_ITEM_RE = re.compile(r"^(?P<lead>\s*[-*]\s+\[)(?P<mark>[ xX])(?P<tail>\]\s+)(?P<text>.*?)\s*$")
GROUP_LEAD = "lead"
GROUP_MARK = "mark"
GROUP_TAIL = "tail"
GROUP_TEXT = "text"
CHECK_MARK_TICKED = "x"
CHECK_MARK_UNTICKED = " "
LINE_SEPARATOR = "\n"
CARRIAGE_RETURN = "\r"

CMD_LIST_ISSUES = "list-issues"
CMD_GET_ISSUE = "get-issue"
CMD_GET_ISSUE_COMMENTS = "get-issue-comments"
CMD_COMMENT_ISSUE = "comment-issue"
CMD_CREATE_ISSUE = "create-issue"
CMD_UPDATE_ISSUE = "update-issue"
CMD_REOPEN_ISSUE = "reopen-issue"
CMD_CHECKLIST = "checklist"

ARG_ISSUE_NUMBER = "issue_number"
OPTION_STATE = "--state"
OPTION_LABELS = "--labels"
OPTION_ASSIGNEE = "--assignee"
OPTION_LIMIT = "--limit"
OPTION_TITLE = "--title"
OPTION_TICK = "--tick"
OPTION_UNTICK = "--untick"


def _repository_params(*, owner: str, repo: str) -> Dict[str, Any]:
    """The path parameters of a repository-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo}


def _issue_params(*, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """The path parameters of an issue-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo, PATH_ISSUE_NUMBER: issue_number}


def _label_names(*, text: str) -> List[str]:
    """The comma-separated ``--labels`` value as the fork splits it: each name stripped, empty names dropped."""
    return [name.strip() for name in text.split(sep=LABEL_SEPARATOR) if name.strip()]


def _read_issue(*, transport: Transport, path_params: Mapping[str, Any]) -> Dict[str, Any]:
    """One fresh read of the issue (``issues/get``); a response that is not a JSON object raises ``GitHubAPIError``."""
    issue = registry.call(transport=transport, operation_id=OP_GET, path_params=path_params)
    if not isinstance(issue, dict):
        raise GitHubAPIError(
            message=f"Unexpected issue payload for #{path_params[PATH_ISSUE_NUMBER]}: not a JSON object.",
            details=issue,
        )
    return issue


def _issue_line(*, issue: Mapping[str, Any]) -> str:
    """The fork's ``list-issues`` line of one issue."""
    return f"#{issue[FIELD_NUMBER]:<6} {issue[FIELD_STATE]:<8} {issue[FIELD_TITLE]}"


def cmd_list_issues(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print up to ``--limit`` issues, one line each; pull requests are left out and do not count toward the limit, so
    the pages are read until ``--limit`` issues are printed or the list ends. ``per_page`` stays constant across
    pages, as the fork keeps it."""
    if args.limit <= 0:
        return
    query: Dict[str, Any] = {QUERY_STATE: args.state, QUERY_PER_PAGE: GITHUB_MAX_PER_PAGE}
    if args.labels:
        query[QUERY_LABELS] = args.labels
    if args.assignee:
        query[QUERY_ASSIGNEE] = args.assignee
    printed = 0
    for issue in registry.pages(
        transport=transport,
        operation_id=OP_LIST_FOR_REPO,
        path_params=_repository_params(owner=owner, repo=repo),
        query=query,
    ):
        if FIELD_PULL_REQUEST in issue:
            continue
        print_line(text=_issue_line(issue=issue))
        printed += 1
        if printed >= args.limit:
            break


def cmd_get_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the issue as indented JSON."""
    data = registry.call(
        transport=transport,
        operation_id=OP_GET,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=args.issue_number),
    )
    print_json(value=data)


def cmd_get_issue_comments(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print every comment of the issue as one indented JSON list, every page read."""
    comments = list(
        registry.pages(
            transport=transport,
            operation_id=OP_LIST_COMMENTS,
            path_params=_issue_params(owner=owner, repo=repo, issue_number=args.issue_number),
            query={QUERY_PER_PAGE: GITHUB_MAX_PER_PAGE},
        )
    )
    print_json(value=comments)


def cmd_comment_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Post ``--body`` or ``--body-file`` as a comment and print the created comment."""
    body = resolve_body(args=args)
    if body is None:
        raise GitHubAPIError(message=f"{CMD_COMMENT_ISSUE} requires --body or --body-file")
    data = registry.call(
        transport=transport,
        operation_id=OP_CREATE_COMMENT,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=args.issue_number),
        body={FIELD_BODY: body},
    )
    print_json(value=data)


def cmd_create_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Create an issue with ``--title``, the body when it is not empty and the labels when given; print it."""
    payload: Dict[str, Any] = {FIELD_TITLE: args.title}
    resolved_body = resolve_body(args=args)
    if resolved_body:
        payload[FIELD_BODY] = resolved_body
    if args.labels:
        payload[FIELD_LABELS] = _label_names(text=args.labels)
    data = registry.call(
        transport=transport,
        operation_id=OP_CREATE,
        path_params=_repository_params(owner=owner, repo=repo),
        body=payload,
    )
    print_json(value=data)


def cmd_update_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Update the fields given (``--labels`` replaces the whole set) and print the issue; nothing given raises."""
    payload: Dict[str, Any] = {}
    resolved_body = resolve_body(args=args)
    if args.title is not None:
        payload[FIELD_TITLE] = args.title
    if resolved_body is not None:
        payload[FIELD_BODY] = resolved_body
    if args.state is not None:
        payload[FIELD_STATE] = args.state
    if args.labels is not None:
        payload[FIELD_LABELS] = _label_names(text=args.labels)
    if not payload:
        raise GitHubAPIError(
            message=f"{CMD_UPDATE_ISSUE} requires at least one of --title, --body/--body-file, --state, --labels"
        )
    data = registry.call(
        transport=transport,
        operation_id=OP_UPDATE,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=args.issue_number),
        body=payload,
    )
    print_json(value=data)


def cmd_reopen_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Reopen the issue, then re-read it and raise unless it now reads ``open``; an open issue is reported and not
    written (idempotent)."""
    path_params = _issue_params(owner=owner, repo=repo, issue_number=args.issue_number)
    before = _read_issue(transport=transport, path_params=path_params)
    if before.get(FIELD_STATE) == ISSUE_STATE_OPEN:
        print_compact_json(value={KEY_ISSUE: args.issue_number, FIELD_STATE: ISSUE_STATE_OPEN, KEY_CHANGED: False})
        return
    registry.call(
        transport=transport, operation_id=OP_UPDATE, path_params=path_params, body={FIELD_STATE: ISSUE_STATE_OPEN}
    )
    after = _read_issue(transport=transport, path_params=path_params)
    if after.get(FIELD_STATE) != ISSUE_STATE_OPEN:
        raise GitHubAPIError(
            message=(
                f"issue #{args.issue_number} still reads state={json.dumps(obj=after.get(FIELD_STATE))} "
                "after the reopen PATCH"
            )
        )
    print_compact_json(value={KEY_ISSUE: args.issue_number, FIELD_STATE: ISSUE_STATE_OPEN, KEY_CHANGED: True})


def _checklist_items(*, body: str) -> List[Tuple[int, re.Match[str]]]:
    """Every task-list line of ``body`` as ``(line index, match)``; line endings are not part of a match."""
    items: List[Tuple[int, re.Match[str]]] = []
    for index, line in enumerate(body.split(sep=LINE_SEPARATOR)):
        match = CHECKLIST_ITEM_RE.match(string=line.rstrip(CARRIAGE_RETURN))
        if match is not None:
            items.append((index, match))
    return items


def _checklist_counts(*, body: str) -> Dict[str, Any]:
    """The ticked count, the total and the unticked items' text of ``body``'s task list."""
    items = _checklist_items(body=body)
    unticked = [match.group(GROUP_TEXT) for _, match in items if match.group(GROUP_MARK) == CHECK_MARK_UNTICKED]
    return {KEY_TICKED: len(items) - len(unticked), KEY_TOTAL: len(items), KEY_UNTICKED: unticked}


def _flip_checklist_item(*, body: str, needle: str, to_mark: str) -> str:
    """``body`` with exactly ONE item containing ``needle`` flipped to ``to_mark``, its line ending kept. Only items in
    the other state are candidates; zero or several candidates raise ``GitHubAPIError``, naming them."""
    from_ticked = to_mark == CHECK_MARK_UNTICKED
    candidates = [
        (index, match)
        for index, match in _checklist_items(body=body)
        if needle in match.group(GROUP_TEXT) and (match.group(GROUP_MARK) != CHECK_MARK_UNTICKED) == from_ticked
    ]
    if len(candidates) != 1:
        names = [match.group(GROUP_TEXT) for _, match in candidates]
        raise GitHubAPIError(
            message=(
                f"{OPTION_TICK}/{OPTION_UNTICK} {json.dumps(obj=needle)} must match exactly one item; "
                f"matched {json.dumps(obj=names)}"
            )
        )
    index, match = candidates[0]
    lines = body.split(sep=LINE_SEPARATOR)
    ending = CARRIAGE_RETURN if lines[index].endswith(CARRIAGE_RETURN) else ""
    lead, tail, text = match.group(GROUP_LEAD), match.group(GROUP_TAIL), match.group(GROUP_TEXT)
    lines[index] = f"{lead}{to_mark}{tail}{text}{ending}"
    return LINE_SEPARATOR.join(lines)


def _issue_body(*, issue: Mapping[str, Any]) -> str:
    """The issue's body as the fork reads it: an absent or empty body is the empty string."""
    return str(issue.get(FIELD_BODY) or "")


def cmd_checklist(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Without an action, print the task list's ticked count, total and unticked items from a fresh read; with
    ``--tick``/``--untick``, flip ONE item by substring, write the body, and raise unless a re-read returns it."""
    path_params = _issue_params(owner=owner, repo=repo, issue_number=args.issue_number)
    body = _issue_body(issue=_read_issue(transport=transport, path_params=path_params))
    needle = args.tick if args.tick is not None else args.untick
    if needle is None:
        print_compact_json(value={KEY_ISSUE: args.issue_number, **_checklist_counts(body=body)})
        return
    to_mark = CHECK_MARK_TICKED if args.tick is not None else CHECK_MARK_UNTICKED
    new_body = _flip_checklist_item(body=body, needle=needle, to_mark=to_mark)
    registry.call(transport=transport, operation_id=OP_UPDATE, path_params=path_params, body={FIELD_BODY: new_body})
    reread = _issue_body(issue=_read_issue(transport=transport, path_params=path_params))
    if reread != new_body:
        raise GitHubAPIError(
            message=f"issue #{args.issue_number}: the checklist write did not land (body differs on re-read)"
        )
    print_compact_json(value={KEY_ISSUE: args.issue_number, KEY_ITEM: needle, **_checklist_counts(body=reread)})


def _add_command(
    *, subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str, help_text: str, handler: Handler
) -> argparse.ArgumentParser:
    """The subparser ``name`` with the fork's help text, carrying ``handler`` as ``handler`` (D6)."""
    parser = subparsers.add_parser(name=name, help=help_text)
    parser.set_defaults(handler=handler)
    return parser


def _register_reads(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``list-issues``, ``get-issue`` and ``get-issue-comments``, as the fork's ``_register_issue_subcommands``."""
    parser = _add_command(subparsers=subparsers, name=CMD_LIST_ISSUES, help_text="List issues", handler=cmd_list_issues)
    parser.add_argument(OPTION_STATE, default=ISSUE_STATE_OPEN, choices=LIST_STATES)
    parser.add_argument(OPTION_LABELS, help="Comma-separated label names")
    parser.add_argument(OPTION_ASSIGNEE, help="Filter by assignee login, or '*' (any) / 'none'")
    parser.add_argument(OPTION_LIMIT, type=int, default=LIST_LIMIT_DEFAULT)

    parser = _add_command(
        subparsers=subparsers, name=CMD_GET_ISSUE, help_text="Show a single issue", handler=cmd_get_issue
    )
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)

    parser = _add_command(
        subparsers=subparsers,
        name=CMD_GET_ISSUE_COMMENTS,
        help_text="List comments on an issue",
        handler=cmd_get_issue_comments,
    )
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)


def _register_writes(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``comment-issue``, ``update-issue`` and ``create-issue``, as the fork's ``_register_issue_subcommands``."""
    parser = _add_command(
        subparsers=subparsers,
        name=CMD_COMMENT_ISSUE,
        help_text="Add a comment to an issue",
        handler=cmd_comment_issue,
    )
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)
    add_body_arguments(parser=parser)

    parser = _add_command(
        subparsers=subparsers, name=CMD_UPDATE_ISSUE, help_text="Update an issue", handler=cmd_update_issue
    )
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)
    parser.add_argument(OPTION_TITLE)
    add_body_arguments(parser=parser)
    parser.add_argument(OPTION_STATE, choices=UPDATE_STATES)
    parser.add_argument(OPTION_LABELS, help="Comma-separated label names (replaces existing)")

    parser = _add_command(
        subparsers=subparsers, name=CMD_CREATE_ISSUE, help_text="Create a new issue", handler=cmd_create_issue
    )
    parser.add_argument(OPTION_TITLE, required=True)
    add_body_arguments(parser=parser)
    parser.add_argument(OPTION_LABELS, help="Comma-separated label names")


def _register_verified(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """``reopen-issue`` and ``checklist``, as the fork's ``_register_wait_and_task_item_subcommands``."""
    parser = _add_command(
        subparsers=subparsers,
        name=CMD_REOPEN_ISSUE,
        help_text="Reopen an issue, then re-read and verify it is open (idempotent)",
        handler=cmd_reopen_issue,
    )
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)

    parser = _add_command(
        subparsers=subparsers,
        name=CMD_CHECKLIST,
        help_text="Count an issue's task list (ticked/total + unticked items), or tick/untick ONE item, verified",
        handler=cmd_checklist,
    )
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)
    action = parser.add_mutually_exclusive_group()
    action.add_argument(OPTION_TICK, help="Tick the ONE unticked item whose text contains this substring")
    action.add_argument(OPTION_UNTICK, help="Untick the ONE ticked item whose text contains this substring")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add the issues subcommands to the entry script's ``subparsers``, each carrying its handler (D6)."""
    _register_reads(subparsers=subparsers)
    _register_writes(subparsers=subparsers)
    _register_verified(subparsers=subparsers)
