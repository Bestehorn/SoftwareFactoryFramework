"""Contract test of the GitLab wrapper's GraphQL records against the GraphQL reference (issue #44, design D7).

Every ``GraphQLOperation`` of ``gitlab_api.graphql_only`` is held to ``docs/api-reference/gitlab/graphql/``.
``reference_schema`` reads each type's fields, with their types and arguments, and each object's ``- Implements:``
names, as the reference writes them; ``read_document`` reads the GraphQL subset the records use; ``document_problems``
walks a record's selection from its root type and names each way the record departs from the reference;
``selected_members`` names the members and types a record's walk visits; ``row_members`` reads the members each "Only
in GraphQL" row of ``conventions.md`` names, with the argument or selection its code span gives; and
``member_problems`` names each member of a row that no record of its capability selects as the row writes it. The
tests prove the method on the reference and on altered copies of named records, then hold every record to it (AC-1.1,
AC-1.2, AC-1.3, AC-4.1).
``test_the_map_names_the_graphql_call`` holds the ``src/payload/scripts/gitlab_api/`` bullet of the project map to
naming the GraphQL call (D8, AC-5.2).

The reference exists only in this repository, so this module lives in ``test/``, as ``test_gitlab_wrapper_contract.py``
does. It loads the product package ``gitlab_api`` from ``src/payload/scripts/``: each test imports a module of the
package itself, after asserting that its file exists, and finds the records by iterating ``graphql_only.OPERATIONS``,
so while a record is not written the test fails on the assertion that names it. Standard library and pytest only; no
test opens a connection.

Run: ``python scripts/run_tests.py test/test_gitlab_graphql_contract.py``.
"""

from __future__ import annotations

import functools
import importlib
import json
import re
import socket
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Optional, Protocol, Sequence, Union

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "src" / "payload" / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
REGISTRY = "registry"
GRAPHQL_ONLY = "graphql_only"
PYTHON_SUFFIX = ".py"
MODULE_SEPARATOR = "."
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING_CAPABILITIES = "PENDING_CAPABILITIES"
GRAPHQL_OPERATION = "GraphQLOperation"
TEXT_ENCODING = "utf-8"

# The reference files D7 reads.
GRAPHQL_DIR = ROOT / "docs" / "api-reference" / "gitlab" / "graphql"
QUERIES_FILE = "queries.md"
MUTATION_FILES = ("mutations-a-j.md", "mutations-j-w.md")
OBJECT_FILES = "objects-*.md"
INTERFACES_FILE = "interfaces.md"
CONVENTIONS = GRAPHQL_DIR / "conventions.md"

# How the reference writes a section, a signature line, an input or payload label, a table and an argument.
GROUP_NAME = "name"
GROUP_TYPE = "type"
GROUP_ARGUMENTS = "arguments"
GROUP_RETURNS = "returns"
GROUP_PAIRS = "pairs"
GROUP_NAMES = "names"
GROUP_LITERAL = "literal"
IDENTIFIER = r"[_A-Za-z][_0-9A-Za-z]*"
SECTION_PREFIX = "## "
SECTION_HEADING = re.compile(rf"## `(?P<{GROUP_NAME}>{IDENTIFIER})`")
SIGNATURE_LINE = re.compile(
    rf"`(?P<{GROUP_NAME}>{IDENTIFIER})(?:\((?P<{GROUP_ARGUMENTS}>[^()]*)\))?` → (?P<{GROUP_RETURNS}>.+)"
)
SIGNATURE_ARGUMENT_SEPARATOR = ", "
# `name: Type`, then any default (` = [TITLE, DESCRIPTION]`) and any notes (` (experiment since 19.2)`), both cut.
ARGUMENT_SPAN = re.compile(
    rf"(?P<{GROUP_NAME}>{IDENTIFIER}): (?P<{GROUP_TYPE}>[\[\]!_0-9A-Za-z]+)(?: = [^()]+)?(?: \([^()]+\))?"
)
INPUT_LABEL = re.compile(rf"Input `(?P<{GROUP_NAME}>{IDENTIFIER})`:")
PAYLOAD_LABEL = re.compile(rf"Payload `(?P<{GROUP_NAME}>{IDENTIFIER})`:")
IMPLEMENTS_PREFIX = "- Implements:"
CODE_SPAN = re.compile(r"`([^`]+)`")
TABLE_ROW_PREFIX = "|"
CELL_SEPARATOR = "|"
SEPARATOR_CELL = re.compile(r":?-+:?")
COLUMN_FIELD = "Field"
COLUMN_INPUT_FIELD = "Input field"
COLUMN_PAYLOAD_FIELD = "Payload field"
COLUMN_TYPE = "Type"
COLUMN_ARGUMENTS = "Arguments"
COLUMN_DEFAULT = "Default"
COLUMN_NOTES = "Notes"
FIELD_TABLE_HEADER = (COLUMN_FIELD, COLUMN_TYPE, COLUMN_ARGUMENTS, COLUMN_NOTES)
INPUT_TABLE_HEADER = (COLUMN_INPUT_FIELD, COLUMN_TYPE, COLUMN_DEFAULT, COLUMN_NOTES)
PAYLOAD_TABLE_HEADER = (COLUMN_PAYLOAD_FIELD, COLUMN_TYPE, COLUMN_NOTES)
# A mutation section's two labelled tables: the label, the table's header, and the column of its field names.
MUTATION_TABLES = (
    (INPUT_LABEL, INPUT_TABLE_HEADER, COLUMN_INPUT_FIELD),
    (PAYLOAD_LABEL, PAYLOAD_TABLE_HEADER, COLUMN_PAYLOAD_FIELD),
)
TYPE_WRAPPERS = str.maketrans("", "", "[]!")
NON_NULL = "!"
LIST_START = "["

# The "Only in GraphQL" table of conventions.md: its heading, its columns, and how a GraphQL cell's code span writes a
# member (`workItem`, `Project.workItems`, `pipelineCreate(async: true)`, `queryComplexity { score limit }`).
ONLY_IN_GRAPHQL_HEADING = "### Only in GraphQL"
HEADING_PREFIX = "#"
COLUMN_CAPABILITY = "Capability"
COLUMN_GRAPHQL = "GraphQL"
ROW_MEMBER_SPAN = re.compile(
    rf"(?P<{GROUP_NAME}>{IDENTIFIER}(?:\.{IDENTIFIER})?)"
    rf"(?:\((?P<{GROUP_PAIRS}>[^()]+)\))?"
    rf"(?: \{{ (?P<{GROUP_NAMES}>[^{{}}]+) \}})?"
)
ROW_PAIR = re.compile(rf"(?P<{GROUP_NAME}>{IDENTIFIER}): (?P<{GROUP_LITERAL}>\S+)")
PAIR_SEPARATOR = ", "
INTEGER_LITERAL = re.compile(r"-?(?:0|[1-9][0-9]*)")
MEMBER_SEPARATOR = "."
# Row 2 names `WorkItem` "with widgets" in words; AC-1.3 asks for the field.
EPICS_CAPABILITY = "Epics with new features (assignees, health status, links to other item types)"
ROW_ADDED_MEMBERS = {EPICS_CAPABILITY: ("WorkItem.widgets",)}

# The GraphQL the records use (D1, D2): the root types, the paging fields, the payload's errors, the ID prefix.
QUERY_TYPE = "Query"
MUTATION_TYPE = "Mutation"
OPERATION_QUERY = "query"
OPERATION_MUTATION = "mutation"
ROOT_TYPES = {OPERATION_QUERY: QUERY_TYPE, OPERATION_MUTATION: MUTATION_TYPE}
ROOT_TYPE_NAMES = frozenset(ROOT_TYPES.values())
TYPENAME_FIELD = "__typename"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
FIELD_ERRORS = "errors"
PAGE_FIELDS = frozenset({FIELD_NODES, FIELD_PAGE_INFO})
PAGE_INFO_FIELDS = frozenset({"hasNextPage", "endCursor"})
ARGUMENT_AFTER = "after"
ARGUMENT_INPUT = "input"
TYPE_STRING = "String"
TYPE_BOOLEAN = "Boolean"
TYPE_INT = "Int"
VARIABLE_SIGIL = "$"
GRAPHQL_ID_PREFIX = "graphql#"
KEYWORD_TRUE = "true"
KEYWORD_FALSE = "false"
KEYWORD_ON = "on"
BOOLEAN_KEYWORDS = {KEYWORD_TRUE: True, KEYWORD_FALSE: False}

