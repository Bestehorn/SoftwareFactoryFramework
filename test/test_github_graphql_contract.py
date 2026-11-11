"""Contract test of the GitHub wrapper's GraphQL records against the GraphQL reference (issue #30, design D6).

Every ``GraphQLOperation`` of ``github_api.graphql_only`` is held to ``docs/api-reference/github/graphql/``.
``reference_schema`` reads each type's fields, with their types and arguments, as the reference writes them;
``read_document`` reads the GraphQL subset the records use; ``document_problems`` walks a record's selection from its
root type and names each way the record departs from the reference; ``selected_members`` names the members a record's
walk visits, and ``row_members`` the members each "Only in GraphQL" row of ``conventions.md`` names. The tests prove
the method on the reference and on altered copies of named records, then hold every record to it (AC-1.1, AC-1.2,
AC-1.3, AC-3.1). ``test_the_map_names_the_graphql_call`` holds the project map to naming the GraphQL call (D7, AC-4.2).

The reference exists only in this repository, so this module lives in ``test/`` (cross-wrapper decision X1). It loads
the product package ``github_api`` from ``src/payload/scripts/`` as ``test_github_wrapper_coverage.py`` does: each
test imports the package itself, so while a module is not written the test fails on the assertion that names it.
Standard library and pytest only; no test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_graphql_contract.py``.
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
PACKAGE = "github_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
REGISTRY = "registry"
GRAPHQL_ONLY = "graphql_only"
PYTHON_SUFFIX = ".py"
MODULE_SEPARATOR = "."
ATTRIBUTE_OPERATIONS = "OPERATIONS"
ATTRIBUTE_PENDING_CAPABILITIES = "PENDING_CAPABILITIES"
GRAPHQL_OPERATION = "GraphQLOperation"

# The reference files D6 reads.
GRAPHQL_DIR = ROOT / "docs" / "api-reference" / "github" / "graphql"
QUERIES_FILE = "queries.md"
MUTATIONS_FILE = "mutations.md"
TYPE_FILES = ("objects-a-p.md", "objects-p-w.md", "interfaces.md")
CONVENTIONS = GRAPHQL_DIR / "conventions.md"

# The project map, and how it names a GraphQL call (D7, AC-4.2).
LLM_MAP = ROOT / "docs" / "forLLMConsumption.md"
CALL_SUBCOMMAND = "call"

# How the reference writes a section, a signature line, a table and an argument.
GROUP_NAME = "name"
GROUP_TYPE = "type"
GROUP_ARGUMENTS = "arguments"
GROUP_RETURNS = "returns"
SECTION_PREFIX = "## "
SECTION_HEADING = re.compile(rf"## `(?P<{GROUP_NAME}>[_A-Za-z][_0-9A-Za-z]*)`")
SIGNATURE_LINE = re.compile(
    rf"`(?P<{GROUP_NAME}>[_A-Za-z][_0-9A-Za-z]*)(?:\((?P<{GROUP_ARGUMENTS}>[^()]*)\))?` → (?P<{GROUP_RETURNS}>.+)"
)
SIGNATURE_ARGUMENT_SEPARATOR = ", "
ARGUMENT_SPAN = re.compile(rf"(?P<{GROUP_NAME}>[_A-Za-z][_0-9A-Za-z]*): (?P<{GROUP_TYPE}>[\[\]!_0-9A-Za-z]+)(?: = .+)?")
CODE_SPAN = re.compile(r"`([^`]+)`")
TABLE_ROW_PREFIX = "|"
CELL_SEPARATOR = "|"
SEPARATOR_CELL = re.compile(r":?-+:?")
COLUMN_FIELD = "Field"
COLUMN_PAYLOAD_FIELD = "Payload field"
COLUMN_TYPE = "Type"
COLUMN_ARGUMENTS = "Arguments"
COLUMN_NOTES = "Notes"
FIELD_TABLE_HEADER = (COLUMN_FIELD, COLUMN_TYPE, COLUMN_ARGUMENTS, COLUMN_NOTES)
PAYLOAD_TABLE_HEADER = (COLUMN_PAYLOAD_FIELD, COLUMN_TYPE, COLUMN_NOTES)
TYPE_WRAPPERS = str.maketrans("", "", "[]!")
NON_NULL = "!"

# The "Only in GraphQL" table of conventions.md: its marker line, the column of members, what is no member.
ONLY_IN_GRAPHQL_MARKER = "**Only in GraphQL**"
GRAPHQL_COLUMN = "GraphQL"
ARGUMENTS_START = "("
NOT_A_MEMBER = "..."
MEMBER_SEPARATOR = "."

# The GraphQL the records use (D1, D2): the root types, the paging fields, the mutation argument, the ID prefix.
QUERY_TYPE = "Query"
MUTATION_TYPE = "Mutation"
OPERATION_QUERY = "query"
OPERATION_MUTATION = "mutation"
ROOT_TYPES = {OPERATION_QUERY: QUERY_TYPE, OPERATION_MUTATION: MUTATION_TYPE}
TYPENAME_FIELD = "__typename"
FIELD_NODES = "nodes"
FIELD_PAGE_INFO = "pageInfo"
PAGE_FIELDS = frozenset({FIELD_NODES, FIELD_PAGE_INFO})
PAGE_INFO_FIELDS = frozenset({"hasNextPage", "endCursor"})
ARGUMENT_AFTER = "after"
ARGUMENT_INPUT = "input"
TYPE_STRING = "String"
VARIABLE_SIGIL = "$"
GRAPHQL_ID_PREFIX = "graphql/"

# The tokens of a document: white space and commas are ignored ("Insignificant Commas"); anything else is "other".
TOKEN_IGNORED = "ignored"
TOKEN_PUNCTUATOR = "punctuator"
TOKEN_NAME = "name"
TOKEN_INTEGER = "integer"
TOKEN_OTHER = "other"
TOKEN_END = "end"
TOKEN_PATTERN = re.compile(
    rf"(?P<{TOKEN_IGNORED}>[\s,]+)"
    rf"|(?P<{TOKEN_PUNCTUATOR}>[{{}}():!$\[\]])"
    rf"|(?P<{TOKEN_NAME}>[_A-Za-z][_0-9A-Za-z]*)"
    rf"|(?P<{TOKEN_INTEGER}>-?(?:0|[1-9][0-9]*)(?![._0-9A-Za-z]))"
    rf'|(?P<{TOKEN_OTHER}>\.\.\.|"[^"]*"|\S)'
)
OPEN_ARGUMENTS = "("
CLOSE_ARGUMENTS = ")"
OPEN_SELECTION = "{"
CLOSE_SELECTION = "}"
OPEN_LIST = "["
CLOSE_LIST = "]"
DEFINES = ":"

# test_the_reference_is_read_as_written's examples (design Correctness Properties, "Q's method").
REPOSITORY_TYPE = "Repository"
QUERY_REPOSITORY = "repository"
QUERY_REPOSITORY_ARGUMENTS = {"followRenames": "Boolean", "name": "String!", "owner": "String!"}
REPOSITORY_MERGE_QUEUE = "mergeQueue"
REPOSITORY_MERGE_QUEUE_ARGUMENTS = {"branch": "String"}
MERGE_QUEUE_TYPE = "MergeQueue"
MERGE_QUEUE_ENTRIES = "entries"
MERGE_QUEUE_ENTRIES_TYPE = "MergeQueueEntryConnection"
MUTATION_PIN_ISSUE = "pinIssue"
PIN_ISSUE_ARGUMENTS = {ARGUMENT_INPUT: "PinIssueInput!"}
PIN_ISSUE_PAYLOAD = "PinIssuePayload"
PIN_ISSUE_PAYLOAD_FIELDS = frozenset({"clientMutationId", "issue"})
ROW_MEMBER_EXAMPLES = {
    "Read a merge queue, remove an entry": frozenset(
        {"Repository.mergeQueue", "MergeQueue.entries", "dequeuePullRequest"}
    ),
    "Repository discussions": frozenset(
        {"Repository.discussions", "createDiscussion", "addDiscussionComment", "markDiscussionCommentAsAnswer"}
    ),
    "Branch protection with wildcard patterns": frozenset({"createBranchProtectionRule"}),
}
# (record ID, a member its walk visits, a member it does not visit)
SELECTED_MEMBER_EXAMPLES = (
    ("graphql/pinIssue", "pinIssue", "unpinIssue"),
    ("graphql/Repository.discussions", "Repository.discussions", "Repository.discussionCategories"),
)

# The named records test_the_method_rejects_a_document_that_differs alters.
MARK_READY = "graphql/markPullRequestReadyForReview"
DISCUSSIONS = "graphql/Repository.discussions"
REVIEW_THREADS = "graphql/PullRequest.reviewThreads"
PIN_ISSUE = "graphql/pinIssue"
MERGE_QUEUE = "graphql/Repository.mergeQueue"
ENABLE_AUTO_MERGE = "graphql/enablePullRequestAutoMerge"
DISABLE_AUTO_MERGE = "graphql/disablePullRequestAutoMerge"


# ---------------------------------------------------------------------------------------------------------------------
# The reference's types (D6: reference_schema)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldDefinition:
    """One field of a reference type: its ``type`` as the reference writes it (``[String!]``, ``PinIssuePayload``) and
    its ``arguments``, each name to its type as written."""

    type: str
    arguments: Mapping[str, str]


Schema = Mapping[str, Mapping[str, FieldDefinition]]


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
    for line in path.read_text(encoding="utf-8").splitlines():
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


def _code_span(*, cell: str, where: str) -> str:
    """The text of the first code span of a cell: a name cell's name, or a Type cell's link text."""
    match = CODE_SPAN.search(cell)
    if match is None:
        raise ValueError(f"{where}: the cell {cell!r} holds no code span")
    return match.group(1)


def _arguments_of(*, spans: Sequence[str], where: str) -> dict[str, str]:
    """Each ``name: Type`` span (any default after ``=``) as its name to its type; any other span, or a name given
    twice, raises ``ValueError``."""
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
    """The fields of a field or payload table: the name cell's code span, the Type cell's link text, and the
    Arguments cell's spans (a payload table has none)."""
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
    """The field a ``queries.md`` or ``mutations.md`` section defines, from its one signature line
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


def _root_fields(*, path: Path) -> dict[str, FieldDefinition]:
    """The fields of a root type: one per section of ``queries.md`` or ``mutations.md``, from its signature line."""
    fields: dict[str, FieldDefinition] = {}
    for name, lines in _sections(path=path):
        if name in fields:
            raise ValueError(f"{path.name}: two sections define {name!r}")
        fields[name] = _signature(name=name, lines=lines, where=f"{path.name} {name}")
    return fields


def _payload_types(*, path: Path) -> dict[str, dict[str, FieldDefinition]]:
    """Each mutation's payload type, named by its signature line, with the fields of its payload table."""
    payloads: dict[str, dict[str, FieldDefinition]] = {}
    for name, lines in _sections(path=path):
        where = f"{path.name} {name}"
        rows = _section_rows(lines=lines, header=PAYLOAD_TABLE_HEADER, where=where)
        if rows is None:
            raise ValueError(f"{where}: the section has no {list(PAYLOAD_TABLE_HEADER)} table")
        payload = _named_type(type_text=_signature(name=name, lines=lines, where=where).type)
        _define(
            schema=payloads,
            name=payload,
            fields=_field_definitions(rows=rows, name_column=COLUMN_PAYLOAD_FIELD, where=where),
        )
    return payloads


