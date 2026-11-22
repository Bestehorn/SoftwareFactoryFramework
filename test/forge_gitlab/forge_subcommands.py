"""F:subcommands (#13): the GitLab wrapper's subcommands on the transport, against this run's project (issue #11,
design.md D6, D10; AC-1.3, AC-4.2, AC-8.1, AC-8.2).

Four tests through the product GitLab wrapper, which ``ephemeral_project.wrapper`` starts with the test marker in the
fixture clone, so every record takes the project of the clone's ``config/gitlab.json``, the run's
``bestehorn-sff-test/sff-test-<run id>``, which the wrapper's guard lets through (AC-4.2); no invocation names a
project. Each step's effect is read back through the wrapper:

- ``test_an_issue_and_label_round_trip``: ``label create`` of a fresh ``forge-<hex>`` label and ``label list``; then
  ``issue create``, ``issue show``, ``issue comment``, ``issue label-add`` of that label, ``issue show``, ``issue
  close`` and ``issue show`` again;
- ``test_a_merge_request_round_trip``: a branch ``forge-merge-request-<hex>`` with one new file, pushed from the clone
  with git (``push_branch``); ``mr create``; ``wait_until_checked``, which reads ``mr get`` until GitLab has decided the
  mergeability it checks asynchronously (D6 "Mergeability"), then ``mergeable``; ``mr merge`` and ``mr get`` again. The
  merge moves the default branch, so F:records reads the seed by its SHA (D6 "The seed moves");
- ``test_delete_branch_removes_a_pushed_branch``: a pushed branch ``forge-delete-branch-<hex>``, read with ``call
  create#retrieve-a-repository-branch``, deleted with ``delete-branch``, and read again: exit 1, and the transport's
  ``answered 404`` on standard error;
- ``test_no_pipeline_has_run`` (AC-1.3): ``pipeline status`` lists no pipeline, since the seed holds no
  ``.gitlab-ci.yml`` and the creation turned Auto DevOps off (D9 step 6), so none of the suite's pushes starts one.

Each invocation's exit code and printed JSON are asserted against what the test knows in advance: the label, the
titles, the description and the comment of this run (each naming the run id), the branches and the pushed commits,
and the states GitLab documents (``opened``, ``closed``, ``merged``). Everything is created inside the run's project,
which the session's teardown deletes. The token's scope ``api`` covers every invocation (D6's table). ``push_branch``
and ``wait_until_checked`` are the support module's, ``sys.modules["forge_gitlab_ephemeral"]``, which ``conftest.py``
registers when it loads ``ephemeral.py`` by path; they are read inside the test bodies (#10's DL-005).

Run: ``python scripts/run_tests.py --workers 1 test/forge_gitlab`` (with the test credential file,
``docs/forge-suite.md``).
"""

from __future__ import annotations

import sys
import uuid
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence, Tuple

#: The ``sys.modules`` key of the by-path load of ``ephemeral.py`` that ``conftest.py`` registers (#10's DL-005).
SUPPORT_MODULE = "forge_gitlab_ephemeral"

WRAPPER_EXIT_OK = 0
#: The product GitLab wrapper's exit on a ``GitLabAPIError``; its standard error then carries ``Transport._send``'s
#: ``"{method} {url} answered {status}: {error_text}"``, and its standard output nothing.
WRAPPER_API_FAILURE = 1
NOT_FOUND_ANSWER = "answered 404"
ARGUMENT_SEPARATOR = " "

# The product GitLab wrapper's subcommands and their options (src/payload/scripts/gitlab_api/commands/).
LABEL_GROUP = "label"
ISSUE_GROUP = "issue"
MR_GROUP = "mr"
PIPELINE_GROUP = "pipeline"
ACTION_CREATE = "create"
ACTION_LIST = "list"
ACTION_SHOW = "show"
ACTION_COMMENT = "comment"
ACTION_LABEL_ADD = "label-add"
ACTION_CLOSE = "close"
ACTION_GET = "get"
ACTION_MERGE = "merge"
ACTION_STATUS = "status"
CMD_DELETE_BRANCH = "delete-branch"
CMD_CALL = "call"
OPTION_NAME = "--name"
OPTION_COLOR = "--color"
OPTION_TITLE = "--title"
OPTION_DESCRIPTION = "--description"
OPTION_BODY = "--body"
OPTION_LABELS = "--labels"
OPTION_SOURCE = "--source"
OPTION_TARGET = "--target"
OPTION_PATH = "--path"
PARAMETER_ASSIGNMENT = "="
# The record that reads one branch (``families/create.py``, "Branches API: Get single repository branch") and its
# ``:branch`` path parameter.
BRANCH_RECORD = "create#retrieve-a-repository-branch"
BRANCH_PARAMETER = "branch"

