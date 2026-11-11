"""Tests for ``gitlab_api/registry.py`` — the operation records, path expansion, value encoding and id lookup.

What is pinned (issue #13, ``design.md`` D5): a value substituted into a path parameter is ONE percent-encoded segment
(``/`` as ``%2F``; an empty value, ``.`` and ``..`` refused — AC-2.2); an array of hashes in a query string or a form
body is sent in the bracket form ``name[0][key]=value`` (AC-2.3); ``lookup`` refuses an unknown and a twice-declared
operation id, each naming the id, and ``call`` refuses a value its record does not declare, naming it, before anything
is sent (AC-1.1).

Issue #41 (``design.md`` D2) adds: ``send`` returns the ``Response`` of a REST record's request and refuses a GraphQL
record with nothing sent (AC-1.2); ``attribute_name`` drops one trailing ``[]`` (AC-1.3); ``variables`` names each
``$name`` that a ``:`` follows in a record's document, in order, a connection record's cursor ``after`` left out
(AC-2.2). Their ``GraphQLOperation`` records carry D2's ``capability``.

Issue #44 (``design.md`` D4) adds: ``upload_variables`` maps each variable a record's document defines with the type
``Upload``, or a list of it, to whether it is a list; ``split_uploads`` replaces each ``pathlib.Path`` value, and each
one in a list, with ``None`` and returns the files with the operations path each fills, in order (AC-3.1).
``upload_variables`` also leaves out a definition that has no type, and still reads the ones around it.

Issue #40 (``design.md`` D1, D5) adds the path forms of the reference: ``placeholders`` names every ``:name`` and
``*name`` in path order (AC-2.4); ``expand`` writes a ``*name`` glob with each ``/`` kept and each part one segment,
refusing an empty, ``.`` or ``..`` part (AC-2.1, AC-2.2), an optional ``(...)`` group only when its parameter has a
value (AC-2.3), and an escaped ``\\(`` or ``\\)`` as its parenthesis (AC-2.5); ``send`` sends a raw-body record the
bytes it is given as its body, and refuses bytes for any other record with nothing sent (AC-3.2).

Issue #43 (``design.md`` D1, D2) adds: ``placeholders`` reads a name that continues past a ``-`` a name character
follows as one name (``:module-name``), and ``expand`` writes it as one segment, while the in-segment forms hold the
names they hold on #40's base (AC-3.1, UB-4); ``route`` writes the prefix value a call names in place of a record's
``/<route-prefix>``, and returns a record with no route prefix, given none, as itself (AC-2.2); ``expand`` and ``send``
refuse a prefix record no prefix was written into, with nothing sent (AC-2.4).

Issue #63 (``design.md`` D1 to D5) adds the request forms the records lacked, each on synthetic records: ``lookup``
returns, of the records one family declares with an id, the one whose ``(method, path)`` equals the ``endpoint`` it is
given, and the first declared when it is given none; any other endpoint is refused naming the declared ones in order,
and an id declared twice is refused as before (AC-2.2, AC-2.4). ``expand`` writes each place of a name in a record's
``positional_names`` from its own value, while any other name still takes its one value at every place (AC-3.1,
AC-3.2, UB-1), and a ``[.name]`` suffix as ``.`` and its value only when it is given (AC-4.1). ``base_of`` reads
whether a path is sent under ``/api/v4``, at the host root or to the container registry (AC-5.1); ``encode`` sends a
``Location.HEADER`` value as a request header and nowhere else (AC-6.2); ``send`` refuses a container-registry record
given no project, with nothing sent (AC-5.2).

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; each
test imports the production module inside its body, so a module not written yet fails the test on an assertion. The
fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_registry.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE_DIR = SCRIPTS_DIR / "gitlab_api"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# The keywords of ``Transport.request`` that ``registry.encode``'s result feeds (design.md D4, D5).
PART_QUERY = "query"
PART_FORM = "form"

# conventions.md "Arrays, hashes and arrays of hashes": `variables[0][key]=VAR1&variables[0][value]=hello&...`.
VARIABLES = [{"key": "VAR1", "value": "hello"}, {"key": "VAR2", "value": "world"}]
VARIABLES_PAIRS = [
    ("variables[0][key]", "VAR1"),
    ("variables[0][value]", "hello"),
    ("variables[1][key]", "VAR2"),
    ("variables[1][value]", "world"),
]

# The record `registry.call` reaches through a monkeypatched `lookup`, and a value it does not declare: a misspelling
# of its declared `confidential`, which `call` must refuse rather than send or drop.
CALL_OPERATION_ID = "synthetic#update-an-issue"
UNDECLARED_NAME = "confidental"
# The `Transport` of design.md D4 built for a test: a fixed clock, a recording sleep, the default opener.
FIXED_CLOCK_SECONDS = 0.0
TOKEN_TYPE_PRIVATE = "private"

# The records of the registry additions (issue #41, design.md D2). `send` is tested on a REST record answered `204` (an
# empty body, whose decoded value is `None`, so only the `Response` itself tells `send` from `call`) and on a GraphQL
# record, which `send` refuses.
SEND_OPERATION_ID = "synthetic#delete-a-repository-branch"
SEND_PATH = "/projects/:id/repository/branches/:branch"
SEND_VALUES = {"id": "diaspora/diaspora", "branch": "feature/x"}
SEND_SENT_PATH = "/projects/diaspora%2Fdiaspora/repository/branches/feature%2Fx"
STATUS_NO_CONTENT = 204
GRAPHQL_OPERATION_ID = "graphql#syntheticProject"
SYNTHETIC_CAPABILITY = "Synthetic project lookup"
# design.md § Correctness Properties AC-2.2: `$fullPath` and `$first` are defined (`$first` with white space before its
# `:`); `$fullPath` in the selection set is a use, not a definition.
PROJECT_DOCUMENT = "query Q($fullPath: ID!, $first : Int = 2) { project(fullPath: $fullPath) { id } }"
# A connection document over several lines: `$after` is the cursor `Transport.graphql_nodes` sets on every page.
ISSUES_DOCUMENT = (
    "query Issues($fullPath: ID!,\n"
    "    $after: String) {\n"
    "  project(fullPath: $fullPath) { issues(after: $after) { nodes { iid } pageInfo { hasNextPage endCursor } } }\n"
    "}\n"
)
ISSUES_CONNECTION = ("project", "issues")

# The upload records of issue #44 (design.md D4, § Correctness Properties AC-3.1): `$files` is a list of `Upload`, with
# white space before its `:`; `$file` is one `Upload`; `$n` is a list of another type, so no upload variable.
UPLOAD_OPERATION_ID = "graphql#syntheticUpload"
FILES_DOCUMENT = "mutation M($files : [Upload!]!) { syntheticUpload(input: {files: $files}) { errors } }"
FILE_DOCUMENT = "mutation M($file: Upload) { syntheticUpload(input: {file: $file}) { errors } }"
INT_LIST_DOCUMENT = "query Q($n: [Int!]) { syntheticList(n: $n) { id } }"
ALL_UPLOADS_DOCUMENT = (
    "mutation M($files : [Upload!]!, $file: Upload,\n"
    "    $n: [Int!]) {\n"
    "  syntheticUpload(input: {files: $files, file: $file, n: $n}) { errors }\n"
    "}\n"
)
FILES_UPLOADS: Dict[str, bool] = {"files": True}
FILE_UPLOADS: Dict[str, bool] = {"file": False}
NO_UPLOADS: Dict[str, bool] = {}
ALL_UPLOADS: Dict[str, bool] = {"files": True, "file": False}
# `split_uploads`' values as `commands/call.py` `call_values` gives them (design.md D4): a list of files, one file, and
# text. The files are never read here, so they need not exist.
FIRST_FILE = Path("first.png")
SECOND_FILE = Path("second.png")
THIRD_FILE = Path("import.csv")
SPLIT_VALUES: Dict[str, Any] = {"projectPath": "g/p", "files": [FIRST_FILE, SECOND_FILE], "file": THIRD_FILE}
SPLIT_VARIABLES: Dict[str, Any] = {"projectPath": "g/p", "files": [None, None], "file": None}
SPLIT_FILES: Tuple[Tuple[str, Path], ...] = (
    ("variables.files.0", FIRST_FILE),
    ("variables.files.1", SECOND_FILE),
    ("variables.file", THIRD_FILE),
)
# The path forms of issue #40 (design.md D1), each on a reference path of operations-index.md as its row writes it (a
# `\` is `\\` here, as `families/openapi_only.py` spells it): a `*name` glob, an optional `(...)` group, an escaped
# parenthesis, and a `:name` inside a segment.
MAVEN_OPERATION_ID = "synthetic#workhorse-authorize-the-maven-package-file-upload"
MAVEN_AUTHORIZE_PATH = "/projects/:id/packages/maven/*path/:file_name/authorize"
MAVEN_VALUES = {"id": 1, "file_name": "x.jar"}
# The glob of MAVEN_AUTHORIZE_PATH as a refusal names it (design.md § Correctness Properties AC-2.2).
MAVEN_GLOB = "*path"
GENERIC_OPERATION_ID = "synthetic#download-package-file"
GENERIC_PACKAGE_PATH = "/projects/:id/packages/generic/:package_name/*package_version/(*path/):file_name"
GENERIC_VALUES = {"id": 1, "package_name": "pkg", "package_version": "1.0", "file_name": "file.txt"}
GENERIC_WITH_GROUP = "/projects/1/packages/generic/pkg/1.0/a/b/file.txt"
GENERIC_WITHOUT_GROUP = "/projects/1/packages/generic/pkg/1.0/file.txt"
NUGET_SINGLE_PACKAGE_PATH = (
    "/projects/:project_id/packages/nuget/v2/Packages\\(Id='*package_name',Version='*package_version'\\)"
)
NUGET_FIND_BY_ID_PATH = "/projects/:project_id/packages/nuget/v2/FindPackagesById\\(\\)"
NUGET_ENUMERATE_PATH = "/projects/:project_id/packages/nuget/v2/Packages\\(\\)"
NUGET_METADATA_PATH = "/projects/:id/packages/nuget/v2/$metadata"
DEBIAN_INDEX_PATH = "/projects/:id/packages/debian/dists/*distribution/:component/binary-:architecture/Packages"
# design.md § Correctness Properties AC-2.5: each case's path and values, and the path `expand` writes for it.
ESCAPED_CASES = {
    "single-package": (NUGET_SINGLE_PACKAGE_PATH, {"project_id": 7, "package_name": "N", "package_version": "1.0"}),
    "find-by-id": (NUGET_FIND_BY_ID_PATH, {"project_id": 7}),
    "enumerate-with-no-value": (NUGET_ENUMERATE_PATH, {"project_id": 7}),
    "metadata": (NUGET_METADATA_PATH, {"id": 7}),
    "glob-value-with-parentheses": (
        NUGET_SINGLE_PACKAGE_PATH,
        {"project_id": 7, "package_name": "a(b)'", "package_version": "1.0"},
    ),
}
ESCAPED_WRITTEN = {
    "single-package": "/projects/7/packages/nuget/v2/Packages(Id='N',Version='1.0')",
    "find-by-id": "/projects/7/packages/nuget/v2/FindPackagesById()",
    "enumerate-with-no-value": "/projects/7/packages/nuget/v2/Packages()",
    "metadata": "/projects/7/packages/nuget/v2/$metadata",
    "glob-value-with-parentheses": "/projects/7/packages/nuget/v2/Packages(Id='a%28b%29%27',Version='1.0')",
}
# The raw-body record of design.md D5 on the reference path of `openapi-only#create-or-update-a-terraform-state`, a
# record on the same path that is not one, and bytes a text-layer read would translate (`\r\n`) or fail to decode
# (`\xff`) (design.md § Correctness Properties AC-3.2).
RAW_OPERATION_ID = "synthetic#create-or-update-a-terraform-state"
PLAIN_OPERATION_ID = "synthetic#create-or-update-a-terraform-state-without-a-raw-body"
TERRAFORM_STATE_PATH = "/projects/:id/terraform/state/:name"
TERRAFORM_STATE_VALUES = {"id": 1, "name": "production"}
TERRAFORM_STATE_SENT_PATH = "/projects/1/terraform/state/production"
RAW_MEDIA_TYPE = "application/octet-stream"
RAW_BYTES = b"terraform state\r\nserial \xff\x00"
# The hyphenated name of issue #43 (design.md D1, § Correctness Properties AC-3.1 and UB-4): the reference path of
# `package#upload-module` as its operations-index.md row writes it, two synthetic paths that show where a hyphenated
# name ends, and the in-segment forms of three package.md rows, which hold the names they hold on #40's base.
UPLOAD_MODULE_OPERATION_ID = "synthetic#upload-module"
UPLOAD_MODULE_PATH = "/projects/:id/packages/terraform/modules/:module-name/:module-system/:module-version/file"
UPLOAD_MODULE_VALUES = {"id": 1, "module-name": "infra", "module-system": "aws", "module-version": "1.0.0"}
UPLOAD_MODULE_WRITTEN = "/projects/1/packages/terraform/modules/infra/aws/1.0.0/file"
HYPHEN_CASES = {
    "upload-module": UPLOAD_MODULE_PATH,
    "hyphen-before-a-slash": "/a/:name-/b",
    "hyphens-between-name-characters": "/a/:a-b-c",
    "hyphen-before-the-sigil": "/<route-prefix>/dists/*distribution/:component/binary-:architecture/Packages",
    "dollar-between-names": "/group/:id/-/packages/composer/:package_name$:sha",
    "dot-after-a-name": "/projects/:id/packages/go/:module_name/@v/:module_version.info",
}
HYPHEN_NAMES = {
    "upload-module": ("id", "module-name", "module-system", "module-version"),
    "hyphen-before-a-slash": ("name",),
    "hyphens-between-name-characters": ("a-b-c",),
    "hyphen-before-the-sigil": ("distribution", "component", "architecture"),
    "dollar-between-names": ("id", "package_name", "sha"),
    "dot-after-a-name": ("id", "module_name", "module_version"),
}
# The route prefix of issue #43 (design.md D2, § Correctness Properties AC-2.2, AC-2.4 and UB-4): a synthetic record on
# the reference path of `package#list-all-dist-tags` with the values of the npm page's `<route-prefix>` line
# (rest/package.md "npm API"), in the line's order, and the path each value gives; a synthetic record on the path of
# `package#download-a-debugging-symbol-file-pdb`, which holds `:file_name` twice, with the NuGet page's values.
DIST_TAGS_OPERATION_ID = "synthetic#list-all-dist-tags"
DIST_TAGS_PATH = "/<route-prefix>/-/package/:package_name/dist-tags"
NPM_PREFIX_VALUES = ("/packages/npm", "/projects/:id/packages/npm", "/groups/:id/-/packages/npm")
DIST_TAGS_ROUTED_PATHS = {
    "/packages/npm": "/packages/npm/-/package/:package_name/dist-tags",
    "/projects/:id/packages/npm": "/projects/:id/packages/npm/-/package/:package_name/dist-tags",
    "/groups/:id/-/packages/npm": "/groups/:id/-/packages/npm/-/package/:package_name/dist-tags",
}
# Every value of the unrouted path, so a refusal of it is the prefix's and never `encode`'s refusal of an `id` the
# unrouted path does not hold.
DIST_TAGS_VALUES = {"package_name": "pkg"}
GROUP_NPM_PREFIX = "/groups/:id/-/packages/npm"
GROUP_NPM_VALUES = {"id": 7, "package_name": "pkg"}
GROUP_NPM_SENT_PATH = "/groups/7/-/packages/npm/-/package/pkg/dist-tags"
SYMBOL_FILE_OPERATION_ID = "synthetic#download-a-debugging-symbol-file-pdb"
SYMBOL_FILE_PATH = "/<route-prefix>/symbolfiles/:file_name/:signature/:file_name"
NUGET_PREFIX_VALUES = ("/groups/:id/-/packages/nuget", "/projects/:id/packages/nuget")
PROJECT_NUGET_PREFIX = "/projects/:id/packages/nuget"
SYMBOL_FILE_VALUES = {"id": 1, "file_name": "a.pdb", "signature": "s"}
SYMBOL_FILE_WRITTEN = "/projects/1/packages/nuget/symbolfiles/a.pdb/s/a.pdb"
# The request forms of issue #63 (design.md D1 to D5, § Correctness Properties), each on a reference path as its
# operations-index.md row writes it. F1: the three endpoints of plan.md "Add an emoji reaction to a resource", declared
# in an order that is neither the section's nor sorted, so only "the first declared" gives the merge-request record;
# and endpoints no record of the id declares: another path, another method, the method in lower case, another `:name`.
EMOJI_OPERATION_ID = "synthetic#add-an-emoji-reaction-to-a-resource"
EMOJI_ENDPOINTS = (
    ("POST", "/projects/:id/merge_requests/:merge_request_iid/award_emoji"),
    ("POST", "/projects/:id/snippets/:snippet_id/award_emoji"),
    ("POST", "/projects/:id/issues/:issue_iid/award_emoji"),
)
UNDECLARED_ENDPOINTS = (
    ("POST", "/projects/:id/epics"),
    ("PUT", "/projects/:id/issues/:issue_iid/award_emoji"),
    ("post", "/projects/:id/merge_requests/:merge_request_iid/award_emoji"),
    ("POST", "/projects/:id/snippets/:snippet/award_emoji"),
)
# An id one record declares (UB-1); an id two records of one family declare with one key; an id two families declare.
ONCE_OPERATION_ID = "synthetic#declared-once"
ONCE_ENDPOINT = ("GET", "/once")
SAME_KEY_OPERATION_ID = "synthetic#declared-twice-on-one-key"
SAME_KEY_ENDPOINT = ("GET", "/twice")
TWO_FAMILIES_OPERATION_ID = "synthetic-beta#declared-in-two-families"
TWO_FAMILIES_ENDPOINTS = (("GET", "/alpha/twice"), ("GET", "/beta/twice"))
DECLARED_TIMES = re.compile(pattern=r"declared [0-9]+ times")
GRAPHQL_ENDPOINT = ("POST", "/api/graphql")
# F2: the path of create.md "Delete a group SSH certificate", whose `:id` is the group and then the certificate. Each
# case gives the two values as a list or a tuple, in place order; one value, three, and a value that is no list are
# refused (design.md D2, § Correctness Properties AC-3.1, AC-3.2).
CERTIFICATE_OPERATION_ID = "synthetic#delete-a-group-ssh-certificate"
CERTIFICATE_PATH = "/groups/:id/ssh_certificates/:id"
POSITIONAL_NAMES = ("id",)
POSITIONAL_CASES: Dict[str, Dict[str, Any]] = {
    "list": {"id": ["7", "my/group"]},
    "tuple": {"id": ("my/group", "7")},
}
POSITIONAL_WRITTEN = {
    "list": "/groups/7/ssh_certificates/my%2Fgroup",
    "tuple": "/groups/my%2Fgroup/ssh_certificates/7",
}
POSITIONAL_REFUSED: Dict[str, Dict[str, Any]] = {
    "one-value": {"id": ["7"]},
    "three-values": {"id": ["7", "my/group", "9"]},
    "no-list": {"id": "7"},
}
# F3: the path of create.md "Retrieve file archive from a repository" and the formats of docs.gitlab.com
# `repositories` "Available options" (design.md D3, § Correctness Properties AC-4.1).
ARCHIVE_OPERATION_ID = "synthetic#retrieve-file-archive-from-a-repository"
ARCHIVE_PATH = "/projects/:id/repository/archive[.format]"
ARCHIVE_FORMATS = ("bz2", "tar", "tar.bz2", "tar.gz", "tb2", "tbz", "tbz2", "zip")
ARCHIVE_NAMED = ("id", "format")
ARCHIVE_REQUIRED = ("id",)
ARCHIVE_CASES: Dict[str, Dict[str, Any]] = {
    "zip": {"id": 1, "format": "zip"},
    "dotted-format": {"id": 1, "format": "tar.gz"},
    "absent": {"id": 1},
    "none": {"id": 1, "format": None},
}
ARCHIVE_WRITTEN = {
    "zip": "/projects/1/repository/archive.zip",
    "dotted-format": "/projects/1/repository/archive.tar.gz",
    "absent": "/projects/1/repository/archive",
    "none": "/projects/1/repository/archive",
}
# F4: the three index paths that are not under `/api/v4` — software-supply-chain-security.md "Retrieve the token
# information" at the host root, package.md "Delete image tags by reference" and "Listing all container repositories"
# on the container registry — and two that are; each with the `registry.Base` member name `base_of` reads and the rest
# of the path (design.md D4, § Correctness Properties AC-5.1).
TOKEN_INFO_PATH = "https://HOST/oauth/token/info"
REGISTRY_DELETE_PATH = "/http(s)://${CI_REGISTRY}/v2/${CI_REGISTRY_IMAGE}/tags/reference/${CI_COMMIT_SHORT_SHA}"
REGISTRY_CATALOG_PATH = "/http(s)://${CI_REGISTRY}/v2/_catalog"
USER_STATUS_PATH = "/user/status"
BASE_CASES = {
    "host-root": TOKEN_INFO_PATH,
    "registry-delete": REGISTRY_DELETE_PATH,
    "registry-catalog": REGISTRY_CATALOG_PATH,
    "rest": USER_STATUS_PATH,
    "rest-route-prefix": DIST_TAGS_PATH,
}
BASE_READ = {
    "host-root": ("HOST", "/oauth/token/info"),
    "registry-delete": ("CONTAINER_REGISTRY", "/v2/${CI_REGISTRY_IMAGE}/tags/reference/${CI_COMMIT_SHORT_SHA}"),
    "registry-catalog": ("CONTAINER_REGISTRY", "/v2/_catalog"),
    "rest": ("REST", USER_STATUS_PATH),
    "rest-route-prefix": ("REST", DIST_TAGS_PATH),
}
REGISTRY_DELETE_NAMES = ("CI_REGISTRY_IMAGE", "CI_COMMIT_SHORT_SHA")
# F5: the record of software-supply-chain-security.md "Set status of an external control" — its three
# `- Request headers:` names and its `status` row — with requirements.md AC-6.2's values, given in an order that is not
# the declared one, so "in the caller's order" shows (design.md D5, § Correctness Properties AC-6.2).
EXTERNAL_CONTROL_OPERATION_ID = "synthetic#set-status-of-an-external-control"
EXTERNAL_CONTROL_PATH = "/projects/:id/compliance_external_controls/:external_control_id/status"
EXTERNAL_CONTROL_HEADERS = ("X-Gitlab-Timestamp", "X-Gitlab-Nonce", "X-Gitlab-Hmac-Sha256")
STATUS_NAME = "status"
NONCE_HEADER = "X-Gitlab-Nonce"
EXTERNAL_CONTROL_VALUES: Dict[str, Any] = {
    "id": 1,
    "external_control_id": 3,
    "X-Gitlab-Hmac-Sha256": "ab12",
    STATUS_NAME: "pass",
    "X-Gitlab-Timestamp": 1700000000,
    NONCE_HEADER: "n1",
}
WITHOUT_NONCE = {name: value for name, value in EXTERNAL_CONTROL_VALUES.items() if name != NONCE_HEADER}
SENT_HEADERS = [("X-Gitlab-Hmac-Sha256", "ab12"), ("X-Gitlab-Timestamp", "1700000000"), (NONCE_HEADER, "n1")]
SENT_HEADERS_WITHOUT_NONCE = [("X-Gitlab-Hmac-Sha256", "ab12"), ("X-Gitlab-Timestamp", "1700000000")]
PART_JSON = "json_body"
PART_HEADERS = "headers"
STATUS_PAIRS = [(STATUS_NAME, "pass")]
STATUS_BODY = {STATUS_NAME: "pass"}
HEADER_ENCODED_PARTS: Dict[str, Dict[str, Any]] = {
    "json-body": {PART_QUERY: [], PART_FORM: [], PART_JSON: STATUS_BODY, PART_HEADERS: SENT_HEADERS},
    "form-body": {PART_QUERY: [], PART_FORM: STATUS_PAIRS, PART_JSON: None, PART_HEADERS: SENT_HEADERS},
    "nonce-not-given": {
        PART_QUERY: [],
        PART_FORM: [],
        PART_JSON: STATUS_BODY,
        PART_HEADERS: SENT_HEADERS_WITHOUT_NONCE,
    },
}
# F4's container registry: a record on the path of package.md "Delete image tags by reference" with its scope
# (docs.gitlab.com `container_registry`: `repository:${CI_PROJECT_PATH}:delete`) and its two `${NAME}` values, and the
# answers design.md D4's steps 1 to 4 read, in step order (§ Correctness Properties AC-5.2).
REGISTRY_DELETE_OPERATION_ID = "synthetic#delete-image-tags-by-reference"
REGISTRY_DELETE_SCOPE = "repository:${CI_REGISTRY_IMAGE}:delete"
REGISTRY_DELETE_VALUES = {"CI_REGISTRY_IMAGE": "group/app", "CI_COMMIT_SHORT_SHA": "1a2b3c4"}
FIELD_USERNAME = "username"
FIELD_IMAGE_PREFIX = "container_registry_image_prefix"
FIELD_REGISTRY_CREDENTIAL = "token"
REGISTRY_STEP_ANSWERS: Tuple[Any, ...] = (
    {FIELD_USERNAME: "registry-user"},
    {FIELD_IMAGE_PREFIX: "registry.example.com/group/app"},
    {FIELD_REGISTRY_CREDENTIAL: "scripted-registry-answer"},
    None,
)


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


def encoded_part(*, encoded: Any, name: str) -> List[Tuple[str, str]]:
    """The name-value pairs of one part of ``registry.encode``'s result, by the ``Transport.request`` keyword the
    part feeds; read as an attribute or as a mapping key, the two shapes D5 leaves open."""
    part = encoded[name] if isinstance(encoded, Mapping) else getattr(encoded, name)
    return [(str(pair_name), str(pair_value)) for pair_name, pair_value in part]


def sent_parts(*, encoded: Any) -> Dict[str, Any]:
    """Where ``registry.encode``'s result sends its values: the query, form and header pairs and the JSON body (issue
    #63, design.md D5)."""
    return {
        PART_QUERY: encoded_part(encoded=encoded, name=PART_QUERY),
        PART_FORM: encoded_part(encoded=encoded, name=PART_FORM),
        PART_JSON: encoded[PART_JSON] if isinstance(encoded, Mapping) else getattr(encoded, PART_JSON),
        PART_HEADERS: encoded_part(encoded=encoded, name=PART_HEADERS),
    }


