"""The ``mr`` subcommands of the GitLab wrapper (issue #13, design.md D6; UB-1)::

    mr create --source B --target T --title X   remove_source_branch=true
    mr get <iid>
    mr checks <iid>                              the merge request's pipelines, every page
    mr approve <iid>
    mr merge <iid>                               should_remove_source_branch=true

Each handler composes the ``ai-coding`` family's merge request records by id through ``gitlab_api.registry``
(``rest/ai-coding.md`` "Merge requests API" and "Merge request approvals API"). A body goes as JSON. Every result is
printed as JSON on standard output; a failure raises ``GitLabAPIError``, which the entry script logs on standard error
and exits 1 with.

The own-MR approval caveat (the skeleton's implementation notes on ``mr_approve``): approving "requires the approvals
feature; a user cannot approve their own MR on many instances — surface that so the orchestrator polls for external
approval instead". GitLab refuses approving your own merge request when the project forbids it; ``mr approve`` then
gets an error status, which is a ``GitLabAPIError`` (exit 1, nothing on standard output), and the caller waits for an
approval by another user instead of retrying.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any, Dict

from gitlab_api import registry
from gitlab_api.commands._common import FIELD_TITLE, PATH_PROJECT, add_command, add_group, add_iid, print_json

if TYPE_CHECKING:
    from gitlab_api.commands._common import SubParsers
    from gitlab_api.transport import Transport

GROUP = "mr"

# The records the handlers compose (design.md D6).
OP_CREATE_MR = "ai-coding#create-a-merge-request"
OP_SHOW_MR = "ai-coding#retrieve-a-merge-request"
OP_LIST_MR_PIPELINES = "ai-coding#list-merge-request-pipelines"
OP_APPROVE_MR = "ai-coding#approve-merge-request"
OP_MERGE_MR = "ai-coding#merge-a-merge-request"

# The `:merge_request_iid` path parameter of the merge request records.
PATH_MR_IID = "merge_request_iid"

# Body keys only this module sends (rest/ai-coding.md "Create a merge request" and "Merge a merge request").
FIELD_SOURCE_BRANCH = "source_branch"
FIELD_TARGET_BRANCH = "target_branch"
FIELD_REMOVE_SOURCE_BRANCH = "remove_source_branch"
FIELD_SHOULD_REMOVE_SOURCE_BRANCH = "should_remove_source_branch"


def _mr_path(*, project: str, iid: int) -> Dict[str, Any]:
    """The path values of one merge request of the configured project."""
    return {PATH_PROJECT: project, PATH_MR_IID: iid}


# --- The handlers (design.md D6) ----------------------------------------------------------------------------------


def create_mr(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``mr create --source B --target T --title X``: the created merge request, its source branch removed on merge."""
    values = {
        PATH_PROJECT: project,
        FIELD_SOURCE_BRANCH: args.source,
        FIELD_TARGET_BRANCH: args.target,
        FIELD_TITLE: args.title,
        FIELD_REMOVE_SOURCE_BRANCH: True,
    }
    print_json(value=registry.call(transport=transport, operation_id=OP_CREATE_MR, values=values))


def get_mr(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``mr get <iid>``: the merge request."""
    values = _mr_path(project=project, iid=args.iid)
    print_json(value=registry.call(transport=transport, operation_id=OP_SHOW_MR, values=values))


def checks_mr(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``mr checks <iid>``: the merge request's pipelines, every page."""
    values = _mr_path(project=project, iid=args.iid)
    print_json(value=list(registry.pages(transport=transport, operation_id=OP_LIST_MR_PIPELINES, values=values)))


def approve_mr(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``mr approve <iid>``: the approval, sent with no body; a refusal (the own-MR caveat above) raises
    ``GitLabAPIError``."""
    values = _mr_path(project=project, iid=args.iid)
    print_json(value=registry.call(transport=transport, operation_id=OP_APPROVE_MR, values=values))


def merge_mr(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``mr merge <iid>``: the merged merge request, its source branch removed."""
    values = {**_mr_path(project=project, iid=args.iid), FIELD_SHOULD_REMOVE_SOURCE_BRANCH: True}
    print_json(value=registry.call(transport=transport, operation_id=OP_MERGE_MR, values=values))


# --- The argv group -----------------------------------------------------------------------------------------------


def register(subparsers: SubParsers) -> None:
    """Add the ``mr`` group and its subcommands to the entry script's top-level ``subparsers``."""
    group = add_group(subparsers=subparsers, name=GROUP, help_text="GitLab merge requests: create, read and merge them")
    create = add_command(subparsers=group, name="create", handler=create_mr, help_text="open a merge request")
    create.add_argument("--source", required=True, help="the source branch")
    create.add_argument("--target", required=True, help="the target branch")
    create.add_argument("--title", required=True, help="the title")
    by_iid = (
        ("get", get_mr, "print one merge request"),
        ("checks", checks_mr, "list the merge request's pipelines, every page"),
        ("approve", approve_mr, "approve the merge request; refused on your own one where the project forbids it"),
        ("merge", merge_mr, "merge the merge request and remove its source branch"),
    )
    for name, handler, help_text in by_iid:
        parser = add_command(subparsers=group, name=name, handler=handler, help_text=help_text)
        add_iid(parser=parser, help_text="the merge request's iid")
