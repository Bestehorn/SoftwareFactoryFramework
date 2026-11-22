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

Run: ``python scripts/run_tests.py test/test_forge_gitlab_layout.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

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
    r"\bsecrets\s*(?:\.\s*" + GITLAB_SECRET_NAME + r"\b|\[\s*['\"]" + GITLAB_SECRET_NAME + r"['\"]\s*\])"
)
GITLAB_SECRET_EXPRESSION = re.compile(r"^\$\{\{\s*secrets\." + GITLAB_SECRET_NAME + r"\s*\}\}$")
# The GitLab forge job's id or its suite's directory, as a word of its own (`forge-gitlab`, `test/forge_gitlab`).
GITLAB_FORGE_MENTION = re.compile(r"(?<![\w-])forge[-_]gitlab(?![\w-])")

GITLAB_FORGE_RESULT = r"\"?\$\{\{\s*needs\.forge-gitlab\.result\s*\}\}\"?"
SUCCESS = r"\"?success\"?"
FAILING_STATUS = r"status=[1-9][0-9]*"
# `if [ "<result>" != "success" ]; then status=N; fi`, or `[ "<result>" = "success" ] || status=N`.
GITLAB_FORGE_GUARDS = (
    re.compile(
        r"^if\s+\[\[?\s*"
        + GITLAB_FORGE_RESULT
        + r"\s*!=\s*"
        + SUCCESS
        + r"\s*\]\]?\s*;\s*then\s+"
        + FAILING_STATUS
        + r"\s*;\s*fi$"
    ),
    re.compile(
        r"^\[\[?\s*" + GITLAB_FORGE_RESULT + r"\s*==?\s*" + SUCCESS + r"\s*\]\]?\s*\|\|\s*" + FAILING_STATUS + r"$"
    ),
)

# The GitLab forge suite's modules, read with L's `ast` helpers (D10; AC-8.7): every `.py` file under
# test/forge_gitlab/, whichever wave adds it.
GITLAB_FORGE_DIRECTORY = ROOT / GITLAB_FORGE_SUITE
# The GitLab fake host, which no module of the suite may load (AC-8.7).
GITLAB_FIXTURES_MODULE = "gitlab_wrapper_fixtures"
# A `--path id=`, which names a project other than the configured one: its value an argv entry of its own (`id=...`)
# or after `--path` in one string; `--path merge_request_iid=` and `--path issue_iid=` name no project.
GITLAB_TARGETING_ARGUMENT = re.compile(r"(?:^|--path[ =])id=")
GITLAB_TARGETING_DESCRIPTION = "a string starting `id=` or holding `--path id=`"
# The records that create and delete a project (D9); `create-a-project-for-a-user` and the `-topic` records are others.
PROJECT_CREATION = "tenant-scale#create-a-project"
PROJECT_DELETION = "tenant-scale#delete-a-project"
GITLAB_PROJECT_LIFECYCLE = re.compile(
    r"(?<![\w#/-])(?:" + re.escape(PROJECT_CREATION) + r"|" + re.escape(PROJECT_DELETION) + r")(?![\w-])"
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
GITLAB_HOST_MENTION = re.compile(r"(?<![\w.-])" + re.escape(GITLAB_HOST) + r"(?![\w-]|\.\w)")
# The scope `api` as a word of its own: not `read_api`, not `API`, not a path segment (`docs.gitlab.com/api/...`).
GITLAB_SCOPE_MENTION = re.compile(r"(?<![\w./-])" + re.escape(GITLAB_TOKEN_SCOPE) + r"(?![\w/-]|\.\w)")
# The GitLab forge job's id as a word of its own, never the suite's directory `test/forge_gitlab`.
GITLAB_FORGE_JOB_MENTION = re.compile(r"(?<![\w/-])" + re.escape(JOB_FORGE_GITLAB) + r"(?![\w-])")
GITLAB_LOCAL_ONLY_CLAIM = (
    "a sentence saying that only a machine that runs the GitLab forge suite locally needs the file"
)
# The word that a heading of the setup note's GitLab section holds.
GITLAB_WORD = re.compile(r"\bGitLab\b")
# An ATX heading: up to three spaces, one to six `#`, whitespace, its title.
MARKDOWN_HEADING = re.compile(r"^ {0,3}(?P<marks>#{1,6})[ \t]+(?P<title>\S.*?)[ \t]*$")
# A line opening or closing a fenced code block, whose `#` lines are no headings.
MARKDOWN_FENCE = re.compile(r"^ {0,3}(?:`{3,}|~{3,})")


@dataclass(frozen=True)
class MarkdownHeading:
    """An ATX heading of a Markdown text: the index of its line, its level (its count of ``#``) and its title."""

    line: int
    level: int
    title: str


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
    guards = [index for index, line in enumerate(lines) if any(guard.match(line) for guard in GITLAB_FORGE_GUARDS)]
    assert guards, (
        f"no line of the verdict sets a failing status unless the `{JOB_FORGE_GITLAB}` job's result is success:\n"
        f"{script}"
    )
    overwrites = [line for line in lines[guards[-1] + 1 :] if layout.STATUS_ASSIGNMENT.match(line)]
    assert not overwrites, (
        f"the verdict overwrites the `{JOB_FORGE_GITLAB}` job's failing status afterwards: {overwrites}"
    )
    assert layout.STATUS_EXIT.match(lines[-1]), f'the verdict ends with `{lines[-1]}`, not with `exit "$status"`'


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
        for node in ast.walk(tree)
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
        if MARKDOWN_FENCE.match(line):
            fenced = not fenced
            continue
        heading = None if fenced else MARKDOWN_HEADING.match(line)
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


def test_the_gitlab_forge_job_runs_beside_verify() -> None:
    layout = _layout()
    workflow = layout.read_workflow()
    triggers = workflow.get(layout.KEY_ON)
    assert triggers == layout.EXPECTED_TRIGGERS, (
        f"`{layout.KEY_ON}:` is {triggers}, expected exactly {layout.EXPECTED_TRIGGERS}"
    )
    for name in (layout.JOB_VERIFY, layout.JOB_FORGE):
        job = layout.job_named(workflow=workflow, name=name)
        naming = [text for text in layout.scalars_of(node=job) if GITLAB_FORGE_MENTION.search(text)]
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
    references = GITLAB_SECRET_REFERENCE.findall(layout.WORKFLOW.read_text(encoding=layout.SOURCE_ENCODING))
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
    assert isinstance(secret, str) and GITLAB_SECRET_EXPRESSION.match(secret), (
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
        if command != GITLAB_CREDENTIAL_COMMAND and not layout.INSTALL_COMMAND.match(command)
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
    openings = [heading for heading in headings[1:] if GITLAB_WORD.search(heading.title)]
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
    missing += [item for pattern, item in patterns if pattern.search(prose) is None]
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
        (GITLAB_FORGE_JOB_MENTION.search(prose) is not None, f"the CI job `{JOB_FORGE_GITLAB}`"),
    )
    missing = [item for present, item in checks if not present]
    assert not missing, f"{layout.LLM_MAP_NAME} does not name: {missing}"
