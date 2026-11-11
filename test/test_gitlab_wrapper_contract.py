"""The contract test of the GitLab wrapper: every declared REST record against its section of the reference (D5).

Issue #41, design.md D5. The reference is `docs/api-reference/gitlab/rest/<stem>.md`; a record's id is
`<stem>#<anchor>`, the scheme of the Reference links of `operations-index.md`. The method has two halves:

- the REFERENCE half: `reference_sections` reads every page once into `Section`s (the endpoints of the first non-empty
  line under a `###` heading, the rows of its `| Attribute | In | Type |` table, the effective `Offering:`), and
  `record_problems` names every difference between a `RestOperation` and its section;
- the CALL half: `sent_call` reads a request the fake host recorded (method, path after `/api/v4`, the names of its
  query pairs and body members), and `call_problems` names every difference between it and the section.

`is_unreachable` states D5's rule: an operation no `sff-test-*` project on GitLab.com can reach, by its index row's
path (`/admin/`, `/geo/`, `/hooks/`) or by an effective `Offering:` that does not name `GitLab.com`. For such an
operation the two halves are the whole proof (AC-3.1, AC-3.2).

The anchor rule is `scripts/api_reference/verify.py` `anchors`, restated here: the module imports neither `verify.py`
(PyYAML) nor the generator's `common.Slugger`. The registry is imported inside the functions and tests that use it, and
`gitlab_api/commands/call.py` only after its file is asserted to exist, so the module collects whatever is missing.
The fake host and the socket guard (`src/payload/test/gitlab_wrapper_fixtures.py`, loaded by path) are installed for
every test, so no test opens a network connection.

Run: ``python scripts/run_tests.py test/test_gitlab_wrapper_contract.py``
"""

from __future__ import annotations

import email.parser
import importlib
import importlib.util
import json
import re
import sys
import urllib.parse
from dataclasses import dataclass, replace
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, FrozenSet, Iterable, Iterator, List, Mapping, NamedTuple, Optional, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "src" / "payload" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS / PACKAGE
FIXTURES_FILE = ROOT / "src" / "payload" / "test" / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_under_contract"

REFERENCE = ROOT / "docs" / "api-reference" / "gitlab"
REST_DIR = REFERENCE / "rest"
INDEX = REFERENCE / "operations-index.md"
TEXT_ENCODING = "utf-8"
ASCII_ENCODING = "ascii"

# --- The reference as the generator writes it (docs/api-reference/README.md "Reading the generated tables") -------

HEADING = re.compile(pattern=r"^(?P<marks>#{1,6})\s+(?P<text>.*?)\s*$")
GROUP_MARKS = "marks"
GROUP_TEXT = "text"
PAGE_LEVEL = 2
SECTION_LEVEL = 3
FENCE = "```"
# verify.py `anchors`: backticks, `**` and link markup removed, lower-cased; then every character other than a word
# character, `-` and space removed, and spaces written as `-`; a repeated slug numbered `-1`, `-2`, ... in page order.
ANCHOR_MARKUP = re.compile(pattern=r"`|\*\*|\[|\]\([^)]*\)")
ANCHOR_DROPPED = re.compile(pattern=r"[^\w\- ]")
ANCHOR_SPACE = " "
ANCHOR_DASH = "-"
# Every `METHOD path` span of the first non-empty line under a section heading; a line can hold several.
ENDPOINT = re.compile(pattern=r"`(?P<method>[A-Z]+) (?P<path>[^`\s]+)`")
GROUP_METHOD = "method"
GROUP_PATH = "path"
TABLE_HEADER_START = "| Attribute | In | Type |"
TABLE_LINE_START = "|"
TABLE_ROW = re.compile(pattern=r"^\| `(?P<name>[^`]+)` \| (?P<location>[a-z]+) \|")
GROUP_NAME = "name"
GROUP_LOCATION = "location"
# A name is the backticked text up to an annotation (` (deprecated)`) or a footnote (`[^version-attribute-include]`).
NAME_ENDS = (" (", "[^")
# An alternation row (`name or context`) is not an attribute; its alternatives are, as their own rows.
ALTERNATION = " or "
# A row whose name is another row's name followed by one of these is part of that attribute.
MEMBER_MARKS = ("[", ":")
PAGE_LINE_START = "Docs page:"
SECTION_LINE_START = "- Availability:"
OFFERING = re.compile(pattern=r"Offering:\s*(?P<offering>[^;]+)")
GROUP_OFFERING = "offering"
OFFERING_SEPARATOR = ","
GITLAB_COM = "GitLab.com"
UNREACHABLE_PREFIXES = ("/admin/", "/geo/", "/hooks/")

# The `In` column: `form`, a multipart part, is read as `body`; `header` is a request form part 1 does not build.
IN_PATH = "path"
IN_QUERY = "query"
IN_BODY = "body"
IN_FORM = "form"
SENT_PLACES = (IN_QUERY, IN_BODY)
# `parent[key]`: the hash member a query pair or a FORM-body pair names (`not[labels]`, `context[user]`).
PARENT_KEY = re.compile(pattern=r"[A-Za-z_][A-Za-z0-9_]*\[[A-Za-z0-9_]+\]")
BRACKET = "["
PATH_PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")

# conventions.md "Offset-based" and "Keyset-based": the query names a paged record may send or not, by the value of
# its `registry.Paging` member.
PAGING_OFFSET = "offset"
PAGING_KEYSET = "keyset"
PAGING_PARAMETERS: Dict[str, FrozenSet[str]] = {
    PAGING_OFFSET: frozenset({"page", "per_page"}),
    PAGING_KEYSET: frozenset({"pagination", "per_page", "order_by", "sort"}),
}
NO_PAGING_PARAMETERS: FrozenSet[str] = frozenset()

