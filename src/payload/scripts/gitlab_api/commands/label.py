"""The ``label`` subcommands of the GitLab wrapper (issue #13, design.md D6; UB-1)::

    label list                                                        every page
    label create --name N --color C [--description D]

Each handler composes the ``plan`` family's project label records by id through ``gitlab_api.registry``
(``rest/plan.md`` "Project labels API"): ``name`` and ``color`` are required by "Create a project label", and
``description`` is sent only when the flag is given. A body goes as JSON. Every result is printed as JSON on standard
output; a failure raises ``GitLabAPIError``, which the entry script logs on standard error and exits 1 with.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from gitlab_api import registry
from gitlab_api.commands._common import FIELD_DESCRIPTION, PATH_PROJECT, add_command, add_group, print_json

if TYPE_CHECKING:
    from gitlab_api.commands._common import SubParsers
    from gitlab_api.transport import Transport

GROUP = "label"

# The records the handlers compose (design.md D6).
OP_LIST_LABELS = "plan#list-all-project-labels"
OP_CREATE_LABEL = "plan#create-a-project-label"

# Body keys only this module sends (rest/plan.md "Project labels API: Create a project label").
FIELD_NAME = "name"
FIELD_COLOR = "color"


# --- The handlers (design.md D6) ----------------------------------------------------------------------------------


def list_labels(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``label list``: the project's labels, every page."""
    values = {PATH_PROJECT: project}
    print_json(value=list(registry.pages(transport=transport, operation_id=OP_LIST_LABELS, values=values)))


def create_label(*, transport: Transport, project: str, in_progress_label: str, args: argparse.Namespace) -> None:
    """``label create --name N --color C [--description D]``: the created label; ``description`` is not sent when the
    flag is absent."""
    values = {
        PATH_PROJECT: project,
        FIELD_NAME: args.name,
        FIELD_COLOR: args.color,
        FIELD_DESCRIPTION: args.description,
    }
    print_json(value=registry.call(transport=transport, operation_id=OP_CREATE_LABEL, values=values))


# --- The argv group -----------------------------------------------------------------------------------------------


def register(subparsers: SubParsers) -> None:
    """Add the ``label`` group and its subcommands to the entry script's top-level ``subparsers``."""
    group = add_group(subparsers=subparsers, name=GROUP, help_text="GitLab project labels: list and create them")
    add_command(subparsers=group, name="list", handler=list_labels, help_text="list the project's labels, every page")
    create = add_command(subparsers=group, name="create", handler=create_label, help_text="create a project label")
    create.add_argument("--name", required=True, help="the label's name")
    create.add_argument("--color", required=True, help="the label's color, such as #d9534f")
    create.add_argument("--description", help="the label's description")