def reference_schema(*, graphql_dir: Path) -> dict[str, dict[str, FieldDefinition]]:
    """Each type's fields, with their types and arguments, as the reference under ``graphql_dir`` writes them (D6):
    ``Query`` from the signature lines of ``queries.md``; ``Mutation`` from those of ``mutations.md``, and each
    payload type from its ``| Payload field | Type | Notes |`` table; each type section of ``objects-a-p.md``,
    ``objects-p-w.md`` and ``interfaces.md`` from its ``| Field | Type | Arguments | Notes |`` rows. A name no table
    defines is a leaf (a scalar or an enum)."""
    schema: dict[str, dict[str, FieldDefinition]] = {}
    _define(schema=schema, name=QUERY_TYPE, fields=_root_fields(path=graphql_dir / QUERIES_FILE))
    _define(schema=schema, name=MUTATION_TYPE, fields=_root_fields(path=graphql_dir / MUTATIONS_FILE))
    for name, fields in _payload_types(path=graphql_dir / MUTATIONS_FILE).items():
        _define(schema=schema, name=name, fields=fields)
    for file_name in TYPE_FILES:
        path = graphql_dir / file_name
        for name, lines in _sections(path=path):
            where = f"{path.name} {name}"
            rows = _section_rows(lines=lines, header=FIELD_TABLE_HEADER, where=where)
            if rows is not None:
                _define(
                    schema=schema,
                    name=name,
                    fields=_field_definitions(rows=rows, name_column=COLUMN_FIELD, where=where),
                )
    return schema