# The fields of the printed records (docs.gitlab.com/api/labels/, /api/issues/, /api/notes/, /api/merge_requests/,
# /api/branches/) and of the wrapper's own ``delete-branch`` answer (``commands/branch.py``).
FIELD_NAME = "name"
FIELD_IID = "iid"
FIELD_TITLE = "title"
FIELD_DESCRIPTION = "description"
FIELD_STATE = "state"
FIELD_BODY = "body"
FIELD_LABELS = "labels"
FIELD_SOURCE_BRANCH = "source_branch"
FIELD_TARGET_BRANCH = "target_branch"
FIELD_SHA = "sha"
FIELD_DETAILED_MERGE_STATUS = "detailed_merge_status"
FIELD_COMMIT = "commit"
FIELD_COMMIT_ID = "id"
FIELD_BRANCH = "branch"
FIELD_DELETED = "deleted"
STATE_OPENED = "opened"
STATE_CLOSED = "closed"
STATE_MERGED = "merged"
#: The ``detailed_merge_status`` of a merge request that "is mergeable" (docs.gitlab.com/api/merge_requests/).
MERGE_STATUS_MERGEABLE = "mergeable"

# What the tests create (D6): a label ``forge-<hex>``, branches ``forge-<purpose>-<hex>``, and texts naming the run.
FORGE_NAME_PREFIX = "forge"
NAME_SEPARATOR = "-"
LABEL_COLOR = "#1F75CB"
ISSUE_TITLE = "Forge issue round trip of run {run_id}"
ISSUE_DESCRIPTION = "The issue description of the forge run {run_id}."
ISSUE_COMMENT = "The issue comment of the forge run {run_id}."
MERGE_REQUEST_TITLE = "Forge merge-request round trip of run {run_id}"
MERGE_REQUEST_PURPOSE = "merge-request"
DELETED_BRANCH_PURPOSE = "delete-branch"


def _support() -> ModuleType:
    """The GitLab forge suite's support module ``ephemeral.py``, as ``conftest.py`` registered its by-path load."""
    module = sys.modules.get(SUPPORT_MODULE)
    assert module is not None, f"no {SUPPORT_MODULE} in sys.modules: conftest.py did not load ephemeral.py"
    return module


def _label_name() -> str:
    """A fresh label name, ``forge-<hex>``."""
    return FORGE_NAME_PREFIX + NAME_SEPARATOR + uuid.uuid4().hex


def _branch_name(*, purpose: str) -> str:
    """A fresh branch name, ``forge-<purpose>-<hex>``."""
    return NAME_SEPARATOR.join([FORGE_NAME_PREFIX, purpose, uuid.uuid4().hex])


def _answer(*, project: Any, arguments: Sequence[str]) -> Any:
    """The JSON the product GitLab wrapper printed for ``arguments``, run in the clone; an exit other than 0 fails the
    test with the wrapper's standard error."""
    invocation = project.wrapper.run(arguments=list(arguments))
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{command}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation.json()


def _record(*, project: Any, arguments: Sequence[str]) -> Mapping[str, Any]:
    """The one JSON object the product GitLab wrapper printed for ``arguments``."""
    answer = _answer(project=project, arguments=arguments)
    assert isinstance(answer, dict), f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON object: {answer!r}"
    return answer


def _records(*, project: Any, arguments: Sequence[str]) -> List[Mapping[str, Any]]:
    """The JSON array of objects the product GitLab wrapper printed for ``arguments``."""
    answer = _answer(project=project, arguments=arguments)
    assert isinstance(answer, list) and all(isinstance(item, dict) for item in answer), (
        f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON array of objects: {answer!r}"
    )
    return answer


