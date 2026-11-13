"""F:subcommands (#17): the wrapper's compatibility subcommands on the new transport, against this run's repository
(issue #10, design.md D6, AC-8.2).

Two round trips through the product wrapper, which ``ephemeral_repository.wrapper`` starts with the test marker in the
fixture clone, so every record targets the clone's ``origin``, the run's ``sff-test-<run id>`` repository of the test
organization; no invocation names a repository. Each step's effect is read back through the wrapper:

- the issue round trip: ``call issues/create-label``, then ``create-issue``, ``get-issue``, ``comment-issue``,
  ``get-issue-comments``, ``label-add``, ``get-issue``, ``update-issue --state closed`` and ``get-issue`` again;
- the pull-request round trip: in the clone, the branch ``forge-pull-request`` from the seed commit with one file
  committed, pushed with an authenticated ``git push``, and the default branch checked out again, so the clone is back
  on the seed for every other test; then ``create-pr``, ``get-pr``, ``merge-pr`` and ``get-pr`` again.

Each invocation's exit code and printed JSON are asserted against what the test knows in advance: the label, the
titles, bodies and comment of this run (each naming the run id), the branches and the pushed commit. Everything is
created inside the run's repository, which the session's teardown deletes. The token needs the repository permissions
Issues (write), Pull requests (write) and Contents (write) of D6's table.

Run: ``python scripts/run_tests.py --workers 1 test/forge``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

WRAPPER_EXIT_OK = 0
GIT_EXIT_OK = 0
TEXT_ENCODING = "utf-8"
ARGUMENT_SEPARATOR = " "

# The product wrapper's subcommands and their options (src/payload/scripts/github_api/commands/).
CMD_CALL = "call"
CMD_CREATE_ISSUE = "create-issue"
CMD_GET_ISSUE = "get-issue"
CMD_COMMENT_ISSUE = "comment-issue"
CMD_GET_ISSUE_COMMENTS = "get-issue-comments"
CMD_LABEL_ADD = "label-add"
CMD_UPDATE_ISSUE = "update-issue"
CMD_CREATE_PR = "create-pr"
CMD_GET_PR = "get-pr"
CMD_MERGE_PR = "merge-pr"
OPERATION_CREATE_LABEL = "issues/create-label"
OPTION_RAW_FIELD = "-f"
OPTION_TITLE = "--title"
OPTION_BODY = "--body"
OPTION_LABELS = "--labels"
OPTION_STATE = "--state"
OPTION_HEAD = "--head"
OPTION_BASE = "--base"
FIELD_ASSIGNMENT = "="

# The fields of the printed records: a label, an issue, an issue comment, a pull request and a merge result
# (docs.github.com "Create a label", "Get an issue", "Create an issue comment", "Get a pull request", "Merge a pull
# request").
FIELD_NAME = "name"
FIELD_ID = "id"
FIELD_NUMBER = "number"
FIELD_TITLE = "title"
FIELD_BODY = "body"
FIELD_STATE = "state"
FIELD_LABELS = "labels"
FIELD_HEAD = "head"
FIELD_BASE = "base"
FIELD_REF = "ref"
FIELD_SHA = "sha"
FIELD_MERGED = "merged"
STATE_OPEN = "open"
STATE_CLOSED = "closed"

# What the issue round trip creates; the repository is the run's own, so the label's name is fixed (D6).
LABEL = "forge-label"
ISSUE_TITLE = "Forge issue round trip of run {run_id}"
ISSUE_BODY = "The issue body of the forge run {run_id}."
ISSUE_COMMENT = "The issue comment of the forge run {run_id}."

# What the pull-request round trip creates and runs in the clone (D3 "The clone"; D6).
BRANCH = "forge-pull-request"
BRANCH_FILE = "forge-pull-request.md"
BRANCH_FILE_TEXT = "The pull-request round trip of the forge run {run_id}.\n"
COMMIT_MESSAGE = "Add the pull-request file of the forge run {run_id}"
PULL_REQUEST_TITLE = "Forge pull-request round trip of run {run_id}"
PULL_REQUEST_BODY = "The pull-request body of the forge run {run_id}."
ORIGIN_REMOTE = "origin"
GIT_CHECKOUT = "checkout"
GIT_NEW_BRANCH_OPTION = "-b"
GIT_ADD = "add"
GIT_PATHSPEC_SEPARATOR = "--"
GIT_COMMIT = "commit"
GIT_MESSAGE_OPTION = "-m"
GIT_PUSH = "push"
GIT_REV_PARSE = "rev-parse"
HEAD = "HEAD"


def _answer(*, repository: Any, arguments: Sequence[str]) -> Any:
    """The JSON the product wrapper printed for ``arguments``, run in the clone; an exit other than 0 fails the test
    with the wrapper's standard error."""
    invocation = repository.wrapper.run(arguments=list(arguments))
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{command}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation.json()