INDEX_ROW = re.compile(
    pattern=r"^\| (?P<method>[A-Z]+) \| `(?P<path>[^`]+)` \| "
    r"\[.*\]\(rest/(?P<stem>[a-z0-9-]+)\.md#(?P<anchor>[^)]+)\) \|$"
)
GROUP_STEM = "stem"
GROUP_ANCHOR = "anchor"
ID_SEPARATOR = "#"

# --- The request as the fake host recorded it ------------------------------------------------------------------

REST_PREFIX = "/api/v4"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_DISPOSITION = "content-disposition"
DISPOSITION_NAME = "name"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
HEADER_BLOCK_END = "\r\n\r\n"

# --- The calls the tests run (D5's table of typed values) ---------------------------------------------------------

FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
TOKEN = "glpat-wrapper-contract-test"  # pragma: allowlist secret
PROJECT_ID = 1
CALL_COMMAND = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "-f"
OPTION_FIELD = "-F"
OPTION_FILE = "--file"
ASSIGNED = "="
TEST_VALUE = "v1"
TYPED_VALUES: Dict[str, Any] = {
    "array": [TEST_VALUE],
    "hash": {"k": TEST_VALUE},
    "array_of_hashes": [{"k": TEST_VALUE}],
}
UPLOAD_NAME = "upload.bin"
UPLOAD_BYTES = b"v1 upload"
EMPTY_PAGE: List[Any] = []
EMPTY_OBJECT: Dict[str, Any] = {}

# gitlab-dedicated#update-a-geo-site (`PUT /geo_sites/:id`), unreachable by the Offering arm: its page names only
# GitLab Self-Managed. The record a slice writes from "Update a Geo site", every body row a SCALAR but the `array`
# rows; the typed value of each, in table order.
GEO_SITE_ID = "gitlab-dedicated#update-a-geo-site"
GEO_SITE_FAMILY = "families.gitlab_dedicated"
GEO_SITE_METHOD = "PUT"
GEO_SITE_PATH = "/geo_sites/:id"
GEO_SITE_PATH_VALUES: Dict[str, Any] = {"id": "7"}
GEO_SITE_SENT_PATH = "/geo_sites/7"
GEO_SITE_ARRAYS = frozenset({"selective_sync_shards", "selective_sync_namespace_ids"})
GEO_SITE_VALUES: Dict[str, Any] = {
    "enabled": True,
    "name": "site2",
    "url": "https://geo2.example.com",
    "internal_url": "https://geo2-internal.example.com",
    "files_max_capacity": 10,
    "repos_max_capacity": 25,
    "verification_max_capacity": 100,
    "container_repositories_max_capacity": 10,
    "selective_sync_type": "shards",
    "selective_sync_shards": ["default"],
    "selective_sync_namespace_ids": [1, 2],
    "minimum_reverification_interval": 7,
    "blob_download_timeout": 120,
}
GEO_SITE_NAME = "name"
GEO_SITE_ANSWER = {"id": 7}

# software-supply-chain-security#create-an-application (`POST /applications`), as a slice writes it, and the member
# row a record must not declare as a Param of its own.
APPLICATION_ID = "software-supply-chain-security#create-an-application"
APPLICATION_SCALARS = ("name", "redirect_uri", "scopes", "confidential")
APPLICATION_HASHES = "granular_scopes"
APPLICATION_MEMBER = "granular_scopes[].access"


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader, f"{FIXTURES_FILE} is missing"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

CONFIG: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` inside a test, so a module not written yet fails it on an assertion."""
    source = PACKAGE_DIR.joinpath(*name.split(".")).with_suffix(".py")
    assert source.is_file(), f"{PACKAGE}/{'/'.join(name.split('.'))}.py does not exist under {SCRIPTS}"
    return importlib.import_module(name=f"{PACKAGE}.{name}")


# --- The reference half -------------------------------------------------------------------------------------------


class Row(NamedTuple):
    """One row of a section's attribute table: its `In` (`form` read as `body`) and, for a row that is part of another
    attribute (`not[labels]`, `actions[].action`, `strategies:name`), that attribute's name."""

    location: str
    parent: str = ""


NO_ROW = Row(location="")


@dataclass(frozen=True)
class Section:
    """One `###` section of a `rest/<stem>.md` page, keyed `<stem>#<anchor>`."""

    operation_id: str
    endpoints: Tuple[Tuple[str, str], ...]
    rows: Mapping[str, Row]
    offering: Optional[str]

    @property
    def attributes(self) -> Dict[str, str]:
        """Each attribute's `In`: the rows that are part of no other row."""
        return {name: row.location for name, row in self.rows.items() if not row.parent}


class IndexRow(NamedTuple):
    """One method-and-path row of `operations-index.md`, with the id its Reference names."""

    method: str
    path: str
    operation_id: str


def anchor_slug(*, heading: str) -> str:
    """The slug of a heading before numbering (`verify.py` `anchors`, restated)."""
    text = ANCHOR_MARKUP.sub(repl="", string=heading).strip().lower()
    return ANCHOR_DROPPED.sub(repl="", string=text).replace(ANCHOR_SPACE, ANCHOR_DASH)