# ---------------------------------------------------------------------------------------------------------------------
# A record's document (D6: read_document)
# ---------------------------------------------------------------------------------------------------------------------


class DocumentSyntaxError(ValueError):
    """A GraphQL document outside the subset ``read_document`` reads."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True)
class Variable:
    """An argument value that is the variable ``$name``."""

    name: str


ArgumentValue = Union[Variable, int]


@dataclass(frozen=True)
class SelectedField:
    """One field of a selection set: its ``name``, its ``arguments`` (name to value) and its ``selections`` (``()``
    for none)."""

    name: str
    arguments: Mapping[str, ArgumentValue]
    selections: tuple[SelectedField, ...]


@dataclass(frozen=True)
class Document:
    """A read document: its ``operation`` (``query`` or ``mutation``), its ``variables`` (name to type as written),
    its root ``selections``, and the ``problems`` the reader names; a document with a problem holds nothing else."""

    operation: str
    variables: Mapping[str, str]
    selections: tuple[SelectedField, ...]
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


class _DocumentReader:
    """Reads one ``query`` or ``mutation`` with ``$name: Type`` definitions, fields with arguments whose values are a
    ``$variable`` or an integer, and nested selections; any other token raises ``DocumentSyntaxError``."""

    def __init__(self, *, document: str) -> None:
        self._tokens = _tokens(document=document)
        self._position = 0

    def read(self) -> Document:
        operation = self._expect(kind=TOKEN_NAME, expected='"query" or "mutation"').text
        if operation not in ROOT_TYPES:
            raise DocumentSyntaxError(message=f"the document is a {json.dumps(operation)}, not a query or a mutation")
        if self._peek().kind == TOKEN_NAME:
            self._position += 1
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

    def _selection_set(self) -> tuple[SelectedField, ...]:
        self._punctuator(text=OPEN_SELECTION)
        selections: list[SelectedField] = []
        while not self._at(text=CLOSE_SELECTION) or not selections:
            selections.append(self._field())
        self._punctuator(text=CLOSE_SELECTION)
        return tuple(selections)

    def _field(self) -> SelectedField:
        name = self._expect(kind=TOKEN_NAME, expected="a field name").text
        arguments = self._arguments() if self._at(text=OPEN_ARGUMENTS) else {}
        selections = self._selection_set() if self._at(text=OPEN_SELECTION) else ()
        return SelectedField(name=name, arguments=arguments, selections=selections)

    def _arguments(self) -> dict[str, ArgumentValue]:
        self._punctuator(text=OPEN_ARGUMENTS)
        arguments: dict[str, ArgumentValue] = {}
        while not self._at(text=CLOSE_ARGUMENTS) or not arguments:
            name = self._expect(kind=TOKEN_NAME, expected="an argument name").text
            self._punctuator(text=DEFINES)
            if name in arguments:
                raise DocumentSyntaxError(message=f"the argument {json.dumps(name)} is given twice")
            arguments[name] = self._value()
        self._punctuator(text=CLOSE_ARGUMENTS)
        return arguments

    def _value(self) -> ArgumentValue:
        if self._at(text=VARIABLE_SIGIL):
            self._punctuator(text=VARIABLE_SIGIL)
            return Variable(name=self._expect(kind=TOKEN_NAME, expected="a variable name").text)
        return int(self._expect(kind=TOKEN_INTEGER, expected="a $variable or an integer").text)


def read_document(*, document: str) -> Document:
    """``document`` read as the subset the records use (D6): one ``query`` or ``mutation`` with ``$name: Type``
    definitions; fields with arguments whose values are a ``$variable`` or an integer; nested selections. Commas count
    as white space. Any other token is the document's one problem."""
    try:
        return _DocumentReader(document=document).read()
    except DocumentSyntaxError as error:
        return Document(operation="", variables={}, selections=(), problems=(str(error),))


