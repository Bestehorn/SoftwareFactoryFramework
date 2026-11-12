"""L: the forge suite's separation and its CI wiring, read from the repository (issue #10, design.md D1, D5, D6, D10).

The forge suite (``test/forge/``) talks to github.com and runs in its own CI job; these tests run in the default
collection with no network and no test credential (UB-1). They read ``.github/workflows/ci.yml`` as text, through a
small indentation-based reader of the YAML the workflow uses (block mappings and sequences, one-line flow
collections, block scalars, comments), because PyYAML is not a dependency of the dev extra; they run
``pytest --collect-only`` on ``test/forge`` under the default configuration; and they parse the ``.py`` files of
``test/forge/`` with ``ast`` to bound what the suite reaches: only ``ephemeral.py`` starts the product wrapper, and
nothing creates, deletes or targets a repository but the ephemeral one (AC-4.3, AC-8.1, AC-8.6).

Run: ``python scripts/run_tests.py test/test_forge_suite_layout.py``.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
WORKFLOW_NAME = ".github/workflows/ci.yml"
DEFAULT_CONFIGURATION = "pyproject.toml"
FORGE_SUITE = "test/forge"
COLLECTION_TIMEOUT_SECONDS = 300

# The workflow's keys.
KEY_ON = "on"
KEY_JOBS = "jobs"
KEY_NEEDS = "needs"
KEY_IF = "if"
KEY_STEPS = "steps"
KEY_RUN = "run"
KEY_USES = "uses"
KEY_WITH = "with"
KEY_ENV = "env"
KEY_BRANCHES = "branches"
KEY_PERSIST_CREDENTIALS = "persist-credentials"

JOB_VERIFY = "verify"
JOB_FORGE = "forge"
JOB_REPORT = "report"

TRIGGER_PUSH = "push"
TRIGGER_PULL_REQUEST = "pull_request"
TRIGGER_WORKFLOW_DISPATCH = "workflow_dispatch"
TRUNK = "main"
# The triggers of the current ci.yml, which D5 leaves unchanged.
EXPECTED_TRIGGERS = {
    TRIGGER_PUSH: {KEY_BRANCHES: [TRUNK]},
    TRIGGER_PULL_REQUEST: None,
    TRIGGER_WORKFLOW_DISPATCH: None,
}

FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge"
CREDENTIAL_COMMAND = "python test/forge/write_credential.py"
SECRET_NAME = "SFF_TEST_TOKEN"  # pragma: allowlist secret
# Both expression spellings of the secret: the property (`secrets.NAME`) and the index (`secrets['NAME']`).
SECRET_REFERENCE = re.compile(r"\bsecrets\s*(?:\.\s*SFF_TEST_TOKEN\b|\[\s*['\"]SFF_TEST_TOKEN['\"]\s*\])")
SECRET_EXPRESSION = re.compile(r"^\$\{\{\s*secrets\.SFF_TEST_TOKEN\s*\}\}$")
CHECKOUT_ACTION = "actions/checkout@"
YAML_FALSE = "false"
# A command that installs the job's tools rather than checking anything.
INSTALL_COMMAND = re.compile(r"^(?:python\s+-m\s+)?pip\s+install\b")
FORGE_WORD = re.compile(r"\bforge\b")

ALWAYS = "always()"
EXPRESSION = re.compile(r"^\$\{\{\s*(?P<body>.*?)\s*\}\}$")
SUMMARY_COMMAND = "python scripts/run_checks.py --summary-from reports"
FORGE_RESULT = r"\"?\$\{\{\s*needs\.forge\.result\s*\}\}\"?"
SUCCESS = r"\"?success\"?"
FAILING_STATUS = r"status=[1-9][0-9]*"
# `if [ "<result>" != "success" ]; then status=N; fi`, or `[ "<result>" = "success" ] || status=N`.
FORGE_GUARDS = (
    re.compile(
        r"^if\s+\[\[?\s*"
        + FORGE_RESULT
        + r"\s*!=\s*"
        + SUCCESS
        + r"\s*\]\]?\s*;\s*then\s+"
        + FAILING_STATUS
        + r"\s*;\s*fi$"
    ),
    re.compile(r"^\[\[?\s*" + FORGE_RESULT + r"\s*==?\s*" + SUCCESS + r"\s*\]\]?\s*\|\|\s*" + FAILING_STATUS + r"$"),
)
STATUS_ASSIGNMENT = re.compile(r"^status=")
STATUS_EXIT = re.compile(r"^exit\s+\"?\$\{?status\}?\"?$")

NO_TESTS_COLLECTED = "no tests collected"
COLLECTION_ERROR_MARKERS = ("ERROR collecting", "ImportError", "ModuleNotFoundError")

# The forge suite's modules, read with `ast` (D2, D6, D10): every `.py` file under test/forge/, whichever wave adds it.
FORGE_DIRECTORY = ROOT / FORGE_SUITE
PYTHON_FILES = "*.py"
SOURCE_ENCODING = "utf-8"
SUPPORT_MODULE = "ephemeral.py"
SUBPROCESS_MODULE = "subprocess"
PRODUCT_WRAPPER_LOADER = "product_wrapper"
PRODUCT_WRAPPER_PATH = "PRODUCT_WRAPPER"
WRAPPER_RUNNER = "SubprocessWrapperRunner"
# Outside its definition, `PRODUCT_WRAPPER` is named in exactly these two of ephemeral.py, and in each of them (D10).
PRODUCT_WRAPPER_SCOPES = (WRAPPER_RUNNER, PRODUCT_WRAPPER_LOADER)
MODULE_LEVEL = "the module level"
ENTRY_POINT = "main"
FIXTURES_MODULE = "github_wrapper_fixtures"
URLLIB_PACKAGE = "urllib"
MODULE_SEPARATOR = "."
DOCUMENTED_NODES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
SCOPE_NODES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
# `getattr(obj, "name")` and its siblings, as builtins or as methods (`monkeypatch.setattr(obj, "name", value)`).
ATTRIBUTE_BUILTINS = frozenset({"getattr", "hasattr", "setattr", "delattr"})
ATTRIBUTE_NAME_INDEX = 1
# `__import__("m")` and `importlib.import_module("m")`.
DYNAMIC_IMPORTS = frozenset({"__import__", "import_module"})
# `patch(...)`, `setattr(...)`; `mock.patch(...)`, `patch.object(...)`, `patch.dict(...)`, `monkeypatch.setattr(...)`.
PATCH_FUNCTIONS = frozenset({"patch", "setattr", "delattr"})
PATCH_METHODS = frozenset({"patch", "object", "dict", "multiple", "setattr", "delattr", "setitem", "delitem"})
URLLIB_TEXT = re.compile(r"^urllib(?:\.|$)")
# A `--path owner=` or `--path repo=`, its value an argv entry of its own or after `--path` in one string.
TARGETING_ARGUMENT = re.compile(r"(?:^|--path[ =])(?:owner|repo)=")
# The records that create and delete a repository; the `repos/delete-*` records of a repository's parts are others.
REPOSITORY_LIFECYCLE = re.compile(r"(?<![\w/-])repos/(?:create-in-org|delete)(?![\w/-])")

# The YAML reader's syntax.
KEY_LINE = re.compile(r"^(?P<key>[A-Za-z0-9_][\w.\-/]*|\"[^\"]*\"|'[^']*')[ \t]*:(?:[ \t]+(?P<value>.*))?$")
BLOCK_SCALAR = re.compile(r"^[|>](?:[+-]?[1-9]?|[1-9][+-])$")
ITEM_MARK = "-"
ITEM_PREFIX = "- "
COMMENT_MARK = "#"
DOCUMENT_START = "---"
QUOTES = "'\""
SINGLE_QUOTE = "'"
WHITESPACE = " \t"
QUOTE_OPENERS = " \t[{,:"
FLOW_SEQUENCE_OPEN = "["
FLOW_CLOSERS = {"[": "]", "{": "}"}
FLOW_NESTING_OPEN = "[{"
FLOW_NESTING_CLOSE = "]}"
FLOW_SEPARATOR = ","


class WorkflowReadError(Exception):
    """The workflow holds YAML the reader does not support, or malformed YAML."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True)