# The tokens of a document: white space and commas are ignored ("Insignificant Commas"); anything else is "other".
TOKEN_IGNORED = "ignored"
TOKEN_PUNCTUATOR = "punctuator"
TOKEN_NAME = "name"
TOKEN_INTEGER = "integer"
TOKEN_OTHER = "other"
TOKEN_END = "end"
TOKEN_PATTERN = re.compile(
    rf"(?P<{TOKEN_IGNORED}>[\s,]+)"
    rf"|(?P<{TOKEN_PUNCTUATOR}>\.\.\.|[{{}}():!$\[\]])"
    rf"|(?P<{TOKEN_NAME}>{IDENTIFIER})"
    rf"|(?P<{TOKEN_INTEGER}>-?(?:0|[1-9][0-9]*)(?![._0-9A-Za-z]))"
    rf'|(?P<{TOKEN_OTHER}>"[^"]*"|\S)'
)
OPEN_ARGUMENTS = "("
CLOSE_ARGUMENTS = ")"
OPEN_SELECTION = "{"
CLOSE_SELECTION = "}"
OPEN_LIST = "["
CLOSE_LIST = "]"
DEFINES = ":"
SPREAD = "..."

# test_the_reference_is_read_as_written's examples (design Correctness Properties, "Q's method").
WORK_ITEM_QUERY = "workItem"
WORK_ITEM_QUERY_ARGUMENTS = {"id": "WorkItemID!"}
PROJECT_TYPE = "Project"
PROJECT_WORK_ITEMS = "workItems"
WORK_ITEM_CONNECTION = "WorkItemConnection"
PROJECT_WORK_ITEMS_ARGUMENTS = frozenset({"state", "types", ARGUMENT_AFTER})
DESIGN_UPLOAD_MUTATION = "designManagementUpload"
DESIGN_UPLOAD_ARGUMENTS = {ARGUMENT_INPUT: "DesignManagementUploadInput!"}
DESIGN_UPLOAD_INPUT = "DesignManagementUploadInput"
DESIGN_UPLOAD_FILES = "files"
DESIGN_UPLOAD_FILES_TYPE = "[Upload!]!"
DESIGN_UPLOAD_PAYLOAD = "DesignManagementUploadPayload"
DESIGN_UPLOAD_PAYLOAD_FIELDS = frozenset({"designs", "skippedDesigns", FIELD_ERRORS})
ASSIGNEES_WIDGET = "WorkItemWidgetAssignees"
WIDGET_INTERFACE = "WorkItemWidget"
VULNERABILITY_TYPE = "Vulnerability"
VULNERABILITY_DEPENDENCIES = "dependencies"
DEPENDENCIES_LICENSES = "licenses"
DEPENDENCIES_LICENSES_TYPE = "[String!]"
ASYNC_PIPELINE_CAPABILITY = "Asynchronous pipeline creation"
QUERY_COST_CAPABILITY = "Query cost introspection"
WORK_ITEM_WIDGETS_MEMBERS = frozenset({"WorkItem", "WorkItem.widgets", "WorkItemWidgetHealthStatus.healthStatus"})

# The named records test_the_method_rejects_a_document_that_differs alters.
WORK_ITEM = "graphql#workItem"
PROJECT_WORK_ITEMS_RECORD = "graphql#Project.workItems"
PROJECT_BRANCH_RULES = "graphql#Project.branchRules"
WORK_ITEM_UPDATE = "graphql#workItemUpdate"
WORK_ITEM_CREATE = "graphql#workItemCreate"
QUERY_VULNERABILITY = "graphql#Query.vulnerability"
PIPELINE_CREATE = "graphql#pipelineCreate"
DESIGN_UPLOAD = "graphql#designManagementUpload"
WORK_ITEM_WIDGETS = "graphql#WorkItem.widgets"
BRANCH_RULE_DELETE = "graphql#branchRuleDelete"

# test_the_map_names_the_graphql_call (D8, AC-5.2): the map, the first line of its gitlab_api/ bullet, the indent of
# the bullet's other lines, and what the bullet must hold.
LLM_MAP = ROOT / "docs" / "forLLMConsumption.md"
MAP_BULLET_START = "- `src/payload/scripts/gitlab_api/`"
BULLET_CONTINUATION = " "
BULLET_LINE_SEPARATOR = " "
CALL_SUBCOMMAND = "call"
FILE_OPTION = "--file NAME=PATH"
UPLOAD_TYPE = "Upload"
MAP_GRAPHQL_CALL = (f"{CALL_SUBCOMMAND} {GRAPHQL_ID_PREFIX}", FILE_OPTION, UPLOAD_TYPE)


# ---------------------------------------------------------------------------------------------------------------------
# The reference's types (D7: reference_schema)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldDefinition:
    """One field of a reference type: its ``type`` as the reference writes it (``[Upload!]!``, ``WorkItemConnection``)
    and its ``arguments``, each name to its type as written; an input or payload field has none."""

    type: str
    arguments: Mapping[str, str]


@dataclass(frozen=True)
class ReferenceSchema:
    """The reference as ``reference_schema`` reads it: ``types``, each type's name to its fields (the root types, each
    object and interface, and the input and payload types of the mutation sections), and ``implements``, each object's
    name to the interfaces its ``- Implements:`` line names."""

    types: Mapping[str, Mapping[str, FieldDefinition]]
    implements: Mapping[str, frozenset[str]]


def _named_type(*, type_text: str) -> str:
    """The type a walk enters for a field of type ``type_text``: that text with ``[``, ``]`` and ``!`` removed."""
    return type_text.translate(TYPE_WRAPPERS)


def _cells(*, line: str) -> list[str]:
    """The stripped cells of one Markdown table row."""
    return [cell.strip() for cell in line.strip().strip(CELL_SEPARATOR).split(CELL_SEPARATOR)]


def _sections(*, path: Path) -> list[tuple[str, list[str]]]:
    """Every ``## `name` `` section of a reference file, as its name and the lines under its heading; a ``## `` line
    without a code span (``## Contents``) ends a section and opens none."""
    sections: list[tuple[str, list[str]]] = []
    current: Optional[list[str]] = None
    for line in path.read_text(encoding=TEXT_ENCODING).splitlines():
        if line.startswith(SECTION_PREFIX):
            heading = SECTION_HEADING.fullmatch(line)
            current = None
            if heading is not None:
                current = []
                sections.append((heading.group(GROUP_NAME), current))
        elif current is not None:
            current.append(line)
    return sections


def _table_from(*, lines: Sequence[str], start: int, where: str) -> tuple[list[str], list[list[str]]]:
    """The header and the data rows of the Markdown table whose header row is the first table line at or after
    ``start``; a missing separator row, or a row whose cell count is not the header's, raises ``ValueError``."""
    block: list[list[str]] = []
    for line in lines[start:]:
        if line.startswith(TABLE_ROW_PREFIX):
            block.append(_cells(line=line))
        elif block:
            break
    if len(block) < 2 or not all(SEPARATOR_CELL.fullmatch(cell) for cell in block[1]):
        raise ValueError(f"{where}: the table at line {start + 1} has no header and separator row")
    header, rows = block[0], block[2:]
    uneven = [row for row in rows if len(row) != len(header)]
    if uneven:
        raise ValueError(f"{where}: the rows {uneven} do not have the {len(header)} cells of the header {header}")
    return header, rows


def _section_rows(*, lines: Sequence[str], header: Sequence[str], where: str) -> Optional[list[dict[str, str]]]:
    """The rows of the one table of a section whose header row is ``header``, each as column name to cell; ``None``
    when the section has no such table, ``ValueError`` when it has two."""
    starts = [
        number
        for number, line in enumerate(lines)
        if line.startswith(TABLE_ROW_PREFIX) and _cells(line=line) == list(header)
    ]
    if not starts:
        return None
    if len(starts) > 1:
        raise ValueError(f"{where}: {len(starts)} tables have the header {list(header)}")
    found, rows = _table_from(lines=lines, start=starts[0], where=where)
    return [dict(zip(found, row)) for row in rows]


def _labelled_rows(
    *, lines: Sequence[str], label: re.Pattern[str], header: Sequence[str], where: str
) -> Optional[tuple[str, list[dict[str, str]]]]:
    """The type a ``label`` line names (``Input `I`:``, ``Payload `P`:``) and the rows of the table under it, each as
    column name to cell; ``None`` when the section has no such line. A second such line, or a table under it whose
    header is not ``header``, raises ``ValueError``."""
    labels = [(number, label.fullmatch(line)) for number, line in enumerate(lines)]
    found = [(number, match) for number, match in labels if match is not None]
    if not found:
        return None
    if len(found) > 1:
        raise ValueError(f"{where}: {len(found)} lines match {label.pattern!r}, expected one")
    number, match = found[0]
    table_header, rows = _table_from(lines=lines, start=number + 1, where=where)
    if table_header != list(header):
        raise ValueError(f"{where}: the table under {lines[number]!r} has the header {table_header}, not {header}")
    return match.group(GROUP_NAME), [dict(zip(table_header, row)) for row in rows]