def page_headings(*, lines: List[str]) -> Iterator[Tuple[int, int, str]]:
    """``(line index, level, anchor)`` of every heading of a page outside fenced code, in page order; a slug that
    repeats on the page gets ``-1``, ``-2``, ... counted over every heading."""
    seen: Dict[str, int] = {}
    fenced = False
    for number, line in enumerate(lines):
        if line.lstrip().startswith(FENCE):
            fenced = not fenced
            continue
        match = None if fenced else HEADING.match(string=line)
        if match is None:
            continue
        base = anchor_slug(heading=match.group(GROUP_TEXT))
        seen[base] = seen.get(base, -1) + 1
        yield number, len(match.group(GROUP_MARKS)), base if seen[base] == 0 else f"{base}-{seen[base]}"


def line_offering(*, lines: Iterable[str], start: str) -> Optional[str]:
    """The `Offering:` of the first line beginning with ``start``; ``None`` when no such line names one."""
    for line in lines:
        if line.startswith(start):
            match = OFFERING.search(string=line)
            return match.group(GROUP_OFFERING).strip() if match else None
    return None


def section_endpoints(*, lines: Iterable[str]) -> Tuple[Tuple[str, str], ...]:
    """Every `` `METHOD path` `` span of the first non-empty line."""
    first = next((line for line in lines if line.strip()), "")
    return tuple((match.group(GROUP_METHOD), match.group(GROUP_PATH)) for match in ENDPOINT.finditer(string=first))


def table_name(*, cell: str, attribute_name: Callable[..., str]) -> str:
    """A row's attribute name: the backticked text up to an annotation or a footnote, then `registry.attribute_name`."""
    for end in NAME_ENDS:
        cell = cell.split(end, 1)[0]
    return attribute_name(name=cell)


def parent_of(*, name: str, names: Iterable[str]) -> str:
    """The shortest other row name that ``name`` continues with `[` or `:`; empty when there is none."""
    parents = [
        other for other in names if other != name and any(name.startswith(other + mark) for mark in MEMBER_MARKS)
    ]
    return min(parents, key=len) if parents else ""


def table_rows(*, lines: Iterable[str], attribute_name: Callable[..., str]) -> Dict[str, Row]:
    """The rows of the section's `| Attribute | In | Type |` table, by name; a name read twice is one row, the first."""
    locations: Dict[str, str] = {}
    in_table = False
    for line in lines:
        if line.startswith(TABLE_HEADER_START):
            in_table = True
            continue
        if in_table and not line.startswith(TABLE_LINE_START):
            break
        match = TABLE_ROW.match(string=line) if in_table else None
        if match is None:
            continue
        name = table_name(cell=match.group(GROUP_NAME), attribute_name=attribute_name)
        if ALTERNATION in name:
            continue
        location = match.group(GROUP_LOCATION)
        locations.setdefault(name, IN_BODY if location == IN_FORM else location)
    return {
        name: Row(location=location, parent=parent_of(name=name, names=locations))
        for name, location in locations.items()
    }


def page_sections(*, stem: str, text: str, attribute_name: Callable[..., str]) -> Iterator[Section]:
    """The `###` sections of one page; a section runs from its heading to the next heading, and a page's offering is
    the one on the `Docs page:` line under its `##` heading."""
    lines = text.splitlines()
    headings = list(page_headings(lines=lines))
    page_offering: Optional[str] = None
    for position, (number, level, anchor) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        body = lines[number + 1 : end]
        if level == PAGE_LEVEL:
            page_offering = line_offering(lines=body, start=PAGE_LINE_START)
        elif level == SECTION_LEVEL:
            yield Section(
                operation_id=f"{stem}{ID_SEPARATOR}{anchor}",
                endpoints=section_endpoints(lines=body),
                rows=table_rows(lines=body, attribute_name=attribute_name),
                offering=line_offering(lines=body, start=SECTION_LINE_START) or page_offering,
            )


def reference_sections(*, rest_dir: Path) -> Dict[str, Section]:
    """Every section of every `rest/<stem>.md`, each page read once, keyed `<stem>#<anchor>`."""
    registry = gitlab_module(name="registry")
    sections: Dict[str, Section] = {}
    for page in sorted(rest_dir.glob("*.md")):
        text = page.read_text(encoding=TEXT_ENCODING)
        for section in page_sections(stem=page.stem, text=text, attribute_name=registry.attribute_name):
            sections[section.operation_id] = section
    return sections


def index_rows(*, path: Path) -> List[IndexRow]:
    """Every method-and-path row of an operations index, in file order."""
    rows: List[IndexRow] = []
    for line in path.read_text(encoding=TEXT_ENCODING).splitlines():
        match = INDEX_ROW.match(string=line.rstrip())
        if match is not None:
            rows.append(
                IndexRow(
                    method=match.group(GROUP_METHOD),
                    path=match.group(GROUP_PATH),
                    operation_id=f"{match.group(GROUP_STEM)}{ID_SEPARATOR}{match.group(GROUP_ANCHOR)}",
                )
            )
    assert rows, f"{path} holds no method-and-path row"
    return rows


def is_unreachable(*, path: str, section: Section) -> bool:
    """D5's rule: the index row's path is under `/admin/`, `/geo/` or `/hooks/`, or the section's effective `Offering:`
    does not name `GitLab.com` (a section with none counts as offered on GitLab.com)."""
    if path.startswith(UNREACHABLE_PREFIXES):
        return True
    if section.offering is None:
        return False
    return GITLAB_COM not in [part.strip() for part in section.offering.split(OFFERING_SEPARATOR)]


