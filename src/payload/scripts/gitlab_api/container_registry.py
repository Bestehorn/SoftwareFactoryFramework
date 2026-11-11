"""The container registry of a GitLab instance: the login, the origin and the registry token a registry request needs,
then the request itself (issue #63, design.md D4).

A record whose path starts ``/http(s)://${CI_REGISTRY}`` (``registry.Base.CONTAINER_REGISTRY``) is sent to the
registry, not to the configured host. ``registry.send`` hands ``send`` the record's method, its path after that root
and its query, each ``${NAME}`` written, the record's ``token_scope`` with each ``${NAME}`` written, and the configured
project. ``send`` then takes four steps, each only once the one before it has succeeded:

1. ``login``: for a ``private`` token, the ``username`` of ``GET /user``
   (``software-supply-chain-security#as-a-regular-user-1``); for a ``job`` token ``gitlab-ci-token``, with no request
   (gitlab-org/gitlab ``lib/gitlab/auth.rb`` ``CI_JOB_USER``); a ``bearer`` token raises ``GitLabAPIError`` with
   nothing sent, as the registry's authentication page lists no OAuth credential;
2. ``registry_origin``: ``https://`` and the text before the first ``/`` of the configured project's
   ``container_registry_image_prefix`` (``tenant-scale#retrieve-a-project``), a text that must be non-empty and hold
   none of ``@``, ``?``, ``#``, ``\\`` or white space, else ``GitLabAPIError`` is raised before step 3;
3. ``Transport.container_registry_token``: the registry token, asked of the configured host's ``/jwt/auth`` for the
   scope with ``Authorization: Basic`` of the login and the configured token;
4. ``Transport.container_registry_request``: the request, sent to the registry origin with ``Authorization: Bearer``
   of the registry token alone; its ``Response`` is returned.

Steps 1 and 2 are sent through ``registry.send`` as any REST record is: with the configured credential header, to the
configured origin. Each way a step can fail raises ``GitLabAPIError`` before step 4, so the registry receives nothing
(design.md D4 "AC-5.3"): an error status or no response (``Transport._send``), an answer that is not a JSON object
whose field the step reads is a non-empty string (``username``, ``container_registry_image_prefix``, ``token``), and a
registry origin ``transport.origin`` refuses. The configured token is held by the transport alone and never read here;
the registry token goes from step 3 to step 4 and into no exception message of this module, which writes no log record.
Nothing here reads the process environment. Standard library only; Python 3.9.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from gitlab_api import registry
from gitlab_api.errors import GitLabAPIError

if TYPE_CHECKING:
    # For the annotations only: gitlab_api.transport imports gitlab_api.registry, which sends a container-registry
    # record through this module.
    from gitlab_api.transport import Response, Transport

# Step 1 (design.md D4): the record of `GET /user` and its answer's login field; the login of a job token
# (gitlab-org/gitlab `lib/gitlab/auth.rb` `find_for_git_client`: a job token is read only under CI_JOB_USER).
OP_CURRENT_USER = "software-supply-chain-security#as-a-regular-user-1"
FIELD_USERNAME = "username"
JOB_LOGIN = "gitlab-ci-token"

# Step 2 (design.md D4): the record of "Retrieve a project", its path parameter, and the answer field whose text before
# the first `/` is the registry's host (doc/api/projects.md: `registry.example.com/diaspora/diaspora-client`).
OP_RETRIEVE_PROJECT = "tenant-scale#retrieve-a-project"
PATH_ID = "id"
FIELD_IMAGE_PREFIX = "container_registry_image_prefix"
HOST_END = "/"
REGISTRY_SCHEME = "https://"
# What the registry's host may not hold: userinfo (`@`), a query (`?`), a fragment (`#`), a backslash, white space.
REFUSED_IN_HOST = re.compile(pattern=r"[@?#\\\s]")


def _answer_text(*, answer: Any, field: str, operation_id: str) -> str:
    """The non-empty string at ``field`` of ``answer``, the decoded answer of the record ``operation_id``. An answer
    that is not a JSON object, or whose ``field`` is absent or not a non-empty string, raises ``GitLabAPIError`` naming
    the record and the field (design.md D4 "AC-5.3")."""
    text = answer.get(field) if isinstance(answer, Mapping) else None
    if isinstance(text, str) and text:
        return text
    raise GitLabAPIError(
        f"{operation_id} answered no non-empty string {field!r}, which a container-registry request needs: nothing is "
        "sent to the registry"
    )


def login(*, transport: Transport) -> str:
    """The login the configured token is sent under to ``/jwt/auth`` (design.md D4 step 1).

    A ``private`` token logs in as its user: the ``username`` of ``GET /user``, sent through ``registry.send``; an
    answer without a non-empty string ``username`` raises ``GitLabAPIError``. A ``job`` token logs in as
    ``gitlab-ci-token``, with no request. A ``bearer`` token raises ``GitLabAPIError`` with nothing sent."""
    # Imported here, not at the top: gitlab_api.transport imports gitlab_api.registry, which sends a container-registry
    # record through this module.
    from gitlab_api.transport import TokenType

    if transport.token_type is TokenType.PRIVATE:
        answer = registry.send(transport=transport, operation_id=OP_CURRENT_USER).value
        return _answer_text(answer=answer, field=FIELD_USERNAME, operation_id=OP_CURRENT_USER)
    if transport.token_type is TokenType.JOB:
        return JOB_LOGIN
    raise GitLabAPIError(
        f"token_type {transport.token_type.value!r} has no login the container registry's /jwt/auth accepts: a "
        "container-registry record is sent with a private or a job token"
    )


def registry_origin(*, transport: Transport, project: str) -> str:
    """The origin of the configured project's container registry (design.md D4 step 2).

    ``GET /projects/<project>`` is sent through ``registry.send``; the origin is ``https://`` and the text of its
    answer's ``container_registry_image_prefix`` before the first ``/``, so ``registry.example.com/group/project`` gives
    ``https://registry.example.com``. An answer without a non-empty string ``container_registry_image_prefix`` raises
    ``GitLabAPIError`` naming the field; a text before the first ``/`` that is empty, or holds ``@``, ``?``, ``#``,
    ``\\`` or white space, raises ``GitLabAPIError`` naming the prefix."""
    answer = registry.send(transport=transport, operation_id=OP_RETRIEVE_PROJECT, values={PATH_ID: project}).value
    prefix = _answer_text(answer=answer, field=FIELD_IMAGE_PREFIX, operation_id=OP_RETRIEVE_PROJECT)
    host = prefix.split(sep=HOST_END, maxsplit=1)[0]
    if not host or REFUSED_IN_HOST.search(string=host):
        raise GitLabAPIError(
            f"the project {project!r} answered the {FIELD_IMAGE_PREFIX} {prefix!r}, whose registry host before the "
            "first '/' is empty or holds '@', '?', '#', a backslash or white space"
        )
    return REGISTRY_SCHEME + host


def send(
    *,
    transport: Transport,
    method: str,
    path: str,
    query: Sequence[registry.Pair],
    scope: str,
    project: str,
) -> Response:
    """One request of a container-registry record, sent to the registry with a registry token (design.md D4).

    ``path`` is the record's path after ``/http(s)://${CI_REGISTRY}`` and ``scope`` its ``token_scope``, each with the
    call's values written; ``query`` is the request's query pairs; ``project`` is the configured project. The four steps
    of the module docstring are taken in order, and the registry's ``Response`` is returned; a step that fails raises
    ``GitLabAPIError`` with nothing sent to the registry (design.md D4 "AC-5.3")."""
    registry_login = login(transport=transport)
    origin = registry_origin(transport=transport, project=project)
    registry_token = transport.container_registry_token(login=registry_login, scope=scope)
    return transport.container_registry_request(
        origin=origin, method=method, path=path, query=query, token=registry_token
    )