class SourceLine:
    """One line that carries YAML: its indentation, its text without the comment, its 0-based line number."""

    indent: int
    text: str
    number: int


def indentation(*, text: str) -> int:
    return len(text) - len(text.lstrip(" "))


def strip_comment(*, text: str) -> str:
    """``text`` without its trailing comment: a ``#`` at the start or after whitespace, outside a quoted scalar."""
    quote = ""
    for index, char in enumerate(text):
        if quote:
            quote = "" if char == quote else quote
        elif char in QUOTES and (index == 0 or text[index - 1] in QUOTE_OPENERS):
            quote = char
        elif char == COMMENT_MARK and (index == 0 or text[index - 1] in WHITESPACE):
            return text[:index].rstrip()
    return text.rstrip()


def significant_lines(*, raw_lines: list[str]) -> list[SourceLine]:
    """The lines that carry YAML: blank lines, comment lines and a document start dropped."""
    lines = []
    for number, raw in enumerate(raw_lines):
        text = strip_comment(text=raw.lstrip(" "))
        if text and not (text == DOCUMENT_START and indentation(text=raw) == 0):
            lines.append(SourceLine(indent=indentation(text=raw), text=text, number=number))
    return lines


def is_item(*, text: str) -> bool:
    return text == ITEM_MARK or text.startswith(ITEM_PREFIX)


