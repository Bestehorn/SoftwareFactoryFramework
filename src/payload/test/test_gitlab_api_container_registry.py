"""Tests for ``gitlab_api/container_registry.py`` — the login, origin and registry token a registry request needs.

What is pinned (issue #63, ``design.md`` D4 and "Correctness Properties" AC-5.2):

- under a ``job`` token, ``send`` logs in as ``gitlab-ci-token`` and asks GitLab nothing for the login: no
  ``GET /user`` (step 1); ``GET /projects/<project>`` carries the configured ``Job-token`` (step 2); the ``/jwt/auth``
  request carries ``Authorization: Basic`` of ``gitlab-ci-token:<token>`` as its only credential header (step 3); the
  registry request carries ``Authorization: Bearer <registry token>`` alone (step 4), and ``send`` returns its answer.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; each
test imports the production module inside its body, as ``test_gitlab_api_transport.py`` does, so a module not written
yet fails the test on an assertion. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by
path) are installed for every test; the fake serves the registry's origin as it serves the configured one. Every
expected URL, header and value is a literal (design.md D10).

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_container_registry.py`` (no network).
"""

from __future__ import annotations

import base64
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE_DIR = SCRIPTS_DIR / "gitlab_api"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

HOST = "gitlab.example.com"
TOKEN = "job-token-for-the-test"  # pragma: allowlist secret
REGISTRY_TOKEN = "registry-token-for-the-test"  # pragma: allowlist secret
FIXED_CLOCK_SECONDS = 1_000.0

TOKEN_TYPE_JOB = "job"
# The login of a job token (lib/gitlab/auth.rb CI_JOB_USER; design.md D4 step 1, Sources).
JOB_LOGIN = "gitlab-ci-token"

# The credential headers, by lower-cased name (conventions.md "Credential types").
HEADER_PRIVATE_TOKEN = "private-token"
HEADER_JOB_TOKEN = "job-token"
HEADER_AUTHORIZATION = "authorization"
CREDENTIAL_HEADER_NAMES = frozenset({HEADER_PRIVATE_TOKEN, HEADER_JOB_TOKEN, HEADER_AUTHORIZATION})
BASIC_PREFIX = "Basic "
BEARER_PREFIX = "Bearer "

# The answer fields the steps read (design.md D4): `username` of `GET /user`, `container_registry_image_prefix` of
# "Retrieve a project", `token` of `/jwt/auth`.
FIELD_USERNAME = "username"
FIELD_ID = "id"
FIELD_IMAGE_PREFIX = "container_registry_image_prefix"
FIELD_TOKEN = "token"

# `package#delete-image-tags-by-reference` with `CI_REGISTRY_IMAGE=group/project` and `CI_COMMIT_SHORT_SHA=1a2b3c4`, as
# `registry.send` hands it on (D4): the path after `/http(s)://${CI_REGISTRY}` and the `token_scope`, each `${NAME}`
# written; the configured project.
METHOD_DELETE = "DELETE"
REGISTRY_PATH = "/v2/group/project/tags/reference/1a2b3c4"
SCOPE = "repository:group/project:delete"
PROJECT = "group/project"

USER_URL = "https://gitlab.example.com/api/v4/user"
PROJECT_URL = "https://gitlab.example.com/api/v4/projects/group%2Fproject"
JWT_URL = "https://gitlab.example.com/jwt/auth?service=container_registry&scope=repository%3Agroup%2Fproject%3Adelete"
REGISTRY_URL = "https://registry.example.com/v2/group/project/tags/reference/1a2b3c4"
# The answer the fake gives the registry request, returned by `send` as step 4's Response.
REGISTRY_STATUS = 202


def fixed_clock() -> float:
    return FIXED_CLOCK_SECONDS