def _record(*, repository: Any, arguments: Sequence[str]) -> Mapping[str, Any]:
    """The one JSON object the product wrapper printed for ``arguments``."""
    answer = _answer(repository=repository, arguments=arguments)
    assert isinstance(answer, dict), f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON object: {answer!r}"
    return answer


def _records(*, repository: Any, arguments: Sequence[str]) -> List[Mapping[str, Any]]:
    """The JSON array of objects the product wrapper printed for ``arguments``."""
    answer = _answer(repository=repository, arguments=arguments)
    assert isinstance(answer, list) and all(isinstance(item, dict) for item in answer), (
        f"`{ARGUMENT_SEPARATOR.join(arguments)}` printed no JSON array of objects: {answer!r}"
    )
    return answer


def _git(*, repository: Any, arguments: Sequence[str], authenticated: bool = False) -> str:
    """The standard output, stripped, of git run in the clone with ``arguments``; an exit other than 0 fails the test
    with git's standard error."""
    invocation = repository.git.run(arguments=list(arguments), authenticated=authenticated)
    command = ARGUMENT_SEPARATOR.join(arguments)
    assert invocation.returncode == GIT_EXIT_OK, (
        f"`git {command}` exited {invocation.returncode}, not {GIT_EXIT_OK}: {invocation.stderr.strip()}"
    )
    return invocation.stdout.strip()


def _label_names(*, labels: Sequence[Mapping[str, Any]]) -> List[str]:
    """The names of a list of label objects, in their order."""
    return [label[FIELD_NAME] for label in labels]


def _push_branch(*, repository: Any) -> str:
    """D6: the branch ``forge-pull-request`` from the seed commit, one file committed (not under ``credentials/``),
    pushed to ``origin``, and the default branch checked out again, even when a step failed; answers the pushed
    commit."""
    run_id = repository.run_id
    _git(repository=repository, arguments=[GIT_CHECKOUT, GIT_NEW_BRANCH_OPTION, BRANCH, repository.seed_sha])
    try:
        text = BRANCH_FILE_TEXT.format(run_id=run_id)
        (repository.clone / BRANCH_FILE).write_bytes(data=text.encode(encoding=TEXT_ENCODING))
        _git(repository=repository, arguments=[GIT_ADD, GIT_PATHSPEC_SEPARATOR, BRANCH_FILE])
        _git(repository=repository, arguments=[GIT_COMMIT, GIT_MESSAGE_OPTION, COMMIT_MESSAGE.format(run_id=run_id)])
        pushed = _git(repository=repository, arguments=[GIT_REV_PARSE, HEAD])
        _git(repository=repository, arguments=[GIT_PUSH, ORIGIN_REMOTE, BRANCH], authenticated=True)
    finally:
        _git(repository=repository, arguments=[GIT_CHECKOUT, repository.default_branch])
    restored = _git(repository=repository, arguments=[GIT_REV_PARSE, HEAD])
    assert restored == repository.seed_sha, (
        f"the clone's {repository.default_branch} is at {restored} after the push, not at the seed "
        f"{repository.seed_sha}"
    )
    assert pushed != repository.seed_sha, f"the commit on {BRANCH} is the seed {repository.seed_sha} itself"
    return pushed


def _pull_request_view(*, pull: Mapping[str, Any]) -> Dict[str, Any]:
    """What the round trip knows of a pull request in advance: its number, title, body, head branch and commit, base
    branch and state."""
    return {
        FIELD_NUMBER: pull[FIELD_NUMBER],
        FIELD_TITLE: pull[FIELD_TITLE],
        FIELD_BODY: pull[FIELD_BODY],
        FIELD_HEAD: (pull[FIELD_HEAD][FIELD_REF], pull[FIELD_HEAD][FIELD_SHA]),
        FIELD_BASE: pull[FIELD_BASE][FIELD_REF],
        FIELD_STATE: pull[FIELD_STATE],
    }


