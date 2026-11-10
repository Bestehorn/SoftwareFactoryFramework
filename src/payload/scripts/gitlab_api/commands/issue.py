"""The ``issue`` subcommands of the GitLab wrapper (issue #13, design.md D6; UB-1)::

    issue list [--state opened|closed|all] [--assignee <username>|"*"|none] [--labels L]   every page
    issue show <iid>
    issue create --title T [--description D] [--labels L]
    issue comment <iid> --body B
    issue start <iid>          the in-progress claim, verified by a re-read: exit 0 when it took, 1 otherwise
    issue claim-check <iid>    read only: exit 0 when claimed or not open, 3 when open and unclaimed
    issue release <iid>        the claim dropped: the in-progress label removed, every assignee unassigned
    issue label-add <iid> --labels L / issue label-remove <iid> --labels L   additive; never the replacing `labels`
    issue assign <iid> --me | --user <username> | --unassign
    issue close <iid>
    issue reopen <iid>         exit 0 also for an issue already open, which is printed and not changed

Each handler composes records by id through ``gitlab_api.registry``: the ``plan`` family's issue and note records and
the ``software-supply-chain-security`` family's ``GET /user`` and ``GET /users``. A body goes as JSON, so
``assignee_ids`` is an integer array in which ``0`` unassigns (``rest/plan.md`` "Update an issue"). The label a claim
adds and verifies is the configured ``in_progress_label``. Every result is printed as JSON on standard output; a
refused or unconfirmed claim raises ``GitLabClaimError`` and any other failure ``GitLabAPIError``, which the entry
script logs on standard error and exits 1 with.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence

from gitlab_api import registry
from gitlab_api.commands._common import (
    FIELD_DESCRIPTION,
    FIELD_ID,
    FIELD_TITLE,
    PATH_PROJECT,
    add_command,
    add_group,
    add_iid,
    print_json,
)
from gitlab_api.errors import GitLabAPIError, GitLabClaimError

if TYPE_CHECKING:
    from gitlab_api.commands._common import SubParsers
    from gitlab_api.transport import Transport

GROUP = "issue"

# The records the handlers compose (design.md D6).
OP_LIST_ISSUES = "plan#list-all-project-issues"
OP_SHOW_ISSUE = "plan#retrieve-a-project-issue"
OP_CREATE_ISSUE = "plan#create-an-issue"
OP_CREATE_NOTE = "plan#create-an-issue-note"
OP_UPDATE_ISSUE = "plan#update-an-issue"
OP_CURRENT_USER = "software-supply-chain-security#as-a-regular-user-1"
OP_LIST_USERS = "software-supply-chain-security#as-a-regular-user"

# The `:issue_iid` path parameter of the issue records.
PATH_ISSUE_IID = "issue_iid"

# Request and response keys only this module reads or sends (rest/plan.md "Issues API" and "Notes API",
# rest/software-supply-chain-security.md "Users API") and the keys of `claim-check`'s output.
FIELD_IID = "iid"
FIELD_STATE = "state"
FIELD_LABELS = "labels"
FIELD_ASSIGNEE = "assignee"
FIELD_ASSIGNEES = "assignees"
FIELD_ASSIGNEE_ID = "assignee_id"
FIELD_ASSIGNEE_USERNAME = "assignee_username"
FIELD_ASSIGNEE_IDS = "assignee_ids"
FIELD_ADD_LABELS = "add_labels"
FIELD_REMOVE_LABELS = "remove_labels"
FIELD_STATE_EVENT = "state_event"
FIELD_BODY = "body"
FIELD_USERNAME = "username"
FIELD_CLAIMED = "claimed"

STATE_OPENED = "opened"
STATE_CHOICES = (STATE_OPENED, "closed", "all")
EVENT_CLOSE = "close"
EVENT_REOPEN = "reopen"
# `--assignee` values with a meaning of their own, and the `assignee_id` values they send (rest/plan.md "List all
# project issues": `None` lists the issues with no assignee, `Any` those with one).
ASSIGNEE_ANY = "*"
ASSIGNEE_NONE = "none"
ASSIGNEE_ID_ANY = "Any"
ASSIGNEE_ID_NONE = "None"
# `assignee_ids: [0]` unassigns every assignee (rest/plan.md "Update an issue").
UNASSIGN_ID = 0
# `issue claim-check` on an open issue with neither the in-progress label nor an assignee.
EXIT_CLAIM_UNCLAIMED = 3
LIST_SEPARATOR = ", "
NOTHING_LISTED = "none"


# --- Reading the records' answers ---------------------------------------------------------------------------------


def _issue_path(*, project: str, iid: int) -> Dict[str, Any]:
    """The path values of one issue of the configured project."""
    return {PATH_PROJECT: project, PATH_ISSUE_IID: iid}


def _json_object(*, value: Any, operation_id: str) -> Dict[str, Any]:
    """``value`` when it is a JSON object; another answer raises ``GitLabAPIError`` naming the record."""
    if not isinstance(value, dict):
        raise GitLabAPIError(f"{operation_id} answered {type(value).__name__}, not a JSON object")
    return value


def _read_issue(*, transport: Transport, project: str, iid: int) -> Dict[str, Any]:
    """The issue as ``GET /projects/:id/issues/:issue_iid`` returns it."""
    value = registry.call(transport=transport, operation_id=OP_SHOW_ISSUE, values=_issue_path(project=project, iid=iid))
    return _json_object(value=value, operation_id=OP_SHOW_ISSUE)


def _update_issue(*, transport: Transport, project: str, iid: int, changes: Mapping[str, Any]) -> Any:
    """One ``PUT /projects/:id/issues/:issue_iid`` with ``changes`` as its JSON body; the updated issue."""
    values = {**_issue_path(project=project, iid=iid), **changes}
    return registry.call(transport=transport, operation_id=OP_UPDATE_ISSUE, values=values)


def _labels(*, issue: Mapping[str, Any]) -> List[str]:
    """The issue's label names."""
    labels = issue.get(FIELD_LABELS)
    return [str(label) for label in labels] if isinstance(labels, list) else []