def synthetic_family(*, name: str, operations: Sequence[Any]) -> ModuleType:
    """A stand-in for one ``gitlab_api/families/<family>.py`` module (D2's family module contract)."""
    module = ModuleType(name=f"synthetic_families.{name.replace('-', '_')}")
    module.__dict__.update(FAMILY=name, OPERATIONS=tuple(operations), PENDING=frozenset())
    return module


def serve_families(*, monkeypatch: pytest.MonkeyPatch, registry: ModuleType, families: Sequence[ModuleType]) -> None:
    """Make ``registry.discover_families`` return exactly ``families``, so ``lookup`` reads their records."""

    def discover_families(*, package: Any = None) -> Tuple[ModuleType, ...]:
        return tuple(families)

    monkeypatch.setattr(registry, "discover_families", discover_families)


@pytest.mark.parametrize(
    ("path", "values", "expected"),
    [
        ("/projects/:id", {"id": "diaspora/diaspora"}, "/projects/diaspora%2Fdiaspora"),
        (
            "/projects/:id",
            {"id": "my-group/my-subgroup/my-project"},
            "/projects/my-group%2Fmy-subgroup%2Fmy-project",
        ),
        ("/projects/:id", {"id": 42}, "/projects/42"),
        (
            "/projects/:id/repository/branches/:branch",
            {"id": "diaspora/diaspora", "branch": "my/branch"},
            "/projects/diaspora%2Fdiaspora/repository/branches/my%2Fbranch",
        ),
        (
            "/projects/:id/repository/files/:file_path",
            {"id": 1, "file_path": "src/README.md"},
            "/projects/1/repository/files/src%2FREADME.md",
        ),
        (
            "/projects/:id/repository/tags/:tag_name",
            {"id": 1, "tag_name": "my/tag"},
            "/projects/1/repository/tags/my%2Ftag",
        ),
    ],
    ids=["full-path", "subgroup-path", "numeric-id", "branch", "file-path", "tag"],
)
def test_project_path_is_encoded(path: str, values: Dict[str, Any], expected: str) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.RestOperation(operation_id="synthetic#expand", method="GET", path=path)
    assert registry.expand(operation=operation, values=values) == expected, (
        "each path value is one segment, `/` sent as %2F (conventions.md 'URL-encoding path parameters')"
    )