def unquote(*, text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in QUOTES:
        inner = text[1:-1]
        return inner.replace("''", SINGLE_QUOTE) if text[0] == SINGLE_QUOTE else inner.replace('\\"', '"')
    return text


def split_flow(*, body: str) -> list[str]:
    """The entries of a flow collection's body, split at its top-level commas."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote = ""
    for char in body:
        if quote:
            quote = "" if char == quote else quote
        elif char in QUOTES:
            quote = char
        elif char in FLOW_NESTING_OPEN:
            depth += 1
        elif char in FLOW_NESTING_CLOSE:
            depth -= 1
        elif char == FLOW_SEPARATOR and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def parse_flow(*, text: str) -> Any:
    """A one-line flow sequence (``[a, b]``) as a list, or a flow mapping (``{k: v}``) as a dict."""
    if not text.endswith(FLOW_CLOSERS[text[0]]):
        raise WorkflowReadError("a flow collection that is unclosed or spans lines", details={"text": text})
    parts = split_flow(body=text[1:-1])
    if text[0] == FLOW_SEQUENCE_OPEN:
        return [parse_inline(text=part) for part in parts]
    mapping: dict[str, Any] = {}
    for part in parts:
        entry = KEY_LINE.match(part)
        if entry is None:
            raise WorkflowReadError("a flow mapping entry without a key", details={"text": text, "entry": part})
        value = entry.group("value")
        mapping[unquote(text=entry.group("key"))] = None if value is None else parse_inline(text=value)
    return mapping


def parse_inline(*, text: str) -> Any:
    """A value written on its key's line: a flow collection, or a quoted or plain scalar kept as a string."""
    if text[0] in FLOW_CLOSERS:
        return parse_flow(text=text)
    return unquote(text=text)


def dedent_block(*, lines: list[str]) -> str:
    """A block scalar's lines, without its trailing blank lines, dedented by its first line's indentation."""
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    if not lines:
        return ""
    width = indentation(text=next(line for line in lines if line.strip()))
    return "\n".join(line[width:] for line in lines)


class WorkflowReader:
    """Reads the YAML subset a GitHub Actions workflow uses into dicts, lists and strings (``None`` for no value).

    Supported: block mappings and block sequences (an item's mapping may start on its dash line, and a sequence may
    sit at its key's indentation), flow sequences and mappings on one line, ``|`` and ``>`` block scalars (kept line
    by line, never folded), quoted and plain scalars, and comments. Every scalar stays a string, so ``false`` reads
    as ``"false"``. Anything else raises ``WorkflowReadError``.
    """

    def __init__(self, *, text: str) -> None:
        self._raw = text.splitlines()
        self._lines = significant_lines(raw_lines=self._raw)
        self._position = 0

    def read(self) -> dict[str, Any]:
        if not self._lines:
            raise WorkflowReadError("the workflow holds no YAML")
        document = self._node(indent=self._lines[0].indent)
        if self._has_line():
            raise self._error(problem="a line outside the document's structure", line=self._current())
        if not isinstance(document, dict):
            raise WorkflowReadError("the workflow is not a mapping")
        return document

    def _has_line(self) -> bool:
        return self._position < len(self._lines)

    def _current(self) -> SourceLine:
        return self._lines[self._position]

    def _error(self, *, problem: str, line: SourceLine) -> WorkflowReadError:
        return WorkflowReadError(f"{WORKFLOW_NAME}:{line.number + 1}: {problem}", details={"text": line.text})

    def _node(self, *, indent: int) -> Any:
        line = self._current()
        if is_item(text=line.text):
            return self._sequence(indent=indent)
        if KEY_LINE.match(line.text):
            return self._mapping(indent=indent)
        self._position += 1
        return parse_inline(text=line.text)

    def _mapping(self, *, indent: int) -> dict[str, Any]:
        mapping: dict[str, Any] = {}
        while self._has_line():
            line = self._current()
            if line.indent < indent:
                break
            if line.indent > indent or is_item(text=line.text):
                raise self._error(problem="unexpected indentation or a sequence item inside a mapping", line=line)
            entry = KEY_LINE.match(line.text)
            if entry is None:
                raise self._error(problem="a line that is neither a key nor a sequence item", line=line)
            key = unquote(text=entry.group("key"))
            if key in mapping:
                raise self._error(problem=f"the key {key!r} is repeated", line=line)
            self._position += 1
            mapping[key] = self._entry_value(indent=indent, line=line, value_text=entry.group("value") or "")
        return mapping

    def _entry_value(self, *, indent: int, line: SourceLine, value_text: str) -> Any:
        if BLOCK_SCALAR.match(value_text):
            return self._block_scalar(indent=indent, line=line)
        if value_text:
            return parse_inline(text=value_text)
        if not self._has_line():
            return None
        following = self._current()
        if following.indent > indent:
            return self._node(indent=following.indent)
        if following.indent == indent and is_item(text=following.text):
            return self._sequence(indent=indent)
        return None

    def _sequence(self, *, indent: int) -> list[Any]:
        items: list[Any] = []
        while self._has_line():
            line = self._current()
            if line.indent > indent:
                raise self._error(problem="unexpected indentation inside a sequence", line=line)
            if line.indent < indent or not is_item(text=line.text):
                break
            items.append(self._item(indent=indent, line=line))
        return items

    def _item(self, *, indent: int, line: SourceLine) -> Any:
        rest = line.text[len(ITEM_MARK) :]
        content = rest.lstrip(" ")
        if not content:
            self._position += 1
            if self._has_line() and self._current().indent > indent:
                return self._node(indent=self._current().indent)
            return None
        if BLOCK_SCALAR.match(content):
            self._position += 1
            return self._block_scalar(indent=indent, line=line)
        if is_item(text=content) or KEY_LINE.match(content):
            # The item's node starts on the dash line, at the column of its first character.
            column = indent + len(ITEM_MARK) + len(rest) - len(content)
            self._lines[self._position] = SourceLine(indent=column, text=content, number=line.number)
            return self._node(indent=column)
        self._position += 1
        return parse_inline(text=content)

    def _block_scalar(self, *, indent: int, line: SourceLine) -> str:
        """The raw lines after ``line`` that are blank or indented deeper than ``indent``, comments included."""
        end = line.number + 1
        while end < len(self._raw) and (not self._raw[end].strip() or indentation(text=self._raw[end]) > indent):
            end += 1
        while self._has_line() and self._current().number < end:
            self._position += 1
        return dedent_block(lines=self._raw[line.number + 1 : end])


def read_workflow() -> dict[str, Any]:
    return WorkflowReader(text=WORKFLOW.read_text(encoding="utf-8")).read()


def job_named(*, workflow: dict[str, Any], name: str) -> dict[str, Any]:
    jobs = workflow.get(KEY_JOBS)
    assert isinstance(jobs, dict), f"{WORKFLOW_NAME} has no `{KEY_JOBS}:` mapping"
    job = jobs.get(name)
    assert isinstance(job, dict), f"{WORKFLOW_NAME} has no job `{name}`; its jobs are {sorted(jobs)}"
    return job


def steps_of(*, job: dict[str, Any], name: str) -> list[dict[str, Any]]:
    steps = job.get(KEY_STEPS)
    assert isinstance(steps, list) and steps, f"the job `{name}` has no `{KEY_STEPS}:` sequence"
    assert all(isinstance(step, dict) for step in steps), f"a step of the job `{name}` is not a mapping: {steps}"
    return steps


def needs_of(*, job: dict[str, Any]) -> list[str]:
    """The jobs ``job`` waits for: its ``needs:`` as a list, empty when it has none."""
    needs = job.get(KEY_NEEDS)
    if needs is None:
        return []
    return [needs] if isinstance(needs, str) else [str(need) for need in needs]


def run_of(*, step: dict[str, Any]) -> Optional[str]:
    """The command ``step`` runs, stripped; ``None`` for a step that runs no command (a ``uses:`` step)."""
    command = step.get(KEY_RUN)
    return command.strip() if isinstance(command, str) else None


def run_commands(*, steps: list[dict[str, Any]]) -> list[str]:
    return [command for command in (run_of(step=step) for step in steps) if command is not None]


def scalars_of(*, node: Any) -> list[str]:
    """Every key and scalar value under ``node``, depth first."""
    if isinstance(node, dict):
        return [text for key, value in node.items() for text in [key, *scalars_of(node=value)]]
    if isinstance(node, list):
        return [text for item in node for text in scalars_of(node=item)]
    return [] if node is None else [str(node)]


def condition_of(*, job: dict[str, Any]) -> str:
    """The job's ``if:`` condition, without a ``${{ }}`` wrapper."""
    condition = str(job.get(KEY_IF, "")).strip()
    wrapped = EXPRESSION.match(condition)
    return wrapped.group("body") if wrapped else condition


def assert_fails_unless_forge_succeeded(*, script: str) -> None:
    """``script`` sets a failing status unless the forge job succeeded, keeps it, and exits with it."""
    lines = [line.strip() for line in script.splitlines() if line.strip()]
    guards = [index for index, line in enumerate(lines) if any(guard.match(line) for guard in FORGE_GUARDS)]
    assert guards, f"no line of the verdict sets a failing status unless the forge job's result is success:\n{script}"
    overwrites = [line for line in lines[guards[-1] + 1 :] if STATUS_ASSIGNMENT.match(line)]
    assert not overwrites, f"the verdict overwrites the forge job's failing status afterwards: {overwrites}"
    assert STATUS_EXIT.match(lines[-1]), f'the verdict ends with `{lines[-1]}`, not with `exit "$status"`'


@dataclass(frozen=True)
class ForgeModule:
    """One ``.py`` file under ``test/forge/``, parsed; ``name`` is its path from the repository root."""

    name: str
    tree: ast.Module
    is_support: bool


def read_forge_modules() -> list[ForgeModule]:
    support = FORGE_DIRECTORY / SUPPORT_MODULE
    return [
        ForgeModule(
            name=path.relative_to(ROOT).as_posix(),
            tree=ast.parse(source=path.read_text(encoding=SOURCE_ENCODING), filename=str(path)),
            is_support=path == support,
        )
        for path in sorted(FORGE_DIRECTORY.rglob(PYTHON_FILES))
    ]


def line_of(*, node: ast.AST) -> int:
    return int(getattr(node, "lineno", 0))


def located(*, module: ForgeModule, lines: list[int], problem: str) -> list[str]:
    return [f"{module.name}:{line}: {problem}" for line in lines]


def is_within(*, module: str, package: str) -> bool:
    """``module`` is ``package`` or one of its submodules."""
    return module == package or module.startswith(package + MODULE_SEPARATOR)


def docstring_constants(*, tree: ast.Module) -> set[ast.AST]:
    """The docstrings of ``tree``'s module, classes and functions."""
    found: set[ast.AST] = set()
    for node in ast.walk(tree):
        first = node.body[0] if isinstance(node, DOCUMENTED_NODES) and node.body else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            found.add(first.value)
    return found


def string_constants(*, tree: ast.Module) -> list[tuple[int, str]]:
    """The line and text of every string constant of ``tree`` but its docstrings, f-strings' literal parts included."""
    docstrings = docstring_constants(tree=tree)
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node not in docstrings
    ]


