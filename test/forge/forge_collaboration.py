"""F:collaboration, issue #32's slice of the forge suite: ``call`` on the ``issues``, ``reactions``, ``pulls``,
``search``, ``activity`` and ``gists`` records, against this run's ephemeral repository (issue #10, design.md D6).

Each test takes the session's ``ephemeral_repository``, runs the product wrapper through its ``wrapper`` (the test
marker set, the clone as working directory) and asserts every invocation's exit code and what it printed, against
what the test knows in advance (AC-8.1, AC-8.5). No call names an owner or a repository, so every repository record
targets the clone's ``origin``; ``<hex>`` is a fresh ``uuid.uuid4().hex`` of the test.

- ``test_issue_and_reaction_records``: the issue is made with ``create-issue``, since ``call`` refuses
  ``issues/create`` and names that subcommand; then ``call issues/get`` answers its ``number`` and ``title``, ``call
  reactions/create-for-issue -f content=+1`` answers a ``+1`` reaction, and ``call reactions/list-for-issue`` lists
  exactly that one. The issue is this test's own, so the other slices' issues in the repository change no answer.
- ``test_pulls_search_activity_and_gists_records``: the reads whose answer a new private repository fixes.
  ``pulls/list`` filtered by ``head`` on a branch no test pushes answers ``[]``. ``search/repos`` for ``<hex>``
  answers ``[]``: a fresh random text has a known answer, while GitHub documents no indexing delay for a new
  private repository, so nothing asserts that the repository is found. ``activity/list-stargazers-for-repo``
  answers ``[]``, as no one stars the repository. ``gists/get`` of ``<hex>`` exits 1 with ``HTTP 404``
  (docs.github.com "Get a gist": ``404`` "Resource not found") and prints nothing: a read that creates nothing,
  since the token is the test organization's and account permissions "can only be used when the current user is
  the resource owner", so it reaches no user gist, and ``gists/list-public`` would page every public gist, as
  ``call`` reads every page of a ``Paging.LINK`` record.

The token's permissions (D6's table): Issues (write) for ``create-issue``, ``issues/get`` and the two reaction
records; Pull requests for ``pulls/list``; Contents for ``activity/list-stargazers-for-repo``; ``search/repos`` and
``gists/get`` need none.

Run: ``python scripts/run_tests.py --workers 1 test/forge``.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, List, Sequence

# The product wrapper's subcommands and the options of ``call`` (``github_api/commands/call.py``, ``issues.py``).
CALL = "call"
CREATE_ISSUE = "create-issue"
TITLE_OPTION = "--title"
PATH_OPTION = "--path"
QUERY_OPTION = "--query"
RAW_FIELD_OPTION = "-f"
ASSIGNMENT = "="

# The records this slice sends, by operation ID (``github_api/families/``).
ISSUE_GET = "issues/get"
REACTION_CREATE = "reactions/create-for-issue"
REACTION_LIST = "reactions/list-for-issue"
PULL_LIST = "pulls/list"
REPOSITORY_SEARCH = "search/repos"
STARGAZER_LIST = "activity/list-stargazers-for-repo"
GIST_GET = "gists/get"

# Their parameters, and the fields of their answers this slice reads.
ISSUE_NUMBER_PARAMETER = "issue_number"
CONTENT_PARAMETER = "content"
STATE_PARAMETER = "state"
HEAD_PARAMETER = "head"
SEARCH_PARAMETER = "q"
GIST_PARAMETER = "gist_id"
FIELD_NUMBER = "number"
FIELD_TITLE = "title"
FIELD_CONTENT = "content"

REACTION_PLUS_ONE = "+1"
STATE_ALL = "all"
ISSUE_TITLE_PREFIX = "forge-collaboration-"
#: A branch no test pushes; ``pulls/list`` takes ``head`` as ``<organization>:<branch>``.
ABSENT_BRANCH_PREFIX = "forge-absent-"
HEAD_SEPARATOR = ":"

WRAPPER_EXIT_OK = 0
#: The product wrapper's exit on a ``GitHubAPIError``, whose ``ERROR:`` line names the status
#: (``transport._http_failure``: ``... failed: HTTP <status>``).
WRAPPER_API_FAILURE = 1
NOT_FOUND_ANSWER = re.compile(r"\bHTTP 404\b")


def _assignment(*, option: str, name: str, value: str) -> List[str]:
    """One ``NAME=VALUE`` of ``call``: ``<option> <name>=<value>``."""
    return [option, name + ASSIGNMENT + value]


def _answer(*, repository: Any, arguments: Sequence[str]) -> Any:
    """The JSON the product wrapper printed for ``arguments``, after asserting that it exited 0."""
    invocation = repository.wrapper.run(arguments=list(arguments))
    assert invocation.returncode == WRAPPER_EXIT_OK, (
        f"`{' '.join(arguments)}` exited {invocation.returncode}, not {WRAPPER_EXIT_OK}: {invocation.stderr}"
    )
    return invocation.json()


def test_issue_and_reaction_records(ephemeral_repository: Any) -> None:
    title = ISSUE_TITLE_PREFIX + uuid.uuid4().hex
    created = _answer(repository=ephemeral_repository, arguments=[CREATE_ISSUE, TITLE_OPTION, title])
    assert created[FIELD_TITLE] == title, f"`{CREATE_ISSUE}` answered the title {created[FIELD_TITLE]!r}"
    number = created[FIELD_NUMBER]
    assert isinstance(number, int), f"`{CREATE_ISSUE}` answered the number {number!r}, not an integer"
    issue = _assignment(option=PATH_OPTION, name=ISSUE_NUMBER_PARAMETER, value=str(number))

    read = _answer(repository=ephemeral_repository, arguments=[CALL, ISSUE_GET, *issue])
    assert read[FIELD_NUMBER] == number, f"`{ISSUE_GET}` answered the number {read[FIELD_NUMBER]!r}, not {number}"
    assert read[FIELD_TITLE] == title, f"`{ISSUE_GET}` answered the title {read[FIELD_TITLE]!r}, not {title!r}"

    plus_one = _assignment(option=RAW_FIELD_OPTION, name=CONTENT_PARAMETER, value=REACTION_PLUS_ONE)
    reaction = _answer(repository=ephemeral_repository, arguments=[CALL, REACTION_CREATE, *issue, *plus_one])
    assert reaction[FIELD_CONTENT] == REACTION_PLUS_ONE, (
        f"`{REACTION_CREATE}` answered the content {reaction[FIELD_CONTENT]!r}, not {REACTION_PLUS_ONE!r}"
    )

    reactions = _answer(repository=ephemeral_repository, arguments=[CALL, REACTION_LIST, *issue])
    assert isinstance(reactions, list), f"`{REACTION_LIST}` printed {reactions!r}, not a list"
    contents = [item[FIELD_CONTENT] for item in reactions]
    assert contents == [REACTION_PLUS_ONE], f"`{REACTION_LIST}` listed the reactions {contents}, not one +1"


def test_pulls_search_activity_and_gists_records(ephemeral_repository: Any) -> None:
    fresh = uuid.uuid4().hex
    head = ephemeral_repository.owner + HEAD_SEPARATOR + ABSENT_BRANCH_PREFIX + fresh
    pulls = _answer(
        repository=ephemeral_repository,
        arguments=[
            CALL,
            PULL_LIST,
            *_assignment(option=QUERY_OPTION, name=STATE_PARAMETER, value=STATE_ALL),
            *_assignment(option=QUERY_OPTION, name=HEAD_PARAMETER, value=head),
        ],
    )
    assert pulls == [], f"`{PULL_LIST}` with the head {head} listed {pulls!r}, not []"

    found = _answer(
        repository=ephemeral_repository,
        arguments=[CALL, REPOSITORY_SEARCH, *_assignment(option=QUERY_OPTION, name=SEARCH_PARAMETER, value=fresh)],
    )
    assert found == [], f"`{REPOSITORY_SEARCH}` for {fresh} found {found!r}, not []"

    stargazers = _answer(repository=ephemeral_repository, arguments=[CALL, STARGAZER_LIST])
    assert stargazers == [], f"`{STARGAZER_LIST}` listed {stargazers!r}, not []"

    gist = ephemeral_repository.wrapper.run(
        arguments=[CALL, GIST_GET, *_assignment(option=PATH_OPTION, name=GIST_PARAMETER, value=fresh)]
    )
    assert gist.returncode == WRAPPER_API_FAILURE, (
        f"`{GIST_GET}` of {fresh} exited {gist.returncode}, not {WRAPPER_API_FAILURE}: {gist.stderr}"
    )
    assert NOT_FOUND_ANSWER.search(string=gist.stderr), (
        f"`{GIST_GET}` of {fresh} did not answer HTTP 404: {gist.stderr}"
    )
    assert gist.stdout == "", f"`{GIST_GET}` of {fresh} printed {gist.stdout!r}"