@pytest.mark.parametrize("value", ["", ".", ".."], ids=["empty", "dot", "dot-dot"])
def test_empty_and_dot_segments_are_refused(value: str) -> None:
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    operation = registry.RestOperation(
        operation_id="synthetic#retrieve-a-branch",
        method="GET",
        path="/projects/:id/repository/branches/:branch",
    )
    with pytest.raises(errors.GitLabAPIError):
        registry.expand(operation=operation, values={"id": "diaspora/diaspora", "branch": value})


@pytest.mark.parametrize(
    ("location", "body", "part"),
    [("QUERY", "JSON", PART_QUERY), ("BODY", "FORM", PART_FORM)],
    ids=["query-string", "form-body"],
)
def test_array_of_hashes_pairs(location: str, body: str, part: str) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.RestOperation(
        operation_id="synthetic#create-a-pipeline",
        method="POST",
        path="/projects/:id/pipeline",
        params=(
            registry.Param(
                name="variables",
                location=getattr(registry.Location, location),
                kind=registry.Kind.ARRAY_OF_HASHES,
            ),
        ),
        body=getattr(registry.BodyFormat, body),
    )
    encoded = registry.encode(operation=operation, values={"id": 7, "variables": VARIABLES})
    assert encoded_part(encoded=encoded, name=part) == VARIABLES_PAIRS, (
        "an array of hashes is sent as name[index][key]=value pairs, in list and key order (AC-2.3)"
    )