def constants_matching(*, tree: ast.Module, pattern: re.Pattern[str]) -> list[int]:
    return [line for line, text in string_constants(tree=tree) if pattern.search(text)]


def called_name(*, call: ast.Call) -> Optional[str]:
    """The name a call spells its function with: ``f`` for ``f(...)`` and for ``obj.f(...)``."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def string_argument(*, call: ast.Call, index: int) -> Optional[str]:
    """The call's positional argument ``index`` when it is a string constant."""
    argument = call.args[index] if len(call.args) > index else None
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    return None


def imported_modules(*, node: ast.AST) -> list[str]:
    """What an import statement loads: ``m`` for ``import m``; ``m`` and ``m.a`` for ``from m import a``."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    base = node.module or ""
    loaded = [base + MODULE_SEPARATOR + alias.name if base else alias.name for alias in node.names]
    return [base, *loaded] if base else loaded


def dynamic_imports(*, node: ast.AST) -> list[str]:
    """The module ``__import__("m")`` or ``importlib.import_module("m")`` loads."""
    if isinstance(node, ast.Call) and called_name(call=node) in DYNAMIC_IMPORTS:
        module = string_argument(call=node, index=0)
        return [] if module is None else [module]
    return []


def attribute_by_string(*, node: ast.AST) -> Optional[str]:
    """The attribute ``getattr(obj, "name")`` names, or ``hasattr``, ``setattr`` or ``delattr``."""
    if isinstance(node, ast.Call) and called_name(call=node) in ATTRIBUTE_BUILTINS:
        return string_argument(call=node, index=ATTRIBUTE_NAME_INDEX)
    return None


def named_identifiers(*, node: ast.AST) -> list[str]:
    """The identifiers ``node`` itself names: a name, an attribute, every dotted part and alias of an import, a
    ``global`` or ``nonlocal`` name, and an attribute named by a string."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, (ast.Global, ast.Nonlocal)):
        return list(node.names)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        parts = [part for module in imported_modules(node=node) for part in module.split(MODULE_SEPARATOR)]
        return parts + [alias for alias in (name.asname for name in node.names) if alias]
    attribute = attribute_by_string(node=node)
    return [] if attribute is None else [attribute]