def _code_span(*, cell: str, where: str) -> str:
    """The text of the first code span of a cell: a name cell's name, or a Type cell's link text."""
    match = CODE_SPAN.search(cell)
    if match is None:
        raise ValueError(f"{where}: the cell {cell!r} holds no code span")
    return match.group(1)


def _arguments_of(*, spans: Sequence[str], where: str) -> dict[str, str]:
    """Each ``name: Type`` span (any default after `` = `` and any notes in `` (…)`` cut) as its name to its type; any
    other span, or a name given twice, raises ``ValueError``."""
    arguments: dict[str, str] = {}
    for span in spans:
        match = ARGUMENT_SPAN.fullmatch(span)
        if match is None:
            raise ValueError(f"{where}: the argument {span!r} is not `name: Type`")
        if match.group(GROUP_NAME) in arguments:
            raise ValueError(f"{where}: the argument {match.group(GROUP_NAME)!r} is given twice")
        arguments[match.group(GROUP_NAME)] = match.group(GROUP_TYPE)
    return arguments


def _field_definitions(
    *, rows: Sequence[Mapping[str, str]], name_column: str, where: str
) -> dict[str, FieldDefinition]:
    """The fields of a field, input or payload table: the name cell's code span, the Type cell's link text, and the
    Arguments cell's spans (an input or a payload table has none)."""
    fields: dict[str, FieldDefinition] = {}
    for row in rows:
        name = _code_span(cell=row[name_column], where=where)
        if name in fields:
            raise ValueError(f"{where}: the field {name!r} is on two rows")
        fields[name] = FieldDefinition(
            type=_code_span(cell=row[COLUMN_TYPE], where=where),
            arguments=_arguments_of(spans=CODE_SPAN.findall(row.get(COLUMN_ARGUMENTS, "")), where=where),
        )
    return fields


def _signature(*, name: str, lines: Sequence[str], where: str) -> FieldDefinition:
    """The field a ``queries.md`` or mutations section defines, from its one signature line
    `` `name(arg: Type, …)` → <return type> ``: the return type is the first code span after the arrow."""
    matches = [match for match in (SIGNATURE_LINE.fullmatch(line) for line in lines) if match is not None]
    if len(matches) != 1 or matches[0].group(GROUP_NAME) != name:
        raise ValueError(f"{where}: {len(matches)} signature lines, expected one for {name!r}")
    arguments = matches[0].group(GROUP_ARGUMENTS)
    return FieldDefinition(
        type=_code_span(cell=matches[0].group(GROUP_RETURNS), where=where),
        arguments=_arguments_of(spans=arguments.split(SIGNATURE_ARGUMENT_SEPARATOR) if arguments else [], where=where),
    )


def _define(*, schema: dict[str, dict[str, FieldDefinition]], name: str, fields: dict[str, FieldDefinition]) -> None:
    """Add the type ``name``; a type the reference defines twice raises ``ValueError``."""
    if name in schema:
        raise ValueError(f"the reference defines the type {name!r} twice")
    schema[name] = fields


def _root_fields(*, paths: Sequence[Path]) -> dict[str, FieldDefinition]:
    """The fields of a root type: one per section of the files ``paths``, from its signature line."""
    fields: dict[str, FieldDefinition] = {}
    for path in paths:
        for name, lines in _sections(path=path):
            if name in fields:
                raise ValueError(f"{path.name}: two sections define {name!r}")
            fields[name] = _signature(name=name, lines=lines, where=f"{path.name} {name}")
    return fields


def _mutation_types(*, path: Path) -> dict[str, dict[str, FieldDefinition]]:
    """Each mutation section's input type, from the table under its ``Input `I`:`` line, and its payload type, from
    the table under its ``Payload `P`:`` line."""
    types: dict[str, dict[str, FieldDefinition]] = {}
    for name, lines in _sections(path=path):
        where = f"{path.name} {name}"
        for label, header, name_column in MUTATION_TABLES:
            labelled = _labelled_rows(lines=lines, label=label, header=header, where=where)
            if labelled is not None:
                type_name, rows = labelled
                _define(
                    schema=types,
                    name=type_name,
                    fields=_field_definitions(rows=rows, name_column=name_column, where=where),
                )
    return types


def _implemented(*, lines: Sequence[str], where: str) -> frozenset[str]:
    """The interfaces the one ``- Implements:`` line of a section names, each a code span; none without the line."""
    found = [line for line in lines if line.startswith(IMPLEMENTS_PREFIX)]
    if len(found) > 1:
        raise ValueError(f"{where}: {len(found)} lines start with {IMPLEMENTS_PREFIX!r}, expected at most one")
    if not found:
        return frozenset()
    names = CODE_SPAN.findall(found[0])
    if not names:
        raise ValueError(f"{where}: the line {found[0]!r} names no interface")
    return frozenset(names)


def _object_types(
    *, path: Path, types: dict[str, dict[str, FieldDefinition]], implements: dict[str, frozenset[str]]
) -> None:
    """Add each section of an objects or interfaces file: its ``| Field | Type | Arguments | Notes |`` rows to
    ``types`` and its ``- Implements:`` names to ``implements``."""
    for name, lines in _sections(path=path):
        where = f"{path.name} {name}"
        rows = _section_rows(lines=lines, header=FIELD_TABLE_HEADER, where=where)
        if rows is not None:
            _define(
                schema=types, name=name, fields=_field_definitions(rows=rows, name_column=COLUMN_FIELD, where=where)
            )
        interfaces = _implemented(lines=lines, where=where)
        if interfaces:
            implements[name] = interfaces


def reference_schema(*, graphql_dir: Path) -> ReferenceSchema:
    """Each type's fields, with their types and arguments, as the reference under ``graphql_dir`` writes them (D7):
    ``Query`` from the signature lines of ``queries.md``; ``Mutation`` from those of the mutations files, and each
    mutation's input and payload types from the tables under its ``Input `I`:`` and ``Payload `P`:`` lines; each
    section of ``objects-*.md`` and ``interfaces.md`` from its ``| Field | Type | Arguments | Notes |`` rows, with its
    ``- Implements:`` names. A name no table defines is a leaf (a scalar or an enum)."""
    types: dict[str, dict[str, FieldDefinition]] = {}
    implements: dict[str, frozenset[str]] = {}
    mutation_paths = [graphql_dir / file_name for file_name in MUTATION_FILES]
    _define(schema=types, name=QUERY_TYPE, fields=_root_fields(paths=[graphql_dir / QUERIES_FILE]))
    _define(schema=types, name=MUTATION_TYPE, fields=_root_fields(paths=mutation_paths))
    for path in mutation_paths:
        for name, fields in _mutation_types(path=path).items():
            _define(schema=types, name=name, fields=fields)
    for path in [*sorted(graphql_dir.glob(OBJECT_FILES)), graphql_dir / INTERFACES_FILE]:
        _object_types(path=path, types=types, implements=implements)
    return ReferenceSchema(types=types, implements=implements)


# ---------------------------------------------------------------------------------------------------------------------
# A record's document (D7: read_document)
# ---------------------------------------------------------------------------------------------------------------------


class DocumentSyntaxError(ValueError):
    """A GraphQL document outside the subset ``read_document`` reads."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True)
class Variable:
    """An argument or input-field value that is the variable ``$name``."""

    name: str


@dataclass(frozen=True)
class IntValue:
    """An integer value, ``100``."""

    value: int


@dataclass(frozen=True)
class BooleanValue:
    """A ``true`` or ``false`` value."""

    value: bool


@dataclass(frozen=True)
class ObjectValue:
    """An input object written into the document, ``{name: value, …}``: each field's name to its value."""

    fields: Mapping[str, Value]


Value = Union[Variable, IntValue, BooleanValue, ObjectValue]


@dataclass(frozen=True)
class SelectedField:
    """One field of a selection set: its ``name``, its ``arguments`` (name to value) and its ``selections`` (``()``
    for none)."""

    name: str
    arguments: Mapping[str, Value]
    selections: tuple[Selection, ...]


@dataclass(frozen=True)
class InlineFragment:
    """An inline fragment ``... on T { … }``: its ``type_condition`` ``T`` and its ``selections``."""

    type_condition: str
    selections: tuple[Selection, ...]


Selection = Union[SelectedField, InlineFragment]