def test_lookup_refuses_unknown_and_duplicate_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = gitlab_module(name="registry")

    def record(*, operation_id: str, path: str) -> Any:
        return registry.RestOperation(operation_id=operation_id, method="GET", path=path)

    declared_once = record(operation_id="synthetic-alpha#declared-once", path="/alpha")
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[
            synthetic_family(name="synthetic-alpha", operations=[declared_once]),
            synthetic_family(
                name="synthetic-beta",
                operations=[record(operation_id="synthetic-beta#declared-once", path="/beta")],
            ),
        ],
    )
    assert registry.lookup(operation_id="synthetic-alpha#declared-once") == declared_once, (
        "lookup reads the records of the families discover_families returns"
    )
    unknown = "synthetic-alpha#no-such-operation"
    with pytest.raises(ValueError, match=re.escape(unknown)) as unknown_refusal:
        registry.lookup(operation_id=unknown)

    twice = "synthetic-beta#declared-twice"
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[
            synthetic_family(name="synthetic-alpha", operations=[record(operation_id=twice, path="/alpha/twice")]),
            synthetic_family(name="synthetic-beta", operations=[record(operation_id=twice, path="/beta/twice")]),
        ],
    )
    with pytest.raises(ValueError, match=re.escape(twice)) as duplicate_refusal:
        registry.lookup(operation_id=twice)
    duplicate_message = str(duplicate_refusal.value).replace(twice, "<id>")
    unknown_message = str(unknown_refusal.value).replace(unknown, "<id>")
    assert duplicate_message != unknown_message, "a twice-declared id is refused as declared twice, not as unknown"


