"""L: the forge suite's separation and its CI wiring, read from the repository (issue #10, design.md D1, D5, D6, D9,
D10).

The forge suite (``test/forge/``) talks to github.com and runs in its own CI job; these tests run in the default
collection with no network and no test credential (UB-1). They read ``.github/workflows/ci.yml`` as text, through a
small indentation-based reader of the YAML the workflow uses (block mappings and sequences, one-line flow
collections, block scalars, comments), because PyYAML is not a dependency of the dev extra; they run
``pytest --collect-only`` on ``test/forge`` under the default configuration and under the suite's own
``test/forge/pytest.ini``, which no fixture runs under, so no token or network is needed (AC-7.1, AC-7.2); and they
parse the ``.py`` files of ``test/forge/`` with ``ast`` to bound what the suite reaches: only ``ephemeral.py`` starts
the product wrapper, and nothing creates, deletes or targets a repository but the ephemeral one (AC-4.3, AC-8.1,
AC-8.6); the session fixture of ``conftest.py`` wraps one provision (AC-1.1, AC-1.4); and nothing skips, xfails,
ends or hooks a forge test's run, ``pytest.ini`` read with ``configparser`` (AC-5.2, AC-7.3). They read the test
credential's setup note ``docs/forge-suite.md`` (D7), the map ``docs/forLLMConsumption.md`` and
``docs/ProjectPlan.md`` (D10) as text (AC-9.1 to AC-9.3).

Run: ``python scripts/run_tests.py test/test_forge_suite_layout.py``.
"""

from __future__ import annotations

import ast
import configparser
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence, Union

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
# docs.github.com "Workflow syntax for GitHub Actions": on a step, it "allow[s] a job to pass when this step fails".
KEY_CONTINUE_ON_ERROR = "continue-on-error"

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