@dataclass(frozen=True)
class Document:
    """A read document: its ``operation`` (``query`` or ``mutation``), its ``variables`` (name to type as written),
    its root ``selections``, and the ``problems`` the reader names; a document with a problem holds nothing else."""

    operation: str
    variables: Mapping[str, str]
    selections: tuple[Selection, ...]
    problems: tuple[str, ...]


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    offset: int


def _tokens(*, document: str) -> list[_Token]:
    """The tokens of ``document``, white space and commas left out, ending with an end token."""
    tokens = [
        _Token(kind=str(match.lastgroup), text=match.group(), offset=match.start())
        for match in TOKEN_PATTERN.finditer(string=document)
        if match.lastgroup != TOKEN_IGNORED
    ]
    tokens.append(_Token(kind=TOKEN_END, text="", offset=len(document)))
    return tokens


def _described(*, token: _Token) -> str:
    return "the end of the document" if token.kind == TOKEN_END else json.dumps(token.text)


def _variable(*, name: str) -> str:
    return json.dumps(f"{VARIABLE_SIGIL}{name}")


class _DocumentReader:
    """Reads one ``query`` or ``mutation`` with or without ``$name: Type`` definitions; fields whose argument values
    are a ``$variable``, an integer, ``true``, ``false`` or an object of these; nested selections; inline fragments
    ``... on T { … }``. Any other token raises ``DocumentSyntaxError``."""

    def __init__(self, *, document: str) -> None:
        self._tokens = _tokens(document=document)
        self._position = 0

    def read(self) -> Document:
        operation = self._expect(kind=TOKEN_NAME, expected='"query" or "mutation"').text
        if operation not in ROOT_TYPES:
            raise DocumentSyntaxError(message=f"the document is a {json.dumps(operation)}, not a query or a mutation")
        variables = self._variable_definitions() if self._at(text=OPEN_ARGUMENTS) else {}
        selections = self._selection_set()
        self._expect(kind=TOKEN_END, expected="the end of the document")
        return Document(operation=operation, variables=variables, selections=selections, problems=())

    def _peek(self) -> _Token:
        return self._tokens[self._position]

    def _at(self, *, text: str) -> bool:
        token = self._peek()
        return token.kind == TOKEN_PUNCTUATOR and token.text == text

    def _expect(self, *, kind: str, expected: str, text: Optional[str] = None) -> _Token:
        token = self._peek()
        if token.kind != kind or (text is not None and token.text != text):
            raise DocumentSyntaxError(
                message=f"expected {expected} at offset {token.offset}, found {_described(token=token)}"
            )
        self._position += 1
        return token

    def _punctuator(self, *, text: str) -> None:
        self._expect(kind=TOKEN_PUNCTUATOR, text=text, expected=json.dumps(text))

    def _variable_definitions(self) -> dict[str, str]:
        self._punctuator(text=OPEN_ARGUMENTS)
        variables: dict[str, str] = {}
        while not self._at(text=CLOSE_ARGUMENTS) or not variables:
            self._punctuator(text=VARIABLE_SIGIL)
            name = self._expect(kind=TOKEN_NAME, expected="a variable name").text
            self._punctuator(text=DEFINES)
            if name in variables:
                raise DocumentSyntaxError(message=f"the variable {_variable(name=name)} is defined twice")
            variables[name] = self._type_reference()
        self._punctuator(text=CLOSE_ARGUMENTS)
        return variables

    def _type_reference(self) -> str:
        if self._at(text=OPEN_LIST):
            self._punctuator(text=OPEN_LIST)
            text = f"{OPEN_LIST}{self._type_reference()}{CLOSE_LIST}"
            self._punctuator(text=CLOSE_LIST)
        else:
            text = self._expect(kind=TOKEN_NAME, expected="a type name").text
        if self._at(text=NON_NULL):
            self._punctuator(text=NON_NULL)
            text = f"{text}{NON_NULL}"
        return text

    def _selection_set(self) -> tuple[Selection, ...]:
        self._punctuator(text=OPEN_SELECTION)
        selections: list[Selection] = []
        while not self._at(text=CLOSE_SELECTION) or not selections:
            selections.append(self._fragment() if self._at(text=SPREAD) else self._field())
        self._punctuator(text=CLOSE_SELECTION)
        return tuple(selections)

    def _fragment(self) -> InlineFragment:
        self._punctuator(text=SPREAD)
        self._expect(kind=TOKEN_NAME, text=KEYWORD_ON, expected=json.dumps(KEYWORD_ON))
        type_condition = self._expect(kind=TOKEN_NAME, expected="a type name").text
        return InlineFragment(type_condition=type_condition, selections=self._selection_set())

    def _field(self) -> SelectedField:
        name = self._expect(kind=TOKEN_NAME, expected="a field name").text
        arguments: dict[str, Value] = {}
        if self._at(text=OPEN_ARGUMENTS):
            self._punctuator(text=OPEN_ARGUMENTS)
            arguments = self._pairs(close=CLOSE_ARGUMENTS, what="an argument")
        selections = self._selection_set() if self._at(text=OPEN_SELECTION) else ()
        return SelectedField(name=name, arguments=arguments, selections=selections)

    def _pairs(self, *, close: str, what: str) -> dict[str, Value]:
        """At least one ``name: value`` up to ``close``, which it reads; a name given twice raises."""
        pairs: dict[str, Value] = {}
        while not self._at(text=close) or not pairs:
            name = self._expect(kind=TOKEN_NAME, expected=f"the name of {what}").text
            self._punctuator(text=DEFINES)
            if name in pairs:
                raise DocumentSyntaxError(message=f"{what} {json.dumps(name)} is given twice")
            pairs[name] = self._value()
        self._punctuator(text=close)
        return pairs

    def _value(self) -> Value:
        if self._at(text=VARIABLE_SIGIL):
            self._punctuator(text=VARIABLE_SIGIL)
            return Variable(name=self._expect(kind=TOKEN_NAME, expected="a variable name").text)
        if self._at(text=OPEN_SELECTION):
            self._punctuator(text=OPEN_SELECTION)
            return ObjectValue(fields=self._pairs(close=CLOSE_SELECTION, what="an input field"))
        token = self._peek()
        if token.kind == TOKEN_NAME and token.text in BOOLEAN_KEYWORDS:
            self._position += 1
            return BooleanValue(value=BOOLEAN_KEYWORDS[token.text])
        expected = "a $variable, an integer, true, false or an object"
        return IntValue(value=int(self._expect(kind=TOKEN_INTEGER, expected=expected).text))


def read_document(*, document: str) -> Document:
    """``document`` read as the subset the records use (D7): one ``query`` or ``mutation``, with or without
    ``$name: Type`` definitions; fields whose argument values are a ``$variable``, an integer, ``true``, ``false``, or
    an object ``{name: value, …}`` of these; nested selections; inline fragments ``... on T { … }``. Commas count as
    white space. Any other token is the document's one problem."""
    try:
        return _DocumentReader(document=document).read()
    except DocumentSyntaxError as error:
        return Document(operation="", variables={}, selections=(), problems=(str(error),))


# ---------------------------------------------------------------------------------------------------------------------
# A record against the reference (D7: document_problems, selected_members)
# ---------------------------------------------------------------------------------------------------------------------


class GraphQLRecord(Protocol):
    """The fields of a ``GraphQLOperation`` this module reads."""

    @property
    def operation_id(self) -> str: ...

    @property
    def capability(self) -> str: ...

    @property
    def document(self) -> str: ...

    @property
    def connection(self) -> Sequence[str]: ...


TYPENAME_DEFINITION = FieldDefinition(type="String!", arguments={})


def _given(*, value: Union[IntValue, BooleanValue]) -> str:
    """How a problem names a literal value: ``the integer 1``, ``true``."""
    if isinstance(value, BooleanValue):
        return KEYWORD_TRUE if value.value else KEYWORD_FALSE
    return f"the integer {value.value}"