# ---------------------------------------------------------------------------------------------------------------------
# A record against the reference (D6: document_problems, selected_members)
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


def _variable(*, name: str) -> str:
    return json.dumps(f"{VARIABLE_SIGIL}{name}")


@dataclass
class _Walk:
    """One walk of a read document's selection through the reference, from its root type: the ``problems`` it names
    and the ``members`` it visits (``<Type>.<field>``, and a root mutation field's bare name)."""

    schema: Schema
    variables: Mapping[str, str]
    problems: list[str] = field(default_factory=list)
    members: set[str] = field(default_factory=set)

    def selections(self, *, parent: str, selections: Sequence[SelectedField]) -> None:
        for selected in selections:
            self._visit(parent=parent, selected=selected)

    def _visit(self, *, parent: str, selected: SelectedField) -> None:
        member = f"{parent}{MEMBER_SEPARATOR}{selected.name}"
        typename = selected.name == TYPENAME_FIELD
        definition = TYPENAME_DEFINITION if typename else self.schema[parent].get(selected.name)
        if definition is None:
            self.problems.append(f"the type {json.dumps(parent)} has no field {json.dumps(selected.name)}")
            return
        if not typename:
            self.members.add(member)
        if parent == MUTATION_TYPE:
            self.members.add(selected.name)
        self._arguments(member=member, definition=definition, arguments=selected.arguments)
        self._selection(member=member, definition=definition, selected=selected)

    def _arguments(self, *, member: str, definition: FieldDefinition, arguments: Mapping[str, ArgumentValue]) -> None:
        for name, value in arguments.items():
            expected = definition.arguments.get(name)
            if expected is None:
                self.problems.append(f"{json.dumps(member)} has no argument {json.dumps(name)}")
            elif isinstance(value, Variable):
                self._variable_type(member=member, argument=name, expected=expected, variable=value.name)

    def _variable_type(self, *, member: str, argument: str, expected: str, variable: str) -> None:
        """A declared variable's type must be the argument's type, or that type with ``!`` added
        (``AreTypesCompatible``, GraphQL spec §5.8.5)."""
        declared = self.variables.get(variable)
        if declared is not None and declared not in (expected, f"{expected}{NON_NULL}"):
            self.problems.append(
                f"the variable {_variable(name=variable)} is declared {json.dumps(declared)}, but the argument "
                f"{json.dumps(argument)} of {json.dumps(member)} is {json.dumps(expected)}"
            )

    def _selection(self, *, member: str, definition: FieldDefinition, selected: SelectedField) -> None:
        named = _named_type(type_text=definition.type)
        if named not in self.schema:
            if selected.selections:
                self.problems.append(
                    f"{json.dumps(member)} is of the leaf type {json.dumps(named)} and has a selection"
                )
            return
        if not selected.selections:
            self.problems.append(f"{json.dumps(member)} is of the type {json.dumps(named)} and selects no field")
            return
        self.selections(parent=named, selections=selected.selections)