def read_attributes(*, node: ast.AST) -> list[str]:
    """The attributes ``node`` itself reads: an attribute, a name ``from m import`` takes from ``m``, and an
    attribute named by a string."""
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, ast.ImportFrom):
        return [alias.name for alias in node.names]
    attribute = attribute_by_string(node=node)
    return [] if attribute is None else [attribute]


def lines_naming(*, root: ast.AST, identifier: str, excluded: Sequence[ast.AST] = ()) -> list[int]:
    """The lines of the nodes under ``root`` (``root`` included, ``excluded`` left out) that name ``identifier``."""
    return [
        line_of(node=node)
        for node in ast.walk(root)
        if identifier in named_identifiers(node=node) and all(node is not skipped for skipped in excluded)
    ]


def entry_point_reads(*, tree: ast.Module) -> list[int]:
    return [line_of(node=node) for node in ast.walk(tree) if ENTRY_POINT in read_attributes(node=node)]


def fixture_loads(*, tree: ast.Module) -> list[int]:
    """An import of ``github_wrapper_fixtures`` (as any dotted part), or a string naming it, as a load by path would."""
    imports = [
        line_of(node=node)
        for node in ast.walk(tree)
        if any(FIXTURES_MODULE in module.split(MODULE_SEPARATOR) for module in imported_modules(node=node))
    ]
    paths = [line for line, text in string_constants(tree=tree) if FIXTURES_MODULE in text]
    return sorted(imports + paths)