@dataclass
class _Walk:
    """One walk of a read document's selection through the reference, from its root type: the ``problems`` it names,
    the ``members`` it visits (``<Type>.<field>``, a root field's bare name, and each type it enters), and the
    ``fields`` it visits under each member name."""

    schema: ReferenceSchema
    variables: Mapping[str, str]
    problems: list[str] = field(default_factory=list)
    members: set[str] = field(default_factory=set)
    fields: dict[str, list[SelectedField]] = field(default_factory=dict)

    def selections(self, *, parent: str, selections: Sequence[Selection]) -> None:
        for selection in selections:
            if isinstance(selection, InlineFragment):
                self._fragment(parent=parent, fragment=selection)
            else:
                self._field(parent=parent, selected=selection)

    def _fragment(self, *, parent: str, fragment: InlineFragment) -> None:
        """A fragment's type must be a type of the reference that is ``parent`` or implements it."""
        condition = fragment.type_condition
        if condition not in self.schema.types:
            self.problems.append(f"the fragment type {json.dumps(condition)} is no type of the reference")
            return
        if condition != parent and parent not in self.schema.implements.get(condition, frozenset()):
            self.problems.append(
                f"the fragment type {json.dumps(condition)} does not implement {json.dumps(parent)}, the type it is "
                "selected on"
            )
            return
        self.members.add(condition)
        self.selections(parent=condition, selections=fragment.selections)

    def _visit(self, *, member: str, selected: SelectedField) -> None:
        self.members.add(member)
        self.fields.setdefault(member, []).append(selected)

    def _field(self, *, parent: str, selected: SelectedField) -> None:
        typename = selected.name == TYPENAME_FIELD
        definition = TYPENAME_DEFINITION if typename else self.schema.types[parent].get(selected.name)
        if definition is None:
            self.problems.append(f"the type {json.dumps(parent)} has no field {json.dumps(selected.name)}")
            return
        member = f"{parent}{MEMBER_SEPARATOR}{selected.name}"
        if not typename:
            self._visit(member=member, selected=selected)
        if not typename and parent in ROOT_TYPE_NAMES:
            self._visit(member=selected.name, selected=selected)
        for name, value in selected.arguments.items():
            expected = definition.arguments.get(name)
            if expected is None:
                self.problems.append(f"{json.dumps(member)} has no argument {json.dumps(name)}")
            else:
                location = f"the argument {json.dumps(name)} of {json.dumps(member)}"
                self._value(location=location, type_text=expected, value=value)
        self._selection(member=member, definition=definition, selected=selected)

    def _value(self, *, location: str, type_text: str, value: Value) -> None:
        if isinstance(value, Variable):
            self._variable_type(location=location, type_text=type_text, variable=value.name)
        elif isinstance(value, ObjectValue):
            self._object(location=location, type_text=type_text, value=value)
        else:
            expected = TYPE_BOOLEAN if isinstance(value, BooleanValue) else TYPE_INT
            if type_text.rstrip(NON_NULL) != expected:
                self.problems.append(
                    f"{location} is of the type {json.dumps(type_text)} and is given {_given(value=value)}"
                )

    def _variable_type(self, *, location: str, type_text: str, variable: str) -> None:
        """A declared variable's type must be the location's type, or that type with ``!`` added
        (``AreTypesCompatible``, GraphQL spec §5.8.5)."""
        declared = self.variables.get(variable)
        if declared is not None and declared not in (type_text, f"{type_text}{NON_NULL}"):
            self.problems.append(
                f"the variable {_variable(name=variable)} is declared {json.dumps(declared)}, but {location} is "
                f"{json.dumps(type_text)}"
            )

    def _object(self, *, location: str, type_text: str, value: ObjectValue) -> None:
        """An object value's location must be an input type the reference defines, holding each of its fields."""
        input_type = _named_type(type_text=type_text)
        input_fields = self.schema.types.get(input_type)
        if type_text.startswith(LIST_START) or input_fields is None:
            self.problems.append(
                f"{location} is of the type {json.dumps(type_text)}, no input object the reference defines, and is "
                "given an object"
            )
            return
        for name, field_value in value.fields.items():
            definition = input_fields.get(name)
            if definition is None:
                self.problems.append(f"the input type {json.dumps(input_type)} has no field {json.dumps(name)}")
            else:
                location = f"the field {json.dumps(name)} of {json.dumps(input_type)}"
                self._value(location=location, type_text=definition.type, value=field_value)

    def _selection(self, *, member: str, definition: FieldDefinition, selected: SelectedField) -> None:
        named = _named_type(type_text=definition.type)
        if named not in self.schema.types:
            if selected.selections:
                self.problems.append(
                    f"{json.dumps(member)} is of the leaf type {json.dumps(named)} and has a selection"
                )
            return
        if not selected.selections:
            self.problems.append(f"{json.dumps(member)} is of the type {json.dumps(named)} and selects no field")
            return
        self.members.add(named)
        self.selections(parent=named, selections=selected.selections)


def _walked(*, document: Document, schema: ReferenceSchema) -> _Walk:
    walk = _Walk(schema=schema, variables=document.variables)
    walk.selections(parent=ROOT_TYPES[document.operation], selections=document.selections)
    return walk


def _value_variables(*, value: Value) -> set[str]:
    """The name of every ``$variable`` a value holds, inside an object value too."""
    if isinstance(value, Variable):
        return {value.name}
    used: set[str] = set()
    if isinstance(value, ObjectValue):
        for item in value.fields.values():
            used |= _value_variables(value=item)
    return used


def _used_variables(*, selections: Sequence[Selection]) -> set[str]:
    """The name of every ``$variable`` an argument anywhere in ``selections`` holds."""
    used: set[str] = set()
    for selection in selections:
        if isinstance(selection, SelectedField):
            for value in selection.arguments.values():
                used |= _value_variables(value=value)
        used |= _used_variables(selections=selection.selections)
    return used


def _variable_problems(*, document: Document) -> list[str]:
    """A ``$variable`` that is not declared, and a declared variable that is never used."""
    used = _used_variables(selections=document.selections)
    problems = [
        f"the variable {_variable(name=name)} is not declared" for name in sorted(used - set(document.variables))
    ]
    problems.extend(
        f"the variable {_variable(name=name)} is declared but never used"
        for name in document.variables
        if name not in used
    )
    return problems


def _direct_fields(*, selected: SelectedField) -> dict[str, SelectedField]:
    """The fields ``selected`` selects directly, by name; a fragment's fields are not direct."""
    return {child.name: child for child in selected.selections if isinstance(child, SelectedField)}


def _selected_path(*, selections: Sequence[Selection]) -> tuple[tuple[str, ...], Optional[SelectedField]]:
    """The path of selected fields from the root: each the one field of its selection set that has a selection and is
    no ``nodes`` or ``pageInfo``; and the path's last field."""
    path: list[str] = []
    last: Optional[SelectedField] = None
    current = selections
    while len(current) == 1 and isinstance(current[0], SelectedField):
        if not current[0].selections or current[0].name in PAGE_FIELDS:
            break
        last = current[0]
        path.append(last.name)
        current = last.selections
    return tuple(path), last


def _selects_a_page(*, selected: SelectedField) -> bool:
    """Whether ``selected`` selects both ``nodes`` and ``pageInfo { hasNextPage endCursor }``."""
    by_name = _direct_fields(selected=selected)
    page_info = by_name.get(FIELD_PAGE_INFO)
    if FIELD_NODES not in by_name or page_info is None:
        return False
    return PAGE_INFO_FIELDS <= set(_direct_fields(selected=page_info))


def _connection_problems(*, record: GraphQLRecord, document: Document) -> list[str]:
    """For a record with a ``connection``: a selected path that differs from it; only on a path that matches it, a
    last field without ``after: $after``, a selection without both ``nodes`` and ``pageInfo { hasNextPage
    endCursor }``, or a ``$after`` that is not declared ``String``."""
    connection = tuple(record.connection)
    if not connection:
        return []
    path, last = _selected_path(selections=document.selections)
    if path != connection or last is None:
        return [f"the connection {json.dumps(list(connection))} is not the selected path {json.dumps(list(path))}"]
    problems = []
    if last.arguments.get(ARGUMENT_AFTER) != Variable(name=ARGUMENT_AFTER):
        problems.append(f"the connection's last field {json.dumps(last.name)} has no argument after: $after")
    if not _selects_a_page(selected=last):
        problems.append(f"{json.dumps(last.name)} does not select both nodes and pageInfo {{ hasNextPage endCursor }}")
    declared = document.variables.get(ARGUMENT_AFTER)
    if declared != TYPE_STRING:
        problems.append(f"the variable {_variable(name=ARGUMENT_AFTER)} is declared {json.dumps(declared)}, not String")
    return problems


def _mutation_problems(*, record: GraphQLRecord, document: Document) -> list[str]:
    """For a mutation: more than one root selection, no ``errors`` in its root field's selection, or an operation ID
    other than ``graphql#`` and the root field's name (D2), so a refused ID is the mutation the document runs."""
    root = document.selections[0] if len(document.selections) == 1 else None
    if not isinstance(root, SelectedField):
        return [f"the mutation has {len(document.selections)} root selections, not one field"]
    problems = []
    if FIELD_ERRORS not in _direct_fields(selected=root):
        problems.append(f"the mutation {json.dumps(root.name)} does not select {json.dumps(FIELD_ERRORS)}")
    expected = f"{GRAPHQL_ID_PREFIX}{root.name}"
    if record.operation_id != expected:
        problems.append(
            f"the mutation runs {json.dumps(root.name)}, so its operation ID must be {json.dumps(expected)}, not "
            f"{json.dumps(record.operation_id)}"
        )
    return problems