def _walked(*, document: Document, schema: Schema) -> _Walk:
    walk = _Walk(schema=schema, variables=document.variables)
    walk.selections(parent=ROOT_TYPES[document.operation], selections=document.selections)
    return walk


def _used_variables(*, selections: Sequence[SelectedField]) -> set[str]:
    """The name of every ``$variable`` an argument anywhere in ``selections`` holds."""
    used: set[str] = set()
    for selected in selections:
        used.update(value.name for value in selected.arguments.values() if isinstance(value, Variable))
        used |= _used_variables(selections=selected.selections)
    return used


def _variable_problems(*, document: Document) -> list[str]:
    """A ``$variable`` argument that is not declared, and a declared variable that is never used."""
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


def _selected_path(*, selections: Sequence[SelectedField]) -> tuple[tuple[str, ...], Optional[SelectedField]]:
    """The path of selected fields from the root: each the one field of its selection set that has a selection and is
    no ``nodes`` or ``pageInfo``; and the path's last field."""
    path: list[str] = []
    last: Optional[SelectedField] = None
    current = selections
    while len(current) == 1 and current[0].selections and current[0].name not in PAGE_FIELDS:
        last = current[0]
        path.append(last.name)
        current = last.selections
    return tuple(path), last


def _selects_a_page(*, selected: SelectedField) -> bool:
    """Whether ``selected`` selects both ``nodes`` and ``pageInfo { hasNextPage endCursor }``."""
    by_name = {child.name: child for child in selected.selections}
    page_info = by_name.get(FIELD_PAGE_INFO)
    if FIELD_NODES not in by_name or page_info is None:
        return False
    return PAGE_INFO_FIELDS <= {child.name for child in page_info.selections}


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
    """For a mutation: more than one root field, an ``input`` argument that is not ``$input``, or an operation ID
    other than ``graphql/`` and the root field's name (D2), so a refused ID is the mutation the document runs."""
    if document.operation != OPERATION_MUTATION:
        return []
    if len(document.selections) != 1:
        names = [selected.name for selected in document.selections]
        return [f"the mutation selects the {len(names)} root fields {json.dumps(names)}, not one"]
    root = document.selections[0]
    problems = []
    if root.arguments.get(ARGUMENT_INPUT) != Variable(name=ARGUMENT_INPUT):
        problems.append(f"the mutation {json.dumps(root.name)} is given no input: $input")
    expected = f"{GRAPHQL_ID_PREFIX}{root.name}"
    if record.operation_id != expected:
        problems.append(
            f"the mutation runs {json.dumps(root.name)}, so its operation ID must be {json.dumps(expected)}, not "
            f"{json.dumps(record.operation_id)}"
        )
    return problems