def test_an_issue_round_trip(ephemeral_repository: Any) -> None:
    repository = ephemeral_repository
    title = ISSUE_TITLE.format(run_id=repository.run_id)
    body = ISSUE_BODY.format(run_id=repository.run_id)
    comment = ISSUE_COMMENT.format(run_id=repository.run_id)

    label = _record(
        repository=repository,
        arguments=[CMD_CALL, OPERATION_CREATE_LABEL, OPTION_RAW_FIELD, FIELD_NAME + FIELD_ASSIGNMENT + LABEL],
    )
    assert label[FIELD_NAME] == LABEL, f"the created label is {label}"

    created = _record(repository=repository, arguments=[CMD_CREATE_ISSUE, OPTION_TITLE, title, OPTION_BODY, body])
    number = created[FIELD_NUMBER]
    assert isinstance(number, int), f"the created issue has no number: {created}"
    issue = str(number)
    expected = {FIELD_NUMBER: number, FIELD_TITLE: title, FIELD_BODY: body, FIELD_STATE: STATE_OPEN}
    assert {field: created[field] for field in expected} == expected

    read = _record(repository=repository, arguments=[CMD_GET_ISSUE, issue])
    assert {field: read[field] for field in expected} == expected

    posted = _record(repository=repository, arguments=[CMD_COMMENT_ISSUE, issue, OPTION_BODY, comment])
    assert posted[FIELD_BODY] == comment, f"the posted comment is {posted}"

    comments = _records(repository=repository, arguments=[CMD_GET_ISSUE_COMMENTS, issue])
    assert [(each[FIELD_ID], each[FIELD_BODY]) for each in comments] == [(posted[FIELD_ID], comment)]

    added = _records(repository=repository, arguments=[CMD_LABEL_ADD, issue, OPTION_LABELS, LABEL])
    assert _label_names(labels=added) == [LABEL]

    labelled = _record(repository=repository, arguments=[CMD_GET_ISSUE, issue])
    assert _label_names(labels=labelled[FIELD_LABELS]) == [LABEL]

    closed = _record(repository=repository, arguments=[CMD_UPDATE_ISSUE, issue, OPTION_STATE, STATE_CLOSED])
    assert (closed[FIELD_NUMBER], closed[FIELD_STATE]) == (number, STATE_CLOSED)

    reread = _record(repository=repository, arguments=[CMD_GET_ISSUE, issue])
    assert (reread[FIELD_NUMBER], reread[FIELD_STATE]) == (number, STATE_CLOSED)


def test_a_pull_request_round_trip(ephemeral_repository: Any) -> None:
    repository = ephemeral_repository
    title = PULL_REQUEST_TITLE.format(run_id=repository.run_id)
    body = PULL_REQUEST_BODY.format(run_id=repository.run_id)
    pushed = _push_branch(repository=repository)

    created = _record(
        repository=repository,
        arguments=[
            CMD_CREATE_PR,
            OPTION_HEAD,
            BRANCH,
            OPTION_BASE,
            repository.default_branch,
            OPTION_TITLE,
            title,
            OPTION_BODY,
            body,
        ],
    )
    number = created[FIELD_NUMBER]
    assert isinstance(number, int), f"the created pull request has no number: {created}"
    pull = str(number)
    expected = {
        FIELD_NUMBER: number,
        FIELD_TITLE: title,
        FIELD_BODY: body,
        FIELD_HEAD: (BRANCH, pushed),
        FIELD_BASE: repository.default_branch,
        FIELD_STATE: STATE_OPEN,
    }
    assert _pull_request_view(pull=created) == expected

    read = _record(repository=repository, arguments=[CMD_GET_PR, pull])
    assert _pull_request_view(pull=read) == expected
    assert read[FIELD_MERGED] is False, f"pull request #{number} reads as merged before the merge: {read[FIELD_MERGED]}"

    merged = _record(repository=repository, arguments=[CMD_MERGE_PR, pull])
    assert merged[FIELD_MERGED] is True, f"the merge of pull request #{number} answered {merged}"

    after = _record(repository=repository, arguments=[CMD_GET_PR, pull])
    assert _pull_request_view(pull=after) == {**expected, FIELD_STATE: STATE_CLOSED}
    assert after[FIELD_MERGED] is True, f"pull request #{number} does not read as merged: {after[FIELD_MERGED]}"
