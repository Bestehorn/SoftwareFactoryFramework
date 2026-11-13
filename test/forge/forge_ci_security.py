"""F:ci_security (issue #31's slice): the CI and security families' records, sent to this run's repository (D6).

Each test sends one record of the ``actions``, ``code-scanning``, ``secret-scanning`` or ``dependabot`` family through
the product wrapper's ``call``, with the test marker set and the clone as the working directory and no ``--path``, so
the record's ``{owner}`` and ``{repo}`` are the clone's ``origin``: this run's private ``sff-test-*`` repository of the
test organization, whose seed holds no workflow file. Each test asserts the invocation's exit code and what it printed
against the answer GitHub documents for such a repository (AC-8.1, AC-8.4):

- ``actions/list-workflow-runs-for-repo``: no workflow run (``[]``), since no workflow file is ever pushed;
- ``code-scanning/list-alerts-for-repo``: exit 1 with ``HTTP 403``, "Response if GitHub Advanced Security is not
  enabled for this repository" (docs.github.com "List code scanning alerts for a repository"), and not "Resource not
  accessible by personal access token", the answer to a missing permission (``docs/api-reference/github/conventions.md``
  "Authentication");
- ``secret-scanning/list-alerts-for-repo``: exit 1 with ``HTTP 404``, "Repository is public, or secret scanning is
  disabled for the repository, or the resource is not found" (docs.github.com "List secret scanning alerts for a
  repository");
- ``dependabot/list-repo-secrets``: no Dependabot secret (``[]``), an answer documented for any repository; the
  family's alerts record is not sent, since its documented ``403`` "Forbidden" does not tell a disabled feature from a
  missing permission.

The ``checks`` family is named here and not called: GitHub lists "Using fine-grained personal access token to call the
Checks API" among the gaps of the fine-grained personal access token, the kind the test credential is (docs.github.com
"Managing your personal access tokens"; ``conventions.md`` "no Checks API"), so no permission of the test token reaches
it.

Run: ``python scripts/run_tests.py --workers 1 test/forge`` (D1), with the test credential file in place (D8).
"""

from __future__ import annotations

import re
from typing import Any

# The ``call`` subcommand and the records this slice sends (``src/payload/scripts/github_api/families/``).
CALL_SUBCOMMAND = "call"
WORKFLOW_RUNS = "actions/list-workflow-runs-for-repo"
CODE_SCANNING_ALERTS = "code-scanning/list-alerts-for-repo"
SECRET_SCANNING_ALERTS = "secret-scanning/list-alerts-for-repo"  # pragma: allowlist secret
DEPENDABOT_SECRETS = "dependabot/list-repo-secrets"  # pragma: allowlist secret

# The product wrapper's exits: 0 for an answered record, 1 for a ``GitHubAPIError``, whose ``ERROR:`` line on standard
# error names the status (``transport._http_failure``: ``... failed: HTTP <status>``) and whose ``Details:`` line the
# error body. A failed record prints nothing on standard output.
WRAPPER_EXIT_OK = 0
WRAPPER_API_FAILURE = 1
NOTHING_PRINTED = ""
NO_ITEMS: list[Any] = []
FORBIDDEN_ANSWER = re.compile(r"\bHTTP 403\b")
NOT_FOUND_ANSWER = re.compile(r"\bHTTP 404\b")
# The message of GitHub's answer to a fine-grained token that lacks the record's permission (``conventions.md``
# "Authentication").
MISSING_PERMISSION_ANSWER = "Resource not accessible by personal access token"


def _described(*, invocation: Any) -> str:
    """What one invocation answered, for an assertion's message: its exit code, standard output and standard error."""
    return (
        f"the product wrapper exited {invocation.returncode}\n"
        f"standard output:\n{invocation.stdout}\n"
        f"standard error:\n{invocation.stderr}"
    )


def _call(*, repository: Any, operation: str) -> Any:
    """The ``Invocation`` of ``call <operation>`` with no parameter, in ``repository``'s clone: the record targets the
    clone's ``origin``."""
    return repository.wrapper.run(arguments=[CALL_SUBCOMMAND, operation])


def _assert_lists_nothing(*, invocation: Any, operation: str) -> None:
    """``invocation`` exited 0 and printed an empty JSON array: ``call`` prints every item of every page of a paged
    record as one array, and ``operation`` answered none."""
    assert invocation.returncode == WRAPPER_EXIT_OK, f"{operation}: {_described(invocation=invocation)}"
    listed = invocation.json()
    assert listed == NO_ITEMS, f"{operation} listed {listed}, expected {NO_ITEMS}"


def _assert_answered_with(*, invocation: Any, operation: str, status: re.Pattern[str]) -> None:
    """``invocation`` exited 1, printed nothing, and its standard error names the HTTP ``status``."""
    described = _described(invocation=invocation)
    assert invocation.returncode == WRAPPER_API_FAILURE, f"{operation}: {described}"
    assert status.search(string=invocation.stderr), f"{operation} answered no `{status.pattern}`: {described}"
    assert invocation.stdout == NOTHING_PRINTED, f"{operation} printed an answer: {described}"


def test_no_workflow_has_run(ephemeral_repository: Any) -> None:
    """``call actions/list-workflow-runs-for-repo``: exit 0 and ``[]``, as the repository never held a workflow."""
    invocation = _call(repository=ephemeral_repository, operation=WORKFLOW_RUNS)
    _assert_lists_nothing(invocation=invocation, operation=WORKFLOW_RUNS)


def test_code_scanning_answers_as_documented(ephemeral_repository: Any) -> None:
    """``call code-scanning/list-alerts-for-repo``: exit 1 with ``HTTP 403``, GitHub Advanced Security not enabled, and
    not the missing-permission answer, which is a ``403`` too."""
    invocation = _call(repository=ephemeral_repository, operation=CODE_SCANNING_ALERTS)
    _assert_answered_with(invocation=invocation, operation=CODE_SCANNING_ALERTS, status=FORBIDDEN_ANSWER)
    assert MISSING_PERMISSION_ANSWER not in invocation.stderr, (
        f"{CODE_SCANNING_ALERTS} was refused for a missing permission of the test token: "
        f"{_described(invocation=invocation)}"
    )


def test_secret_scanning_answers_as_documented(ephemeral_repository: Any) -> None:
    """``call secret-scanning/list-alerts-for-repo``: exit 1 with ``HTTP 404``, secret scanning being disabled for the
    private repository."""
    invocation = _call(repository=ephemeral_repository, operation=SECRET_SCANNING_ALERTS)
    _assert_answered_with(invocation=invocation, operation=SECRET_SCANNING_ALERTS, status=NOT_FOUND_ANSWER)


def test_dependabot_lists_no_secret(ephemeral_repository: Any) -> None:
    """``call dependabot/list-repo-secrets``: exit 0 and ``[]``, as the repository holds no Dependabot secret."""
    invocation = _call(repository=ephemeral_repository, operation=DEPENDABOT_SECRETS)
    _assert_lists_nothing(invocation=invocation, operation=DEPENDABOT_SECRETS)