def document_problems(*, record: GraphQLRecord, schema: Schema) -> list[str]:
    """Every way ``record`` departs from the reference (D6), each prefixed with its operation ID: the reader's
    problem; a field its parent type lacks (``__typename`` aside) or an argument its field lacks; a ``$variable``
    undeclared, unused, or declared with a type its argument does not accept; a leaf with a selection, or an object or
    interface without one; and the connection and mutation rules."""
    document = read_document(document=record.document)
    problems = list(document.problems)
    if not problems:
        problems = [
            *_walked(document=document, schema=schema).problems,
            *_variable_problems(document=document),
            *_connection_problems(record=record, document=document),
            *_mutation_problems(record=record, document=document),
        ]
    return [f"{record.operation_id}: {problem}" for problem in problems]


def selected_members(*, record: GraphQLRecord, schema: Schema) -> frozenset[str]:
    """``<Type>.<field>`` for every field the walk of ``record``'s selection visits, and the bare name of a root
    mutation field; none for a document the reader cannot read."""
    document = read_document(document=record.document)
    if document.problems:
        return frozenset()
    return frozenset(_walked(document=document, schema=schema).members)


# ---------------------------------------------------------------------------------------------------------------------
# The members the "Only in GraphQL" table names (D6: row_members)
# ---------------------------------------------------------------------------------------------------------------------


def row_members(*, conventions: Path) -> dict[str, frozenset[str]]:
    """Each "Only in GraphQL" row's capability (its first cell, verbatim) to the code spans of its GraphQL cell, each
    cut at its first ``(``; a ``...`` is not a member."""
    lines = conventions.read_text(encoding="utf-8").splitlines()
    starts = [number for number, line in enumerate(lines) if line.startswith(ONLY_IN_GRAPHQL_MARKER)]
    if len(starts) != 1:
        raise ValueError(f"{conventions.name}: {len(starts)} lines start with {ONLY_IN_GRAPHQL_MARKER!r}, expected one")
    header, rows = _table_from(lines=lines, start=starts[0] + 1, where=conventions.name)
    if GRAPHQL_COLUMN not in header:
        raise ValueError(
            f"{conventions.name}: the table after {ONLY_IN_GRAPHQL_MARKER!r} has no {GRAPHQL_COLUMN} column"
        )
    column = header.index(GRAPHQL_COLUMN)
    members: dict[str, frozenset[str]] = {}
    for row in rows:
        if row[0] in members:
            raise ValueError(f"{conventions.name}: the capability {row[0]!r} is on two rows")
        spans = (span.split(ARGUMENTS_START, 1)[0] for span in CODE_SPAN.findall(row[column]))
        members[row[0]] = frozenset(span for span in spans if span != NOT_A_MEMBER)
    return members


# ---------------------------------------------------------------------------------------------------------------------
# Altered copies of named records (Correctness Properties, Q's method)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RecordChange:
    """One way to alter a named record: the ``case``, the ``operation_id`` of the record altered, and the text one
    problem of the altered copy must hold, ``named``, which is what differs."""

    case: str
    operation_id: str
    named: str

    def altered(self, *, record: Any, registry: ModuleType) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class RecordTextChange(RecordChange):
    """The first match of ``pattern`` in the record's document replaced by ``replacement``."""

    pattern: str
    replacement: str

    def altered(self, *, record: Any, registry: ModuleType) -> Any:
        return replace(
            record, document=re.sub(pattern=self.pattern, repl=self.replacement, string=record.document, count=1)
        )


