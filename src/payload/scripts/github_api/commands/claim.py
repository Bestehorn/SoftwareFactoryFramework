"""The claim subcommands of the GitHub wrapper (design D5): ``start-issue``, ``release-issue``, ``claim-check``,
``label-add``, ``label-remove`` and ``assign``, each also spelled ``issue start|release|claim-check|label-add|
label-remove|assign`` in the nested ``issue`` group.

The two spellings of a verb are one ``ClaimSubcommand`` (``CLAIM_SUBCOMMANDS``): ONE argument helper and ONE handler,
so they can never accept different flags or behave differently, as the fork's ``ISSUE_GROUP_DISPATCH`` maps every
nested verb onto its flat handler. ``register`` adds each flat subcommand and the ``issue`` group with the fork's
arguments (``_add_start_issue_arguments``, ``_add_label_add_arguments``, ``_add_label_remove_arguments``,
``_add_assign_arguments`` and the bare ``issue_number``), without ``--token-stdin`` (UB-1.1). Each subparser carries
its handler as ``handler``, called as ``handler(transport=..., owner=..., repo=..., args=...)`` (D6). A handler sends
the fork handler's requests on the ``issues`` and ``users`` families' records through ``github_api.registry`` and
writes the fork handler's indented-JSON standard output:

- ``start-issue``: ``issues/get``, refusing an issue that is not open; ``users/get-authenticated`` for the working
  identity; with ``--strict``, refusing any existing claim; refusing a claim held by another (another assignee, or the
  ``in-progress`` label with nobody assigned) unless ``--force``; ``issues/add-labels`` and ``issues/add-assignees``,
  each only when not yet satisfied; then a fresh ``issues/get`` that must show both, else exit 1.
- ``release-issue``: ``issues/get``; ``users/get-authenticated`` only when the issue has assignees; ``issues/update``
  with the whole label set minus ``in-progress`` (the fork's read-then-write ``PATCH``, not the single-label delete);
  ``issues/remove-assignees`` for your own login only.
- ``claim-check``: ``issues/get`` only, writing nothing; exit 3 when the issue is open and has neither the
  ``in-progress`` label nor an assignee, else 0 — a contract the claim-before-worktree gate keys on.
- ``label-add``: ``issues/add-labels``; ``label-remove``: ``issues/remove-label``, the name percent-encoded as one
  path segment; ``assign``: ``issues/add-assignees`` for ``--me`` (``users/get-authenticated``) or ``--user``, or for
  ``--unassign`` an ``issues/get`` and ``issues/remove-assignees`` of the current assignees.

Every refusal raises ``GitHubAPIError`` (exit 1).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from github_api import registry
from github_api.commands._common import FIELD_LABELS, FIELD_NAME, FIELD_NUMBER, FIELD_STATE, print_json
from github_api.errors import GitHubAPIError
from github_api.transport import Transport

#: What a subparser's ``handler`` is: called with ``transport``, ``owner``, ``repo`` and ``args``; returns ``None`` or
#: an exit code (D6).
Handler = Callable[..., Optional[int]]
#: What registers one verb's arguments on a parser, called as ``add_arguments(parser=...)``.
ArgumentHelper = Callable[..., None]

OP_GET = "issues/get"
OP_UPDATE = "issues/update"
OP_ADD_LABELS = "issues/add-labels"
OP_REMOVE_LABEL = "issues/remove-label"
OP_ADD_ASSIGNEES = "issues/add-assignees"
OP_REMOVE_ASSIGNEES = "issues/remove-assignees"
OP_GET_AUTHENTICATED = "users/get-authenticated"

PATH_OWNER = "owner"
PATH_REPO = "repo"
PATH_ISSUE_NUMBER = "issue_number"
PATH_LABEL_NAME = "name"

FIELD_ASSIGNEES = "assignees"
FIELD_LOGIN = "login"

KEY_CLAIMED = "claimed"
KEY_EXIT_CODE = "exit_code"
#: ``True`` in the ``start-issue`` verdict only when a FRESH re-read showed both the label and the assignment.
KEY_VERIFIED = "verified"
#: The logins a ``release-issue`` or ``assign --unassign`` verdict dropped.
KEY_UNASSIGNED = "unassigned"

#: The canonical "someone is working this issue" label (the fork's ``LABEL_IN_PROGRESS``).
LABEL_IN_PROGRESS = "in-progress"
ISSUE_STATE_OPEN = "open"
LABEL_SEPARATOR = ","

# ``claim-check``'s exit statuses, a contract with the claim-before-worktree gate: do not renumber them.
EXIT_OK = 0
EXIT_OPEN_AND_UNCLAIMED = 3

CMD_START_ISSUE = "start-issue"
CMD_RELEASE_ISSUE = "release-issue"
CMD_CLAIM_CHECK = "claim-check"
CMD_LABEL_ADD = "label-add"
CMD_LABEL_REMOVE = "label-remove"
CMD_ASSIGN = "assign"
CMD_ISSUE_GROUP = "issue"
CMD_ISSUE_GROUP_START = "start"
CMD_ISSUE_GROUP_RELEASE = "release"
#: The ``argparse`` ``dest`` of the verb chosen inside the nested group (the fork's ``DEST_ISSUE_SUBCOMMAND``).
DEST_ISSUE_SUBCOMMAND = "issue_subcommand"

ARG_ISSUE_NUMBER = "issue_number"
OPTION_FORCE = "--force"
OPTION_STRICT = "--strict"
OPTION_LABELS = "--labels"
OPTION_LABEL = "--label"
OPTION_ME = "--me"
OPTION_USER = "--user"
OPTION_UNASSIGN = "--unassign"
ACTION_STORE_TRUE = "store_true"

# The fork's help texts.
CLAIM_CHECK_HELP = (
    "READ-ONLY claim probe (writes nothing): exit 0 = claimed or not open, exit 3 = OPEN and "
    "UNCLAIMED, exit 1 = API error. The claim-before-worktree gate blocks ONLY on exit 3."
)
START_ISSUE_HELP = (
    "THE claim: idempotent AND fail-closed. Refuses a non-open or foreign-held issue, ADDS the "
    "'in-progress' label additively, assigns you, then RE-READS to verify both landed (exit 1 if not)."
)
RELEASE_ISSUE_HELP = "Release a claim: REMOVE the 'in-progress' label AND your own assignment (inverts start-issue)"
RELEASE_ALIAS_HELP = "Alias of release-issue: drop the label + your assignment"
LABEL_ADD_HELP = (
    "ADD labels without touching the others (POST .../labels). Use this instead of "
    "'update-issue --labels', whose 'labels' field REPLACES the whole set and drops siblings."
)
LABEL_REMOVE_HELP = "REMOVE exactly one label, leaving every other label intact (DELETE .../labels/{name})"
ASSIGN_HELP = "Set or clear the assignee via the additive assignees endpoints (--me / --user LOGIN / --unassign)"
ISSUE_GROUP_HELP = "Nested claim verbs: 'issue claim-check|start|release|label-add|label-remove|assign <n>'"


def _issue_params(*, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """The path parameters of an issue-level record."""
    return {PATH_OWNER: owner, PATH_REPO: repo, PATH_ISSUE_NUMBER: issue_number}


def _fetch_issue(*, transport: Transport, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """One fresh read of the issue (``issues/get``); a response that is not a JSON object raises ``GitHubAPIError``.
    ``start-issue`` calls it twice on purpose: once to decide, once to verify."""
    issue = registry.call(
        transport=transport,
        operation_id=OP_GET,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=issue_number),
    )
    if not isinstance(issue, dict):
        raise GitHubAPIError(message=f"Unexpected issue payload for #{issue_number}: not a JSON object.", details=issue)
    return issue


def _label_names(*, issue: Mapping[str, Any]) -> List[str]:
    """The label names of an issue object."""
    return [label[FIELD_NAME] for label in issue.get(FIELD_LABELS) or []]


def _assignee_logins(*, issue: Mapping[str, Any]) -> List[str]:
    """The assignee logins of an issue object."""
    return [user[FIELD_LOGIN] for user in issue.get(FIELD_ASSIGNEES) or []]


def _split_label_names(*, text: str) -> List[str]:
    """A comma-separated ``--labels`` value as the fork splits it: each name stripped, empty names dropped."""
    return [name.strip() for name in text.split(sep=LABEL_SEPARATOR) if name.strip()]


def _authenticated_login(*, transport: Transport) -> str:
    """The login of the account the token belongs to (``users/get-authenticated``): the working identity a claim
    records, resolved from the token rather than configured anywhere."""
    user = registry.call(transport=transport, operation_id=OP_GET_AUTHENTICATED, path_params={})
    login = user.get(FIELD_LOGIN) if isinstance(user, dict) else None
    if not isinstance(login, str) or not login:
        raise GitHubAPIError(message="GET /user returned no 'login' — cannot determine the working identity.")
    return login


def _add_assignees(*, transport: Transport, owner: str, repo: str, issue_number: int, assignees: List[str]) -> Any:
    """ADD assignees, keeping any already present (``issues/add-assignees``)."""
    return registry.call(
        transport=transport,
        operation_id=OP_ADD_ASSIGNEES,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=issue_number),
        body={FIELD_ASSIGNEES: assignees},
    )


def _remove_assignees(*, transport: Transport, owner: str, repo: str, issue_number: int, assignees: List[str]) -> Any:
    """REMOVE the named assignees, leaving any others in place (``issues/remove-assignees``)."""
    return registry.call(
        transport=transport,
        operation_id=OP_REMOVE_ASSIGNEES,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=issue_number),
        body={FIELD_ASSIGNEES: assignees},
    )


def _add_labels(*, transport: Transport, owner: str, repo: str, issue_number: int, labels: List[str]) -> Any:
    """ADD labels, leaving every other label untouched (``issues/add-labels``)."""
    return registry.call(
        transport=transport,
        operation_id=OP_ADD_LABELS,
        path_params=_issue_params(owner=owner, repo=repo, issue_number=issue_number),
        body={FIELD_LABELS: labels},
    )


def _issue_is_claimed(*, issue: Mapping[str, Any]) -> bool:
    """The one "is somebody already working this?" test: the ``in-progress`` label OR any assignee."""
    return LABEL_IN_PROGRESS in _label_names(issue=issue) or bool(_assignee_logins(issue=issue))


def _claim_is_held_by_another(*, labels: List[str], assignees: List[str], me: str) -> bool:
    """Would claiming take over somebody else's claim? Another login assigned is theirs; the label with nobody
    assigned has no establishable holder, so it counts as held (fail-closed); the label with ``me`` assigned is mine."""
    if any(login != me for login in assignees):
        return True
    return LABEL_IN_PROGRESS in labels and me not in assignees


def cmd_claim_check(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Print the issue's claim verdict and return 3 when it is open and unclaimed, else 0; writes nothing."""
    issue = _fetch_issue(transport=transport, owner=owner, repo=repo, issue_number=args.issue_number)
    state = issue.get(FIELD_STATE)
    claimed = _issue_is_claimed(issue=issue)
    exit_code = EXIT_OPEN_AND_UNCLAIMED if state == ISSUE_STATE_OPEN and not claimed else EXIT_OK
    print_json(
        value={
            FIELD_NUMBER: args.issue_number,
            FIELD_STATE: state,
            FIELD_LABELS: _label_names(issue=issue),
            FIELD_ASSIGNEES: _assignee_logins(issue=issue),
            KEY_CLAIMED: claimed,
            KEY_EXIT_CODE: exit_code,
        }
    )
    return exit_code