def refuse_sleep(seconds: float, /) -> None:
    """Stands in for ``time.sleep``: no answer of these tests asks for a wait."""
    raise AssertionError(f"the transport waited {seconds} seconds; no answer here is a 429")


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` inside a test, so a module not written yet fails it on an assertion."""
    source = PACKAGE_DIR / f"{name}.py"
    assert source.is_file(), f"gitlab_api/{name}.py does not exist under {SCRIPTS_DIR}"
    return importlib.import_module(name=f"gitlab_api.{name}")


def credentials_sent(*, request: Any) -> Dict[str, str]:
    """Every credential header the recorded request carried, by lower-cased name."""
    return {name.lower(): value for name, value in request.headers.items() if name.lower() in CREDENTIAL_HEADER_NAMES}


# --- AC-5.2 a job token's login -------------------------------------------------------------------------------------


def test_a_job_token_logs_in_as_gitlab_ci_token(fake_gitlab: Any) -> None:
    container_registry = gitlab_module(name="container_registry")
    transport = gitlab_module(name="transport")
    client = transport.Transport(
        host=HOST,
        token=TOKEN,
        token_type=transport.TokenType(TOKEN_TYPE_JOB),
        sleep=refuse_sleep,
        clock=fixed_clock,
    )
    # A `GET /user` would be answered with another login, so a lookup shows in the requests and in the Basic login.
    fake_gitlab.script(method="GET", url=USER_URL, body={FIELD_USERNAME: "the-user-of-the-token"})
    fake_gitlab.script(
        method="GET",
        url=PROJECT_URL,
        body={FIELD_ID: 1, FIELD_IMAGE_PREFIX: "registry.example.com/group/project"},
    )
    fake_gitlab.script(method="GET", url=JWT_URL, body={FIELD_TOKEN: REGISTRY_TOKEN})
    fake_gitlab.script(method=METHOD_DELETE, url=REGISTRY_URL, status=REGISTRY_STATUS)

    response = container_registry.send(
        transport=client,
        method=METHOD_DELETE,
        path=REGISTRY_PATH,
        query=(),
        scope=SCOPE,
        project=PROJECT,
    )

    assert [(request.method, request.url) for request in fake_gitlab.requests] == [
        ("GET", PROJECT_URL),
        ("GET", JWT_URL),
        (METHOD_DELETE, REGISTRY_URL),
    ], "a job token sends no GET /user: the project, the registry token, then the registry (D4 steps 2 to 4)"
    assert fake_gitlab.remaining() == [("GET", USER_URL)], "the login of a job token is not looked up (D4 step 1)"

    project_request, jwt_request, registry_request = fake_gitlab.requests
    assert credentials_sent(request=project_request) == {HEADER_JOB_TOKEN: TOKEN}, (
        "the project is read with the configured header (D4 step 2)"
    )

    jwt_credentials = credentials_sent(request=jwt_request)
    assert list(jwt_credentials) == [HEADER_AUTHORIZATION], (
        f"Authorization is the /jwt/auth request's only credential header (D4 step 3), got {sorted(jwt_credentials)}"
    )
    authorization = jwt_credentials[HEADER_AUTHORIZATION]
    assert authorization.startswith(BASIC_PREFIX), (
        f"the /jwt/auth credential is Basic (RFC 7617), got {authorization!r}"
    )
    login_and_token = base64.b64decode(s=authorization[len(BASIC_PREFIX) :], validate=True).decode(encoding="utf-8")
    assert login_and_token == f"{JOB_LOGIN}:{TOKEN}", (
        "Basic decodes to gitlab-ci-token:<token> for a job token (AC-5.2)"
    )

    assert credentials_sent(request=registry_request) == {HEADER_AUTHORIZATION: f"{BEARER_PREFIX}{REGISTRY_TOKEN}"}, (
        "the registry request carries the registry token alone (D4 step 4, UB-2)"
    )
    assert all(TOKEN not in value for value in registry_request.headers.values()), (
        "the configured token reaches no request off the configured origin (UB-2)"
    )
    assert response.status == REGISTRY_STATUS, "send returns the registry's answer (D4 step 4)"
