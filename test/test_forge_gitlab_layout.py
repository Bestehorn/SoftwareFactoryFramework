"""G: the GitLab forge suite's separation, its CI wiring and its docs, read from the repository (issue #11, design.md
D1, D5, D7).

The GitLab forge suite (``test/forge_gitlab/``) talks to gitlab.com and runs in its own CI job, ``forge-gitlab``,
beside ``verify`` and ``forge``; these tests run in the default collection with no network and no test credential
(UB-1). They load L, ``test/test_forge_suite_layout.py``, by path from inside each test body (``_layout``), registered
in ``sys.modules`` under its own key before it runs, as #10's S ``_load_by_path`` does, and never at import, so this
file collects whatever L holds. They apply L's workflow reader (``read_workflow``, ``job_named``, ``steps_of``,
``needs_of``, ``run_of``, ``run_commands``, ``scalars_of``, ``condition_of``) to the ``forge-gitlab`` and ``report``
jobs of ``.github/workflows/ci.yml`` (AC-5.1, AC-5.2, AC-5.4, AC-6.3), and L's ``collect_only`` to
``test/forge_gitlab`` under the default configuration, which no fixture runs under, so no token or network is needed
(AC-7.1). They parse the ``.py`` files of ``test/forge_gitlab/`` with ``ast`` into L's ``ForgeModule`` and apply L's
``ast`` helpers to bound what the suite reaches: ``product_wrapper_problems`` to ``ephemeral.py``, so
``PRODUCT_WRAPPER`` is named in ``SubprocessWrapperRunner`` and ``product_wrapper`` and nowhere else but its
definition (D10), and to every module the checks of L's ``module_problems`` with this suite's fake host, project
argument and project records, so only ``ephemeral.py`` starts the product wrapper or names, creates or deletes a
project (AC-4.3, AC-8.1, AC-8.7). They read the docs as text with L's ``read_document``, ``collapse_whitespace``,
``phrase_pattern`` and ``says_only_local_machines_need_it``: the GitLab section of the setup note
``docs/forge-suite.md``, from the first heading after its title that names GitLab to the next heading of that level or
above, so the GitHub sections' names count for nothing (AC-9.1), and the map ``docs/forLLMConsumption.md``, where the
suite's path counts only outside its local command (AC-9.2).

They read the suite's own wiring with L's helpers: ``session_fixture_problems`` on the session fixture
``ephemeral_project`` of ``test/forge_gitlab/conftest.py`` (AC-1.1, AC-1.4); ``collect_only`` on ``test/forge_gitlab``
under its own ``pytest.ini``, which runs no fixture either, its listing read with ``collected_tests`` against the
``test_`` functions of its ``forge_*.py`` (AC-7.2); that ``pytest.ini``, read with ``CaseKeepingParser``, against
#10's four keys, and ``skipping_outcomes`` and ``collection_hooks`` on every module (AC-5.2, AC-7.3); and the module
docstring of ``forge_request_forms.py``, split with ``sentences_of``, for each record of #63 that D6 does not call,
named in a sentence that gives D6's reason for it, a record no other string constant of the suite names (AC-8.5,
AC-8.6).

Run: ``python scripts/run_tests.py test/test_forge_gitlab_layout.py``.
"""

from __future__ import annotations

import ast
import configparser
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "test" / "test_forge_suite_layout.py"
#: The fixed ``sys.modules`` key of L's by-path load; its dataclasses resolve their module through it.
LAYOUT_MODULE = "forge_suite_layout"
LAYOUT_DESCRIPTION = "the forge suite's layout test"

GITLAB_FORGE_SUITE = "test/forge_gitlab"
JOB_FORGE_GITLAB = "forge-gitlab"
GITLAB_FORGE_COMMAND = "python scripts/run_tests.py --workers 1 test/forge_gitlab"
GITLAB_CREDENTIAL_COMMAND = "python test/forge_gitlab/write_credential.py"
GITLAB_SECRET_NAME = "SFF_GITLAB_TEST_TOKEN"  # pragma: allowlist secret
# Both expression spellings of the secret: the property (`secrets.NAME`) and the index (`secrets['NAME']`).
GITLAB_SECRET_REFERENCE = re.compile(
    pattern=r"\bsecrets\s*(?:\.\s*" + GITLAB_SECRET_NAME + r"\b|\[\s*['\"]" + GITLAB_SECRET_NAME + r"['\"]\s*\])"
)
GITLAB_SECRET_EXPRESSION = re.compile(pattern=r"^\$\{\{\s*secrets\." + GITLAB_SECRET_NAME + r"\s*\}\}$")
# The GitLab forge job's id or its suite's directory, as a word of its own (`forge-gitlab`, `test/forge_gitlab`).
GITLAB_FORGE_MENTION = re.compile(pattern=r"(?<![\w-])forge[-_]gitlab(?![\w-])")