def _query_problems(*, record: GraphQLRecord, members: frozenset[str]) -> list[str]:
    """For a query: an operation ID that is not ``graphql#`` and a member (D2) its walk visits."""
    if not record.operation_id.startswith(GRAPHQL_ID_PREFIX):
        return [
            f"the operation ID {json.dumps(record.operation_id)} does not start with {json.dumps(GRAPHQL_ID_PREFIX)}"
        ]
    member = record.operation_id[len(GRAPHQL_ID_PREFIX) :]
    if member not in members:
        return [f"the query does not select {json.dumps(member)}, the member its operation ID names"]
    return []


def document_problems(*, record: GraphQLRecord, schema: ReferenceSchema) -> list[str]:
    """Every way ``record`` departs from the reference (D7), each prefixed with its operation ID: the reader's
    problem; a field its parent type lacks (``__typename`` aside), an argument its field lacks, an input-object field
    its input type lacks; a ``$variable`` undeclared, unused, or declared with a type its location does not accept;
    ``true`` or ``false`` where the type is not ``Boolean``, an integer where it is not ``Int``; a leaf with a
    selection, an object or interface without one; a fragment type that does not implement the field's type; and the
    connection, mutation and query rules."""
    document = read_document(document=record.document)
    problems = list(document.problems)
    if not problems:
        walk = _walked(document=document, schema=schema)
        operation = (
            _mutation_problems(record=record, document=document)
            if document.operation == OPERATION_MUTATION
            else _query_problems(record=record, members=frozenset(walk.members))
        )
        problems = [
            *walk.problems,
            *_variable_problems(document=document),
            *_connection_problems(record=record, document=document),
            *operation,
        ]
    return [f"{record.operation_id}: {problem}" for problem in problems]


def selected_members(*, record: GraphQLRecord, schema: ReferenceSchema) -> frozenset[str]:
    """``<Type>.<field>`` for every field the walk of ``record``'s selection visits (a fragment's under its type), each
    root field also bare, and every type the walk enters; none for a document the reader cannot read."""
    document = read_document(document=record.document)
    if document.problems:
        return frozenset()
    return frozenset(_walked(document=document, schema=schema).members)


# ---------------------------------------------------------------------------------------------------------------------
# The members the "Only in GraphQL" table names (D7: row_members, member_problems)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RowMember:
    """One member an "Only in GraphQL" row names: its ``name`` (``workItem``, ``Project.workItems``, ``WorkItem``), the
    ``pairs`` inside its ``( )`` (each name to its literal as written, ``async`` to ``true``) and the ``names`` inside
    its ``{ }``."""

    name: str
    pairs: Mapping[str, str]
    names: frozenset[str]


@dataclass(frozen=True)
class CapabilityRow:
    """One "Only in GraphQL" row: its ``capability`` (the first cell, verbatim) and the ``members`` it names."""

    capability: str
    members: tuple[RowMember, ...]


def _literal(*, text: str, where: str) -> Union[IntValue, BooleanValue]:
    """The value a row's ``name: literal`` pair writes: ``true``, ``false`` or an integer; anything else raises."""
    if text in BOOLEAN_KEYWORDS:
        return BooleanValue(value=BOOLEAN_KEYWORDS[text])
    if INTEGER_LITERAL.fullmatch(text):
        return IntValue(value=int(text))
    raise ValueError(f"{where}: the literal {text!r} is not true, false or an integer")


def _row_member(*, span: str, where: str) -> RowMember:
    """A GraphQL cell's code span as a member: the name up to its ``(`` or `` {``, the ``name: literal`` pairs inside
    its ``( )`` and the names inside its ``{ }``; a span written otherwise raises ``ValueError``."""
    match = ROW_MEMBER_SPAN.fullmatch(span)
    if match is None:
        raise ValueError(f"{where}: the code span {span!r} is no member as the table writes one")
    pairs: dict[str, str] = {}
    written_pairs = match.group(GROUP_PAIRS)
    for text in written_pairs.split(PAIR_SEPARATOR) if written_pairs else []:
        pair = ROW_PAIR.fullmatch(text)
        if pair is None:
            raise ValueError(f"{where}: {text!r} in {span!r} is not `name: literal`")
        _literal(text=pair.group(GROUP_LITERAL), where=where)
        pairs[pair.group(GROUP_NAME)] = pair.group(GROUP_LITERAL)
    names = frozenset((match.group(GROUP_NAMES) or "").split())
    return RowMember(name=match.group(GROUP_NAME), pairs=pairs, names=names)


def _only_in_graphql_start(*, lines: Sequence[str], where: str) -> int:
    """The number of the one ``### Only in GraphQL`` line."""
    starts = [number for number, line in enumerate(lines) if line.rstrip() == ONLY_IN_GRAPHQL_HEADING]
    if len(starts) != 1:
        raise ValueError(f"{where}: {len(starts)} lines are {ONLY_IN_GRAPHQL_HEADING!r}, expected one")
    return starts[0]


def first_cells(*, conventions: Path) -> list[str]:
    """The first cell of every data row of the table under ``### Only in GraphQL``, read line by line up to the table's
    end: the capabilities ``row_members`` must give, in the table's order."""
    lines = conventions.read_text(encoding=TEXT_ENCODING).splitlines()
    table: list[str] = []
    for line in lines[_only_in_graphql_start(lines=lines, where=conventions.name) + 1 :]:
        if line.startswith(TABLE_ROW_PREFIX):
            table.append(line)
        elif table or line.startswith(HEADING_PREFIX):
            break
    return [_cells(line=line)[0] for line in table[2:]]


def row_members(*, conventions: Path) -> tuple[CapabilityRow, ...]:
    """Each "Only in GraphQL" row, in the table's order: its capability (its Capability cell, verbatim) and each code
    span of its GraphQL cell as a member (``_row_member``); row 2 also holds ``WorkItem.widgets`` (AC-1.3)."""
    lines = conventions.read_text(encoding=TEXT_ENCODING).splitlines()
    start = _only_in_graphql_start(lines=lines, where=conventions.name)
    header, rows = _table_from(lines=lines, start=start + 1, where=conventions.name)
    missing = [column for column in (COLUMN_CAPABILITY, COLUMN_GRAPHQL) if column not in header]
    if missing:
        raise ValueError(f"{conventions.name}: the table under {ONLY_IN_GRAPHQL_HEADING!r} has no column {missing}")
    capability_column, graphql_column = header.index(COLUMN_CAPABILITY), header.index(COLUMN_GRAPHQL)
    read: list[CapabilityRow] = []
    for row in rows:
        capability = row[capability_column]
        where = f"{conventions.name} {capability!r}"
        members = [_row_member(span=span, where=where) for span in CODE_SPAN.findall(row[graphql_column])]
        members.extend(
            RowMember(name=name, pairs={}, names=frozenset()) for name in ROW_ADDED_MEMBERS.get(capability, ())
        )
        read.append(CapabilityRow(capability=capability, members=tuple(members)))
    return tuple(read)


def _passes(*, node: SelectedField, name: str, value: Value) -> bool:
    """Whether ``node`` passes ``name`` as ``value``: as its argument, or as a field of its ``input`` object."""
    if node.arguments.get(name) == value:
        return True
    given = node.arguments.get(ARGUMENT_INPUT)
    return isinstance(given, ObjectValue) and given.fields.get(name) == value


def _member_row_problems(
    *, capability: str, member: RowMember, selected: frozenset[str], nodes: Sequence[SelectedField]
) -> list[str]:
    """What the records of ``capability`` leave of one member: the member itself, or a pair or a name of it."""
    where = json.dumps(capability)
    if member.name not in selected:
        return [f"{where}: no record of the capability selects {json.dumps(member.name)}"]
    problems = [
        f"{where}: no record of the capability passes {json.dumps(name)} as {literal} at {json.dumps(member.name)}"
        for name, literal in member.pairs.items()
        if not any(_passes(node=node, name=name, value=_literal(text=literal, where=where)) for node in nodes)
    ]
    problems.extend(
        f"{where}: no record of the capability selects {json.dumps(name)} directly under {json.dumps(member.name)}"
        for name in sorted(member.names)
        if not any(name in _direct_fields(selected=node) for node in nodes)
    )
    return problems