def paging_parameters(*, record: Any) -> FrozenSet[str]:
    """The query names a paged record may declare or not (`PAGING_PARAMETERS`), none for `Paging.NONE`."""
    return PAGING_PARAMETERS.get(record.paging.value, NO_PAGING_PARAMETERS)


def endpoint_problems(*, record: Any, section: Section, registry: ModuleType) -> List[str]:
    """A record method and path that is no endpoint of the section; a `path` row no endpoint has as a placeholder."""
    problems: List[str] = []
    if (record.method, record.path) not in section.endpoints:
        problems.append(f"{record.method} {record.path} is none of the section's endpoints {list(section.endpoints)}")
    placeholders = {name for _, path in section.endpoints for name in registry.placeholders(path=path)}
    problems.extend(
        f"the path row {name!r} is a placeholder of none of the section's endpoints"
        for name, row in section.rows.items()
        if row.location == IN_PATH and name not in placeholders
    )
    return problems


def is_member_name_allowed(*, record: Any, param: Any, registry: ModuleType) -> bool:
    """A name holding `[` or `:` is a `parent[key]` name of a query `Param` or of a FORM-body record."""
    if not any(mark in param.name for mark in MEMBER_MARKS):
        return True
    in_hash = param.location is registry.Location.QUERY or record.body is registry.BodyFormat.FORM
    return bool(PARENT_KEY.fullmatch(string=param.name)) and in_hash


def param_problems(*, record: Any, section: Section, registry: ModuleType) -> List[str]:
    """Each `Param` that matches no row, sits elsewhere than its row's `In`, or names a member it may not."""
    problems: List[str] = []
    optional = paging_parameters(record=record)
    for param in record.params:
        row = section.rows.get(param.name)
        if row is None and param.name not in optional:
            problems.append(f"the Param {param.name!r} matches no row of the section's table")
        elif row is not None and row.location != param.location.value:
            problems.append(
                f"the Param {param.name!r} is declared {param.location.value}, its row is In {row.location}"
            )
        if not is_member_name_allowed(record=record, param=param, registry=registry):
            problems.append(
                f"the Param {param.name!r} holds '[' or ':' but is no parent[key] name of a query Param or of a"
                " FORM-body record"
            )
    return problems


def record_problems(*, record: Any, section: Optional[Section]) -> List[str]:
    """Every difference between a REST record and its section, each prefixed with the record's id (D5)."""
    if section is None:
        return [f"{record.operation_id}: no section of rest/*.md has this id"]
    registry = gitlab_module(name="registry")
    declared = {param.name for param in record.params}
    optional = paging_parameters(record=record)
    problems = endpoint_problems(record=record, section=section, registry=registry)
    problems.extend(param_problems(record=record, section=section, registry=registry))
    problems.extend(
        f"the {location} row {name!r} is not declared by the record"
        for name, location in section.attributes.items()
        if location in SENT_PLACES and name not in declared and name not in optional
    )
    problems.extend(
        f"the fixed name {name!r} is not a query row"
        for name, _ in record.fixed
        if section.rows.get(name, NO_ROW).location != IN_QUERY
    )
    return [f"{record.operation_id}: {problem}" for problem in problems]


# --- The call half ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SentCall:
    """The shape of one sent request: its method, its path after `/api/v4`, the names of its query pairs and of its
    body members, in the order sent."""

    method: str
    path: str
    query: Tuple[str, ...] = ()
    body: Tuple[str, ...] = ()


def media_type(*, content_type: str) -> str:
    """The lower-cased media type of a `Content-Type` value, without its parameters."""
    message = Message()
    message[HEADER_CONTENT_TYPE] = content_type
    return message.get_content_type()


def multipart_names(*, content_type: str, body: bytes) -> Tuple[str, ...]:
    """The `Content-Disposition` `name` of every part of a `multipart/form-data` body, read with `BytesParser`."""
    head = f"{HEADER_CONTENT_TYPE}: {content_type}{HEADER_BLOCK_END}".encode(encoding=ASCII_ENCODING)
    message = email.parser.BytesParser().parsebytes(text=head + body)
    assert message.is_multipart(), f"a {CONTENT_TYPE_MULTIPART} body that is not multipart: {body!r}"
    return tuple(
        str(part.get_param(param=DISPOSITION_NAME, header=HEADER_CONTENT_DISPOSITION)) for part in message.get_payload()
    )


def body_members(*, request: Any) -> Tuple[str, ...]:
    """The top-level keys of a JSON body, the pair names of a form body, the part names of a multipart body."""
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    if request.body is None or not content_type:
        return ()
    media = media_type(content_type=content_type)
    if media == CONTENT_TYPE_JSON:
        return tuple(json.loads(s=request.body.decode(encoding=TEXT_ENCODING)))
    if media == CONTENT_TYPE_FORM:
        pairs = urllib.parse.parse_qsl(qs=request.body.decode(encoding=ASCII_ENCODING), keep_blank_values=True)
        return tuple(name for name, _ in pairs)
    if media == CONTENT_TYPE_MULTIPART:
        return multipart_names(content_type=content_type, body=request.body)
    raise AssertionError(f"{request.method} {request.url} sent a body of the media type {media}")


def sent_call(*, request: Any) -> SentCall:
    """The shape of a request the fake host recorded (a `RecordedRequest`)."""
    split = urllib.parse.urlsplit(url=request.url)
    path = split.path[len(REST_PREFIX) :] if split.path.startswith(REST_PREFIX) else split.path
    query = tuple(name for name, _ in urllib.parse.parse_qsl(qs=split.query, keep_blank_values=True))
    return SentCall(method=request.method, path=path, query=query, body=body_members(request=request))