def subprocess_imports(*, tree: ast.Module) -> list[int]:
    return [
        line_of(node=node)
        for node in ast.walk(tree)
        if any(
            is_within(module=module, package=SUBPROCESS_MODULE)
            for module in imported_modules(node=node) + dynamic_imports(node=node)
        )
    ]


def urllib_bindings(*, tree: ast.Module) -> set[str]:
    """``urllib`` and every local name an import of ``urllib`` or a part of it binds."""
    bindings = {URLLIB_PACKAGE}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bindings.update(
                alias.asname or alias.name.split(MODULE_SEPARATOR)[0]
                for alias in node.names
                if is_within(module=alias.name, package=URLLIB_PACKAGE)
            )
        elif isinstance(node, ast.ImportFrom) and is_within(module=node.module or "", package=URLLIB_PACKAGE):
            bindings.update(alias.asname or alias.name for alias in node.names)
    return bindings


def refers_to_urllib(*, node: ast.AST, bindings: set[str]) -> bool:
    """``node`` holds a name bound to ``urllib`` or a string spelling a part of it (``"urllib.request.urlopen"``)."""
    for part in ast.walk(node):
        if isinstance(part, ast.Name) and part.id in bindings:
            return True
        if isinstance(part, ast.Constant) and isinstance(part.value, str) and URLLIB_TEXT.match(part.value):
            return True
    return False


def patched_operands(*, node: ast.AST) -> list[ast.expr]:
    """What ``node`` patches: the arguments of a patching call, and the targets of an assignment or a deletion that
    are no bare name (``urllib.request.urlopen = ...``, ``sys.modules["urllib.request"] = ...``)."""
    if isinstance(node, ast.Call):
        function = node.func
        patching = (isinstance(function, ast.Name) and function.id in PATCH_FUNCTIONS) or (
            isinstance(function, ast.Attribute) and function.attr in PATCH_METHODS
        )
        return [*node.args, *(keyword.value for keyword in node.keywords)] if patching else []
    if isinstance(node, (ast.Assign, ast.Delete)):
        targets = list(node.targets)
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
        targets = [node.target]
    else:
        return []
    return [target for target in targets if not isinstance(target, ast.Name)]


def urllib_patches(*, tree: ast.Module) -> list[int]:
    bindings = urllib_bindings(tree=tree)
    return [
        line_of(node=node)
        for node in ast.walk(tree)
        if any(refers_to_urllib(node=operand, bindings=bindings) for operand in patched_operands(node=node))
    ]