def _view(*, record: Mapping[str, Any], fields: Mapping[str, Any]) -> Dict[str, Any]:
    """The values ``record`` holds for the keys of ``fields`` (``None`` for a key it lacks), to compare with
    ``fields``."""
    return {field: record.get(field) for field in fields}


def _iid(*, record: Mapping[str, Any], what: str) -> int:
    """The integer ``iid`` of a created issue or merge request ``record``."""
    iid = record.get(FIELD_IID)
    assert isinstance(iid, int) and not isinstance(iid, bool), f"the created {what} has no integer iid: {record}"
    return iid


def _pushed_branch(*, project: Any, purpose: str) -> Tuple[str, str]:
    """A fresh branch ``forge-<purpose>-<hex>`` with one new file, pushed by the support module's ``push_branch``
    (D10); the branch and the pushed commit, which is not the seed."""
    branch = _branch_name(purpose=purpose)
    pushed = _support().push_branch(git=project.git, default_branch=project.default_branch, branch=branch)
    assert isinstance(pushed, str) and pushed, f"push_branch answered no commit for {branch}: {pushed!r}"
    assert pushed != project.seed_sha, f"the commit pushed on {branch} is the seed {project.seed_sha} itself"
    return branch, pushed


def test_an_issue_and_label_round_trip(ephemeral_project: Any) -> None:
    project = ephemeral_project
    label = _label_name()
    title = ISSUE_TITLE.format(run_id=project.run_id)
    description = ISSUE_DESCRIPTION.format(run_id=project.run_id)
    comment = ISSUE_COMMENT.format(run_id=project.run_id)

    created_label = _record(
        project=project, arguments=[LABEL_GROUP, ACTION_CREATE, OPTION_NAME, label, OPTION_COLOR, LABEL_COLOR]
    )
    assert created_label.get(FIELD_NAME) == label, f"the created label is {created_label}"

    listed = _records(project=project, arguments=[LABEL_GROUP, ACTION_LIST])
    names = [item.get(FIELD_NAME) for item in listed]
    assert label in names, f"`{LABEL_GROUP} {ACTION_LIST}` names {names}, not the created label {label}"

    created = _record(
        project=project,
        arguments=[ISSUE_GROUP, ACTION_CREATE, OPTION_TITLE, title, OPTION_DESCRIPTION, description],
    )
    iid = _iid(record=created, what="issue")
    issue = str(iid)
    opened = {FIELD_STATE: STATE_OPENED, FIELD_TITLE: title}
    assert _view(record=created, fields=opened) == opened, f"the created issue is {created}"

    shown = {FIELD_IID: iid, FIELD_TITLE: title, FIELD_DESCRIPTION: description, FIELD_STATE: STATE_OPENED}
    read = _record(project=project, arguments=[ISSUE_GROUP, ACTION_SHOW, issue])
    assert _view(record=read, fields=shown) == shown

    note = _record(project=project, arguments=[ISSUE_GROUP, ACTION_COMMENT, issue, OPTION_BODY, comment])
    assert note.get(FIELD_BODY) == comment, f"the note posted on issue #{iid} is {note}"

    # The issue was created with no label, so the one added is all it carries.
    labelled = {FIELD_IID: iid, FIELD_LABELS: [label]}
    added = _record(project=project, arguments=[ISSUE_GROUP, ACTION_LABEL_ADD, issue, OPTION_LABELS, label])
    assert _view(record=added, fields=labelled) == labelled, (
        f"issue #{iid} after `{ISSUE_GROUP} {ACTION_LABEL_ADD}` is {added}"
    )
    relabelled = _record(project=project, arguments=[ISSUE_GROUP, ACTION_SHOW, issue])
    assert _view(record=relabelled, fields=labelled) == labelled, f"issue #{iid} reads back as {relabelled}"

    shut = {FIELD_IID: iid, FIELD_STATE: STATE_CLOSED}
    closed = _record(project=project, arguments=[ISSUE_GROUP, ACTION_CLOSE, issue])
    assert _view(record=closed, fields=shut) == shut, f"issue #{iid} after `{ISSUE_GROUP} {ACTION_CLOSE}` is {closed}"
    reread = _record(project=project, arguments=[ISSUE_GROUP, ACTION_SHOW, issue])
    assert _view(record=reread, fields=shut) == shut, f"issue #{iid} reads back as {reread}"