def test_call_refuses_an_undeclared_value(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    operation = registry.RestOperation(
        operation_id=CALL_OPERATION_ID,
        method="PUT",
        path="/projects/:id/issues/:issue_iid",
        params=(
            registry.Param(name="title", location=registry.Location.BODY),
            registry.Param(name="confidential", location=registry.Location.BODY),
        ),
    )

    def lookup(*, operation_id: str) -> Any:
        assert operation_id == CALL_OPERATION_ID, f"call looked up {operation_id!r}, not the id it was given"
        return operation

    monkeypatch.setattr(registry, "lookup", lookup)
    # The request `call` would send if it dropped the undeclared value is scripted, so sending it fails this test on its
    # oracle below rather than on the fake's unscripted-request error.
    fake_gitlab.script(method="PUT", url=f"{fixtures.REST_BASE}/projects/diaspora%2Fdiaspora/issues/7", body={"iid": 7})
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )
    with pytest.raises(ValueError, match=re.escape(UNDECLARED_NAME)):
        registry.call(
            transport=transport,
            operation_id=CALL_OPERATION_ID,
            values={"id": "diaspora/diaspora", "issue_iid": 7, "title": "Renamed", UNDECLARED_NAME: True},
        )
    assert fake_gitlab.requests == [], "a value the record does not declare is refused before any request (AC-1.1)"


def test_send_returns_the_response_of_the_record(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    graphql_only = gitlab_module(name="graphql_only")
    operation = registry.RestOperation(operation_id=SEND_OPERATION_ID, method="DELETE", path=SEND_PATH)
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[synthetic_family(name="synthetic", operations=[operation])],
    )
    sent_url = f"{fixtures.REST_BASE}{SEND_SENT_PATH}"
    fake_gitlab.script(method="DELETE", url=sent_url, status=STATUS_NO_CONTENT)
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )

    response = registry.send(transport=transport, operation_id=SEND_OPERATION_ID, values=SEND_VALUES)
    assert isinstance(response, transport_module.Response), (
        f"send returns the Response of the record's request, not its decoded value; got {response!r} (design.md D2)"
    )
    assert (response.status, response.body) == (STATUS_NO_CONTENT, b""), "the Response is the 204 the host answered"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("DELETE", sent_url)], (
        "send sends the record's one request: its method, its path expanded (AC-1.2)"
    )

    graphql_record = registry.GraphQLOperation(
        operation_id=GRAPHQL_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=PROJECT_DOCUMENT,
    )
    monkeypatch.setattr(graphql_only, "OPERATIONS", (graphql_record,))
    assert registry.lookup(operation_id=GRAPHQL_OPERATION_ID) == graphql_record, (
        "the GraphQL record is declared, so a refusal below is send's and not lookup's unknown id"
    )
    # The request `send` would send if it ran the GraphQL record is scripted, so sending it fails this test on its
    # oracle below rather than on the fake's unscripted-request error.
    fake_gitlab.script(method="POST", url=fixtures.GRAPHQL_URL, body={"data": {"project": {"id": "gid://gitlab/1"}}})
    sent_before = list(fake_gitlab.requests)
    with pytest.raises(ValueError):
        registry.send(transport=transport, operation_id=GRAPHQL_OPERATION_ID, values={"fullPath": "g/p"})
    assert fake_gitlab.requests == sent_before, "send refuses a GraphQL record with no request (design.md D2)"


@pytest.mark.parametrize(
    ("name", "expected"),
    [("iids[]", "iids"), ("a[][]", "a[]"), ("not[labels]", "not[labels]")],
    ids=["array-suffix", "one-pair-only", "hash-key-unchanged"],
)
def test_attribute_name_drops_one_trailing_bracket_pair(name: str, expected: str) -> None:
    registry = gitlab_module(name="registry")
    assert registry.attribute_name(name=name) == expected, (
        f"{name!r} names the Param {expected!r}: one trailing [] is dropped, nothing else (design.md D2, AC-1.3)"
    )


@pytest.mark.parametrize(
    ("document", "connection", "expected"),
    [
        (PROJECT_DOCUMENT, (), ("fullPath", "first")),
        (ISSUES_DOCUMENT, ISSUES_CONNECTION, ("fullPath",)),
        (ISSUES_DOCUMENT, (), ("fullPath", "after")),
    ],
    ids=["definitions-in-order", "connection-drops-after", "no-connection-keeps-after"],
)
def test_variables_are_the_documents_definitions(
    document: str, connection: Tuple[str, ...], expected: Tuple[str, ...]
) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.GraphQLOperation(
        operation_id=GRAPHQL_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=document,
        connection=connection,
    )
    assert registry.variables(operation=operation) == expected, (
        "each $name followed, after any white space, by `:` is a definition, in order; a connection record leaves "
        "out its cursor `after` (design.md D2, AC-2.2)"
    )


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        (FILES_DOCUMENT, FILES_UPLOADS),
        (FILE_DOCUMENT, FILE_UPLOADS),
        (INT_LIST_DOCUMENT, NO_UPLOADS),
        (ALL_UPLOADS_DOCUMENT, ALL_UPLOADS),
    ],
    ids=["list-of-uploads", "one-upload", "list-of-another-type", "all-three-in-one-document"],
)
def test_upload_variables_are_the_documents_upload_definitions(document: str, expected: Dict[str, bool]) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.GraphQLOperation(
        operation_id=UPLOAD_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=document,
    )
    assert registry.upload_variables(operation=operation) == expected, (
        "each defined variable whose type, with `[`, `]`, `!` and white space removed, is `Upload` is mapped to "
        "whether its type begins with `[`; a variable of another type is left out (design.md D4, AC-3.1)"
    )


# A document one of whose definitions has no type `TYPE_REFERENCE` reads: `$broken:` is followed by `,`, which starts
# no Name. The upload variables before and after it are read all the same (design.md D4).
UNTYPED_DEFINITION_NAME = "broken"
UNTYPED_DEFINITION_DOCUMENT = (
    "mutation M($files: [Upload!]!, $broken: , $file: Upload) "
    "{ syntheticUpload(input: {files: $files, file: $file}) { errors } }"
)


def test_upload_variables_leave_out_a_definition_without_a_type() -> None:
    """design.md D4, AC-3.1: a ``$name:`` definition followed by no type is a declared variable (``variables`` names
    it) that ``upload_variables`` leaves out, while it still maps the ``Upload`` variables before and after it."""
    registry = gitlab_module(name="registry")
    operation = registry.GraphQLOperation(
        operation_id=UPLOAD_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=UNTYPED_DEFINITION_DOCUMENT,
    )
    assert UNTYPED_DEFINITION_NAME in registry.variables(operation=operation), (
        f"${UNTYPED_DEFINITION_NAME} is a definition of the document, so upload_variables reads a type for it"
    )
    assert registry.upload_variables(operation=operation) == ALL_UPLOADS, (
        f"a definition without a type, ${UNTYPED_DEFINITION_NAME}, is left out, and the Upload variables around it are "
        "still mapped to whether each is a list (design.md D4, AC-3.1)"
    )