def _refuse_foreign_or_strict_claim(
    *, args: argparse.Namespace, labels: List[str], assignees: List[str], me: str
) -> None:
    """Raise when ``--strict`` meets any existing claim, or when the claim is held by another and ``--force`` was not
    given; nothing has been written at this point."""
    number = args.issue_number
    if args.strict and (LABEL_IN_PROGRESS in labels or assignees):
        raise GitHubAPIError(
            message=(
                f"Issue #{number} already carries a claim ('{LABEL_IN_PROGRESS}' label and/or an assignee) — "
                "strict claim rejected; nothing was written."
            ),
            details={FIELD_NUMBER: number, FIELD_LABELS: labels, FIELD_ASSIGNEES: assignees},
        )
    if _claim_is_held_by_another(labels=labels, assignees=assignees, me=me) and not args.force:
        raise GitHubAPIError(
            message=(
                f"Issue #{number} is already claimed by another worker "
                f"(labels={labels}, assignees={assignees}; you are '{me}') — not starting. "
                f"Pass {OPTION_FORCE} only to deliberately take it over."
            ),
            details={FIELD_NUMBER: number, FIELD_LABELS: labels, FIELD_ASSIGNEES: assignees},
        )


def cmd_start_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Claim the issue: refuse one that is not open or is held by another, add the label and assign the working
    identity where not yet done, then raise unless a fresh re-read shows both; print the verified verdict."""
    number = args.issue_number
    issue = _fetch_issue(transport=transport, owner=owner, repo=repo, issue_number=number)
    state = issue.get(FIELD_STATE)
    if state != ISSUE_STATE_OPEN:
        raise GitHubAPIError(
            message=f"Issue #{number} is not open (state={state}) — refusing to claim work that is not outstanding.",
            details={FIELD_NUMBER: number, FIELD_STATE: state},
        )
    me = _authenticated_login(transport=transport)
    labels_before = _label_names(issue=issue)
    assignees_before = _assignee_logins(issue=issue)
    _refuse_foreign_or_strict_claim(args=args, labels=labels_before, assignees=assignees_before, me=me)
    if LABEL_IN_PROGRESS not in labels_before:
        _add_labels(transport=transport, owner=owner, repo=repo, issue_number=number, labels=[LABEL_IN_PROGRESS])
    if me not in assignees_before:
        _add_assignees(transport=transport, owner=owner, repo=repo, issue_number=number, assignees=[me])
    verified = _fetch_issue(transport=transport, owner=owner, repo=repo, issue_number=number)
    labels_after = _label_names(issue=verified)
    assignees_after = _assignee_logins(issue=verified)
    if LABEL_IN_PROGRESS not in labels_after or me not in assignees_after:
        raise GitHubAPIError(
            message=(
                f"Claim on issue #{number} did NOT land: re-read shows labels={labels_after}, "
                f"assignees={assignees_after} (expected '{LABEL_IN_PROGRESS}' and '{me}'). "
                "Do NOT start work on an unverified claim."
            ),
            details={
                FIELD_NUMBER: number,
                FIELD_LABELS: labels_after,
                FIELD_ASSIGNEES: assignees_after,
                KEY_VERIFIED: False,
            },
        )
    print_json(
        value={
            FIELD_NUMBER: number,
            FIELD_STATE: state,
            FIELD_LABELS: labels_after,
            FIELD_ASSIGNEES: assignees_after,
            KEY_CLAIMED: True,
            KEY_VERIFIED: True,
        }
    )


def cmd_release_issue(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Drop the ``in-progress`` label (a whole-set ``issues/update`` of the other labels) and your own assignment, and
    print the release verdict; an issue with neither to drop is reported and not written."""
    number = args.issue_number
    issue = _fetch_issue(transport=transport, owner=owner, repo=repo, issue_number=number)
    before = _label_names(issue=issue)
    assignees = _assignee_logins(issue=issue)
    mine: List[str] = []
    if assignees:
        me = _authenticated_login(transport=transport)
        mine = [login for login in assignees if login == me]
    if LABEL_IN_PROGRESS not in before and not mine:
        print_json(value={FIELD_NUMBER: number, FIELD_LABELS: before, KEY_CLAIMED: False, KEY_UNASSIGNED: []})
        return
    after = before
    if LABEL_IN_PROGRESS in before:
        updated = registry.call(
            transport=transport,
            operation_id=OP_UPDATE,
            path_params=_issue_params(owner=owner, repo=repo, issue_number=number),
            body={FIELD_LABELS: [name for name in before if name != LABEL_IN_PROGRESS]},
        )
        after = _label_names(issue=updated)
    if mine:
        _remove_assignees(transport=transport, owner=owner, repo=repo, issue_number=number, assignees=mine)
    print_json(value={FIELD_NUMBER: number, FIELD_LABELS: after, KEY_CLAIMED: False, KEY_UNASSIGNED: mine})