def product_wrapper_definitions(*, statement: ast.stmt) -> list[ast.expr]:
    """The ``PRODUCT_WRAPPER`` names a module-level assignment binds."""
    if isinstance(statement, ast.Assign):
        targets = list(statement.targets)
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    else:
        return []
    return [target for target in targets if isinstance(target, ast.Name) and target.id == PRODUCT_WRAPPER_PATH]


def product_wrapper_problems(*, module: ForgeModule) -> list[str]:
    """D10 in ``ephemeral.py``: one module-level definition of ``PRODUCT_WRAPPER``, which outside it is named only in
    ``SubprocessWrapperRunner`` and ``product_wrapper``, and in each of them."""
    definitions: list[ast.expr] = []
    scopes: dict[str, list[int]] = {}
    for statement in module.tree.body:
        definitions += product_wrapper_definitions(statement=statement)
        scope = statement.name if isinstance(statement, SCOPE_NODES) else MODULE_LEVEL
        lines = lines_naming(root=statement, identifier=PRODUCT_WRAPPER_PATH, excluded=definitions)
        if lines:
            scopes.setdefault(scope, []).extend(lines)
    problems = []
    if len(definitions) != 1:
        problems.append(f"{module.name}: defines `{PRODUCT_WRAPPER_PATH}` at module level {len(definitions)} times")
    for scope, lines in scopes.items():
        if scope not in PRODUCT_WRAPPER_SCOPES:
            outside = f"names `{PRODUCT_WRAPPER_PATH}` in {scope}, not in {WRAPPER_RUNNER} or {PRODUCT_WRAPPER_LOADER}"
            problems += located(module=module, lines=lines, problem=outside)
    problems += [
        f"{module.name}: `{scope}` does not name `{PRODUCT_WRAPPER_PATH}`"
        for scope in PRODUCT_WRAPPER_SCOPES
        if scope not in scopes
    ]
    return problems


def module_problems(*, module: ForgeModule) -> list[str]:
    """What ``module`` may not do: read an attribute ``main``, load ``github_wrapper_fixtures`` or patch ``urllib``;
    and, unless it is ``ephemeral.py``, import ``subprocess``, name ``product_wrapper`` or ``PRODUCT_WRAPPER``, give
    ``--path owner=`` or ``--path repo=``, or create or delete a repository."""
    tree = module.tree
    checks = [
        (entry_point_reads(tree=tree), f"reads the attribute `{ENTRY_POINT}`"),
        (fixture_loads(tree=tree), f"loads `{FIXTURES_MODULE}`"),
        (urllib_patches(tree=tree), f"patches `{URLLIB_PACKAGE}`"),
    ]
    if not module.is_support:
        only_support = f"which only {SUPPORT_MODULE} may"
        checks += [
            (subprocess_imports(tree=tree), f"imports `{SUBPROCESS_MODULE}`, {only_support}"),
            (
                lines_naming(root=tree, identifier=PRODUCT_WRAPPER_LOADER),
                f"names `{PRODUCT_WRAPPER_LOADER}`, {only_support}",
            ),
            (
                lines_naming(root=tree, identifier=PRODUCT_WRAPPER_PATH),
                f"names `{PRODUCT_WRAPPER_PATH}`, {only_support}",
            ),
            (constants_matching(tree=tree, pattern=TARGETING_ARGUMENT), "gives `--path owner=` or `--path repo=`"),
            (
                constants_matching(tree=tree, pattern=REPOSITORY_LIFECYCLE),
                f"creates or deletes a repository, {only_support}",
            ),
        ]
    return [problem for lines, text in checks for problem in located(module=module, lines=lines, problem=text)]


def test_the_forge_job_runs_beside_verify() -> None:
    workflow = read_workflow()
    triggers = workflow.get(KEY_ON)
    assert triggers == EXPECTED_TRIGGERS, f"`{KEY_ON}:` is {triggers}, expected exactly {EXPECTED_TRIGGERS}"
    verify = job_named(workflow=workflow, name=JOB_VERIFY)
    naming_forge = [text for text in scalars_of(node=verify) if FORGE_WORD.search(text)]
    assert not naming_forge, f"the job `{JOB_VERIFY}` names `{JOB_FORGE}`: {naming_forge}"
    forge = job_named(workflow=workflow, name=JOB_FORGE)
    assert KEY_NEEDS not in forge, f"the job `{JOB_FORGE}` has `{KEY_NEEDS}: {forge.get(KEY_NEEDS)}`; it runs beside"
    last = steps_of(job=forge, name=JOB_FORGE)[-1]
    assert run_of(step=last) == FORGE_COMMAND, f"the last step of `{JOB_FORGE}` is {last}, not `run: {FORGE_COMMAND}`"