def test_a_merge_request_round_trip(ephemeral_project: Any) -> None:
    project = ephemeral_project
    title = MERGE_REQUEST_TITLE.format(run_id=project.run_id)
    branch, pushed = _pushed_branch(project=project, purpose=MERGE_REQUEST_PURPOSE)

    created = _record(
        project=project,
        arguments=[
            MR_GROUP,
            ACTION_CREATE,
            OPTION_SOURCE,
            branch,
            OPTION_TARGET,
            project.default_branch,
            OPTION_TITLE,
            title,
        ],
    )
    iid = _iid(record=created, what="merge request")
    expected = {
        FIELD_IID: iid,
        FIELD_TITLE: title,
        FIELD_SOURCE_BRANCH: branch,
        FIELD_TARGET_BRANCH: project.default_branch,
        FIELD_SHA: pushed,
        FIELD_STATE: STATE_OPENED,
    }
    assert _view(record=created, fields=expected) == expected

    checked = _support().wait_until_checked(wrapper=project.wrapper, iid=iid)
    assert _view(record=checked, fields=expected) == expected
    assert checked.get(FIELD_DETAILED_MERGE_STATUS) == MERGE_STATUS_MERGEABLE, (
        f"merge request !{iid} was checked as {checked.get(FIELD_DETAILED_MERGE_STATUS)!r}, not "
        f"{MERGE_STATUS_MERGEABLE!r}"
    )

    landed = {FIELD_IID: iid, FIELD_STATE: STATE_MERGED}
    merged = _record(project=project, arguments=[MR_GROUP, ACTION_MERGE, str(iid)])
    assert _view(record=merged, fields=landed) == landed, (
        f"merge request !{iid} after `{MR_GROUP} {ACTION_MERGE}` is {merged}"
    )
    after = _record(project=project, arguments=[MR_GROUP, ACTION_GET, str(iid)])
    assert _view(record=after, fields=landed) == landed, f"merge request !{iid} reads back as {after}"


def test_delete_branch_removes_a_pushed_branch(ephemeral_project: Any) -> None:
    project = ephemeral_project
    branch, pushed = _pushed_branch(project=project, purpose=DELETED_BRANCH_PURPOSE)
    read_arguments = [CMD_CALL, BRANCH_RECORD, OPTION_PATH, BRANCH_PARAMETER + PARAMETER_ASSIGNMENT + branch]

    record = _record(project=project, arguments=read_arguments)
    commit = record.get(FIELD_COMMIT)
    head = commit.get(FIELD_COMMIT_ID) if isinstance(commit, dict) else None
    assert (record.get(FIELD_NAME), head) == (branch, pushed), (
        f"`{ARGUMENT_SEPARATOR.join(read_arguments)}` answered the branch {record.get(FIELD_NAME)!r} at {head!r}, "
        f"not {branch} at the pushed {pushed}"
    )

    deleted = _answer(project=project, arguments=[CMD_DELETE_BRANCH, branch])
    assert deleted == {FIELD_BRANCH: branch, FIELD_DELETED: True}, f"`{CMD_DELETE_BRANCH} {branch}` printed {deleted!r}"

    gone = project.wrapper.run(arguments=read_arguments)
    command = ARGUMENT_SEPARATOR.join(read_arguments)
    assert gone.returncode == WRAPPER_API_FAILURE, (
        f"`{command}` exited {gone.returncode} after the deletion, not {WRAPPER_API_FAILURE}: {gone.stdout!r}"
    )
    assert NOT_FOUND_ANSWER in gone.stderr, (
        f"`{command}` after the deletion logged no `{NOT_FOUND_ANSWER}`: {gone.stderr.strip()}"
    )
    assert gone.stdout == "", f"`{command}` after the deletion printed {gone.stdout!r}"


def test_no_pipeline_has_run(ephemeral_project: Any) -> None:
    project = ephemeral_project
    pipelines = _answer(project=project, arguments=[PIPELINE_GROUP, ACTION_STATUS])
    assert pipelines == [], f"`{PIPELINE_GROUP} {ACTION_STATUS}` lists pipelines of {project.full_path}: {pipelines!r}"