def member_problems(*, row: CapabilityRow, records: Sequence[GraphQLRecord], schema: ReferenceSchema) -> list[str]:
    """Each member of ``row`` that no record of its capability selects; for a member with pairs, each pair no such
    record passes at that field, as an argument or as a field of its input object; for a member with names, each name
    no such record selects directly under it. Each problem names the row and the member."""
    documents = [read_document(document=record.document) for record in records if record.capability == row.capability]
    walks = [_walked(document=document, schema=schema) for document in documents if not document.problems]
    selected = frozenset(member for walk in walks for member in walk.members)
    problems: list[str] = []
    for member in row.members:
        nodes = [node for walk in walks for node in walk.fields.get(member.name, ())]
        problems.extend(_member_row_problems(capability=row.capability, member=member, selected=selected, nodes=nodes))
    return problems


# ---------------------------------------------------------------------------------------------------------------------
# Altered copies of named records (Correctness Properties, Q's method)
# ---------------------------------------------------------------------------------------------------------------------


def _record(*, records: Sequence[Any], operation_id: str) -> Any:
    """The one record of ``records`` with ``operation_id``; the calling test fails on this assertion otherwise."""
    found = [record for record in records if record.operation_id == operation_id]
    assert len(found) == 1, (
        f"{GRAPHQL_ONLY}.{ATTRIBUTE_OPERATIONS} holds {len(found)} records with the ID {operation_id!r}, expected one"
    )
    return found[0]


@dataclass(frozen=True)
class RecordChange:
    """One way to alter a named record: the ``case``, the ``operation_id`` of the record altered, and the text one
    problem of the altered copy must hold, ``named``, which is what differs."""

    case: str
    operation_id: str
    named: str

    def altered(self, *, record: Any, records: Sequence[Any]) -> Any:
        raise NotImplementedError

    def problems(self, *, record: Any, altered: Any, records: Sequence[Any], schema: ReferenceSchema) -> list[str]:
        """What the method names in the altered copy: ``document_problems``."""
        return document_problems(record=altered, schema=schema)


@dataclass(frozen=True)
class RecordTextChange(RecordChange):
    """The first match of ``pattern`` in the record's document replaced by ``replacement``."""

    pattern: str
    replacement: str

    def altered(self, *, record: Any, records: Sequence[Any]) -> Any:
        return replace(
            record, document=re.sub(pattern=self.pattern, repl=self.replacement, string=record.document, count=1)
        )


@dataclass(frozen=True)
class RecordConnectionChange(RecordChange):
    """The record with another ``connection``."""

    connection: tuple[str, ...]

    def altered(self, *, record: Any, records: Sequence[Any]) -> Any:
        return replace(record, connection=self.connection)


@dataclass(frozen=True)
class RecordDocumentSwap(RecordChange):
    """The record with the document of the record ``document_of``."""

    document_of: str

    def altered(self, *, record: Any, records: Sequence[Any]) -> Any:
        return replace(record, document=_record(records=records, operation_id=self.document_of).document)


@dataclass(frozen=True)
class RecordMemberChange(RecordTextChange):
    """A text change ``member_problems`` names: the row of the record's capability held to every record, the altered
    copy in place of the record."""

    def problems(self, *, record: Any, altered: Any, records: Sequence[Any], schema: ReferenceSchema) -> list[str]:
        rows = [row for row in row_members(conventions=CONVENTIONS) if row.capability == altered.capability]
        assert len(rows) == 1, f"{len(rows)} Only in GraphQL rows have the capability {altered.capability!r}"
        others = [item for item in records if item.operation_id != record.operation_id]
        return member_problems(row=rows[0], records=[*others, altered], schema=schema)


RECORD_CHANGES = (
    RecordTextChange(
        case="a_field_the_type_lacks",
        operation_id=WORK_ITEM,
        named='"iidd"',
        pattern=r"\biid\b",
        replacement="iidd",
    ),
    RecordTextChange(
        case="since_in_place_of_after",
        operation_id=PROJECT_WORK_ITEMS_RECORD,
        named='"since"',
        pattern=r"(?<![$\w])after(?=\s*:)",
        replacement="since",
    ),
    RecordTextChange(
        case="a_variable_of_another_type",
        operation_id=PROJECT_BRANCH_RULES,
        named='"String!"',
        pattern=r"\$fullPath\s*:\s*ID!",
        replacement="$fullPath: String!",
    ),
    RecordTextChange(
        case="another_input_type",
        operation_id=WORK_ITEM_UPDATE,
        named='"WorkItemDeleteInput!"',
        pattern=r"\$input\s*:\s*WorkItemUpdateInput!",
        replacement="$input: WorkItemDeleteInput!",
    ),
    RecordTextChange(
        case="an_unused_variable",
        operation_id=QUERY_VULNERABILITY,
        named='"$extra"',
        pattern=r"\(",
        replacement="($extra: String, ",
    ),
    RecordTextChange(
        case="an_integer_for_a_boolean",
        operation_id=PIPELINE_CREATE,
        named="the integer 1",
        pattern=r"\basync\s*:\s*true\b",
        replacement="async: 1",
    ),
    RecordTextChange(
        case="a_field_the_input_type_lacks",
        operation_id=DESIGN_UPLOAD,
        named='"projectPaht"',
        pattern=r"(?<![$\w])projectPath(?=\s*:)",
        replacement="projectPaht",
    ),
    RecordTextChange(
        case="a_fragment_on_a_type_that_is_no_widget",
        operation_id=WORK_ITEM_WIDGETS,
        named='"WorkItemType"',
        pattern=r"\bwidgets\s*\{",
        replacement="widgets { ... on WorkItemType { id } ",
    ),
    RecordConnectionChange(
        case="a_connection_short_of_the_path",
        operation_id=PROJECT_WORK_ITEMS_RECORD,
        named='["project"]',
        connection=("project",),
    ),
    RecordTextChange(
        case="errors_left_out",
        operation_id=BRANCH_RULE_DELETE,
        named=json.dumps(FIELD_ERRORS),
        pattern=r"\s*\berrors\b",
        replacement="",
    ),
    RecordDocumentSwap(
        case="the_creating_document_in_the_updating_record",
        operation_id=WORK_ITEM_UPDATE,
        named=json.dumps(WORK_ITEM_CREATE),
        document_of=WORK_ITEM_CREATE,
    ),
    RecordMemberChange(
        case="async_false_for_the_row_s_async_true",
        operation_id=PIPELINE_CREATE,
        named='"async"',
        pattern=r"\basync\s*:\s*true\b",
        replacement="async: false",
    ),
)

# row_members' examples: row 6's members and row 8's.
ROW_MEMBER_EXAMPLES = {
    ASYNC_PIPELINE_CAPABILITY: (
        RowMember(name="pipelineCreate", pairs={"async": KEYWORD_TRUE}, names=frozenset()),
        RowMember(name="Project.ciPipelineCreationRequest", pairs={}, names=frozenset()),
    ),
    QUERY_COST_CAPABILITY: (RowMember(name="queryComplexity", pairs={}, names=frozenset({"score", "limit"})),),
}


# ---------------------------------------------------------------------------------------------------------------------
# Loading the package and the reference
# ---------------------------------------------------------------------------------------------------------------------


def _refuse_connection(self: socket.socket, address: object) -> None:
    pytest.fail(reason=f"a contract test opened a connection to {address!r}; it reads files only")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs opens a socket connection."""
    monkeypatch.setattr(target=socket.socket, name="connect", value=_refuse_connection)
    monkeypatch.setattr(target=socket.socket, name="connect_ex", value=_refuse_connection)


@pytest.fixture
def scripts_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The product scripts directory first on ``sys.path``, so ``gitlab_api`` imports as the entry script imports it."""
    monkeypatch.syspath_prepend(path=str(SCRIPTS_DIR))


def _import_package_module(*, name: str) -> ModuleType:
    """``gitlab_api.<name>`` from the product scripts directory; while its file is not written, the calling test fails
    on this assertion, and a ``gitlab_api`` imported from any other directory fails it too."""
    path = PACKAGE_DIR / f"{name}{PYTHON_SUFFIX}"
    assert path.is_file(), f"{PACKAGE}/{name}{PYTHON_SUFFIX} is not written: {path} does not exist"
    module = importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")
    loaded_from = Path(str(module.__file__)).resolve()
    assert loaded_from == path.resolve(), f"{module.__name__} was imported from {loaded_from}, not from {path}"
    return module


def _records() -> list[Any]:
    """Every record of ``graphql_only.OPERATIONS``, each a registry ``GraphQLOperation``."""
    record_type = getattr(_import_package_module(name=REGISTRY), GRAPHQL_OPERATION)
    operations = list(getattr(_import_package_module(name=GRAPHQL_ONLY), ATTRIBUTE_OPERATIONS))
    foreign = [repr(item) for item in operations if not isinstance(item, record_type)]
    assert not foreign, f"{GRAPHQL_ONLY}.{ATTRIBUTE_OPERATIONS} holds what is no {GRAPHQL_OPERATION}: {foreign}"
    return operations