def _assignees(*, issue: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """The issue's assignees: its ``assignees`` list, else its single ``assignee``."""
    people = issue.get(FIELD_ASSIGNEES)
    listed = [person for person in people if isinstance(person, Mapping)] if isinstance(people, list) else []
    if listed:
        return listed
    single = issue.get(FIELD_ASSIGNEE)
    return [single] if isinstance(single, Mapping) else []


def _user_id(*, user: Mapping[str, Any], operation_id: str) -> int:
    """A user's integer ``id``; a user without one raises ``GitLabAPIError`` naming the record."""
    user_id = user.get(FIELD_ID)
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise GitLabAPIError(f"{operation_id} answered a user without an integer {FIELD_ID!r}")
    return user_id


def _username(*, user: Mapping[str, Any]) -> str:
    return str(user.get(FIELD_USERNAME) or user.get(FIELD_ID))


def _listed(*, items: Sequence[str]) -> str:
    return LIST_SEPARATOR.join(items) if items else NOTHING_LISTED


def _current_user(*, transport: Transport) -> Mapping[str, Any]:
    """The token's owner, ``GET /user``."""
    value = registry.call(transport=transport, operation_id=OP_CURRENT_USER)
    return _json_object(value=value, operation_id=OP_CURRENT_USER)


def _named_user_id(*, transport: Transport, username: str) -> int:
    """The ``id`` of the user ``GET /users?username=<username>`` returns; no such user raises ``GitLabAPIError``.

    Only an entry whose ``username`` is the one asked for counts (compared case-insensitively), so an answer that
    lists other users never assigns one of them."""
    value = registry.call(transport=transport, operation_id=OP_LIST_USERS, values={FIELD_USERNAME: username})
    users = value if isinstance(value, list) else []
    wanted = username.casefold()
    for user in users:
        if isinstance(user, Mapping) and str(user.get(FIELD_USERNAME, "")).casefold() == wanted:
            return _user_id(user=user, operation_id=OP_LIST_USERS)
    raise GitLabAPIError(f"no GitLab user has the username {username!r}")


def _assignee_filter(*, assignee: Optional[str]) -> Dict[str, Any]:
    """The query values of ``--assignee``: ``*`` any assignee, ``none`` no assignee, else that username."""
    if assignee is None:
        return {}
    if assignee == ASSIGNEE_ANY:
        return {FIELD_ASSIGNEE_ID: ASSIGNEE_ID_ANY}
    if assignee == ASSIGNEE_NONE:
        return {FIELD_ASSIGNEE_ID: ASSIGNEE_ID_NONE}
    return {FIELD_ASSIGNEE_USERNAME: [assignee]}


# --- The claim ----------------------------------------------------------------------------------------------------


def _refuse_not_open(*, issue: Mapping[str, Any], iid: int) -> None:
    """Raise ``GitLabClaimError`` when the issue is not open."""
    state = issue.get(FIELD_STATE)
    if state != STATE_OPENED:
        raise GitLabClaimError(f"issue #{iid} is {state!r}, not {STATE_OPENED!r}: not claimed, nothing changed")


def _refuse_foreign_assignee(*, issue: Mapping[str, Any], iid: int, me: Mapping[str, Any], me_id: int) -> None:
    """Raise ``GitLabClaimError`` when the issue is assigned to any user other than ``me``."""
    others = [person for person in _assignees(issue=issue) if person.get(FIELD_ID) != me_id]
    if others:
        names = _listed(items=[_username(user=person) for person in others])
        raise GitLabClaimError(
            f"issue #{iid} is assigned to {names}, not to {_username(user=me)}: not claimed, nothing changed"
        )


def _verify_claim(*, issue: Mapping[str, Any], iid: int, me: Mapping[str, Any], me_id: int, label: str) -> None:
    """Raise ``GitLabClaimError`` naming the observed labels and assignees unless the re-read issue carries ``label``
    and has ``me`` among its assignees."""
    labels = _labels(issue=issue)
    assignees = _assignees(issue=issue)
    if label in labels and any(person.get(FIELD_ID) == me_id for person in assignees):
        return
    raise GitLabClaimError(
        f"issue #{iid}: the claim did not take; the re-read shows the labels {_listed(items=labels)} and the "
        f"assignees {_listed(items=[_username(user=person) for person in assignees])}, and a claim needs the label "
        f"{label!r} and the assignee {_username(user=me)}"
    )


# --- The handlers (design.md D6) ----------------------------------------------------------------------------------


def list_issues(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue list``: the issues of every page, filtered by state, assignee and labels."""
    values: Dict[str, Any] = {PATH_PROJECT: project, FIELD_STATE: args.state}
    values.update(_assignee_filter(assignee=args.assignee))
    values[FIELD_LABELS] = args.labels
    print_json(value=list(registry.pages(transport=transport, operation_id=OP_LIST_ISSUES, values=values)))


def show_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue show <iid>``: the issue."""
    print_json(value=_read_issue(transport=transport, project=project, iid=args.iid))


def create_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue create``: the created issue."""
    values = {
        PATH_PROJECT: project,
        FIELD_TITLE: args.title,
        FIELD_DESCRIPTION: args.description,
        FIELD_LABELS: args.labels,
    }
    print_json(value=registry.call(transport=transport, operation_id=OP_CREATE_ISSUE, values=values))


def comment_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue comment <iid> --body B``: the created note."""
    values = {**_issue_path(project=project, iid=args.iid), FIELD_BODY: args.body}
    print_json(value=registry.call(transport=transport, operation_id=OP_CREATE_NOTE, values=values))


def start_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue start <iid>``: read the issue, resolve the token's user, ONE claim ``PUT`` (the in-progress label added,
    the user assigned), then re-read and print the issue only when the claim is confirmed. A closed issue and one
    assigned to another user are refused with no ``PUT``; an unconfirmed claim is refused naming what was observed."""
    issue = _read_issue(transport=transport, project=project, iid=args.iid)
    _refuse_not_open(issue=issue, iid=args.iid)
    me = _current_user(transport=transport)
    me_id = _user_id(user=me, operation_id=OP_CURRENT_USER)
    _refuse_foreign_assignee(issue=issue, iid=args.iid, me=me, me_id=me_id)
    claim = {FIELD_ADD_LABELS: in_progress_label, FIELD_ASSIGNEE_IDS: [me_id]}
    _update_issue(transport=transport, project=project, iid=args.iid, changes=claim)
    verified = _read_issue(transport=transport, project=project, iid=args.iid)
    _verify_claim(issue=verified, iid=args.iid, me=me, me_id=me_id, label=in_progress_label)
    print_json(value=verified)


def claim_check_issue(
    *, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace
) -> Optional[int]:
    """``issue claim-check <iid>``, read only: prints ``{iid, state, claimed}``; ``claimed`` is the in-progress label
    or any assignee being present. Exit 0 when claimed or not open, ``EXIT_CLAIM_UNCLAIMED`` when open and
    unclaimed."""
    issue = _read_issue(transport=transport, project=project, iid=args.iid)
    state = issue.get(FIELD_STATE)
    claimed = in_progress_label in _labels(issue=issue) or bool(_assignees(issue=issue))
    print_json(value={FIELD_IID: args.iid, FIELD_STATE: state, FIELD_CLAIMED: claimed})
    if state == STATE_OPENED and not claimed:
        return EXIT_CLAIM_UNCLAIMED
    return None


def release_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue release <iid>``: the in-progress label removed and every assignee unassigned; the issue."""
    changes = {FIELD_REMOVE_LABELS: in_progress_label, FIELD_ASSIGNEE_IDS: [UNASSIGN_ID]}
    print_json(value=_update_issue(transport=transport, project=project, iid=args.iid, changes=changes))


def label_add_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue label-add <iid> --labels L``: ``add_labels``, so the issue's other labels stay; the issue."""
    changes = {FIELD_ADD_LABELS: args.labels}
    print_json(value=_update_issue(transport=transport, project=project, iid=args.iid, changes=changes))


def label_remove_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue label-remove <iid> --labels L``: ``remove_labels``, so the issue's other labels stay; the issue."""
    changes = {FIELD_REMOVE_LABELS: args.labels}
    print_json(value=_update_issue(transport=transport, project=project, iid=args.iid, changes=changes))


def assign_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue assign <iid> --me | --user U | --unassign``: ``assignee_ids`` set to the token's user, the named user
    or ``[0]``; the issue."""
    if args.unassign:
        assignee_id = UNASSIGN_ID
    elif args.me:
        assignee_id = _user_id(user=_current_user(transport=transport), operation_id=OP_CURRENT_USER)
    else:
        assignee_id = _named_user_id(transport=transport, username=args.user)
    changes = {FIELD_ASSIGNEE_IDS: [assignee_id]}
    print_json(value=_update_issue(transport=transport, project=project, iid=args.iid, changes=changes))


def close_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue close <iid>``: ``state_event=close`` in the JSON body; the issue."""
    changes = {FIELD_STATE_EVENT: EVENT_CLOSE}
    print_json(value=_update_issue(transport=transport, project=project, iid=args.iid, changes=changes))


def reopen_issue(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``issue reopen <iid>``: an open issue is printed unchanged, with no ``PUT``; any other gets
    ``state_event=reopen`` and the ``PUT``'s answer is printed."""
    issue = _read_issue(transport=transport, project=project, iid=args.iid)
    if issue.get(FIELD_STATE) == STATE_OPENED:
        print_json(value=issue)
        return
    changes = {FIELD_STATE_EVENT: EVENT_REOPEN}
    print_json(value=_update_issue(transport=transport, project=project, iid=args.iid, changes=changes))


# --- The argv group -----------------------------------------------------------------------------------------------


def _register_reads(*, group: SubParsers) -> None:
    """``list``, ``show``, ``create`` and ``comment``."""
    listing = add_command(subparsers=group, name="list", handler=list_issues, help_text="list the issues, every page")
    listing.add_argument("--state", choices=STATE_CHOICES, help="opened, closed or all")
    listing.add_argument("--assignee", help='a username, "*" (any assignee) or none (no assignee)')
    listing.add_argument("--labels", help="comma-separated label names, all of which an issue carries")
    show = add_command(subparsers=group, name="show", handler=show_issue, help_text="print one issue")
    add_iid(parser=show, help_text="the issue's iid")
    create = add_command(subparsers=group, name="create", handler=create_issue, help_text="create an issue")
    create.add_argument("--title", required=True, help="the title")
    create.add_argument("--description", help="the description (Markdown)")
    create.add_argument("--labels", help="comma-separated label names")
    comment = add_command(subparsers=group, name="comment", handler=comment_issue, help_text="add a note")
    add_iid(parser=comment, help_text="the issue's iid")
    comment.add_argument("--body", required=True, help="the note's text (Markdown)")


def _register_claims(*, group: SubParsers) -> None:
    """``start``, ``claim-check``, ``release``, ``label-add`` and ``label-remove``."""
    claims = (
        ("start", start_issue, "claim the issue: the in-progress label and the token's user, verified by a re-read"),
        ("claim-check", claim_check_issue, "read only: exit 0 when claimed or not open, 3 when open and unclaimed"),
        ("release", release_issue, "drop the claim: remove the in-progress label, unassign everyone"),
    )
    for name, handler, help_text in claims:
        parser = add_command(subparsers=group, name=name, handler=handler, help_text=help_text)
        add_iid(parser=parser, help_text="the issue's iid")
    labelling = (
        ("label-add", label_add_issue, "add labels; the issue's other labels stay"),
        ("label-remove", label_remove_issue, "remove labels; the issue's other labels stay"),
    )
    for name, handler, help_text in labelling:
        parser = add_command(subparsers=group, name=name, handler=handler, help_text=help_text)
        add_iid(parser=parser, help_text="the issue's iid")
        parser.add_argument("--labels", required=True, help="comma-separated label names")


def _register_changes(*, group: SubParsers) -> None:
    """``assign``, ``close`` and ``reopen``."""
    assign = add_command(subparsers=group, name="assign", handler=assign_issue, help_text="set or clear the assignee")
    add_iid(parser=assign, help_text="the issue's iid")
    who = assign.add_mutually_exclusive_group(required=True)
    who.add_argument("--me", action="store_true", help="the token's user")
    who.add_argument("--user", metavar="USERNAME", help="the user with this username")
    who.add_argument("--unassign", action="store_true", help="no assignee")
    states = (
        ("close", close_issue, "close the issue"),
        ("reopen", reopen_issue, "reopen the issue; exit 0 also when it is already open"),
    )
    for name, handler, help_text in states:
        parser = add_command(subparsers=group, name=name, handler=handler, help_text=help_text)
        add_iid(parser=parser, help_text="the issue's iid")


def register(subparsers: SubParsers) -> None:
    """Add the ``issue`` group and its subcommands to the entry script's top-level ``subparsers``."""
    group = add_group(subparsers=subparsers, name=GROUP, help_text="GitLab issues: read, create, claim and change them")
    _register_reads(group=group)
    _register_claims(group=group)
    _register_changes(group=group)