def documented_name(*, name: str, documented: Iterable[str]) -> str:
    """A sent pair or part name read as the longest documented name it equals or continues with `[`; a name that
    matches none, up to its first `[`."""
    matches = [candidate for candidate in documented if name == candidate or name.startswith(candidate + BRACKET)]
    return max(matches, key=len) if matches else name.partition(BRACKET)[0]


def expanded_path(*, path: str, values: Mapping[str, Any]) -> Optional[str]:
    """``path`` with each `:name` replaced by its value; ``None`` when a placeholder has no value."""
    names = [match.group(GROUP_NAME) for match in PATH_PLACEHOLDER.finditer(string=path)]
    if any(name not in values for name in names):
        return None
    return PATH_PLACEHOLDER.sub(repl=lambda match: str(values[match.group(GROUP_NAME)]), string=path)


def route_problems(*, section: Section, values: Mapping[str, Any], sent: SentCall) -> List[str]:
    """A method other than the section's; a path other than the section's with each `:name` replaced by its value."""
    methods = sorted({method for method, _ in section.endpoints})
    paths = [expanded_path(path=path, values=values) for _, path in section.endpoints]
    problems: List[str] = []
    if sent.method not in methods:
        problems.append(f"the method {sent.method!r} is not the section's ({', '.join(methods)})")
    if sent.path not in paths:
        problems.append(f"the path {sent.path!r} is none of the section's paths with the values {paths}")
    return problems


def call_problems(*, section: Section, values: Mapping[str, Any], sent: SentCall) -> List[str]:
    """Every difference between a sent call and its section (D5): the method, the path, a sent query or body name the
    section does not document in that place, a given attribute missing from the place the section documents it in."""
    problems = route_problems(section=section, values=values, sent=sent)
    read: Dict[str, List[str]] = {}
    for place, names in ((IN_QUERY, sent.query), (IN_BODY, sent.body)):
        read[place] = [documented_name(name=name, documented=section.rows) for name in names]
        problems.extend(
            f"the {place} name {name!r} (read as {documented!r}) is not documented in the {place}"
            for name, documented in zip(names, read[place])
            if section.rows.get(documented, NO_ROW).location != place
        )
    path_names = {
        match.group(GROUP_NAME) for _, path in section.endpoints for match in PATH_PLACEHOLDER.finditer(string=path)
    }
    for name in values:
        row = section.rows.get(name, NO_ROW)
        if name not in path_names and row.location in read and name not in read[row.location]:
            problems.append(f"the attribute {name!r} was given but is not sent in the {row.location}")
    return problems


def documented_paging(*, section: Section, record: Any) -> Section:
    """The section with the paging parameters of a paged record documented as query names (D5 "Paging parameters")."""
    added = {name: Row(location=IN_QUERY) for name in paging_parameters(record=record) if name not in section.rows}
    return replace(section, rows={**section.rows, **added})


# --- Records and calls the tests build ----------------------------------------------------------------------------


def rest_records(*, registry: ModuleType) -> List[Any]:
    """Every REST record of every family module discovery finds."""
    return [record for family in registry.discover_families() for record in family.OPERATIONS]


def typed_argument(*, param: Any, registry: ModuleType, upload: Path) -> Tuple[str, str, Any]:
    """The option, its text and the value it gives one `Param`, by its `Kind` and location (D5's table)."""
    if param.kind is registry.Kind.FILE:
        return OPTION_FILE, str(upload), upload
    if param.kind is registry.Kind.SCALAR:
        option = OPTION_QUERY if param.location is registry.Location.QUERY else OPTION_RAW_FIELD
        return option, TEST_VALUE, TEST_VALUE
    value = TYPED_VALUES[param.kind.value]
    return OPTION_FIELD, json.dumps(obj=value), value


def record_call(*, record: Any, registry: ModuleType, upload: Path) -> Tuple[List[str], Dict[str, Any]]:
    """The `call` argv that gives every path parameter and `Param` of ``record`` a typed value, and those values."""
    argv = [CALL_COMMAND, record.operation_id]
    values: Dict[str, Any] = {}
    for name in dict.fromkeys(registry.placeholders(path=record.path)):
        argv.extend([OPTION_PATH, f"{name}{ASSIGNED}{TEST_VALUE}"])
        values[name] = TEST_VALUE
    for param in record.params:
        option, text, value = typed_argument(param=param, registry=registry, upload=upload)
        argv.extend([option, f"{param.name}{ASSIGNED}{text}"])
        values[param.name] = value
    return argv, values


