"""The ``delete-branch`` subcommand of the GitLab wrapper (issue #13, design.md D6; UB-1)::

    delete-branch <branch>     prints {"branch": <branch>, "deleted": true}

The handler calls the ``create`` family's ``create#delete-repository-branch`` record (``rest/create.md`` "Branches API:
Delete repository branch") through ``gitlab_api.registry``, which sends the branch as ONE percent-encoded path segment,
so ``feature/x`` becomes ``feature%2Fx`` (design.md D5). A delete answers ``204`` without a body, so the printed JSON is
the wrapper's own; a failure raises ``GitLabAPIError``, which the entry script logs on standard error and exits 1 with.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from gitlab_api import registry
from gitlab_api.commands._common import PATH_PROJECT, add_command, print_json

if TYPE_CHECKING:
    from gitlab_api.commands._common import SubParsers
    from gitlab_api.transport import Transport

COMMAND = "delete-branch"

# The record the handler calls (design.md D6) and its `:branch` path parameter.
OP_DELETE_BRANCH = "create#delete-repository-branch"
PATH_BRANCH = "branch"

# The positional argument, and the keys of the output (design.md D6: `{branch, deleted: true}`).
BRANCH_ARGUMENT = "branch"
FIELD_BRANCH = "branch"
FIELD_DELETED = "deleted"


def delete_branch(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``delete-branch <branch>``: the branch deleted; ``{branch, deleted: true}``."""
    values = {PATH_PROJECT: project, PATH_BRANCH: args.branch}
    registry.call(transport=transport, operation_id=OP_DELETE_BRANCH, values=values)
    print_json(value={FIELD_BRANCH: args.branch, FIELD_DELETED: True})


def register(subparsers: SubParsers) -> None:
    """Add the ``delete-branch`` subcommand to the entry script's top-level ``subparsers``."""
    parser = add_command(
        subparsers=subparsers, name=COMMAND, handler=delete_branch, help_text="delete a branch of the project"
    )
    parser.add_argument(BRANCH_ARGUMENT, help="the branch's name, such as feature/issue-13-parser")