def test_split_uploads_puts_null_where_each_file_goes() -> None:
    registry = gitlab_module(name="registry")
    sent_variables, files = registry.split_uploads(values=SPLIT_VALUES)
    assert sent_variables == SPLIT_VARIABLES, (
        "each Path value, and each Path item of a list, is replaced by None, the null of the operations part; every "
        "other value is unchanged (design.md D4, AC-3.1)"
    )
    assert files == SPLIT_FILES, (
        "each file with the operations path it fills, variables.<name> or variables.<name>.<index>, in the order of "
        "the values and of each list (design.md D4, AC-3.1)"
    )


@pytest.mark.parametrize(
    ("path", "named", "required"),
    [
        (
            GENERIC_PACKAGE_PATH,
            ("id", "package_name", "package_version", "path", "file_name"),
            ("id", "package_name", "package_version", "file_name"),
        ),
        (
            NUGET_SINGLE_PACKAGE_PATH,
            ("project_id", "package_name", "package_version"),
            ("project_id", "package_name", "package_version"),
        ),
        (
            DEBIAN_INDEX_PATH,
            ("id", "distribution", "component", "architecture"),
            ("id", "distribution", "component", "architecture"),
        ),
        ("/projects/:id/repository/branches/:branch", ("id", "branch"), ("id", "branch")),
    ],
    ids=["optional-group", "escaped-parentheses", "glob-and-placeholder-inside-a-segment", "colon-only"],
)
def test_placeholders_name_every_path_form(path: str, named: Tuple[str, ...], required: Tuple[str, ...]) -> None:
    registry = gitlab_module(name="registry")
    assert registry.placeholders(path=path) == named, (
        f"{path!r} names {named!r}: every :name and *name, without its sigil, in path order, inside an optional group "
        "or not (design.md D1, AC-2.4)"
    )
    assert registry.required_placeholders(path=path) == required, (
        f"{path!r} must be given {required!r}: its placeholders with every optional group's left out (design.md D1, "
        "AC-2.3, AC-2.4)"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.0/rc 1", "/projects/1/packages/maven/1.0/rc%201/x.jar/authorize"),
        ("@scope/pkg", "/projects/1/packages/maven/%40scope/pkg/x.jar/authorize"),
        ("a?b#c", "/projects/1/packages/maven/a%3Fb%23c/x.jar/authorize"),
        ("%2e%2e/x", "/projects/1/packages/maven/%252e%252e/x/x.jar/authorize"),
    ],
    ids=["space", "npm-scope", "query-and-fragment", "encoded-dots"],
)
def test_a_glob_value_keeps_its_slashes(value: str, expected: str) -> None:
    registry = gitlab_module(name="registry")
    operation = registry.RestOperation(operation_id=MAVEN_OPERATION_ID, method="PUT", path=MAVEN_AUTHORIZE_PATH)
    assert registry.expand(operation=operation, values={**MAVEN_VALUES, "path": value}) == expected, (
        f"the glob {MAVEN_GLOB} given {value!r} keeps each `/`, each part between them one percent-encoded segment "
        "(design.md D1, AC-2.1)"
    )


@pytest.mark.parametrize(
    "value",
    ["a//b", "/a", "a/", "a/./b", "a/../b", "", ".", ".."],
    ids=["empty-inner-part", "leading-slash", "trailing-slash", "dot-part", "dot-dot-part", "empty", "dot", "dot-dot"],
)
def test_a_glob_part_that_is_no_segment_is_refused(value: str) -> None:
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    operation = registry.RestOperation(operation_id=MAVEN_OPERATION_ID, method="PUT", path=MAVEN_AUTHORIZE_PATH)
    with pytest.raises(errors.GitLabAPIError, match=re.escape(MAVEN_GLOB)):
        registry.expand(operation=operation, values={**MAVEN_VALUES, "path": value})
    with pytest.raises(ValueError):
        registry.expand(operation=operation, values=MAVEN_VALUES)


def test_an_optional_group_is_written_only_when_given() -> None:
    registry = gitlab_module(name="registry")
    errors = gitlab_module(name="errors")
    operation = registry.RestOperation(operation_id=GENERIC_OPERATION_ID, method="GET", path=GENERIC_PACKAGE_PATH)
    written = {
        "given": registry.expand(operation=operation, values={**GENERIC_VALUES, "path": "a/b"}),
        "absent": registry.expand(operation=operation, values=GENERIC_VALUES),
        "none": registry.expand(operation=operation, values={**GENERIC_VALUES, "path": None}),
    }
    assert written == {"given": GENERIC_WITH_GROUP, "absent": GENERIC_WITHOUT_GROUP, "none": GENERIC_WITHOUT_GROUP}, (
        "the group `(*path/)` is written without its parentheses when `path` has a value, and left out whole when "
        "`path` is absent or None (design.md D1, AC-2.3)"
    )
    with pytest.raises(errors.GitLabAPIError):
        registry.expand(operation=operation, values={**GENERIC_VALUES, "path": ""})


def test_an_escaped_parenthesis_is_sent_without_its_backslash() -> None:
    registry = gitlab_module(name="registry")
    written = {
        case: registry.expand(
            operation=registry.RestOperation(operation_id=f"synthetic#{case}", method="GET", path=path),
            values=values,
        )
        for case, (path, values) in ESCAPED_CASES.items()
    }
    assert written == ESCAPED_WRITTEN, (
        "each `\\(` and `\\)` is sent as its parenthesis and never read as an optional group; `$`, `'`, `,` and `=` "
        "are sent as the path writes them, and a value's parentheses are percent-encoded (design.md D1, AC-2.5)"
    )


def test_send_sends_a_raw_record_its_bytes(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    raw_record = registry.RestOperation(
        operation_id=RAW_OPERATION_ID, method="POST", path=TERRAFORM_STATE_PATH, content_type=RAW_MEDIA_TYPE
    )
    plain_record = registry.RestOperation(operation_id=PLAIN_OPERATION_ID, method="POST", path=TERRAFORM_STATE_PATH)
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[synthetic_family(name="synthetic", operations=[raw_record, plain_record])],
    )
    sent_url = f"{fixtures.REST_BASE}{TERRAFORM_STATE_SENT_PATH}"
    fake_gitlab.script(method="POST", url=sent_url)
    # The request `send` would send if it sent the plain record's bytes is scripted too, so sending it fails this test
    # on its oracle below rather than on the fake's unscripted-request error.
    fake_gitlab.script(method="POST", url=sent_url)
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )

    registry.send(transport=transport, operation_id=RAW_OPERATION_ID, values=TERRAFORM_STATE_VALUES, data=RAW_BYTES)
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("POST", sent_url)], (
        "send sends the raw-body record's one request: its method, its path expanded (design.md D5)"
    )
    sent = fake_gitlab.requests[0]
    assert sent.body == RAW_BYTES, "the bytes go out as the body, unchanged (design.md D5, AC-3.2)"
    assert sent.header(name=fixtures.HEADER_CONTENT_TYPE) == RAW_MEDIA_TYPE, (
        "the body's Content-Type is the record's media type (design.md D5, AC-3.2)"
    )

    sent_before = list(fake_gitlab.requests)
    with pytest.raises(ValueError):
        registry.send(
            transport=transport, operation_id=PLAIN_OPERATION_ID, values=TERRAFORM_STATE_VALUES, data=RAW_BYTES
        )
    assert fake_gitlab.requests == sent_before, (
        "bytes given for a record with no media type are refused with no request (design.md D5)"
    )