# The test credential's setup note and the docs, read as text (D7, D10; AC-9.1 to AC-9.3).
SETUP_NOTE_NAME = "docs/forge-suite.md"
SETUP_NOTE = ROOT / SETUP_NOTE_NAME
LLM_MAP_NAME = "docs/forLLMConsumption.md"
LLM_MAP = ROOT / LLM_MAP_NAME
PROJECT_PLAN_NAME = "docs/ProjectPlan.md"
PROJECT_PLAN = ROOT / PROJECT_PLAN_NAME
TEST_CREDENTIAL_FILE = "credentials/github-sff-testing-pat.txt"
TOKEN_KIND = "fine-grained"
TEST_ORGANIZATION = "bestehorn-sff-test"
REPOSITORY_ACCESS = "All repositories"
ACCESS_READ = "read"
ACCESS_WRITE = "write"
# D6's table: each repository permission the forge suite's requests need, spelled as docs.github.com "Permissions
# required for fine-grained personal access tokens" spells it, and its access.
TOKEN_PERMISSIONS = (
    ("Administration", ACCESS_WRITE),
    ("Contents", ACCESS_WRITE),
    ("Metadata", ACCESS_READ),
    ("Issues", ACCESS_WRITE),
    ("Pull requests", ACCESS_WRITE),
    ("Actions", ACCESS_READ),
    ("Code scanning alerts", ACCESS_READ),
    ("Secret scanning alerts", ACCESS_READ),
    ("Dependabot secrets", ACCESS_READ),
)
READ_WORD = re.compile(r"\bread\b", re.IGNORECASE)
WRITE_WORD = re.compile(r"\bwrite\b", re.IGNORECASE)
# The words of one sentence saying that only a machine running the forge suite locally needs the file.
LOCAL_ONLY_WORDS = tuple(re.compile(r"\b" + word + r"\b", re.IGNORECASE) for word in ("only", "machine", "locally"))
LOCAL_ONLY_CLAIM = "a sentence saying that only a machine that runs the forge suite locally needs the file"
# The forge job, as "`forge` job", "forge job", "forge CI job" or "job `forge`".
FORGE_JOB_MENTION = re.compile(r"(?:`forge`|\bforge)\s+(?:CI\s+)?job\b|\bjob[,:]?\s+`forge`", re.IGNORECASE)
DEBT_LINE = "the ephemeral-repository forge tests need their dedicated create/delete token"
WHITESPACE_RUN = re.compile(r"\s+")
# A paragraph break, or a line that opens a Markdown block: a table row, a heading, a quote or a list item.
BLOCK_BREAK = re.compile(r"\n[ \t]*\n|\n(?=[ \t]*(?:[|#>]|[*+-][ \t]|\d+[.)][ \t]))")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# The suite's own configuration and its conftest, read with `configparser` and `ast` (D1, D9, D10).
FORGE_CONFIGURATION_NAME = "test/forge/pytest.ini"
FORGE_CONFIGURATION = ROOT / FORGE_CONFIGURATION_NAME
CONFTEST_NAME = "test/forge/conftest.py"
CONFTEST = ROOT / CONFTEST_NAME
CONFIGURATION_SECTION = "pytest"
FORGE_MODULES = "forge_*.py"
# D1 "Mechanism", exactly: so no fail-fast, selecting, deselecting, ignoring or collect-only option reaches the run.
EXPECTED_FORGE_CONFIGURATION = {
    "python_files": FORGE_MODULES,
    "addopts": "-p no:cacheprovider",
    "log_cli": "true",
    "log_cli_level": "INFO",
}
TEST_PREFIX = "test_"
FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
WITH_NODES = (ast.With, ast.AsyncWith)
YIELD_NODES = (ast.Yield, ast.YieldFrom)
FunctionNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]
WithNode = Union[ast.With, ast.AsyncWith]
# One line of `--collect-only -q`: a node id `<module>::<test>`, a parametrized test's id with its `[...]` parameters.
COLLECTED_ITEM = re.compile(r"^(?P<module>[^\s:][^:]*\.py)::(?P<test>[^\s\[]+)(?:\[.*\])?$")
SESSION_FIXTURE = "ephemeral_repository"
FIXTURE_FUNCTION = "fixture"
SCOPE_KEYWORD = "scope"
SESSION_SCOPE = "session"
WORKER_ID = "worker_id"
DISTRIBUTED_RUN_REFUSAL = "refuse_distributed_run"
PROVISION = "provision"
PYTEST_MODULE = "pytest"
PYTEST_PACKAGES = (PYTEST_MODULE, "_pytest")
# What skips, xfails or ends a test or the run: as an attribute of a pytest name (`pytest.skip`, `pytest.mark.xfail`,
# `mark.skipif` after `from pytest import mark`), or imported from pytest (`from pytest import skip as s`).
SKIPPING_OUTCOMES = frozenset({"skip", "skipif", "xfail", "importorskip", "exit"})
STAR_IMPORT = "*"
SKIP_EXCEPTION = "SkipTest"
HOOK_PREFIX = "pytest_"
COLLECT_IGNORE_PREFIX = "collect_ignore"

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
    return WorkflowReader(text=WORKFLOW.read_text(encoding=SOURCE_ENCODING)).read()


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


def read_document(*, path: Path) -> str:
    return path.read_text(encoding=SOURCE_ENCODING)


def collapse_whitespace(*, text: str) -> str:
    """``text`` with every run of whitespace, line ends included, read as one space."""
    return WHITESPACE_RUN.sub(" ", text).strip()


def phrase_pattern(*, phrase: str) -> re.Pattern[str]:
    """``phrase`` as whole words, any run of whitespace between them."""
    return re.compile(r"\b" + r"\s+".join(re.escape(word) for word in phrase.split()) + r"\b")


def grants(*, line: str, access: str) -> bool:
    """``line`` names ``access``: ``write`` for write access; ``read`` and no ``write`` for read access."""
    writes = WRITE_WORD.search(line) is not None
    if access == ACCESS_WRITE:
        return writes
    return READ_WORD.search(line) is not None and not writes