@dataclass(frozen=True)
class RecordConnectionChange(RecordChange):
    """The record with another ``connection``."""

    connection: tuple[str, ...]

    def altered(self, *, record: Any, registry: ModuleType) -> Any:
        return replace(record, connection=self.connection)


@dataclass(frozen=True)
class RecordDocumentSwap(RecordChange):
    """The record with the document of the record ``document_of``."""

    document_of: str

    def altered(self, *, record: Any, registry: ModuleType) -> Any:
        return replace(record, document=registry.graphql_lookup(operation_id=self.document_of).document)


RECORD_CHANGES = (
    RecordTextChange(
        case="a_field_the_type_lacks",
        operation_id=MARK_READY,
        named='"isDraftt"',
        pattern=r"\bisDraft\b",
        replacement="isDraftt",
    ),
    RecordTextChange(
        case="since_in_place_of_after",
        operation_id=DISCUSSIONS,
        named='"since"',
        pattern=r"(?<![$\w])after(?=\s*:)",
        replacement="since",
    ),
    RecordTextChange(
        case="a_variable_of_another_type",
        operation_id=REVIEW_THREADS,
        named='"String!"',
        pattern=r"\$number\s*:\s*Int!",
        replacement="$number: String!",
    ),
    RecordTextChange(
        case="another_input_type",
        operation_id=PIN_ISSUE,
        named='"UnpinIssueInput!"',
        pattern=r"\$input\s*:\s*PinIssueInput!",
        replacement="$input: UnpinIssueInput!",
    ),
    RecordTextChange(
        case="an_unused_variable",
        operation_id=PIN_ISSUE,
        named='"$extra"',
        pattern=r"\(",
        replacement="($extra: String, ",
    ),
    RecordConnectionChange(
        case="a_connection_short_of_the_path",
        operation_id=MERGE_QUEUE,
        named='["repository", "mergeQueue"]',
        connection=("repository", "mergeQueue"),
    ),
    RecordDocumentSwap(
        case="the_enabling_document_in_the_disabling_record",
        operation_id=DISABLE_AUTO_MERGE,
        named=json.dumps(ENABLE_AUTO_MERGE),
        document_of=ENABLE_AUTO_MERGE,
    ),
)


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
    """The product scripts directory first on ``sys.path``, so ``github_api`` imports as the entry script imports it."""
    monkeypatch.syspath_prepend(path=str(SCRIPTS_DIR))


def _import_package_module(*, name: str) -> ModuleType:
    """``github_api.<name>`` from the product scripts directory; while its file is not written, the calling test fails
    on this assertion, and a ``github_api`` imported from any other directory fails it too."""
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
def _schema() -> dict[str, dict[str, FieldDefinition]]:
    """The reference read once for the module's tests."""
    return reference_schema(graphql_dir=GRAPHQL_DIR)


# ---------------------------------------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.usefixtures("scripts_on_path")
def test_the_reference_is_read_as_written() -> None:
    """Q's method: ``reference_schema`` reads ``Query.repository``'s arguments, ``Repository.mergeQueue``'s argument
    and type, ``MergeQueue.entries``'s type, ``Mutation.pinIssue``'s ``input`` and ``PinIssuePayload``'s fields as the
    reference writes them; ``row_members`` reads three rows' members; ``selected_members`` of ``graphql/pinIssue`` and
    ``graphql/Repository.discussions`` holds the member each runs and not its sibling's."""
    schema = _schema()
    repository = schema[QUERY_TYPE][QUERY_REPOSITORY]
    assert dict(repository.arguments) == QUERY_REPOSITORY_ARGUMENTS, f"Query.repository is read as {repository}"
    assert repository.type == REPOSITORY_TYPE, f"Query.repository is read as {repository}"
    merge_queue = schema[REPOSITORY_TYPE][REPOSITORY_MERGE_QUEUE]
    assert dict(merge_queue.arguments) == REPOSITORY_MERGE_QUEUE_ARGUMENTS, f"Repository.mergeQueue is {merge_queue}"
    assert merge_queue.type == MERGE_QUEUE_TYPE, f"Repository.mergeQueue is read as {merge_queue}"
    entries = schema[MERGE_QUEUE_TYPE][MERGE_QUEUE_ENTRIES]
    assert entries.type == MERGE_QUEUE_ENTRIES_TYPE, f"MergeQueue.entries is read as {entries}"
    pin_issue = schema[MUTATION_TYPE][MUTATION_PIN_ISSUE]
    assert dict(pin_issue.arguments) == PIN_ISSUE_ARGUMENTS, f"Mutation.pinIssue is read as {pin_issue}"
    assert pin_issue.type == PIN_ISSUE_PAYLOAD, f"Mutation.pinIssue is read as {pin_issue}"
    payload = set(schema.get(PIN_ISSUE_PAYLOAD, {}))
    assert PIN_ISSUE_PAYLOAD_FIELDS <= payload, f"{PIN_ISSUE_PAYLOAD} is read with the fields {sorted(payload)}"

    rows = row_members(conventions=CONVENTIONS)
    read = {capability: rows.get(capability) for capability in ROW_MEMBER_EXAMPLES}
    assert read == ROW_MEMBER_EXAMPLES, f"row_members reads {read}, expected {ROW_MEMBER_EXAMPLES}"

    registry = _import_package_module(name=REGISTRY)
    for operation_id, held, not_held in SELECTED_MEMBER_EXAMPLES:
        members = selected_members(record=registry.graphql_lookup(operation_id=operation_id), schema=schema)
        assert held in members and not_held not in members, (
            f"selected_members of {operation_id} must hold {held!r} and not {not_held!r}; it is {sorted(members)}"
        )