def test_the_secret_reaches_one_step() -> None:
    references = SECRET_REFERENCE.findall(WORKFLOW.read_text(encoding="utf-8"))
    assert len(references) == 1, f"{WORKFLOW_NAME} references the secret {SECRET_NAME} {len(references)} times"
    forge = job_named(workflow=read_workflow(), name=JOB_FORGE)
    steps = steps_of(job=forge, name=JOB_FORGE)
    credential_steps = [step for step in steps if run_of(step=step) == CREDENTIAL_COMMAND]
    assert len(credential_steps) == 1, f"{len(credential_steps)} steps of `{JOB_FORGE}` run `{CREDENTIAL_COMMAND}`"
    environment = credential_steps[0].get(KEY_ENV)
    assert isinstance(environment, dict), f"the credential step has no `{KEY_ENV}:` mapping: {credential_steps[0]}"
    secret = environment.get(SECRET_NAME)
    assert isinstance(secret, str) and SECRET_EXPRESSION.match(secret), (
        f"the credential step's `{KEY_ENV}:` does not hand {SECRET_NAME} the secret: {environment}"
    )
    checkouts = [step for step in steps if str(step.get(KEY_USES, "")).startswith(CHECKOUT_ACTION)]
    assert checkouts, f"the job `{JOB_FORGE}` has no `{CHECKOUT_ACTION}` step"
    for checkout in checkouts:
        inputs = checkout.get(KEY_WITH)
        persisted = str(inputs.get(KEY_PERSIST_CREDENTIALS, "")) if isinstance(inputs, dict) else ""
        assert persisted.lower() == YAML_FALSE, f"the checkout of `{JOB_FORGE}` keeps the token: {checkout}"
    checks = [
        command
        for command in run_commands(steps=steps)
        if command != CREDENTIAL_COMMAND and not INSTALL_COMMAND.match(command)
    ]
    assert checks == [FORGE_COMMAND], f"the check commands of `{JOB_FORGE}` are {checks}, expected [{FORGE_COMMAND}]"


def test_the_report_judges_the_forge_job() -> None:
    report = job_named(workflow=read_workflow(), name=JOB_REPORT)
    needs = needs_of(job=report)
    assert sorted(needs) == sorted([JOB_VERIFY, JOB_FORGE]), f"`{JOB_REPORT}` needs {needs}, not [verify, forge]"
    assert condition_of(job=report) == ALWAYS, f"`{JOB_REPORT}` runs `{KEY_IF}: {report.get(KEY_IF)}`, not {ALWAYS}"
    verdicts = [
        command for command in run_commands(steps=steps_of(job=report, name=JOB_REPORT)) if SUMMARY_COMMAND in command
    ]
    assert len(verdicts) == 1, f"{len(verdicts)} steps of `{JOB_REPORT}` run `{SUMMARY_COMMAND}`"
    assert_fails_unless_forge_succeeded(script=verdicts[0])


def test_the_default_configuration_collects_no_forge_test() -> None:
    completed = subprocess.run(
        args=[
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-c",
            DEFAULT_CONFIGURATION,
            "-p",
            "no:cacheprovider",
            FORGE_SUITE,
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=COLLECTION_TIMEOUT_SECONDS,
        check=False,
    )
    output = completed.stdout + completed.stderr
    expected = int(pytest.ExitCode.NO_TESTS_COLLECTED)
    assert completed.returncode == expected, f"the collection exited {completed.returncode}, not {expected}:\n{output}"
    assert NO_TESTS_COLLECTED in output, f"the collection does not say `{NO_TESTS_COLLECTED}`:\n{output}"
    errors = [marker for marker in COLLECTION_ERROR_MARKERS if marker in output]
    assert not errors, f"the collection reports {errors}:\n{output}"


def test_the_forge_tests_reach_only_the_ephemeral_repository() -> None:
    modules = read_forge_modules()
    supports = [module for module in modules if module.is_support]
    assert len(supports) == 1, f"{FORGE_SUITE} holds no {SUPPORT_MODULE}; its files are {[m.name for m in modules]}"
    problems = product_wrapper_problems(module=supports[0])
    problems += [problem for module in modules for problem in module_problems(module=module)]
    assert not problems, "the forge suite reaches past its ephemeral repository:\n" + "\n".join(problems)