def test_a_hyphenated_name_is_one_placeholder() -> None:
    registry = gitlab_module(name="registry")
    named = {case: registry.placeholders(path=path) for case, path in HYPHEN_CASES.items()}
    assert named == HYPHEN_NAMES, (
        "a name continues past a `-` that a name character follows, so `:module-name` is one placeholder; `:name-/` "
        "ends before its `-`, and `binary-:architecture`, `:package_name$:sha` and `:module_version.info` hold the "
        "names they hold on #40's base (design.md D1, AC-3.1, UB-4)"
    )
    operation = registry.RestOperation(operation_id=UPLOAD_MODULE_OPERATION_ID, method="PUT", path=UPLOAD_MODULE_PATH)
    assert registry.expand(operation=operation, values=UPLOAD_MODULE_VALUES) == UPLOAD_MODULE_WRITTEN, (
        "each hyphenated name is written as one segment, from the value given under the name with its hyphens "
        "(design.md D1, AC-3.1)"
    )


def test_route_writes_the_chosen_prefix() -> None:
    registry = gitlab_module(name="registry")
    record = registry.RestOperation(
        operation_id=DIST_TAGS_OPERATION_ID, method="GET", path=DIST_TAGS_PATH, route_prefixes=NPM_PREFIX_VALUES
    )
    routed = {prefix: registry.route(operation=record, prefix=prefix) for prefix in DIST_TAGS_ROUTED_PATHS}
    expected = {
        prefix: registry.RestOperation(
            operation_id=DIST_TAGS_OPERATION_ID, method="GET", path=path, route_prefixes=NPM_PREFIX_VALUES
        )
        for prefix, path in DIST_TAGS_ROUTED_PATHS.items()
    }
    assert routed == expected, (
        "each prefix value the record lists gives the record with `/<route-prefix>` replaced by that value, every "
        "other field unchanged (design.md D2, AC-2.2)"
    )

    plain = registry.RestOperation(operation_id=SEND_OPERATION_ID, method="DELETE", path=SEND_PATH)
    assert registry.route(operation=plain, prefix=None) is plain, (
        "a record with no route prefix, given none, is returned itself (design.md D2)"
    )

    symbol_file = registry.RestOperation(
        operation_id=SYMBOL_FILE_OPERATION_ID, method="GET", path=SYMBOL_FILE_PATH, route_prefixes=NUGET_PREFIX_VALUES
    )
    routed_symbol_file = registry.route(operation=symbol_file, prefix=PROJECT_NUGET_PREFIX)
    assert registry.expand(operation=routed_symbol_file, values=SYMBOL_FILE_VALUES) == SYMBOL_FILE_WRITTEN, (
        "the prefix's `:id` is written as one segment, and `:file_name`, which the path holds twice, takes its one "
        "value at both places (design.md D2, UB-4)"
    )


def test_a_prefix_record_is_sent_only_under_a_prefix(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    record = registry.RestOperation(
        operation_id=DIST_TAGS_OPERATION_ID, method="GET", path=DIST_TAGS_PATH, route_prefixes=NPM_PREFIX_VALUES
    )
    with pytest.raises(ValueError):
        registry.expand(operation=record, values=DIST_TAGS_VALUES)

    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[synthetic_family(name="synthetic", operations=[record])],
    )
    sent_url = f"{fixtures.REST_BASE}{GROUP_NPM_SENT_PATH}"
    fake_gitlab.script(method="GET", url=sent_url)
    # Any request `send` would send without a prefix is answered too, so sending one fails this test on its oracle
    # below rather than on the fake's unscripted-request error.
    fake_gitlab.script_next()
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )

    with pytest.raises(ValueError):
        registry.send(transport=transport, operation_id=DIST_TAGS_OPERATION_ID, values=DIST_TAGS_VALUES)
    assert fake_gitlab.requests == [], "a prefix record called with no prefix is refused with no request (AC-2.4)"

    registry.send(
        transport=transport, operation_id=DIST_TAGS_OPERATION_ID, values=GROUP_NPM_VALUES, prefix=GROUP_NPM_PREFIX
    )
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [("GET", sent_url)], (
        "send sends the record's one request under the prefix it is given, the prefix's `:id` written in (design.md "
        "D2, AC-2.2)"
    )


def test_lookup_chooses_an_endpoint_of_a_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = gitlab_module(name="registry")
    graphql_only = gitlab_module(name="graphql_only")

    def record(*, operation_id: str, endpoint: Tuple[str, str]) -> Any:
        method, path = endpoint
        return registry.RestOperation(operation_id=operation_id, method=method, path=path)

    records = {endpoint: record(operation_id=EMOJI_OPERATION_ID, endpoint=endpoint) for endpoint in EMOJI_ENDPOINTS}
    declared_once = record(operation_id=ONCE_OPERATION_ID, endpoint=ONCE_ENDPOINT)
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[synthetic_family(name="synthetic", operations=[*records.values(), declared_once])],
    )
    chosen = {
        endpoint: registry.lookup(operation_id=EMOJI_OPERATION_ID, endpoint=endpoint) for endpoint in EMOJI_ENDPOINTS
    }
    assert chosen == records, (
        "each endpoint of the id, given as its (method, path), chooses the record that declares it (design.md D1, "
        "AC-2.4)"
    )
    assert registry.lookup(operation_id=EMOJI_OPERATION_ID) == records[EMOJI_ENDPOINTS[0]], (
        "given no endpoint, lookup returns the first record declared with the id, its base endpoint (design.md D1, "
        "AC-2.2)"
    )
    once = {
        "no-endpoint": registry.lookup(operation_id=ONCE_OPERATION_ID),
        "its-endpoint": registry.lookup(operation_id=ONCE_OPERATION_ID, endpoint=ONCE_ENDPOINT),
    }
    assert once == {"no-endpoint": declared_once, "its-endpoint": declared_once}, (
        "an id one record declares is that record, given no endpoint or its own (design.md D1, UB-1)"
    )

    declared = [f"{method} {path}" for method, path in EMOJI_ENDPOINTS]
    for endpoint in UNDECLARED_ENDPOINTS:
        with pytest.raises(ValueError, match=re.escape(EMOJI_OPERATION_ID)) as refusal:
            registry.lookup(operation_id=EMOJI_OPERATION_ID, endpoint=endpoint)
        message = str(refusal.value)
        assert all(part in message for part in endpoint), (
            f"the refusal of {endpoint!r} names the endpoint given; got {message!r} (design.md D1, AC-2.4)"
        )
        positions = [message.find(text) for text in declared]
        assert -1 not in positions and positions == sorted(positions), (
            f"the refusal of {endpoint!r} names each declared endpoint as METHOD path, in declaration order "
            f"{declared!r}; got {message!r} (design.md D1, AC-2.4)"
        )

    alpha_endpoint, beta_endpoint = TWO_FAMILIES_ENDPOINTS
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[
            synthetic_family(
                name="synthetic-alpha",
                operations=[
                    record(operation_id=SAME_KEY_OPERATION_ID, endpoint=SAME_KEY_ENDPOINT),
                    record(operation_id=SAME_KEY_OPERATION_ID, endpoint=SAME_KEY_ENDPOINT),
                    record(operation_id=TWO_FAMILIES_OPERATION_ID, endpoint=alpha_endpoint),
                ],
            ),
            synthetic_family(
                name="synthetic-beta",
                operations=[record(operation_id=TWO_FAMILIES_OPERATION_ID, endpoint=beta_endpoint)],
            ),
        ],
    )
    twice = (
        (SAME_KEY_OPERATION_ID, None),
        (SAME_KEY_OPERATION_ID, SAME_KEY_ENDPOINT),
        (TWO_FAMILIES_OPERATION_ID, None),
        (TWO_FAMILIES_OPERATION_ID, alpha_endpoint),
        (TWO_FAMILIES_OPERATION_ID, beta_endpoint),
    )
    for operation_id, given in twice:
        with pytest.raises(ValueError, match=re.escape(operation_id)) as duplicate_refusal:
            registry.lookup(operation_id=operation_id, endpoint=given)
        assert DECLARED_TIMES.search(string=str(duplicate_refusal.value)), (
            f"{operation_id!r}, declared twice with one key in one family or once in each of two families, is refused "
            f"as declared more than once whatever the endpoint ({given!r}); got {duplicate_refusal.value} (design.md "
            "D1, AC-2.4)"
        )

    graphql_record = registry.GraphQLOperation(
        operation_id=GRAPHQL_OPERATION_ID,
        capability=SYNTHETIC_CAPABILITY,
        document=PROJECT_DOCUMENT,
    )
    monkeypatch.setattr(graphql_only, "OPERATIONS", (graphql_record,))
    assert registry.lookup(operation_id=GRAPHQL_OPERATION_ID) == graphql_record, (
        "a GraphQL record given no endpoint is found, so the refusal below is the endpoint's (design.md D1)"
    )
    with pytest.raises(ValueError):
        registry.lookup(operation_id=GRAPHQL_OPERATION_ID, endpoint=GRAPHQL_ENDPOINT)