@pytest.mark.usefixtures("scripts_on_path")
def test_every_record_matches_the_reference() -> None:
    """AC-1.1, AC-3.1: ``document_problems`` is empty for every record of ``graphql_only.OPERATIONS``; the test fails
    when it finds no record."""
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
    """Q's method: a copy of a named record made with ``dataclasses.replace`` that differs from the reference gives at
    least one problem, and one of them names what differs."""
    registry = _import_package_module(name=REGISTRY)
    record = registry.graphql_lookup(operation_id=change.operation_id)
    altered = change.altered(record=record, registry=registry)
    assert altered != record, f"the change {change.case} leaves {change.operation_id} as it is: {record}"

    problems = document_problems(record=altered, schema=_schema())

    assert problems, f"document_problems finds nothing in {altered}"
    assert any(change.named in problem for problem in problems), (
        f"no problem names {change.named}, which differs in {change.case}:\n" + "\n".join(problems)
    )


@pytest.mark.usefixtures("scripts_on_path")
def test_every_capability_has_a_record() -> None:
    """AC-1.2: every capability of the "Only in GraphQL" table is the ``capability`` of a record, and
    ``graphql_only.PENDING_CAPABILITIES`` is empty."""
    capabilities = list(row_members(conventions=CONVENTIONS))
    assert capabilities, f"{CONVENTIONS.name}: the {ONLY_IN_GRAPHQL_MARKER} table has no row"
    served = {record.capability for record in _records()}

    missing = [capability for capability in capabilities if capability not in served]

    assert not missing, "capabilities no record serves:\n" + "\n".join(missing)
    pending = getattr(_import_package_module(name=GRAPHQL_ONLY), ATTRIBUTE_PENDING_CAPABILITIES)
    assert pending == frozenset(), f"{GRAPHQL_ONLY}.{ATTRIBUTE_PENDING_CAPABILITIES} still holds {sorted(pending)}"


@pytest.mark.usefixtures("scripts_on_path")
def test_every_member_a_row_names_is_selected() -> None:
    """AC-1.3: for each "Only in GraphQL" row, every member ``row_members`` gives is in the union of
    ``selected_members`` over that capability's records; a failure names the row and the member."""
    schema = _schema()
    records = _records()
    unselected: list[str] = []
    for capability, members in row_members(conventions=CONVENTIONS).items():
        selected: set[str] = set()
        for record in records:
            if record.capability == capability:
                selected |= selected_members(record=record, schema=schema)
        unselected.extend(f"{json.dumps(capability)}: {member}" for member in sorted(members - selected))

    assert not unselected, "members a row names that no record of its capability selects:\n" + "\n".join(unselected)


def test_the_map_names_the_graphql_call() -> None:
    """AC-4.2: the project map, ``docs/forLLMConsumption.md``, names how to make a GraphQL call: it holds
    ``call graphql/``."""
    graphql_call = f"{CALL_SUBCOMMAND} {GRAPHQL_ID_PREFIX}"

    text = LLM_MAP.read_text(encoding="utf-8")

    assert graphql_call in text, f"{LLM_MAP.relative_to(ROOT)} does not hold {graphql_call!r}: it names no GraphQL call"