def missing_permissions(*, text: str) -> list[str]:
    """The permissions of D6's table that no line of ``text`` names together with their access."""
    lines = text.splitlines()
    missing = []
    for permission, access in TOKEN_PERMISSIONS:
        name = phrase_pattern(phrase=permission)
        if not any(name.search(line) and grants(line=line, access=access) for line in lines):
            missing.append(f"the permission {permission} ({access})")
    return missing


def sentences_of(*, text: str) -> list[str]:
    """The sentences of a Markdown ``text``, whitespace collapsed: split at a paragraph break, at a line that opens a
    block, and at whitespace after a full stop, a question mark or an exclamation mark."""
    return [
        collapse_whitespace(text=sentence)
        for block in BLOCK_BREAK.split(text)
        for sentence in SENTENCE_END.split(block)
        if sentence.strip()
    ]


def says_only_local_machines_need_it(*, text: str) -> bool:
    return any(all(word.search(sentence) for word in LOCAL_ONLY_WORDS) for sentence in sentences_of(text=text))


def collect_only(*, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """``python -m pytest --collect-only -q -p no:cacheprovider`` with ``arguments``, from the repository root."""
    return subprocess.run(
        args=[sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *arguments],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=COLLECTION_TIMEOUT_SECONDS,
        check=False,
    )


def forge_test_functions() -> set[tuple[str, str]]:
    """Each module-level ``test_`` function of ``test/forge/forge_*.py``: its module's path from ``test/forge``, the
    rootdir the suite's own configfile makes, and its name."""
    found: set[tuple[str, str]] = set()
    for path in sorted(FORGE_DIRECTORY.glob(FORGE_MODULES)):
        tree = ast.parse(source=read_document(path=path), filename=str(path))
        module = path.relative_to(FORGE_DIRECTORY).as_posix()
        found.update(
            (module, node.name)
            for node in tree.body
            if isinstance(node, FUNCTION_NODES) and node.name.startswith(TEST_PREFIX)
        )
    return found


def collected_tests(*, output: str) -> set[tuple[str, str]]:
    """Each test ``--collect-only -q`` lists: its module's path from the rootdir and its name, without parameters."""
    items = (COLLECTED_ITEM.match(line.strip()) for line in output.splitlines())
    return {(item.group("module"), item.group("test")) for item in items if item}


@dataclass(frozen=True)
class PytestBindings:
    """What a module binds to pytest: the names of a pytest package (``pytest``, ``import pytest as pt``, ``import
    _pytest.outcomes``), and each name an import from one binds, with the name it imports (``from pytest import mark
    as m`` binds ``m`` to ``mark``)."""

    modules: frozenset[str]
    imported: dict[str, str]

    def roots(self) -> frozenset[str]:
        return self.modules | frozenset(self.imported)


def is_pytest_package(*, module: str) -> bool:
    return any(is_within(module=module, package=package) for package in PYTEST_PACKAGES)


def pytest_bindings(*, tree: ast.Module) -> PytestBindings:
    modules = {PYTEST_MODULE}
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(
                alias.asname or alias.name.split(MODULE_SEPARATOR)[0]
                for alias in node.names
                if is_pytest_package(module=alias.name)
            )
        elif isinstance(node, ast.ImportFrom) and is_pytest_package(module=node.module or ""):
            imported.update({alias.asname or alias.name: alias.name for alias in node.names})
    return PytestBindings(modules=frozenset(modules), imported=imported)


def root_name(*, node: ast.AST) -> Optional[str]:
    """The name an attribute chain starts from: ``pytest`` for ``pytest.mark.skip``; ``None`` for any other root."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def is_rooted_in(*, node: ast.AST, roots: frozenset[str]) -> bool:
    name = root_name(node=node)
    return name is not None and name in roots


def reaches_skipping_outcome(*, node: ast.AST, roots: frozenset[str]) -> bool:
    """``node`` is a skipping attribute of a pytest name (``pytest.skip``, ``pytest.mark.xfail``), or names one by a
    string (``getattr(pytest, "exit")``)."""
    if isinstance(node, ast.Attribute):
        return node.attr in SKIPPING_OUTCOMES and is_rooted_in(node=node.value, roots=roots)
    attribute = attribute_by_string(node=node)
    if attribute is None or attribute not in SKIPPING_OUTCOMES:
        return False
    return isinstance(node, ast.Call) and bool(node.args) and is_rooted_in(node=node.args[0], roots=roots)


def imports_skipping_outcome(*, node: ast.AST) -> bool:
    """``node`` imports a skipping name, or every name, from a pytest package (``from pytest import skip as s``)."""
    if not isinstance(node, ast.ImportFrom) or not is_pytest_package(module=node.module or ""):
        return False
    return any(alias.name in SKIPPING_OUTCOMES or alias.name == STAR_IMPORT for alias in node.names)


def skipping_outcomes(*, tree: ast.Module) -> list[int]:
    """The lines that reach what skips, xfails or ends a test or the run, and every line naming ``SkipTest``."""
    roots = pytest_bindings(tree=tree).roots()
    reached = [
        line_of(node=node)
        for node in ast.walk(tree)
        if reaches_skipping_outcome(node=node, roots=roots) or imports_skipping_outcome(node=node)
    ]
    return sorted(reached + lines_naming(root=tree, identifier=SKIP_EXCEPTION))


def defines_hook(*, node: ast.AST) -> bool:
    """``node`` defines or binds a ``pytest_`` name: a hook function, or ``pytest_plugins``."""
    if isinstance(node, FUNCTION_NODES):
        return node.name.startswith(HOOK_PREFIX)
    return isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id.startswith(HOOK_PREFIX)


def collection_hooks(*, tree: ast.Module) -> list[int]:
    """The lines that define a pytest hook or bind ``pytest_plugins``, and the lines that name ``collect_ignore`` or
    ``collect_ignore_glob``, as an identifier or a string."""
    hooks = [
        line_of(node=node)
        for node in ast.walk(tree)
        if defines_hook(node=node)
        or any(identifier.startswith(COLLECT_IGNORE_PREFIX) for identifier in named_identifiers(node=node))
    ]
    ignores = [line for line, text in string_constants(tree=tree) if text.startswith(COLLECT_IGNORE_PREFIX)]
    return sorted(hooks + ignores)


class CaseKeepingParser(configparser.ConfigParser):
    """An INI reader that keeps each key as written, as pytest reads its ``pytest.ini``."""

    def optionxform(self, optionstr: str) -> str:
        return optionstr


def configuration_problems() -> list[str]:
    """D1 "Mechanism": ``test/forge/pytest.ini`` holds the one section ``[pytest]`` with exactly its four keys."""
    if not FORGE_CONFIGURATION.is_file():
        return [f"{FORGE_CONFIGURATION_NAME} does not exist"]
    parser = CaseKeepingParser(interpolation=None)
    try:
        parser.read_string(string=read_document(path=FORGE_CONFIGURATION), source=FORGE_CONFIGURATION_NAME)
    except configparser.Error as exc:
        return [f"{FORGE_CONFIGURATION_NAME} is not an INI file configparser reads: {exc}"]
    sections = parser.sections()
    if sections != [CONFIGURATION_SECTION]:
        return [f"{FORGE_CONFIGURATION_NAME} holds the sections {sections}, not exactly [{CONFIGURATION_SECTION}]"]
    keys = dict(parser[CONFIGURATION_SECTION])
    if keys != EXPECTED_FORGE_CONFIGURATION:
        return [f"{FORGE_CONFIGURATION_NAME} holds {keys}, not exactly {EXPECTED_FORGE_CONFIGURATION}"]
    return []


def is_session_fixture(*, decorator: ast.expr, bindings: PytestBindings) -> bool:
    """``decorator`` is ``pytest.fixture(scope="session")``, or ``fixture(scope="session")`` imported from pytest."""
    if not isinstance(decorator, ast.Call):
        return False
    function = decorator.func
    if isinstance(function, ast.Attribute):
        names_fixture = function.attr == FIXTURE_FUNCTION and is_rooted_in(node=function.value, roots=bindings.modules)
    else:
        names_fixture = isinstance(function, ast.Name) and bindings.imported.get(function.id) == FIXTURE_FUNCTION
    scopes = [keyword.value for keyword in decorator.keywords if keyword.arg == SCOPE_KEYWORD]
    return (
        names_fixture and len(scopes) == 1 and isinstance(scopes[0], ast.Constant) and scopes[0].value == SESSION_SCOPE
    )


def parameter_names(*, function: FunctionNode) -> list[str]:
    arguments = function.args
    return [argument.arg for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)]


def body_nodes(*, function: FunctionNode) -> list[ast.AST]:
    """Every node of ``function``'s body; its decorators and its parameters' defaults left out."""
    return [node for statement in function.body for node in ast.walk(statement)]


def calls_named(*, nodes: Sequence[ast.AST], name: str) -> list[ast.Call]:
    return [node for node in nodes if isinstance(node, ast.Call) and called_name(call=node) == name]


def holding_statement(*, function: FunctionNode, node: ast.AST) -> int:
    """The index of the statement of ``function``'s body that holds ``node``, a node of its body."""
    return next(
        index for index, statement in enumerate(function.body) if any(part is node for part in ast.walk(statement))
    )


def the_refusal(*, function: FunctionNode, nodes: Sequence[ast.AST]) -> Optional[ast.Call]:
    """The one ``refuse_distributed_run(...)`` call of ``nodes``, when it is a statement of ``function``'s own body,
    so it runs whatever happens; ``None`` otherwise."""
    refusals = calls_named(nodes=nodes, name=DISTRIBUTED_RUN_REFUSAL)
    if len(refusals) != 1:
        return None
    statements = [statement for statement in function.body if isinstance(statement, ast.Expr)]
    return refusals[0] if any(statement.value is refusals[0] for statement in statements) else None


def passes_own_worker_id(*, call: ast.Call) -> bool:
    """``call`` passes exactly ``worker_id=worker_id``."""
    if call.args or len(call.keywords) != 1:
        return False
    keyword = call.keywords[0]
    return keyword.arg == WORKER_ID and isinstance(keyword.value, ast.Name) and keyword.value.id == WORKER_ID


def the_provision_block(*, nodes: Sequence[ast.AST]) -> Optional[WithNode]:
    """The ``with`` statement whose item is the one ``provision(...)`` call of ``nodes``; ``None`` unless
    ``provision`` is called exactly once, as a ``with`` item."""
    provisions = calls_named(nodes=nodes, name=PROVISION)
    if len(provisions) != 1:
        return None
    blocks = [
        node
        for node in nodes
        if isinstance(node, WITH_NODES) and any(item.context_expr is provisions[0] for item in node.items)
    ]
    return blocks[0] if blocks else None


def yield_problems(*, nodes: Sequence[ast.AST], block: Optional[WithNode]) -> list[str]:
    """The fixture's body holds one ``yield``, and it lies inside the ``with provision(...)`` block."""
    yields = [node for node in nodes if isinstance(node, YIELD_NODES)]
    if len(yields) != 1 or not isinstance(yields[0], ast.Yield):
        return [f"its body holds {len(yields)} `yield` or `yield from` expressions, not one `yield`"]
    inside = block is not None and any(node is yields[0] for statement in block.body for node in ast.walk(statement))
    return [] if inside else [f"its `yield` is not inside the `with {PROVISION}(...)` block"]


def refusal_problems(*, function: FunctionNode, nodes: Sequence[ast.AST], block: Optional[WithNode]) -> list[str]:
    """The fixture calls ``refuse_distributed_run(worker_id=worker_id)`` once, unconditionally, before ``provision``."""
    refusal = the_refusal(function=function, nodes=nodes)
    if refusal is None:
        return [f"it does not call `{DISTRIBUTED_RUN_REFUSAL}` exactly once, as a statement of its own body"]
    problems = []
    if not passes_own_worker_id(call=refusal):
        problems.append(f"it does not call `{DISTRIBUTED_RUN_REFUSAL}({WORKER_ID}={WORKER_ID})`")
    if block is not None and holding_statement(function=function, node=refusal) >= holding_statement(
        function=function, node=block
    ):
        problems.append(f"it calls `{DISTRIBUTED_RUN_REFUSAL}` after, not before, `{PROVISION}`")
    return problems


def session_fixture_problems(*, function: FunctionNode, bindings: PytestBindings) -> list[str]:
    """AC-1.1, AC-1.4: ``ephemeral_repository`` is a session fixture taking ``worker_id``, refuses a distributed run
    before it provisions, and yields once, inside the one ``with provision(...)`` block."""
    problems = []
    if not any(is_session_fixture(decorator=decorator, bindings=bindings) for decorator in function.decorator_list):
        problems.append(f'it is not decorated `pytest.fixture({SCOPE_KEYWORD}="{SESSION_SCOPE}")`')
    parameters = parameter_names(function=function)
    if WORKER_ID not in parameters:
        problems.append(f"it takes no `{WORKER_ID}` parameter; its parameters are {parameters}")
    nodes = body_nodes(function=function)
    block = the_provision_block(nodes=nodes)
    if block is None:
        problems.append(f"it does not call `{PROVISION}` exactly once, as the item of a `with` statement")
    problems += refusal_problems(function=function, nodes=nodes, block=block)
    problems += yield_problems(nodes=nodes, block=block)
    return problems


def test_the_forge_job_runs_beside_verify() -> None:
    workflow = read_workflow()
    triggers = workflow.get(KEY_ON)
    assert triggers == EXPECTED_TRIGGERS, f"`{KEY_ON}:` is {triggers}, expected exactly {EXPECTED_TRIGGERS}"
    verify = job_named(workflow=workflow, name=JOB_VERIFY)
    naming_forge = [text for text in scalars_of(node=verify) if FORGE_WORD.search(text)]
    assert not naming_forge, f"the job `{JOB_VERIFY}` names `{JOB_FORGE}`: {naming_forge}"
    forge = job_named(workflow=workflow, name=JOB_FORGE)
    assert KEY_NEEDS not in forge, f"the job `{JOB_FORGE}` has `{KEY_NEEDS}: {forge.get(KEY_NEEDS)}`; it runs beside"
    steps = steps_of(job=forge, name=JOB_FORGE)
    assert KEY_CONTINUE_ON_ERROR not in forge, (
        f"the job `{JOB_FORGE}` has `{KEY_CONTINUE_ON_ERROR}: {forge.get(KEY_CONTINUE_ON_ERROR)}`; it hides a failure"
    )
    muted = [step for step in steps if KEY_CONTINUE_ON_ERROR in step]
    assert not muted, (
        f"steps of `{JOB_FORGE}` have `{KEY_CONTINUE_ON_ERROR}:`, so their failure passes the job: {muted}"
    )
    last = steps[-1]
    assert run_of(step=last) == FORGE_COMMAND, f"the last step of `{JOB_FORGE}` is {last}, not `run: {FORGE_COMMAND}`"


def test_the_secret_reaches_one_step() -> None:
    references = SECRET_REFERENCE.findall(WORKFLOW.read_text(encoding=SOURCE_ENCODING))
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


def test_the_setup_note_names_the_credential() -> None:
    assert SETUP_NOTE.is_file(), f"the test credential's setup note {SETUP_NOTE_NAME} does not exist"
    text = read_document(path=SETUP_NOTE)
    prose = collapse_whitespace(text=text)
    phrases = (TEST_CREDENTIAL_FILE, TEST_ORGANIZATION, REPOSITORY_ACCESS, SECRET_NAME)
    missing = [f"`{phrase}`" for phrase in phrases if phrase not in prose]
    if TOKEN_KIND not in prose.casefold():
        missing.append(f"the token kind `{TOKEN_KIND}`")
    missing += missing_permissions(text=text)
    if not says_only_local_machines_need_it(text=text):
        missing.append(LOCAL_ONLY_CLAIM)
    assert not missing, f"{SETUP_NOTE_NAME} does not name: {missing}"


def test_the_map_names_the_forge_suite() -> None:
    assert LLM_MAP.is_file(), f"the map {LLM_MAP_NAME} does not exist"
    prose = collapse_whitespace(text=read_document(path=LLM_MAP))
    beside_the_command = prose.replace(FORGE_COMMAND, "")
    checks = (
        (FORGE_SUITE in beside_the_command, f"the forge suite `{FORGE_SUITE}`, beside its command"),
        (FORGE_COMMAND in prose, f"the local command `{FORGE_COMMAND}`"),
        (TEST_CREDENTIAL_FILE in prose, f"the test credential file `{TEST_CREDENTIAL_FILE}`"),
        (SETUP_NOTE_NAME in prose, f"the setup note `{SETUP_NOTE_NAME}`"),
        (FORGE_JOB_MENTION.search(prose) is not None, f"the CI job `{JOB_FORGE}`"),
    )
    missing = [item for present, item in checks if not present]
    assert not missing, f"{LLM_MAP_NAME} does not name: {missing}"


def test_the_debt_line_is_gone() -> None:
    assert PROJECT_PLAN.is_file(), f"{PROJECT_PLAN_NAME} does not exist"
    prose = collapse_whitespace(text=read_document(path=PROJECT_PLAN)).casefold()
    assert DEBT_LINE.casefold() not in prose, f"{PROJECT_PLAN_NAME} still lists the known debt `{DEBT_LINE}`"


def test_the_session_fixture_wraps_one_provision() -> None:
    assert CONFTEST.is_file(), f"{CONFTEST_NAME}, which defines the session fixture `{SESSION_FIXTURE}`, does not exist"
    tree = ast.parse(source=read_document(path=CONFTEST), filename=str(CONFTEST))
    fixtures = [node for node in tree.body if isinstance(node, FUNCTION_NODES) and node.name == SESSION_FIXTURE]
    assert len(fixtures) == 1, f"{CONFTEST_NAME} defines `{SESSION_FIXTURE}` at module level {len(fixtures)} times"
    problems = session_fixture_problems(function=fixtures[0], bindings=pytest_bindings(tree=tree))
    assert not problems, f"{CONFTEST_NAME} `{SESSION_FIXTURE}`:\n" + "\n".join(problems)


def test_the_forge_path_collects_every_forge_test() -> None:
    assert FORGE_CONFIGURATION.is_file(), f"{FORGE_CONFIGURATION_NAME}, the forge suite's configfile, does not exist"
    expected = forge_test_functions()
    assert expected, f"{FORGE_SUITE}/{FORGE_MODULES} defines no module-level `{TEST_PREFIX}` function"
    completed = collect_only(arguments=[FORGE_SUITE])
    output = completed.stdout + completed.stderr
    succeeded = int(pytest.ExitCode.OK)
    assert completed.returncode == succeeded, (
        f"the collection exited {completed.returncode}, not {succeeded}:\n{output}"
    )
    errors = [marker for marker in COLLECTION_ERROR_MARKERS if marker in output]
    assert not errors, f"the collection reports {errors}:\n{output}"
    collected = collected_tests(output=completed.stdout)
    assert collected == expected, (
        f"the collection of {FORGE_SUITE} lists {sorted(collected - expected)} beyond the `{TEST_PREFIX}` functions "
        f"of {FORGE_SUITE}/{FORGE_MODULES} and misses {sorted(expected - collected)}:\n{output}"
    )


def test_nothing_keeps_a_forge_test_from_running() -> None:
    problems = configuration_problems()
    if not CONFTEST.is_file():
        problems.append(f"{CONFTEST_NAME} does not exist")
    for module in read_forge_modules():
        outcomes = skipping_outcomes(tree=module.tree)
        problems += located(module=module, lines=outcomes, problem="skips, xfails or ends a test or the run")
        hooks = collection_hooks(tree=module.tree)
        problems += located(module=module, lines=hooks, problem="defines a pytest hook or names `collect_ignore`")
    assert not problems, "something keeps a forge test from running:\n" + "\n".join(problems)