def cmd_label_add(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """ADD the ``--labels`` names, keeping every other label, and print the labels the response returns."""
    labels = _split_label_names(text=args.labels)
    if not labels:
        raise GitHubAPIError(message=f"{CMD_LABEL_ADD} requires at least one label name in {OPTION_LABELS}")
    data = _add_labels(transport=transport, owner=owner, repo=repo, issue_number=args.issue_number, labels=labels)
    print_json(value=data)


def cmd_label_remove(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """REMOVE exactly the ``--label`` name, keeping every other label, and print the labels that remain."""
    path_params = {
        **_issue_params(owner=owner, repo=repo, issue_number=args.issue_number),
        PATH_LABEL_NAME: args.label,
    }
    data = registry.call(transport=transport, operation_id=OP_REMOVE_LABEL, path_params=path_params)
    print_json(value=data)


def cmd_assign(*, transport: Transport, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Assign the working identity (``--me``) or a login (``--user``) beside any other assignee, or clear every
    current assignee (``--unassign``, writing nothing when there is none); print the assignment verdict."""
    number = args.issue_number
    if args.unassign:
        current = _assignee_logins(issue=_fetch_issue(transport=transport, owner=owner, repo=repo, issue_number=number))
        if current:
            _remove_assignees(transport=transport, owner=owner, repo=repo, issue_number=number, assignees=current)
        print_json(value={FIELD_NUMBER: number, FIELD_ASSIGNEES: [], KEY_UNASSIGNED: current})
        return
    login = _authenticated_login(transport=transport) if args.me else args.user
    data = _add_assignees(transport=transport, owner=owner, repo=repo, issue_number=number, assignees=[login])
    print_json(value={FIELD_NUMBER: number, FIELD_ASSIGNEES: _assignee_logins(issue=data)})


def _add_issue_number_argument(*, parser: argparse.ArgumentParser) -> None:
    """The bare ``issue_number`` positional of ``claim-check`` and ``release-issue``."""
    parser.add_argument(ARG_ISSUE_NUMBER, type=int)


def _add_start_issue_arguments(*, parser: argparse.ArgumentParser) -> None:
    """``start-issue``'s arguments (the fork's ``_add_start_issue_arguments``)."""
    _add_issue_number_argument(parser=parser)
    parser.add_argument(
        OPTION_FORCE,
        action=ACTION_STORE_TRUE,
        help="Claim even when another worker holds it (deliberate take-over; refused without this)",
    )
    parser.add_argument(
        OPTION_STRICT,
        action=ACTION_STORE_TRUE,
        help="Also refuse a claim that is ALREADY YOURS, demanding a fresh acquisition (as on claim-issue)",
    )


def _add_label_add_arguments(*, parser: argparse.ArgumentParser) -> None:
    """``label-add``'s arguments (the fork's ``_add_label_add_arguments``)."""
    _add_issue_number_argument(parser=parser)
    parser.add_argument(OPTION_LABELS, required=True, help="Comma-separated label names to ADD (existing ones kept)")


def _add_label_remove_arguments(*, parser: argparse.ArgumentParser) -> None:
    """``label-remove``'s arguments (the fork's ``_add_label_remove_arguments``)."""
    _add_issue_number_argument(parser=parser)
    parser.add_argument(OPTION_LABEL, required=True, help="The ONE label name to remove (all others kept)")


def _add_assign_arguments(*, parser: argparse.ArgumentParser) -> None:
    """``assign``'s arguments (the fork's ``_add_assign_arguments``): the three modes are a REQUIRED mutually
    exclusive group, so a call naming no mode is an argparse usage error rather than a silent no-op."""
    _add_issue_number_argument(parser=parser)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(OPTION_ME, action=ACTION_STORE_TRUE, help="Assign the account the PAT belongs to (GET /user)")
    mode.add_argument(OPTION_USER, help="Assign this login")
    mode.add_argument(OPTION_UNASSIGN, action=ACTION_STORE_TRUE, help="Clear the issue's current assignees")


@dataclass(frozen=True)
class ClaimSubcommand:
    """One claim verb in both its spellings: the flat ``flat_name`` and the nested ``issue <nested_name>``, each with
    its help text, sharing ONE ``add_arguments`` helper and ONE ``handler``."""

    flat_name: str
    nested_name: str
    flat_help: str
    nested_help: str
    add_arguments: ArgumentHelper
    handler: Handler


#: Every claim verb, in the fork's nested order (``_register_issue_group_subcommands``).
CLAIM_SUBCOMMANDS: Tuple[ClaimSubcommand, ...] = (
    ClaimSubcommand(
        flat_name=CMD_CLAIM_CHECK,
        nested_name=CMD_CLAIM_CHECK,
        flat_help=CLAIM_CHECK_HELP,
        nested_help=CLAIM_CHECK_HELP,
        add_arguments=_add_issue_number_argument,
        handler=cmd_claim_check,
    ),
    ClaimSubcommand(
        flat_name=CMD_START_ISSUE,
        nested_name=CMD_ISSUE_GROUP_START,
        flat_help=START_ISSUE_HELP,
        nested_help=START_ISSUE_HELP,
        add_arguments=_add_start_issue_arguments,
        handler=cmd_start_issue,
    ),
    ClaimSubcommand(
        flat_name=CMD_RELEASE_ISSUE,
        nested_name=CMD_ISSUE_GROUP_RELEASE,
        flat_help=RELEASE_ISSUE_HELP,
        nested_help=RELEASE_ALIAS_HELP,
        add_arguments=_add_issue_number_argument,
        handler=cmd_release_issue,
    ),
    ClaimSubcommand(
        flat_name=CMD_LABEL_ADD,
        nested_name=CMD_LABEL_ADD,
        flat_help=LABEL_ADD_HELP,
        nested_help=LABEL_ADD_HELP,
        add_arguments=_add_label_add_arguments,
        handler=cmd_label_add,
    ),
    ClaimSubcommand(
        flat_name=CMD_LABEL_REMOVE,
        nested_name=CMD_LABEL_REMOVE,
        flat_help=LABEL_REMOVE_HELP,
        nested_help=LABEL_REMOVE_HELP,
        add_arguments=_add_label_remove_arguments,
        handler=cmd_label_remove,
    ),
    ClaimSubcommand(
        flat_name=CMD_ASSIGN,
        nested_name=CMD_ASSIGN,
        flat_help=ASSIGN_HELP,
        nested_help=ASSIGN_HELP,
        add_arguments=_add_assign_arguments,
        handler=cmd_assign,
    ),
)


def _add_spelling(
    *,
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    help_text: str,
    subcommand: ClaimSubcommand,
) -> None:
    """The subparser ``name`` with ``subcommand``'s arguments, carrying its handler as ``handler`` (D6)."""
    parser = subparsers.add_parser(name=name, help=help_text)
    subcommand.add_arguments(parser=parser)
    parser.set_defaults(handler=subcommand.handler)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add each claim verb's flat spelling and the nested ``issue`` group to the entry script's ``subparsers``."""
    for subcommand in CLAIM_SUBCOMMANDS:
        _add_spelling(
            subparsers=subparsers, name=subcommand.flat_name, help_text=subcommand.flat_help, subcommand=subcommand
        )
    group = subparsers.add_parser(name=CMD_ISSUE_GROUP, help=ISSUE_GROUP_HELP)
    nested = group.add_subparsers(dest=DEST_ISSUE_SUBCOMMAND, required=True)
    for subcommand in CLAIM_SUBCOMMANDS:
        _add_spelling(
            subparsers=nested, name=subcommand.nested_name, help_text=subcommand.nested_help, subcommand=subcommand
        )