def test_each_place_of_a_positional_name_takes_its_own_value() -> None:
    registry = gitlab_module(name="registry")
    certificate = registry.RestOperation(
        operation_id=CERTIFICATE_OPERATION_ID,
        method="DELETE",
        path=CERTIFICATE_PATH,
        positional_names=POSITIONAL_NAMES,
    )
    written = {case: registry.expand(operation=certificate, values=values) for case, values in POSITIONAL_CASES.items()}
    assert written == POSITIONAL_WRITTEN, (
        "each place of `:id`, a name of positional_names, is written from its own item of the list or tuple given, in "
        "path order, each as one percent-encoded segment (design.md D2, AC-3.1, AC-3.2)"
    )
    for values in POSITIONAL_REFUSED.values():
        with pytest.raises(ValueError):
            registry.expand(operation=certificate, values=values)

    symbol_file = registry.RestOperation(
        operation_id=SYMBOL_FILE_OPERATION_ID, method="GET", path=SYMBOL_FILE_PATH, route_prefixes=NUGET_PREFIX_VALUES
    )
    assert symbol_file.positional_names == (), "a record that names no positional name keeps () (design.md D2)"
    routed = registry.route(operation=symbol_file, prefix=PROJECT_NUGET_PREFIX)
    assert registry.expand(operation=routed, values=SYMBOL_FILE_VALUES) == SYMBOL_FILE_WRITTEN, (
        "without positional_names, `:file_name`, which the path holds twice, takes its one value at both places "
        "(design.md D2, UB-1; #43 UB-4)"
    )


def test_the_suffix_is_written_only_when_given() -> None:
    registry = gitlab_module(name="registry")
    assert registry.placeholders(path=ARCHIVE_PATH) == ARCHIVE_NAMED, (
        "the `[.format]` suffix names the path parameter `format`, after `id`, so a call may give it (design.md D3, "
        "AC-4.1)"
    )
    assert registry.required_placeholders(path=ARCHIVE_PATH) == ARCHIVE_REQUIRED, (
        "the suffix is optional: a call need not give `format` (design.md D3, AC-4.1)"
    )
    archive = registry.RestOperation(
        operation_id=ARCHIVE_OPERATION_ID, method="GET", path=ARCHIVE_PATH, suffix_values=ARCHIVE_FORMATS
    )
    written = {case: registry.expand(operation=archive, values=values) for case, values in ARCHIVE_CASES.items()}
    assert written == ARCHIVE_WRITTEN, (
        "the suffix is written as `.` and the format given, verbatim, and left out whole when `format` is absent or "
        "None; `[.format]` is never written (design.md D3, AC-4.1)"
    )


def test_the_base_is_read_from_the_path() -> None:
    registry = gitlab_module(name="registry")
    read = {case: registry.base_of(path=path) for case, path in BASE_CASES.items()}
    expected = {case: (getattr(registry.Base, member), rest) for case, (member, rest) in BASE_READ.items()}
    assert read == expected, (
        "a path starting `https://HOST/` is read as HOST and the rest, one starting `/http(s)://${CI_REGISTRY}/` as "
        "CONTAINER_REGISTRY and the rest, any other as REST and the whole path (design.md D4, AC-5.1)"
    )
    named = {
        "placeholders": registry.placeholders(path=REGISTRY_DELETE_PATH),
        "required": registry.required_placeholders(path=REGISTRY_DELETE_PATH),
    }
    assert named == {"placeholders": REGISTRY_DELETE_NAMES, "required": REGISTRY_DELETE_NAMES}, (
        "each ${NAME} of the rest of a container-registry path is a path parameter, in path order, and the root's "
        "`${CI_REGISTRY}` is none (design.md D4, AC-5.1)"
    )


def test_a_header_param_is_encoded_as_a_header() -> None:
    registry = gitlab_module(name="registry")
    params = (
        *(
            registry.Param(name=name, location=registry.Location.HEADER, required=True)
            for name in EXTERNAL_CONTROL_HEADERS
        ),
        registry.Param(name=STATUS_NAME, location=registry.Location.BODY, required=True),
    )

    def record(*, body: Any) -> Any:
        return registry.RestOperation(
            operation_id=EXTERNAL_CONTROL_OPERATION_ID,
            method="PATCH",
            path=EXTERNAL_CONTROL_PATH,
            params=params,
            body=body,
        )

    json_record = record(body=registry.BodyFormat.JSON)
    form_record = record(body=registry.BodyFormat.FORM)
    encoded = {
        "json-body": registry.encode(operation=json_record, values=EXTERNAL_CONTROL_VALUES),
        "form-body": registry.encode(operation=form_record, values=EXTERNAL_CONTROL_VALUES),
        "nonce-not-given": registry.encode(operation=json_record, values=WITHOUT_NONCE),
    }
    parts = {case: sent_parts(encoded=value) for case, value in encoded.items()}
    assert parts == HEADER_ENCODED_PARTS, (
        "each header value given is in headers, as text, under its declared name, in the caller's order, and never in "
        "the query, the form or the JSON body; a header not given is not there (design.md D5, AC-6.2)"
    )


def test_send_fetches_the_registry_token_before_the_registry(monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any) -> None:
    registry = gitlab_module(name="registry")
    transport_module = gitlab_module(name="transport")
    record = registry.RestOperation(
        operation_id=REGISTRY_DELETE_OPERATION_ID,
        method="DELETE",
        path=REGISTRY_DELETE_PATH,
        token_scope=REGISTRY_DELETE_SCOPE,
    )
    # The real families stay served beside the synthetic one, so the records of design.md D4's steps 1 and 2 are found:
    # a send that went ahead without the project would send step 1, not fail on an unknown id with nothing sent.
    declared = registry.discover_families()
    serve_families(
        monkeypatch=monkeypatch,
        registry=registry,
        families=[*declared, synthetic_family(name="synthetic", operations=[record])],
    )
    assert registry.encode(operation=record, values=REGISTRY_DELETE_VALUES) == registry.EncodedRequest(), (
        "each ${NAME} of the registry path is a path parameter, so the refusal below is send's and not encode's "
        "refusal of an undeclared value (design.md D4)"
    )
    # The answers of the four steps are queued, so a send that went ahead fails this test on its oracle below rather
    # than on the fake's unscripted-request error.
    for answer in REGISTRY_STEP_ANSWERS:
        fake_gitlab.script_next(body=answer)
    sleeps: List[float] = []
    transport = transport_module.Transport(
        host=fixtures.HOST,
        token="registry-test-token",
        token_type=TOKEN_TYPE_PRIVATE,
        sleep=sleeps.append,
        clock=lambda: FIXED_CLOCK_SECONDS,
    )

    with pytest.raises(ValueError):
        registry.send(transport=transport, operation_id=REGISTRY_DELETE_OPERATION_ID, values=REGISTRY_DELETE_VALUES)
    assert fake_gitlab.requests == [], (
        "a container-registry record sent without the configured project is refused before step 1, with no request to "
        "the instance or the registry (design.md D4, AC-5.2)"
    )