GITLAB_FORGE_RESULT = r"\"?\$\{\{\s*needs\.forge-gitlab\.result\s*\}\}\"?"
SUCCESS = r"\"?success\"?"
FAILING_STATUS = r"status=[1-9][0-9]*"
# `if [ "<result>" != "success" ]; then status=N; fi`, or `[ "<result>" = "success" ] || status=N`.
GITLAB_FORGE_GUARDS = (
    re.compile(
        pattern=r"^if\s+\[\[?\s*"
        + GITLAB_FORGE_RESULT
        + r"\s*!=\s*"
        + SUCCESS
        + r"\s*\]\]?\s*;\s*then\s+"
        + FAILING_STATUS
        + r"\s*;\s*fi$"
    ),
    re.compile(
        pattern=r"^\[\[?\s*"
        + GITLAB_FORGE_RESULT
        + r"\s*==?\s*"
        + SUCCESS
        + r"\s*\]\]?\s*\|\|\s*"
        + FAILING_STATUS
        + r"$"
    ),
)

# The GitLab forge suite's modules, read with L's `ast` helpers (D10; AC-8.7): every `.py` file under
# test/forge_gitlab/, whichever wave adds it.
GITLAB_FORGE_DIRECTORY = ROOT / GITLAB_FORGE_SUITE
# The GitLab fake host, which no module of the suite may load (AC-8.7).
GITLAB_FIXTURES_MODULE = "gitlab_wrapper_fixtures"
# A `--path id=`, which names a project other than the configured one: its value an argv entry of its own (`id=...`)
# or after `--path` in one string; `--path merge_request_iid=` and `--path issue_iid=` name no project.
GITLAB_TARGETING_ARGUMENT = re.compile(pattern=r"(?:^|--path[ =])id=")
GITLAB_TARGETING_DESCRIPTION = "a string starting `id=` or holding `--path id=`"
# The records that create and delete a project (D9); `create-a-project-for-a-user` and the `-topic` records are others.
PROJECT_CREATION = "tenant-scale#create-a-project"
PROJECT_DELETION = "tenant-scale#delete-a-project"
GITLAB_PROJECT_LIFECYCLE = re.compile(
    pattern=r"(?<![\w#/-])(?:"
    + re.escape(pattern=PROJECT_CREATION)
    + r"|"
    + re.escape(pattern=PROJECT_DELETION)
    + r")(?![\w-])"
)

# The GitLab forge suite's setup, read as text from the setup note's GitLab section and from the map (D7; AC-9.1,
# AC-9.2).
GITLAB_TEST_CREDENTIAL_FILE = "credentials/gitlab-sff-testing-pat.txt"
GITLAB_TEST_GROUP = "bestehorn-sff-test"
GITLAB_HOST = "gitlab.com"
GITLAB_SERVICE_ACCOUNTS = "Service accounts"
GITLAB_OWNER_ROLE = "Owner"
GITLAB_TOKEN_SCOPE = "api"
# gitlab.com as a host of its own, not the tail of another (`docs.gitlab.com`); a full stop may end its sentence.
GITLAB_HOST_MENTION = re.compile(pattern=r"(?<![\w.-])" + re.escape(pattern=GITLAB_HOST) + r"(?![\w-]|\.\w)")
# The scope `api` as a word of its own: not `read_api`, not `API`, not a path segment (`docs.gitlab.com/api/...`).
GITLAB_SCOPE_MENTION = re.compile(pattern=r"(?<![\w./-])" + re.escape(pattern=GITLAB_TOKEN_SCOPE) + r"(?![\w/-]|\.\w)")
# The GitLab forge job's id as a word of its own, never the suite's directory `test/forge_gitlab`.
GITLAB_FORGE_JOB_MENTION = re.compile(pattern=r"(?<![\w/-])" + re.escape(pattern=JOB_FORGE_GITLAB) + r"(?![\w-])")
GITLAB_LOCAL_ONLY_CLAIM = (
    "a sentence saying that only a machine that runs the GitLab forge suite locally needs the file"
)
# The word that a heading of the setup note's GitLab section holds.
GITLAB_WORD = re.compile(pattern=r"\bGitLab\b")
# An ATX heading: up to three spaces, one to six `#`, whitespace, its title.
MARKDOWN_HEADING = re.compile(pattern=r"^ {0,3}(?P<marks>#{1,6})[ \t]+(?P<title>\S.*?)[ \t]*$")
# A line opening or closing a fenced code block, whose `#` lines are no headings.
MARKDOWN_FENCE = re.compile(pattern=r"^ {0,3}(?:`{3,}|~{3,})")

# The GitLab forge suite's own configuration and its conftest, read with L's INI reader and `ast` helpers (D1, D9;
# AC-1.1, AC-1.4, AC-5.2, AC-7.2, AC-7.3).
GITLAB_CONFIGURATION_NAME = GITLAB_FORGE_SUITE + "/pytest.ini"
GITLAB_CONFIGURATION = ROOT / GITLAB_CONFIGURATION_NAME
GITLAB_CONFTEST_NAME = GITLAB_FORGE_SUITE + "/conftest.py"
GITLAB_CONFTEST = ROOT / GITLAB_CONFTEST_NAME
GITLAB_SESSION_FIXTURE = "ephemeral_project"