def contract_project(*, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A temporary project as the working directory: `config/gitlab.json` for the fake host."""
    fixtures.write_config(root=root, config=CONFIG)
    monkeypatch.chdir(root)


def geo_site_record(*, registry: ModuleType, name_location: Any = None) -> Any:
    """`gitlab-dedicated#update-a-geo-site` as a slice writes it; ``name_location`` moves its `name` elsewhere."""
    params = tuple(
        registry.Param(
            name=name,
            location=(name_location or registry.Location.BODY) if name == GEO_SITE_NAME else registry.Location.BODY,
            kind=registry.Kind.ARRAY if name in GEO_SITE_ARRAYS else registry.Kind.SCALAR,
        )
        for name in GEO_SITE_VALUES
    )
    return registry.RestOperation(operation_id=GEO_SITE_ID, method=GEO_SITE_METHOD, path=GEO_SITE_PATH, params=params)


def geo_site_argv() -> List[str]:
    """`call gitlab-dedicated#update-a-geo-site --path id=7` with a typed value for every attribute."""
    argv = [CALL_COMMAND, GEO_SITE_ID, OPTION_PATH, f"id{ASSIGNED}{GEO_SITE_PATH_VALUES['id']}"]
    for name, value in GEO_SITE_VALUES.items():
        if isinstance(value, str):
            argv.extend([OPTION_RAW_FIELD, f"{name}{ASSIGNED}{value}"])
        else:
            argv.extend([OPTION_FIELD, f"{name}{ASSIGNED}{json.dumps(obj=value)}"])
    return argv


def geo_site_sent(
    *, method: str = GEO_SITE_METHOD, path: str = GEO_SITE_SENT_PATH, query: Tuple[str, ...] = (), body: Any = None
) -> SentCall:
    """The shape of the geo-site call as the section documents it, with one part changed."""
    return SentCall(method=method, path=path, query=query, body=tuple(GEO_SITE_VALUES) if body is None else body)


def application_record(*, registry: ModuleType, member: bool) -> Any:
    """`software-supply-chain-security#create-an-application` as a slice writes it; ``member`` adds the BODY `Param`
    `granular_scopes[].access`, a row that is part of `granular_scopes`."""
    params = [registry.Param(name=name, location=registry.Location.BODY) for name in APPLICATION_SCALARS]
    params.append(
        registry.Param(name=APPLICATION_HASHES, location=registry.Location.BODY, kind=registry.Kind.ARRAY_OF_HASHES)
    )
    if member:
        params.append(registry.Param(name=APPLICATION_MEMBER, location=registry.Location.BODY))
    return registry.RestOperation(
        operation_id=APPLICATION_ID, method="POST", path="/applications", params=tuple(params)
    )


# --- AC-3.1: the rule -----------------------------------------------------------------------------------------------

REACHABLE_ID = "plan#retrieve-a-project-issue"
OFFERING_ARM_IDS = (GEO_SITE_ID, "tenant-scale#transfer-a-project-to-a-group")
PATH_ARM_IDS = (
    "openapi-only#restart-a-batched-background-operation",
    "openapi-only#determine-if-a-geo-site-should-proxy-requests",
    "openapi-only#update-a-custom-header",
)


def test_the_unreachable_rule_has_two_arms() -> None:
    """`is_unreachable` is false for a project issue; true by the Offering arm for a Geo site (its page names only
    GitLab Self-Managed) and a project transfer (its own line, under a page that names GitLab.com); true by the path
    arm only for the three OpenAPI-only operations under `/admin/`, `/geo/` and `/hooks/`, which carry no offering."""
    sections = reference_sections(rest_dir=REST_DIR)
    paths: Dict[str, List[str]] = {}
    for row in index_rows(path=INDEX):
        paths.setdefault(row.operation_id, []).append(row.path)

    assert paths[REACHABLE_ID] == ["/projects/:id/issues/:issue_iid"]
    assert is_unreachable(path=paths[REACHABLE_ID][0], section=sections[REACHABLE_ID]) is False
    for operation_id in OFFERING_ARM_IDS:
        (path,) = paths[operation_id]
        assert not path.startswith(UNREACHABLE_PREFIXES), path
        assert is_unreachable(path=path, section=sections[operation_id]) is True, operation_id
    for operation_id in PATH_ARM_IDS:
        (path,) = paths[operation_id]
        assert sections[operation_id].offering is None, operation_id
        assert is_unreachable(path=path, section=sections[operation_id]) is True, operation_id
        assert is_unreachable(path=paths[REACHABLE_ID][0], section=sections[operation_id]) is False, operation_id


# --- AC-3.2: the reader and the records record_problems passes ----------------------------------------------------


def test_a_section_is_read_as_the_reference_writes_it() -> None:
    """The reader's anchors, endpoints, attributes, member rows and offerings, as D5 pins them; the records
    `record_problems` passes although their tables lack a path row or hold one of another endpoint; and every row of
    `operations-index.md` names, by its Reference, a section whose endpoints hold the row's method and path."""
    registry = gitlab_module(name="registry")
    sections = reference_sections(rest_dir=REST_DIR)
    body, query = registry.Location.BODY, registry.Location.QUERY

    assert sections["software-supply-chain-security#as-a-regular-user"].endpoints == (("GET", "/users"),)
    assert sections["software-supply-chain-security#as-a-regular-user-1"].endpoints == (("GET", "/user"),)

    issues = sections["plan#list-all-project-issues"]
    assert issues.endpoints == (("GET", "/projects/:id/issues"),)
    assert {name: issues.attributes.get(name) for name in ("id", "iids", "not")} == {
        "id": IN_PATH,
        "iids": IN_QUERY,
        "not": IN_QUERY,
    }
    assert "iids[]" not in issues.rows
    assert issues.rows["not[labels]"] == Row(location=IN_QUERY, parent="not")
    assert "not[labels]" not in issues.attributes

    commit = sections["create#create-a-commit"]
    assert commit.attributes.get("actions") == IN_BODY
    assert "actions[].action" not in commit.attributes
    assert commit.rows["actions[].action"].parent == "actions"
    approvals = sections["ai-coding#update-approval-configuration-for-a-project"]
    assert approvals.attributes.get("approvals_before_merge") == IN_BODY
    changelog = sections["create#add-changelog-data-to-file"]
    assert {name: changelog.attributes.get(name) for name in ("version", "from")} == {
        "version": IN_BODY,
        "from": IN_BODY,
    }
    assert not [name for name in changelog.rows if "[^" in name or " (" in name]
    status = sections["create#set-commit-pipeline-status"]
    assert {name: status.attributes.get(name) for name in ("name", "context")} == {"name": IN_BODY, "context": IN_BODY}
    assert "name or context" not in status.rows
    assert sections["plan#upload-a-file-to-a-group"].attributes.get("file") == IN_BODY

    passed = (
        registry.RestOperation(
            operation_id="create#health",
            method="GET",
            path="/projects/:id/repository/health",
            params=(registry.Param(name="generate", location=query),),
        ),
        registry.RestOperation(
            operation_id="growth#force-a-variant-assignment",
            method="POST",
            path="/experiments/:experiment_name/assignments",
            params=tuple(
                registry.Param(name=name, location=body)
                for name in ("variant", "context[user]", "context[namespace]", "context[project]")
            ),
            body=registry.BodyFormat.FORM,
        ),
        registry.RestOperation(
            operation_id="fulfillment#delete-an-ldap-group-link-deprecated",
            method="DELETE",
            path="/groups/:id/ldap_group_links/:cn",
        ),
        registry.RestOperation(
            operation_id="package#retrieve-a-recipe-snapshot",
            method="GET",
            path="/projects/:id/packages/conan/v1/conans/:package_version/:package_username/:package_channel",
        ),
    )
    assert "id" not in sections["create#health"].rows
    assert sections["fulfillment#delete-an-ldap-group-link-deprecated"].rows["provider"].location == IN_PATH
    assert sections["package#retrieve-a-recipe-snapshot"].rows["package_name"].location == IN_PATH
    for record in passed:
        assert record_problems(record=record, section=sections.get(record.operation_id)) == [], record.operation_id

    assert sections["gitlab-dedicated#list-all-system-hooks"].offering == "GitLab Self-Managed"
    assert sections["tenant-scale#transfer-a-project-to-a-group"].offering == "GitLab Self-Managed, GitLab Dedicated"
    assert sections["tenant-scale#create-a-group-invitation"].offering == (
        "GitLab.com, GitLab Self-Managed, GitLab Dedicated"
    )

    unmatched = [
        f"{row.method} {row.path} -> {row.operation_id}"
        for row in index_rows(path=INDEX)
        if row.operation_id not in sections or (row.method, row.path) not in sections[row.operation_id].endpoints
    ]
    assert not unmatched, "\n".join(unmatched)


# --- AC-3.2: the method names every difference ----------------------------------------------------------------------


def differing_method(*, sections: Mapping[str, Section], registry: ModuleType) -> List[str]:
    return call_problems(
        section=sections[GEO_SITE_ID],
        values={**GEO_SITE_PATH_VALUES, **GEO_SITE_VALUES},
        sent=geo_site_sent(method="PATCH"),
    )


def differing_path(*, sections: Mapping[str, Section], registry: ModuleType) -> List[str]:
    return call_problems(
        section=sections[GEO_SITE_ID],
        values={**GEO_SITE_PATH_VALUES, **GEO_SITE_VALUES},
        sent=geo_site_sent(path="/geo_site/7"),
    )


def differing_body_member(*, sections: Mapping[str, Section], registry: ModuleType) -> List[str]:
    body = tuple("site_name" if name == GEO_SITE_NAME else name for name in GEO_SITE_VALUES)
    return call_problems(
        section=sections[GEO_SITE_ID], values={**GEO_SITE_PATH_VALUES, **GEO_SITE_VALUES}, sent=geo_site_sent(body=body)
    )


def differing_place(*, sections: Mapping[str, Section], registry: ModuleType) -> List[str]:
    body = tuple(name for name in GEO_SITE_VALUES if name != GEO_SITE_NAME)
    return call_problems(
        section=sections[GEO_SITE_ID],
        values={**GEO_SITE_PATH_VALUES, **GEO_SITE_VALUES},
        sent=geo_site_sent(query=(GEO_SITE_NAME,), body=body),
    )


def differing_record_location(*, sections: Mapping[str, Section], registry: ModuleType) -> List[str]:
    record = geo_site_record(registry=registry, name_location=registry.Location.QUERY)
    return record_problems(record=record, section=sections[GEO_SITE_ID])


def differing_member_param(*, sections: Mapping[str, Section], registry: ModuleType) -> List[str]:
    record = application_record(registry=registry, member=True)
    problems = record_problems(record=record, section=sections[APPLICATION_ID])
    assert len(problems) == 1, problems
    return problems


@pytest.mark.parametrize(
    ("problems_of", "named"),
    [
        pytest.param(differing_method, "'PATCH'", id="method-PATCH"),
        pytest.param(differing_path, "'/geo_site/7'", id="path-geo_site"),
        pytest.param(differing_body_member, "'site_name'", id="body-site_name-for-name"),
        pytest.param(differing_place, "'name'", id="name-in-the-query"),
        pytest.param(differing_record_location, "'name'", id="record-name-declared-query"),
        pytest.param(differing_member_param, f"'{APPLICATION_MEMBER}'", id="record-member-as-param"),
    ],
)
def test_the_method_rejects_a_call_that_differs(problems_of: Callable[..., List[str]], named: str) -> None:
    """Each case differs from its section in one place, and a problem names that method, path or attribute; the call
    and the records as the sections document them have none."""
    registry = gitlab_module(name="registry")
    sections = reference_sections(rest_dir=REST_DIR)
    geo_site = sections[GEO_SITE_ID]
    assert (
        call_problems(section=geo_site, values={**GEO_SITE_PATH_VALUES, **GEO_SITE_VALUES}, sent=geo_site_sent()) == []
    )
    assert record_problems(record=geo_site_record(registry=registry), section=geo_site) == []
    application = application_record(registry=registry, member=False)
    assert record_problems(record=application, section=sections[APPLICATION_ID]) == []

    problems = problems_of(sections=sections, registry=registry)
    assert any(named in problem for problem in problems), problems


# --- AC-3.1, AC-1.1: every declared record ------------------------------------------------------------------------


def test_every_record_matches_its_reference_section() -> None:
    """Every REST record `discover_families` yields matches its section: endpoint, path rows, every `Param` by name
    and `In`, every query and body row declared (D5's reference half). The message names each record and difference."""
    registry = gitlab_module(name="registry")
    sections = reference_sections(rest_dir=REST_DIR)
    records = rest_records(registry=registry)
    assert records, "discovery found no REST record"
    problems = [
        problem
        for record in records
        for problem in record_problems(record=record, section=sections.get(record.operation_id))
    ]
    assert not problems, "\n".join(problems)


def sent_record_problems(
    *, record: Any, section: Section, values: Mapping[str, Any], code: Any, requests: List[Any], logged: List[str]
) -> List[str]:
    """What one record's `call` did that its section does not document: a refusal or error, other than one request,
    or a difference the call half names."""
    if code != 0:
        return [f"{record.operation_id}: call exited {code}: {' | '.join(logged)}"]
    if len(requests) != 1:
        return [f"{record.operation_id}: call sent {len(requests)} requests, not one"]
    documented = documented_paging(section=section, record=record)
    differences = call_problems(section=documented, values=values, sent=sent_call(request=requests[0]))
    return [f"{record.operation_id}: {problem}" for problem in differences]


def test_every_record_is_sent_as_its_section_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Every discovered REST record outside `GATED_OPERATIONS` runs as `call` through the product's `main`, one
    temporary project and one fake host, every path parameter and `Param` given a typed value (D5's table), answered
    `[]` (paged) or `{}`; each exits 0 and sends one request the call half finds no difference in."""
    call = gitlab_module(name="commands.call")
    registry = gitlab_module(name="registry")
    sections = reference_sections(rest_dir=REST_DIR)
    contract_project(root=tmp_path, monkeypatch=monkeypatch)
    upload = tmp_path / UPLOAD_NAME
    upload.write_bytes(data=UPLOAD_BYTES)
    wrapper = fixtures.load_wrapper(module_name=WRAPPER_MODULE)
    fake = fake_gitlab
    problems: List[str] = []
    for record in rest_records(registry=registry):
        if record.operation_id in call.GATED_OPERATIONS:
            continue
        section = sections.get(record.operation_id)
        if section is None:
            problems.append(f"{record.operation_id}: no section of rest/*.md has this id")
            continue
        argv, values = record_call(record=record, registry=registry, upload=upload)
        fake.script_next(body=EMPTY_OBJECT if record.paging is registry.Paging.NONE else EMPTY_PAGE)
        sent_before, logged_before = len(fake.requests), len(caplog.records)
        code = fixtures.run_main(wrapper=wrapper, argv=argv)
        requests = fake.requests[sent_before:]
        logged = [entry.getMessage() for entry in caplog.records[logged_before:]]
        problems.extend(
            sent_record_problems(
                record=record, section=section, values=values, code=code, requests=requests, logged=logged
            )
        )
        if not requests:
            # The answer queued for this call was never served; the next record gets a fake host of its own.
            fake = fixtures.FakeGitLab().install(monkeypatch=monkeypatch)
    assert not problems, "\n".join(problems)


# --- AC-3.2: an operation no test project can reach -------------------------------------------------------------


def test_an_unreachable_call_matches_its_reference_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_gitlab: Any
) -> None:
    """`gitlab-dedicated#update-a-geo-site`, unreachable by the Offering arm: the record a slice writes matches its
    section; put in `gitlab_dedicated.OPERATIONS` in place of any record declared with its id, for this test only, and
    called with a typed value for every attribute, it exits 0 and sends one request whose JSON body is those values and
    that the call half passes."""
    registry = gitlab_module(name="registry")
    sections = reference_sections(rest_dir=REST_DIR)
    section = sections[GEO_SITE_ID]
    record = geo_site_record(registry=registry)
    assert is_unreachable(path=record.path, section=section)
    assert record_problems(record=record, section=section) == []

    assert (PACKAGE_DIR / "commands" / "call.py").is_file(), "gitlab_api/commands/call.py does not exist"
    dedicated = gitlab_module(name=GEO_SITE_FAMILY)
    others = tuple(declared for declared in dedicated.OPERATIONS if declared.operation_id != GEO_SITE_ID)
    monkeypatch.setattr(target=dedicated, name="OPERATIONS", value=others + (record,))
    contract_project(root=tmp_path, monkeypatch=monkeypatch)
    fake_gitlab.script_next(body=GEO_SITE_ANSWER)

    code = fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=geo_site_argv())

    assert code == 0
    assert len(fake_gitlab.requests) == 1, [(request.method, request.url) for request in fake_gitlab.requests]
    request = fake_gitlab.requests[0]
    values = {**GEO_SITE_PATH_VALUES, **GEO_SITE_VALUES}
    assert call_problems(section=section, values=values, sent=sent_call(request=request)) == []
    assert request.json() == GEO_SITE_VALUES
