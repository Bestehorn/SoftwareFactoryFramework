"""F:graphql, issue #44's slice of the GitLab forge suite: ``call graphql#Project.workItems`` against this run's
ephemeral project (issue #11, design.md D6, AC-8.4).

The test takes the session's ``ephemeral_project``, runs the product GitLab wrapper through its ``wrapper`` (the test
marker set, the fixture clone as working directory, so every record of the configured project targets the run's
``sff-test-<run id>`` project of the test group) and asserts every invocation's exit code and what it printed, against
what the test knows in advance (AC-8.1, AC-8.4). ``<hex>`` is a fresh ``uuid.uuid4().hex`` of the test.

- ``test_the_work_items_of_the_project``: the issue is made with ``issue create --title forge-<hex>``, since ``call``
  refuses ``plan#create-an-issue`` and ``graphql#workItemCreate`` (``commands/call.py`` ``GATED_OPERATIONS``); its
  answer prints the title and the issue's iid N, a number. Then ``call graphql#Project.workItems -f fullPath=P``, P
  the fixture's ``full_path``, lists the project's work items: on a Free project a work item is an issue, so a private
  Free project of a non-administrator serves the record (``gitlab_api/graphql_only.py``, capability "Work items").
  ``call`` prints one JSON array of the nodes of every page of the record's connection (``commands/call.py`` "What
  prints", ``registry.call`` through ``Transport.graphql_nodes``), each node the fields ``WORK_ITEM_FIELDS`` selects,
  ``id iid title state webUrl workItemType { id name }``. Exactly one node is titled ``forge-<hex>``, whatever issues
  the other slices made in the project, and it holds ``iid`` N as text, ``state`` ``OPEN`` and ``workItemType.name``
  ``Issue``: the reference types ``WorkItem.iid`` ``String!`` and ``WorkItem.state`` ``WorkItemState!``, whose values
  are ``CLOSED`` and ``OPEN`` (``docs/api-reference/gitlab/graphql/objects-p-x.md``, ``enums.md``).

The variable ``fullPath`` names a project itself, which the wrapper's project guard does not judge (design.md Security
Considerations, "The guard's bound"), so it is the fixture's ``full_path`` and nothing else (AC-8.7). The reference's
Notes for ``Project.workItems`` read "**deprecated** in 15.9; experiment since 15.1": GitLab may change it without
notice, and a change fails this test until the record follows it (design.md Residuals). The token's scope ``api``
covers both invocations (D6's table).

Run: ``python scripts/run_tests.py --workers 1 test/forge_gitlab``.
"""

from __future__ import annotations

import uuid
from typing import Any, Mapping, Sequence

# The product GitLab wrapper's subcommands and the options this slice gives (``gitlab_api/commands/issue.py``,
# ``gitlab_api/commands/call.py``).
CALL = "call"
ISSUE_GROUP = "issue"
ISSUE_CREATE = "create"
TITLE_OPTION = "--title"
RAW_FIELD_OPTION = "-f"
ASSIGNMENT = "="

# The record this slice sends (``gitlab_api/graphql_only.py``) and its one variable besides the cursor ``after``,
# which ``Transport.graphql_nodes`` sets on every page.
WORK_ITEM_LIST = "graphql#Project.workItems"
FULL_PATH_VARIABLE = "fullPath"

# The fields this slice reads: of the issue ``issue create`` printed, and of a work-item node (``WORK_ITEM_FIELDS``).
FIELD_IID = "iid"
FIELD_TITLE = "title"
FIELD_STATE = "state"
FIELD_WORK_ITEM_TYPE = "workItemType"
FIELD_NAME = "name"

#: A value of ``WorkItemState`` (``docs/api-reference/gitlab/graphql/enums.md``: ``CLOSED``, ``OPEN``).
STATE_OPEN = "OPEN"
#: The name of an issue's work-item type (design.md D6).
TYPE_ISSUE = "Issue"
TITLE_PREFIX = "forge-"

WRAPPER_EXIT_OK = 0


def _answer(*, project: Any, arguments: Sequence[str]) -> Any:
    """The JSON the product GitLab wrapper printed for ``arguments``, after asserting that it exited 0."""
    invocation = project.wrapper.run(arguments=list(arguments))
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{' '.join(arguments)}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}: {invocation.stderr}"
    )
    return invocation.json()


def test_the_work_items_of_the_project(ephemeral_project: Any) -> None:
    title = TITLE_PREFIX + uuid.uuid4().hex
    creation = f"{ISSUE_GROUP} {ISSUE_CREATE}"
    created = _answer(project=ephemeral_project, arguments=[ISSUE_GROUP, ISSUE_CREATE, TITLE_OPTION, title])
    assert isinstance(created, Mapping), f"`{creation}` printed {created!r}, not an object"
    assert created.get(FIELD_TITLE) == title, (
        f"`{creation}` answered the title {created.get(FIELD_TITLE)!r}, not {title!r}"
    )
    iid = created.get(FIELD_IID)
    assert isinstance(iid, int) and not isinstance(iid, bool), f"`{creation}` answered the iid {iid!r}, not a number"

    listing = f"{CALL} {WORK_ITEM_LIST}"
    full_path = FULL_PATH_VARIABLE + ASSIGNMENT + ephemeral_project.full_path
    nodes = _answer(project=ephemeral_project, arguments=[CALL, WORK_ITEM_LIST, RAW_FIELD_OPTION, full_path])
    assert isinstance(nodes, list) and all(isinstance(node, Mapping) for node in nodes), (
        f"`{listing}` printed {nodes!r}, not an array of work-item nodes"
    )
    titled = [node for node in nodes if node.get(FIELD_TITLE) == title]
    assert len(titled) == 1, (
        f"`{listing}` listed {len(titled)} nodes titled {title}, not one; it listed the titles "
        f"{[node.get(FIELD_TITLE) for node in nodes]}"
    )
    node = titled[0]
    assert node.get(FIELD_IID) == str(iid), (
        f"`{listing}` answered the iid {node.get(FIELD_IID)!r} for {title}, not {str(iid)!r}"
    )
    assert node.get(FIELD_STATE) == STATE_OPEN, (
        f"`{listing}` answered the state {node.get(FIELD_STATE)!r} for {title}, not {STATE_OPEN}"
    )
    work_item_type = node.get(FIELD_WORK_ITEM_TYPE)
    type_name = work_item_type.get(FIELD_NAME) if isinstance(work_item_type, Mapping) else None
    assert type_name == TYPE_ISSUE, (
        f"`{listing}` answered the work-item type {work_item_type!r} for {title}, not one named {TYPE_ISSUE}"
    )