# The module whose docstring names the forms of #63 the suite does not call, each with its reason (D6; AC-8.6).
REQUEST_FORMS_NAME = GITLAB_FORGE_SUITE + "/forge_request_forms.py"
REQUEST_FORMS = ROOT / REQUEST_FORMS_NAME


@dataclass(frozen=True)
class MarkdownHeading:
    """An ATX heading of a Markdown text: the index of its line, its level (its count of ``#``) and its title."""

    line: int
    level: int
    title: str


@dataclass(frozen=True)
class UncalledReason:
    """A reason D6 gives for not calling a record: how a failure message names it, and the pattern that finds it in a
    sentence."""

    description: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class UncalledRecord:
    """A record declaring a form of #63 that the GitLab forge suite does not call (D6), and the reasons D6 gives for
    it; a sentence naming the record gives one of them."""

    record: str
    reasons: tuple[UncalledReason, ...]

    def mention(self) -> re.Pattern[str]:
        """The record's ID as a word of its own, never the start of a longer ID (``...-endpoint`` of
        ``...-endpoint-1``)."""
        return re.compile(pattern=r"(?<![\w#/-])" + re.escape(pattern=self.record) + r"(?![\w-])")


# The reasons of AC-8.6's design entry: its tier, `administrator credentials`, no documented answer, outside the
# ephemeral project, or `call`'s refusal.
REASON_TIER = UncalledReason(
    description="its tier (Premium, Ultimate)", pattern=re.compile(pattern=r"\b(?:Premium|Ultimate)\b")
)
REASON_ADMINISTRATOR = UncalledReason(
    description="`administrator credentials`",
    pattern=re.compile(pattern=r"\badministrator\s+credentials\b", flags=re.IGNORECASE),
)
REASON_NO_ANSWER = UncalledReason(
    description="no documented answer",
    pattern=re.compile(pattern=r"\bno\s+documented\s+answer\b|\bdocuments\s+no\s+answer\b", flags=re.IGNORECASE),
)
REASON_OUTSIDE = UncalledReason(
    description="outside the ephemeral project",
    pattern=re.compile(pattern=r"\boutside\s+the\s+ephemeral\s+project\b", flags=re.IGNORECASE),
)
REASON_REFUSAL = UncalledReason(
    description="`call`'s refusal (`GATED_OPERATIONS`)",
    pattern=re.compile(pattern=r"\brefus(?:e|es|ed|al)\b|\bGATED_OPERATIONS\b", flags=re.IGNORECASE),
)
# D6 "The forms of #63 not called": a positional name given once per place, declared only by group records (the group
# SSH certificate record, whose API is Premium and Ultimate, and the four enterprise-user token records that
# tenant_scale.py declares with `positional_names`); the two container-registry records; `--header`, declared by the
# external-control record and the two NuGet symbol-file records; a form-body member below its first bracket level,
# declared only by the S3 import.
UNCALLED_RECORDS = (
    UncalledRecord(record="create#delete-a-group-ssh-certificate", reasons=(REASON_OUTSIDE, REASON_TIER)),
    UncalledRecord(
        record="tenant-scale#revoke-a-personal-access-token-for-an-enterprise-user", reasons=(REASON_OUTSIDE,)
    ),
    UncalledRecord(
        record="tenant-scale#revoke-a-group-or-project-access-token-for-an-enterprise-user", reasons=(REASON_OUTSIDE,)
    ),
    UncalledRecord(
        record="tenant-scale#rotate-a-personal-access-token-for-an-enterprise-user", reasons=(REASON_OUTSIDE,)
    ),
    UncalledRecord(
        record="tenant-scale#rotate-a-group-or-project-access-token-for-an-enterprise-user", reasons=(REASON_OUTSIDE,)
    ),
    UncalledRecord(record="package#listing-all-container-repositories", reasons=(REASON_ADMINISTRATOR,)),
    UncalledRecord(record="package#delete-image-tags-by-reference", reasons=(REASON_NO_ANSWER,)),
    UncalledRecord(record="software-supply-chain-security#set-status-of-an-external-control", reasons=(REASON_TIER,)),
    UncalledRecord(record="openapi-only#the-nuget-symbol-file-download-endpoint", reasons=(REASON_OUTSIDE,)),
    UncalledRecord(record="openapi-only#the-nuget-symbol-file-download-endpoint-1", reasons=(REASON_NO_ANSWER,)),
    UncalledRecord(record="gitlab-dedicated#import-a-project-from-an-aws-s3-bucket", reasons=(REASON_REFUSAL,)),
)