@functools.lru_cache(maxsize=None)
def _schema() -> ReferenceSchema:
    """The reference read once for the module's tests."""
    return reference_schema(graphql_dir=GRAPHQL_DIR)


def _map_bullet(*, path: Path, start: str) -> str:
    """The list bullet of ``path`` whose first line starts with ``start``: that line and each line after it that is
    indented, up to the next bullet, each stripped of its indentation and joined with one space, so a wrapped phrase
    reads as one; the calling test fails on this assertion when no line, or more than one, starts the bullet."""
    lines = path.read_text(encoding=TEXT_ENCODING).splitlines()
    starts = [number for number, line in enumerate(lines) if line.startswith(start)]
    assert len(starts) == 1, f"{path.name}: {len(starts)} lines start with {start!r}, expected one"
    bullet = [lines[starts[0]]]
    for line in lines[starts[0] + 1 :]:
        if not line.startswith(BULLET_CONTINUATION):
            break
        bullet.append(line.strip())
    return BULLET_LINE_SEPARATOR.join(bullet)


# ---------------------------------------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.usefixtures("scripts_on_path")
def test_the_reference_is_read_as_written() -> None:
    """Q's method: ``reference_schema`` reads ``Query.workItem``'s argument, ``Project.workItems``' type and arguments,
    ``Mutation.designManagementUpload``'s ``input`` and its input type's ``files``, the payload's fields,
    ``WorkItemWidgetAssignees``' interface and ``Vulnerability.dependencies``' ``licenses`` as the reference writes
    them; ``row_members`` reads rows 6 and 8; ``selected_members`` of ``graphql#WorkItem.widgets`` holds the type, the
    field and a fragment's field it selects."""
    schema = _schema()
    work_item = schema.types[QUERY_TYPE][WORK_ITEM_QUERY]
    assert dict(work_item.arguments) == WORK_ITEM_QUERY_ARGUMENTS, f"Query.workItem is read as {work_item}"
    work_items = schema.types[PROJECT_TYPE][PROJECT_WORK_ITEMS]
    assert work_items.type == WORK_ITEM_CONNECTION, f"Project.workItems is read as {work_items}"
    assert PROJECT_WORK_ITEMS_ARGUMENTS <= set(work_items.arguments), f"Project.workItems is read as {work_items}"
    upload = schema.types[MUTATION_TYPE][DESIGN_UPLOAD_MUTATION]
    assert dict(upload.arguments) == DESIGN_UPLOAD_ARGUMENTS, f"Mutation.designManagementUpload is read as {upload}"
    files = schema.types.get(DESIGN_UPLOAD_INPUT, {}).get(DESIGN_UPLOAD_FILES)
    assert files is not None and files.type == DESIGN_UPLOAD_FILES_TYPE, f"{DESIGN_UPLOAD_INPUT}.files is {files}"
    payload = set(schema.types.get(DESIGN_UPLOAD_PAYLOAD, {}))
    assert DESIGN_UPLOAD_PAYLOAD_FIELDS <= payload, f"{DESIGN_UPLOAD_PAYLOAD} is read with {sorted(payload)}"
    implemented = schema.implements.get(ASSIGNEES_WIDGET, frozenset())
    assert WIDGET_INTERFACE in implemented, f"{ASSIGNEES_WIDGET} is read implementing {sorted(implemented)}"
    dependencies = schema.types[VULNERABILITY_TYPE][VULNERABILITY_DEPENDENCIES]
    licenses = dependencies.arguments.get(DEPENDENCIES_LICENSES)
    assert licenses == DEPENDENCIES_LICENSES_TYPE, f"Vulnerability.dependencies is read as {dependencies}"

    rows = {row.capability: row.members for row in row_members(conventions=CONVENTIONS)}
    read = {capability: rows.get(capability) for capability in ROW_MEMBER_EXAMPLES}
    assert read == ROW_MEMBER_EXAMPLES, f"row_members reads {read}, expected {ROW_MEMBER_EXAMPLES}"

    widgets = _record(records=_records(), operation_id=WORK_ITEM_WIDGETS)
    members = selected_members(record=widgets, schema=schema)
    absent = sorted(WORK_ITEM_WIDGETS_MEMBERS - members)
    assert not absent, f"selected_members of {WORK_ITEM_WIDGETS} lacks {absent}; it is {sorted(members)}"


@pytest.mark.usefixtures("scripts_on_path")
def test_every_record_matches_the_reference() -> None:
    """AC-1.1, AC-4.1: ``document_problems`` is empty for every record of ``graphql_only.OPERATIONS``, so each
    mutation record's ID is ``graphql#`` and the mutation it runs; the test fails when it finds no record."""
    records = _records()
    assert records, f"{GRAPHQL_ONLY}.{ATTRIBUTE_OPERATIONS} holds no record to hold to the reference"
    schema = _schema()

    problems = [problem for record in records for problem in document_problems(record=record, schema=schema)]

    assert not problems, "records that depart from the GraphQL reference:\n" + "\n".join(problems)


@pytest.mark.usefixtures("scripts_on_path")
@pytest.mark.parametrize(
    argnames="change", argvalues=[pytest.param(change, id=change.case) for change in RECORD_CHANGES]
)
def test_the_method_rejects_a_document_that_differs(change: RecordChange) -> None:
    """Q's method: a copy of a named record made with ``dataclasses.replace`` that differs from the reference, or from
    its row, gives at least one problem, and one of them names what differs."""
    records = _records()
    record = _record(records=records, operation_id=change.operation_id)
    altered = change.altered(record=record, records=records)
    assert altered != record, f"the change {change.case} leaves {change.operation_id} as it is: {record}"

    problems = change.problems(record=record, altered=altered, records=records, schema=_schema())

    assert problems, f"the method finds nothing in {altered}"
    assert any(change.named in problem for problem in problems), (
        f"no problem names {change.named}, which differs in {change.case}:\n" + "\n".join(problems)
    )


@pytest.mark.usefixtures("scripts_on_path")
def test_every_capability_has_a_record() -> None:
    """AC-1.2: every first cell of the "Only in GraphQL" table is the ``capability`` of a record, and
    ``graphql_only.PENDING_CAPABILITIES`` is empty."""
    capabilities = first_cells(conventions=CONVENTIONS)
    assert capabilities, f"{CONVENTIONS.name}: the table under {ONLY_IN_GRAPHQL_HEADING!r} has no row"
    served = {record.capability for record in _records()}

    missing = [capability for capability in capabilities if capability not in served]

    assert not missing, "capabilities no record serves:\n" + "\n".join(missing)
    pending = getattr(_import_package_module(name=GRAPHQL_ONLY), ATTRIBUTE_PENDING_CAPABILITIES)
    assert pending == frozenset(), f"{GRAPHQL_ONLY}.{ATTRIBUTE_PENDING_CAPABILITIES} still holds {sorted(pending)}"


@pytest.mark.usefixtures("scripts_on_path")
def test_every_member_a_row_names_is_selected() -> None:
    """AC-1.3: for each "Only in GraphQL" row, ``member_problems`` is empty: the records of its capability select
    every member it names, with the argument or selection its code span gives; a failure names the row and the member.
    The test fails when the capabilities ``row_members`` gives differ from the table's first cells, or when a row has
    no member."""
    rows = row_members(conventions=CONVENTIONS)
    capabilities = [row.capability for row in rows]
    expected = first_cells(conventions=CONVENTIONS)
    assert capabilities == expected, f"row_members gives the capabilities {capabilities}, the table {expected}"
    memberless = [row.capability for row in rows if not row.members]
    assert not memberless, "rows row_members reads no member of:\n" + "\n".join(memberless)
    records = _records()
    schema = _schema()

    problems = [problem for row in rows for problem in member_problems(row=row, records=records, schema=schema)]

    assert not problems, "members a row names that no record of its capability selects:\n" + "\n".join(problems)


def test_the_map_names_the_graphql_call() -> None:
    """AC-5.2: the ``src/payload/scripts/gitlab_api/`` bullet of the project map, ``docs/forLLMConsumption.md``, names
    the GraphQL call: it holds ``call graphql#``, ``--file NAME=PATH`` and ``Upload`` (D8)."""
    bullet = _map_bullet(path=LLM_MAP, start=MAP_BULLET_START)

    missing = [text for text in MAP_GRAPHQL_CALL if text not in bullet]

    assert not missing, (
        f"the {MAP_BULLET_START!r} bullet of {LLM_MAP.relative_to(ROOT).as_posix()} does not hold {missing}: "
        f"it names no GraphQL call; the bullet is {bullet!r}"
    )