def _load_by_path(*, path: Path, name: str, description: str) -> ModuleType:
    """The file ``path``, loaded by path as the module ``name`` once per process and reused while ``sys.modules`` holds
    it; it is registered there before it runs, so its dataclasses resolve their module.

    Called from inside a test body, so a missing file fails that test with this assertion, never the collection.
    """
    loaded = sys.modules.get(name)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == path:
        return loaded
    assert path.is_file(), f"{description} {path.relative_to(ROOT).as_posix()} does not exist"
    spec = importlib.util.spec_from_file_location(name=name, location=path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module=module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _layout() -> ModuleType:
    """L, ``test/test_forge_suite_layout.py``, the forge suite's layout test, loaded by path (``_load_by_path``)."""
    return _load_by_path(path=LAYOUT_PATH, name=LAYOUT_MODULE, description=LAYOUT_DESCRIPTION)


def assert_fails_unless_gitlab_forge_succeeded(*, script: str, layout: ModuleType) -> None:
    """``script`` sets a failing status unless the GitLab forge job succeeded, keeps it, and exits with it."""
    lines = [line.strip() for line in script.splitlines() if line.strip()]
    guards = [
        index for index, line in enumerate(lines) if any(guard.match(string=line) for guard in GITLAB_FORGE_GUARDS)
    ]
    assert guards, (
        f"no line of the verdict sets a failing status unless the `{JOB_FORGE_GITLAB}` job's result is success:\n"
        f"{script}"
    )
    overwrites = [line for line in lines[guards[-1] + 1 :] if layout.STATUS_ASSIGNMENT.match(string=line)]
    assert not overwrites, (
        f"the verdict overwrites the `{JOB_FORGE_GITLAB}` job's failing status afterwards: {overwrites}"
    )
    assert layout.STATUS_EXIT.match(string=lines[-1]), f'the verdict ends with `{lines[-1]}`, not with `exit "$status"`'


def read_gitlab_forge_modules(*, layout: ModuleType) -> list[Any]:
    """Every ``.py`` file under ``test/forge_gitlab/``, parsed into L's ``ForgeModule``, its ``name`` its path from the
    repository root; ``ephemeral.py`` at the top of the suite is its support module."""
    support = GITLAB_FORGE_DIRECTORY / layout.SUPPORT_MODULE
    return [
        layout.ForgeModule(
            name=path.relative_to(ROOT).as_posix(),
            tree=ast.parse(source=path.read_text(encoding=layout.SOURCE_ENCODING), filename=str(path)),
            is_support=path == support,
        )
        for path in sorted(GITLAB_FORGE_DIRECTORY.rglob(layout.PYTHON_FILES))
    ]


def gitlab_fixture_loads(*, tree: ast.Module, layout: ModuleType) -> list[int]:
    """L's ``fixture_loads`` for the GitLab fake host: an import of ``gitlab_wrapper_fixtures`` (as any dotted part), or
    a string naming it, as a load by path would."""
    imports = [
        layout.line_of(node=node)
        for node in ast.walk(node=tree)
        if any(
            GITLAB_FIXTURES_MODULE in module.split(layout.MODULE_SEPARATOR)
            for module in layout.imported_modules(node=node)
        )
    ]
    paths = [line for line, text in layout.string_constants(tree=tree) if GITLAB_FIXTURES_MODULE in text]
    return sorted(imports + paths)


def gitlab_module_problems(*, module: Any, layout: ModuleType) -> list[str]:
    """What ``module`` may not do (L's ``module_problems`` with this suite's fake host, project argument and project
    records): read an attribute ``main``, load ``gitlab_wrapper_fixtures`` or patch ``urllib``; and, unless it is
    ``ephemeral.py``, import ``subprocess``, name ``product_wrapper`` or ``PRODUCT_WRAPPER``, give a string starting
    ``id=`` or holding ``--path id=``, or name ``tenant-scale#create-a-project`` or
    ``tenant-scale#delete-a-project``."""
    tree = module.tree
    checks = [
        (layout.entry_point_reads(tree=tree), f"reads the attribute `{layout.ENTRY_POINT}`"),
        (gitlab_fixture_loads(tree=tree, layout=layout), f"loads `{GITLAB_FIXTURES_MODULE}`"),
        (layout.urllib_patches(tree=tree), f"patches `{layout.URLLIB_PACKAGE}`"),
    ]
    if not module.is_support:
        only_support = f"which only {layout.SUPPORT_MODULE} may"
        checks += [
            (layout.subprocess_imports(tree=tree), f"imports `{layout.SUBPROCESS_MODULE}`, {only_support}"),
            (
                layout.lines_naming(root=tree, identifier=layout.PRODUCT_WRAPPER_LOADER),
                f"names `{layout.PRODUCT_WRAPPER_LOADER}`, {only_support}",
            ),
            (
                layout.lines_naming(root=tree, identifier=layout.PRODUCT_WRAPPER_PATH),
                f"names `{layout.PRODUCT_WRAPPER_PATH}`, {only_support}",
            ),
            (
                layout.constants_matching(tree=tree, pattern=GITLAB_TARGETING_ARGUMENT),
                f"gives {GITLAB_TARGETING_DESCRIPTION}, {only_support}",
            ),
            (
                layout.constants_matching(tree=tree, pattern=GITLAB_PROJECT_LIFECYCLE),
                f"names `{PROJECT_CREATION}` or `{PROJECT_DELETION}`, {only_support}",
            ),
        ]
    return [problem for lines, text in checks for problem in layout.located(module=module, lines=lines, problem=text)]


def markdown_headings(*, lines: list[str]) -> list[MarkdownHeading]:
    """The ATX headings of the Markdown ``lines``, in order, outside fenced code blocks."""
    headings = []
    fenced = False
    for index, line in enumerate(lines):
        if MARKDOWN_FENCE.match(string=line):
            fenced = not fenced
            continue
        heading = None if fenced else MARKDOWN_HEADING.match(string=line)
        if heading is not None:
            headings.append(
                MarkdownHeading(line=index, level=len(heading.group("marks")), title=heading.group("title"))
            )
    return headings


def section_under(*, lines: list[str], headings: list[MarkdownHeading], opening: MarkdownHeading) -> str:
    """The section ``opening`` heads in ``lines``: its heading's line up to the next heading of its level or above
    (fewer ``#``), or to the end of ``lines``."""
    closings = [heading.line for heading in headings if heading.line > opening.line and heading.level <= opening.level]
    end = closings[0] if closings else len(lines)
    return "\n".join(lines[opening.line : end])


def gitlab_forge_test_functions(*, layout: ModuleType) -> set[tuple[str, str]]:
    """L's ``forge_test_functions`` for this suite: each module-level ``test_`` function of
    ``test/forge_gitlab/forge_*.py``, its module's path from ``test/forge_gitlab``, the rootdir the suite's own
    configfile makes, and its name."""
    found: set[tuple[str, str]] = set()
    for path in sorted(GITLAB_FORGE_DIRECTORY.glob(layout.FORGE_MODULES)):
        tree = ast.parse(source=layout.read_document(path=path), filename=str(path))
        module = path.relative_to(GITLAB_FORGE_DIRECTORY).as_posix()
        found.update(
            (module, node.name)
            for node in tree.body
            if isinstance(node, layout.FUNCTION_NODES) and node.name.startswith(layout.TEST_PREFIX)
        )
    return found


def gitlab_configuration_problems(*, layout: ModuleType) -> list[str]:
    """L's ``configuration_problems`` for this suite: ``test/forge_gitlab/pytest.ini`` holds the one section
    ``[pytest]`` with exactly #10 D1's four keys."""
    if not GITLAB_CONFIGURATION.is_file():
        return [f"{GITLAB_CONFIGURATION_NAME} does not exist"]
    parser = layout.CaseKeepingParser(interpolation=None)
    try:
        parser.read_string(string=layout.read_document(path=GITLAB_CONFIGURATION), source=GITLAB_CONFIGURATION_NAME)
    except configparser.Error as exc:
        return [f"{GITLAB_CONFIGURATION_NAME} is not an INI file configparser reads: {exc}"]
    sections = parser.sections()
    if sections != [layout.CONFIGURATION_SECTION]:
        return [
            f"{GITLAB_CONFIGURATION_NAME} holds the sections {sections}, not exactly [{layout.CONFIGURATION_SECTION}]"
        ]
    keys = dict(parser[layout.CONFIGURATION_SECTION])
    if keys != layout.EXPECTED_FORGE_CONFIGURATION:
        return [f"{GITLAB_CONFIGURATION_NAME} holds {keys}, not exactly {layout.EXPECTED_FORGE_CONFIGURATION}"]
    return []


def module_docstring(*, tree: ast.Module) -> Optional[ast.Constant]:
    """The string constant that is ``tree``'s module docstring; ``None`` when the module has none."""
    first = tree.body[0] if tree.body else None
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first.value
    return None


def uncalled_record_problems(*, docstring: str, layout: ModuleType) -> list[str]:
    """Each record of ``UNCALLED_RECORDS`` that no sentence of ``docstring`` (L's ``sentences_of``) names, or that no
    sentence naming it gives one of its reasons in."""
    sentences = layout.sentences_of(text=docstring)
    problems = []
    for uncalled in UNCALLED_RECORDS:
        mention = uncalled.mention()
        naming = [sentence for sentence in sentences if mention.search(string=sentence)]
        reasons = " or ".join(reason.description for reason in uncalled.reasons)
        if not naming:
            problems.append(f"names no `{uncalled.record}`, which the suite does not call ({reasons})")
        elif not any(reason.pattern.search(string=sentence) for sentence in naming for reason in uncalled.reasons):
            problems.append(f"names `{uncalled.record}` in no sentence that gives its reason, {reasons}: {naming}")
    return problems


def other_constants_naming(*, modules: list[Any]) -> list[str]:
    """Each string constant of the suite's ``modules`` but ``forge_request_forms.py``'s module docstring, other
    docstrings and f-strings' literal parts included, that names a record of ``UNCALLED_RECORDS``."""
    problems = []
    for module in modules:
        kept = module_docstring(tree=module.tree) if module.name == REQUEST_FORMS_NAME else None
        for node in ast.walk(node=module.tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str) or node is kept:
                continue
            problems += [
                f"{module.name}:{node.lineno}: names `{uncalled.record}`, which the suite does not call"
                for uncalled in UNCALLED_RECORDS
                if uncalled.mention().search(string=node.value)
            ]
    return problems


def test_the_gitlab_forge_job_runs_beside_verify() -> None:
    layout = _layout()
    workflow = layout.read_workflow()
    triggers = workflow.get(layout.KEY_ON)
    assert triggers == layout.EXPECTED_TRIGGERS, (
        f"`{layout.KEY_ON}:` is {triggers}, expected exactly {layout.EXPECTED_TRIGGERS}"
    )
    for name in (layout.JOB_VERIFY, layout.JOB_FORGE):
        job = layout.job_named(workflow=workflow, name=name)
        naming = [text for text in layout.scalars_of(node=job) if GITLAB_FORGE_MENTION.search(string=text)]
        assert not naming, f"the job `{name}` names `{JOB_FORGE_GITLAB}` or `{GITLAB_FORGE_SUITE}`: {naming}"
    gitlab = layout.job_named(workflow=workflow, name=JOB_FORGE_GITLAB)
    assert layout.KEY_NEEDS not in gitlab, (
        f"the job `{JOB_FORGE_GITLAB}` has `{layout.KEY_NEEDS}: {gitlab.get(layout.KEY_NEEDS)}`; it runs beside"
    )
    assert layout.KEY_CONTINUE_ON_ERROR not in gitlab, (
        f"the job `{JOB_FORGE_GITLAB}` has `{layout.KEY_CONTINUE_ON_ERROR}: "
        f"{gitlab.get(layout.KEY_CONTINUE_ON_ERROR)}`; it hides a failure"
    )
    steps = layout.steps_of(job=gitlab, name=JOB_FORGE_GITLAB)
    muted = [step for step in steps if layout.KEY_CONTINUE_ON_ERROR in step]
    assert not muted, (
        f"steps of `{JOB_FORGE_GITLAB}` have `{layout.KEY_CONTINUE_ON_ERROR}:`, so their failure passes the job: "
        f"{muted}"
    )
    last = steps[-1]
    assert layout.run_of(step=last) == GITLAB_FORGE_COMMAND, (
        f"the last step of `{JOB_FORGE_GITLAB}` is {last}, not `run: {GITLAB_FORGE_COMMAND}`"
    )


def test_the_gitlab_secret_reaches_one_step() -> None:
    layout = _layout()
    references = GITLAB_SECRET_REFERENCE.findall(string=layout.WORKFLOW.read_text(encoding=layout.SOURCE_ENCODING))
    assert len(references) == 1, (
        f"{layout.WORKFLOW_NAME} references the secret {GITLAB_SECRET_NAME} {len(references)} times, not once"
    )
    gitlab = layout.job_named(workflow=layout.read_workflow(), name=JOB_FORGE_GITLAB)
    steps = layout.steps_of(job=gitlab, name=JOB_FORGE_GITLAB)
    credential_steps = [step for step in steps if layout.run_of(step=step) == GITLAB_CREDENTIAL_COMMAND]
    assert len(credential_steps) == 1, (
        f"{len(credential_steps)} steps of `{JOB_FORGE_GITLAB}` run `{GITLAB_CREDENTIAL_COMMAND}`"
    )
    environment = credential_steps[0].get(layout.KEY_ENV)
    assert isinstance(environment, dict), (
        f"the credential step has no `{layout.KEY_ENV}:` mapping: {credential_steps[0]}"
    )
    secret = environment.get(GITLAB_SECRET_NAME)
    assert isinstance(secret, str) and GITLAB_SECRET_EXPRESSION.match(string=secret), (
        f"the credential step's `{layout.KEY_ENV}:` does not hand {GITLAB_SECRET_NAME} the secret: {environment}"
    )
    checkouts = [step for step in steps if str(step.get(layout.KEY_USES, "")).startswith(layout.CHECKOUT_ACTION)]
    assert checkouts, f"the job `{JOB_FORGE_GITLAB}` has no `{layout.CHECKOUT_ACTION}` step"
    for checkout in checkouts:
        inputs = checkout.get(layout.KEY_WITH)
        persisted = str(inputs.get(layout.KEY_PERSIST_CREDENTIALS, "")) if isinstance(inputs, dict) else ""
        assert persisted.lower() == layout.YAML_FALSE, (
            f"the checkout of `{JOB_FORGE_GITLAB}` keeps the token: {checkout}"
        )
    checks = [
        command
        for command in layout.run_commands(steps=steps)
        if command != GITLAB_CREDENTIAL_COMMAND and not layout.INSTALL_COMMAND.match(string=command)
    ]
    assert checks == [GITLAB_FORGE_COMMAND], (
        f"the check commands of `{JOB_FORGE_GITLAB}` are {checks}, expected [{GITLAB_FORGE_COMMAND}]"
    )


def test_the_report_judges_the_gitlab_forge_job() -> None:
    layout = _layout()
    report = layout.job_named(workflow=layout.read_workflow(), name=layout.JOB_REPORT)
    needs = layout.needs_of(job=report)
    expected = [layout.JOB_VERIFY, layout.JOB_FORGE, JOB_FORGE_GITLAB]
    missing = [job for job in expected if job not in needs]
    assert not missing, f"`{layout.JOB_REPORT}` needs {needs}, missing {missing}; it must run after {expected}"
    assert layout.condition_of(job=report) == layout.ALWAYS, (
        f"`{layout.JOB_REPORT}` runs `{layout.KEY_IF}: {report.get(layout.KEY_IF)}`, not {layout.ALWAYS}"
    )
    verdicts = [
        command
        for command in layout.run_commands(steps=layout.steps_of(job=report, name=layout.JOB_REPORT))
        if layout.SUMMARY_COMMAND in command
    ]
    assert len(verdicts) == 1, f"{len(verdicts)} steps of `{layout.JOB_REPORT}` run `{layout.SUMMARY_COMMAND}`"
    assert_fails_unless_gitlab_forge_succeeded(script=verdicts[0], layout=layout)


def test_the_default_configuration_collects_no_gitlab_forge_test() -> None:
    layout = _layout()
    completed = layout.collect_only(arguments=["-c", layout.DEFAULT_CONFIGURATION, GITLAB_FORGE_SUITE])
    output = completed.stdout + completed.stderr
    expected = int(pytest.ExitCode.NO_TESTS_COLLECTED)
    assert completed.returncode == expected, f"the collection exited {completed.returncode}, not {expected}:\n{output}"
    assert layout.NO_TESTS_COLLECTED in output, f"the collection does not say `{layout.NO_TESTS_COLLECTED}`:\n{output}"
    errors = [marker for marker in layout.COLLECTION_ERROR_MARKERS if marker in output]
    assert not errors, f"the collection reports {errors}:\n{output}"


def test_the_gitlab_forge_tests_reach_only_the_ephemeral_project() -> None:
    layout = _layout()
    modules = read_gitlab_forge_modules(layout=layout)
    supports = [module for module in modules if module.is_support]
    assert len(supports) == 1, (
        f"{GITLAB_FORGE_SUITE} holds no {layout.SUPPORT_MODULE}; its files are {[module.name for module in modules]}"
    )
    # D10: one module-level definition of PRODUCT_WRAPPER, named outside it in SubprocessWrapperRunner and
    # product_wrapper only, and in each of them.
    problems = list(layout.product_wrapper_problems(module=supports[0]))
    problems += [problem for module in modules for problem in gitlab_module_problems(module=module, layout=layout)]
    assert not problems, "the GitLab forge suite reaches past its ephemeral project:\n" + "\n".join(problems)


def test_the_setup_note_names_the_gitlab_credential() -> None:
    layout = _layout()
    assert layout.SETUP_NOTE.is_file(), f"the test credential's setup note {layout.SETUP_NOTE_NAME} does not exist"
    lines = layout.read_document(path=layout.SETUP_NOTE).splitlines()
    headings = markdown_headings(lines=lines)
    # The title, the first heading, heads the whole note and its GitHub sections, so it is never the GitLab section.
    openings = [heading for heading in headings[1:] if GITLAB_WORD.search(string=heading.title)]
    assert openings, (
        f"no heading after the title of {layout.SETUP_NOTE_NAME} names GitLab; its headings are "
        f"{[heading.title for heading in headings]}"
    )
    section = section_under(lines=lines, headings=headings, opening=openings[0])
    prose = layout.collapse_whitespace(text=section)
    phrases = (GITLAB_TEST_CREDENTIAL_FILE, GITLAB_TEST_GROUP, GITLAB_SECRET_NAME, GITLAB_FORGE_COMMAND)
    missing = [f"`{phrase}`" for phrase in phrases if phrase not in prose]
    patterns = (
        (GITLAB_HOST_MENTION, f"the host `{GITLAB_HOST}`"),
        (layout.phrase_pattern(phrase=GITLAB_SERVICE_ACCOUNTS), f'the group\'s "{GITLAB_SERVICE_ACCOUNTS}"'),
        (layout.phrase_pattern(phrase=GITLAB_OWNER_ROLE), f'the role "{GITLAB_OWNER_ROLE}"'),
        (GITLAB_SCOPE_MENTION, f"the token scope `{GITLAB_TOKEN_SCOPE}`"),
    )
    missing += [item for pattern, item in patterns if pattern.search(string=prose) is None]
    if not layout.says_only_local_machines_need_it(text=section):
        missing.append(GITLAB_LOCAL_ONLY_CLAIM)
    assert not missing, f"the GitLab section `{openings[0].title}` of {layout.SETUP_NOTE_NAME} does not name: {missing}"


def test_the_map_names_the_gitlab_forge_suite() -> None:
    layout = _layout()
    assert layout.LLM_MAP.is_file(), f"the map {layout.LLM_MAP_NAME} does not exist"
    prose = layout.collapse_whitespace(text=layout.read_document(path=layout.LLM_MAP))
    # The local command holds the suite's path, so the path counts only outside it.
    beside_the_command = prose.replace(GITLAB_FORGE_COMMAND, "")
    checks = (
        (
            GITLAB_FORGE_SUITE in beside_the_command,
            f"the GitLab forge suite `{GITLAB_FORGE_SUITE}`, beside its command",
        ),
        (GITLAB_FORGE_COMMAND in prose, f"the local command `{GITLAB_FORGE_COMMAND}`"),
        (GITLAB_TEST_CREDENTIAL_FILE in prose, f"the test credential file `{GITLAB_TEST_CREDENTIAL_FILE}`"),
        (layout.SETUP_NOTE_NAME in prose, f"the setup note `{layout.SETUP_NOTE_NAME}`"),
        (GITLAB_FORGE_JOB_MENTION.search(string=prose) is not None, f"the CI job `{JOB_FORGE_GITLAB}`"),
    )
    missing = [item for present, item in checks if not present]
    assert not missing, f"{layout.LLM_MAP_NAME} does not name: {missing}"


def test_the_session_fixture_wraps_one_provision() -> None:
    layout = _layout()
    assert GITLAB_CONFTEST.is_file(), (
        f"{GITLAB_CONFTEST_NAME}, which defines the session fixture `{GITLAB_SESSION_FIXTURE}`, does not exist"
    )
    tree = ast.parse(source=layout.read_document(path=GITLAB_CONFTEST), filename=str(GITLAB_CONFTEST))
    fixtures = [
        node for node in tree.body if isinstance(node, layout.FUNCTION_NODES) and node.name == GITLAB_SESSION_FIXTURE
    ]
    assert len(fixtures) == 1, (
        f"{GITLAB_CONFTEST_NAME} defines `{GITLAB_SESSION_FIXTURE}` at module level {len(fixtures)} times"
    )
    # D1: the fixture's one-keyword `refuse_distributed_run(worker_id=worker_id)` before the one `with provision(...)`,
    # whose block holds its one `yield`.
    problems = layout.session_fixture_problems(function=fixtures[0], bindings=layout.pytest_bindings(tree=tree))
    assert not problems, f"{GITLAB_CONFTEST_NAME} `{GITLAB_SESSION_FIXTURE}`:\n" + "\n".join(problems)


def test_the_gitlab_forge_path_collects_every_gitlab_forge_test() -> None:
    layout = _layout()
    assert GITLAB_CONFIGURATION.is_file(), (
        f"{GITLAB_CONFIGURATION_NAME}, the GitLab forge suite's configfile, does not exist"
    )
    expected = gitlab_forge_test_functions(layout=layout)
    assert expected, (
        f"{GITLAB_FORGE_SUITE}/{layout.FORGE_MODULES} defines no module-level `{layout.TEST_PREFIX}` function"
    )
    completed = layout.collect_only(arguments=[GITLAB_FORGE_SUITE])
    output = completed.stdout + completed.stderr
    succeeded = int(pytest.ExitCode.OK)
    assert completed.returncode == succeeded, (
        f"the collection exited {completed.returncode}, not {succeeded}:\n{output}"
    )
    errors = [marker for marker in layout.COLLECTION_ERROR_MARKERS if marker in output]
    assert not errors, f"the collection reports {errors}:\n{output}"
    collected = layout.collected_tests(output=completed.stdout)
    assert collected == expected, (
        f"the collection of {GITLAB_FORGE_SUITE} lists {sorted(collected - expected)} beyond the "
        f"`{layout.TEST_PREFIX}` functions of {GITLAB_FORGE_SUITE}/{layout.FORGE_MODULES} and misses "
        f"{sorted(expected - collected)}:\n{output}"
    )


def test_nothing_keeps_a_gitlab_forge_test_from_running() -> None:
    layout = _layout()
    problems = gitlab_configuration_problems(layout=layout)
    if not GITLAB_CONFTEST.is_file():
        problems.append(f"{GITLAB_CONFTEST_NAME} does not exist")
    for module in read_gitlab_forge_modules(layout=layout):
        outcomes = layout.skipping_outcomes(tree=module.tree)
        problems += layout.located(module=module, lines=outcomes, problem="skips, xfails or ends a test or the run")
        hooks = layout.collection_hooks(tree=module.tree)
        problems += layout.located(
            module=module, lines=hooks, problem="defines a pytest hook or names `collect_ignore`"
        )
    assert not problems, "something keeps a GitLab forge test from running:\n" + "\n".join(problems)


def test_each_uncalled_form_is_named_with_its_reason() -> None:
    layout = _layout()
    assert REQUEST_FORMS.is_file(), (
        f"{REQUEST_FORMS_NAME}, whose module docstring names the forms of #63 the suite does not call, does not exist"
    )
    modules = read_gitlab_forge_modules(layout=layout)
    forms = [module for module in modules if module.name == REQUEST_FORMS_NAME]
    assert len(forms) == 1, f"{GITLAB_FORGE_SUITE} reads {REQUEST_FORMS_NAME} {len(forms)} times, not once"
    docstring = module_docstring(tree=forms[0].tree)
    assert docstring is not None, f"{REQUEST_FORMS_NAME} has no module docstring"
    problems = [
        f"{REQUEST_FORMS_NAME}'s module docstring {problem}"
        for problem in uncalled_record_problems(docstring=docstring.value, layout=layout)
    ]
    problems += other_constants_naming(modules=modules)
    assert not problems, "the forms of #63 the suite does not call are not named with their reasons:\n" + "\n".join(
        problems
    )
