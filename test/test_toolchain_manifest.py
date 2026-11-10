"""The committed toolchain-manifest tool: a promotion regenerates config/toolchain.json from the release itself.

`scripts/toolchain_manifest.py` lists the release with git (the installable trees at the release tag), maps each
source to its install path, leaves out what `not_installed` names, and carries `deviations` and `not_installed`
forward, dropping an entry whose path the release no longer contains. Its derivation is a pure function
(`derive`), tested here on synthetic release lists; the CLI is tested against the real release tag, which the
tests read from the committed manifest's own `release_tag` and `installed`, never from a hard-coded tag. The step
that runs it is named in `prompts/update.txt` (`## Task` step 7) and in the map, `docs/forLLMConsumption.md`.

Synthetic source paths name files that exist in this repository or carry a `<...>` placeholder: the layout guard
(test/test_layout.py) resolves every framework path a tracked file names.

Run: ``python scripts/run_tests.py test/test_toolchain_manifest.py`` (needs git and the release tag: CI checks out
with fetch-depth 0).
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "toolchain_manifest.py"
MODULE_NAME = "toolchain_manifest"
COMMITTED = ROOT / "config" / "toolchain.json"
UPDATE_PROMPT = ROOT / "prompts" / "update.txt"
MAP = ROOT / "docs" / "forLLMConsumption.md"

KEY_COMMENT = "comment"
KEY_RELEASE_TAG = "release_tag"
KEY_INSTALLED = "installed"
KEY_FILES = "files"
KEY_DEVIATIONS = "deviations"
KEY_NOT_INSTALLED = "not_installed"

FLAG_RELEASE = "--release"
FLAG_INSTALLED = "--installed"
FLAG_MANIFEST = "--manifest"
FLAG_CHECK = "--check"

EXIT_OK = 0
EXIT_DIFFERS = 1
EXIT_TOOL_ERROR = 2

PREVIOUS_TAG = "v2026.01.05"
PREVIOUS_DATE = "2026-01-05"
NEW_TAG = "v2026.12.24"
NEW_DATE = "2026-12-24"
REASON = "a reason this source is not installed here"
ABSENT_TAG = "v0000.00.00"

# One source per row of the install layout (change.md AC-2), nested paths included: (source, install path).
MAPPING = (
    ("clients/claude/agents/spec-author.md", ".claude/agents/spec-author.md"),
    ("clients/claude/commands/auto-work.md", ".claude/commands/auto-work.md"),
    ("clients/claude/docs/run-identity.md", ".claude/docs/run-identity.md"),
    ("clients/claude/rules/proportionality.md", ".claude/rules/proportionality.md"),
    ("clients/claude/rules/<sub>/<f>.md", ".claude/rules/<sub>/<f>.md"),
    ("clients/common/docs/delivery.md", ".claude/docs/delivery.md"),
    ("clients/common/phases/spec-phase-design.md", ".claude/specs/_workflow/phases/spec-phase-design.md"),
    ("src/hooks/hooklib.py", ".claude/hooks/hooklib.py"),
    ("src/hooks/tests/conftest.py", ".claude/hooks/tests/conftest.py"),
    ("src/payload/scripts/run_tests.py", "scripts/run_tests.py"),
    ("src/payload/test/test_instruction_corpus_budget.py", "test/test_instruction_corpus_budget.py"),
    ("templates/githooks/pre-commit", ".githooks/pre-commit"),
    ("templates/docs/codebuild-ci-backup-mechanism.md", "docs/codebuild-ci-backup-mechanism.md"),
    ("templates/setup-hooks.sh.template", "scripts/setup-hooks.sh"),
)
CI_TEMPLATES = ("templates/ci/github-deploy.yml.template", "templates/ci/github-merge-steward.yml.template")
CI_PATTERN = "templates/ci/*"
CONFIG_PATTERN = "templates/config/*"
MERGE_STEWARD = "src/payload/scripts/merge_steward.py"
KIRO_HOOKS = "src/hooks/kiro_hooks.py"
GITLAB_WRAPPER = "src/payload/scripts/gitlab_wrapper.py"
GITHUB_WRAPPER_SOURCE = "src/payload/scripts/github_wrapper.py"
GITHUB_WRAPPER_INSTALLED = "scripts/github_wrapper.py"
RUN_TESTS_SOURCE = "src/payload/scripts/run_tests.py"
RUN_TESTS_INSTALLED = "scripts/run_tests.py"
HOOKLIB_SOURCE = "src/hooks/hooklib.py"
HOOKLIB_INSTALLED = ".claude/hooks/hooklib.py"
SPEC_AUTHOR_SOURCE = "clients/claude/agents/spec-author.md"
SPEC_AUTHOR_INSTALLED = ".claude/agents/spec-author.md"
RETIRED_SOURCE = "clients/claude/agents/<retired>.md"
RETIRED_INSTALLED = ".claude/agents/<retired>.md"
UNMAPPED_README = "clients/claude/README.md"
# Release sources under an installable tree that no row of the layout maps.
UNMAPPED = (UNMAPPED_README, "templates/README.md", "templates/pre-commit-config.yaml.template")
# Two sources whose install paths coincide.
COLLISIONS = (
    ("clients/claude/docs/<same>.md", "clients/common/docs/<same>.md"),
    ("src/payload/docs/<same>.md", "templates/docs/<same>.md"),
)


@pytest.fixture(scope="module")
def tool() -> Iterator[ModuleType]:
    """The committed tool, loaded from its file; while it is absent, every test that needs it fails here."""
    assert SCRIPT.is_file(), f"the manifest tool {SCRIPT.relative_to(ROOT).as_posix()} is not committed"
    spec = importlib.util.spec_from_file_location(name=MODULE_NAME, location=SCRIPT)
    assert spec is not None and spec.loader is not None, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module=module)
    yield module
    sys.modules.pop(MODULE_NAME, None)


def previous_manifest(
    files: dict[str, str] | None = None,
    deviations: dict[str, str] | None = None,
    not_installed: dict[str, str] | None = None,
) -> dict:
    """A synthetic previous manifest with the committed manifest's top-level keys in their committed order."""
    return {
        KEY_COMMENT: "A synthetic manifest.",
        KEY_RELEASE_TAG: PREVIOUS_TAG,
        KEY_INSTALLED: PREVIOUS_DATE,
        KEY_FILES: dict(files or {}),
        KEY_DEVIATIONS: dict(deviations or {}),
        KEY_NOT_INSTALLED: dict(not_installed or {}),
    }


def normalised(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def committed_manifest() -> dict:
    return json.loads(COMMITTED.read_text(encoding="utf-8"))


def serialised(manifest: dict) -> bytes:
    """The written form of change.md AC-4: UTF-8, indent 2, no ASCII escaping, one trailing LF."""
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def run_tool(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def described(result: subprocess.CompletedProcess[str]) -> str:
    return f"exit {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def committed_arguments(manifest_path: Path) -> list[str]:
    """`--release` and `--installed` as the committed manifest records them, on the given manifest file."""
    committed = committed_manifest()
    return [
        FLAG_RELEASE,
        committed[KEY_RELEASE_TAG],
        FLAG_INSTALLED,
        committed[KEY_INSTALLED],
        FLAG_MANIFEST,
        str(manifest_path),
    ]


def section(text: str, heading: str) -> str:
    """The body of a `## ` section of a Markdown-like document, line endings normalised."""
    text = text.replace("\r\n", "\n")
    start = text.find(f"\n{heading}\n")
    assert start != -1, f"no `{heading}` section"
    end = text.find("\n## ", start + len(heading) + 2)
    return text[start:] if end == -1 else text[start:end]


def one_line(text: str) -> str:
    return " ".join(text.split())


# --- AC-1: the promotion's manifest step is named, and the derivation records the release -----------------------


def test_update_step_7_names_the_toolchain_manifest_step() -> None:
    task = section(text=UPDATE_PROMPT.read_text(encoding="utf-8"), heading="## Task")
    match = re.search(r"^7\. (.*?)^8\. ", task, flags=re.MULTILINE | re.DOTALL)
    assert match is not None, "`## Task` has no step 7 followed by a step 8"
    step = one_line(text=match.group(1))
    assert "toolchain manifest" in step.lower(), f"step 7 does not name the toolchain manifest: {step}"
    assert "forLLMConsumption.md" in step, f"step 7 does not point at the map's command: {step}"


def test_the_map_names_the_manifest_command_of_the_promotion() -> None:
    halves = one_line(text=section(text=MAP.read_text(encoding="utf-8"), heading="## Two halves (read this first)"))
    assert "scripts/toolchain_manifest.py --release" in halves, (
        "`## Two halves (read this first)` does not name `python scripts/toolchain_manifest.py --release <tag>`"
    )


def test_the_derivation_sets_the_release_tag_and_the_installed_date(tool: ModuleType) -> None:
    manifest, _ = tool.derive(
        release_paths=[RUN_TESTS_SOURCE], previous=previous_manifest(), release_tag=NEW_TAG, installed=NEW_DATE
    )
    assert manifest[KEY_RELEASE_TAG] == NEW_TAG
    assert manifest[KEY_INSTALLED] == NEW_DATE


# --- AC-2: the install layout, the exclusions, the refusals and the report -----------------------------------------


@pytest.mark.parametrize(("source", "installed"), MAPPING, ids=[source for source, _ in MAPPING])
def test_a_release_source_lands_at_its_install_path(tool: ModuleType, source: str, installed: str) -> None:
    manifest, _ = tool.derive(
        release_paths=[source], previous=previous_manifest(), release_tag=NEW_TAG, installed=NEW_DATE
    )
    assert manifest[KEY_FILES] == {installed: source}


def test_files_are_sorted_by_install_path_and_named_sources_are_left_out(tool: ModuleType) -> None:
    release = [source for source, _ in reversed(MAPPING)] + [*CI_TEMPLATES, MERGE_STEWARD]
    previous = previous_manifest(not_installed={MERGE_STEWARD: REASON, CI_PATTERN: REASON})
    manifest, _ = tool.derive(release_paths=release, previous=previous, release_tag=NEW_TAG, installed=NEW_DATE)
    expected = {installed: source for source, installed in MAPPING}
    assert manifest[KEY_FILES] == expected, "templates/ci/* and the named exact source must not be installed"
    assert list(manifest[KEY_FILES]) == sorted(expected), "files must be sorted by install path"


@pytest.mark.parametrize("source", UNMAPPED)
def test_an_unmapped_source_without_a_not_installed_entry_raises_naming_it(tool: ModuleType, source: str) -> None:
    with pytest.raises(tool.ManifestError) as raised:
        tool.derive(
            release_paths=[RUN_TESTS_SOURCE, source],
            previous=previous_manifest(),
            release_tag=NEW_TAG,
            installed=NEW_DATE,
        )
    assert source in str(raised.value)


@pytest.mark.parametrize(("first", "second"), COLLISIONS, ids=[first for first, _ in COLLISIONS])
def test_two_sources_of_one_install_path_raise_naming_both(tool: ModuleType, first: str, second: str) -> None:
    with pytest.raises(tool.ManifestError) as raised:
        tool.derive(
            release_paths=[first, second], previous=previous_manifest(), release_tag=NEW_TAG, installed=NEW_DATE
        )
    assert first in str(raised.value) and second in str(raised.value)


def test_added_and_removed_files_entries_are_reported(tool: ModuleType) -> None:
    previous = previous_manifest(files={HOOKLIB_INSTALLED: HOOKLIB_SOURCE, RETIRED_INSTALLED: RETIRED_SOURCE})
    manifest, report = tool.derive(
        release_paths=[HOOKLIB_SOURCE, SPEC_AUTHOR_SOURCE], previous=previous, release_tag=NEW_TAG, installed=NEW_DATE
    )
    assert manifest[KEY_FILES] == {HOOKLIB_INSTALLED: HOOKLIB_SOURCE, SPEC_AUTHOR_INSTALLED: SPEC_AUTHOR_SOURCE}
    assert list(report.added) == [SPEC_AUTHOR_INSTALLED]
    assert list(report.removed) == [RETIRED_INSTALLED]


# --- AC-3: no uncommitted tooling ---------------------------------------------------------------------------------


def test_the_tool_imports_only_the_standard_library(tool: ModuleType) -> None:
    tree = ast.parse(source=Path(tool.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module, "absolute imports only"
            imported.add(node.module.split(".")[0])
    outside = sorted(imported - set(sys.stdlib_module_names))
    assert imported and not outside, f"imports outside the standard library: {outside}"


# --- AC-4: the regeneration reproduces the committed manifest, in the committed form -------------------------------


def test_top_level_keys_keep_their_order_and_other_keys_are_verbatim(tool: ModuleType) -> None:
    previous = {
        KEY_COMMENT: "Kept verbatim — including this.",
        KEY_RELEASE_TAG: PREVIOUS_TAG,
        "notes": {"kept": ["as", "it", "is"]},
        KEY_INSTALLED: PREVIOUS_DATE,
        KEY_FILES: {},
        KEY_DEVIATIONS: {},
        KEY_NOT_INSTALLED: {},
    }
    manifest, _ = tool.derive(
        release_paths=[RUN_TESTS_SOURCE], previous=previous, release_tag=NEW_TAG, installed=NEW_DATE
    )
    assert list(manifest) == list(previous)
    assert manifest[KEY_COMMENT] == previous[KEY_COMMENT]
    assert manifest["notes"] == previous["notes"]


@pytest.mark.usefixtures("tool")
def test_regenerating_the_committed_manifest_reproduces_it(tmp_path: Path) -> None:
    committed = COMMITTED.read_bytes()
    copy = tmp_path / "toolchain.json"
    # A CRLF copy, as a core.autocrlf checkout holds it: the tool must write it back in LF.
    copy.write_bytes(normalised(committed).replace(b"\n", b"\r\n"))
    result = run_tool(arguments=committed_arguments(manifest_path=copy))
    assert result.returncode == EXIT_OK, described(result=result)
    written = copy.read_bytes()
    assert b"\r" not in written, "the manifest is written with LF line endings"
    assert json.loads(written.decode("utf-8")) == json.loads(committed.decode("utf-8"))
    assert normalised(written) == normalised(committed)


@pytest.mark.usefixtures("tool")
def test_the_written_form_is_utf8_with_two_space_indent_and_one_newline(tmp_path: Path) -> None:
    manifest = committed_manifest()
    manifest[KEY_COMMENT] = manifest[KEY_COMMENT] + " Non-ASCII text stays as written: — ü."
    copy = tmp_path / "toolchain.json"
    copy.write_text(json.dumps(manifest, indent=4) + "\n\n", encoding="utf-8")
    result = run_tool(arguments=committed_arguments(manifest_path=copy))
    assert result.returncode == EXIT_OK, described(result=result)
    assert copy.read_bytes() == serialised(manifest=manifest)


@pytest.mark.usefixtures("tool")
def test_the_installed_date_defaults_to_today(tmp_path: Path) -> None:
    copy = tmp_path / "toolchain.json"
    copy.write_bytes(COMMITTED.read_bytes())
    tag = committed_manifest()[KEY_RELEASE_TAG]
    before = date.today().isoformat()
    result = run_tool(arguments=[FLAG_RELEASE, tag, FLAG_MANIFEST, str(copy)])
    after = date.today().isoformat()
    assert result.returncode == EXIT_OK, described(result=result)
    written = json.loads(copy.read_text(encoding="utf-8"))
    assert written[KEY_RELEASE_TAG] == tag
    assert written[KEY_INSTALLED] in {before, after}


# --- AC-5: --check writes nothing and reports by its exit code ----------------------------------------------------


@pytest.mark.usefixtures("tool")
def test_check_on_the_committed_manifest_exits_zero_and_writes_nothing() -> None:
    committed = committed_manifest()
    before = COMMITTED.read_bytes()
    try:
        result = run_tool(
            arguments=[FLAG_RELEASE, committed[KEY_RELEASE_TAG], FLAG_INSTALLED, committed[KEY_INSTALLED], FLAG_CHECK]
        )
    finally:
        after = COMMITTED.read_bytes()
        if after != before:  # never leave the checkout dirty, whatever the tool did
            COMMITTED.write_bytes(before)
    assert after == before, "--check must not write the manifest"
    assert result.returncode == EXIT_OK, described(result=result)


@pytest.mark.usefixtures("tool")
def test_check_with_a_later_date_exits_one_and_writes_nothing(tmp_path: Path) -> None:
    copy = tmp_path / "toolchain.json"
    original = COMMITTED.read_bytes()
    copy.write_bytes(original)
    committed = committed_manifest()
    later = (date.fromisoformat(committed[KEY_INSTALLED]) + timedelta(days=1)).isoformat()
    result = run_tool(
        arguments=[
            FLAG_RELEASE,
            committed[KEY_RELEASE_TAG],
            FLAG_INSTALLED,
            later,
            FLAG_MANIFEST,
            str(copy),
            FLAG_CHECK,
        ]
    )
    assert result.returncode == EXIT_DIFFERS, described(result=result)
    assert copy.read_bytes() == original, "--check must not write the manifest"


# --- AC-2 and the exit codes: a tool error exits 2 and writes nothing ----------------------------------------------


@pytest.mark.usefixtures("tool")
def test_an_unmapped_release_source_exits_two_naming_it_and_writes_nothing(tmp_path: Path) -> None:
    manifest = committed_manifest()
    assert UNMAPPED_README in manifest[KEY_NOT_INSTALLED], f"the committed manifest names {UNMAPPED_README}"
    del manifest[KEY_NOT_INSTALLED][UNMAPPED_README]
    copy = tmp_path / "toolchain.json"
    original = serialised(manifest=manifest)
    copy.write_bytes(original)
    result = run_tool(arguments=committed_arguments(manifest_path=copy))
    assert result.returncode == EXIT_TOOL_ERROR, described(result=result)
    assert UNMAPPED_README in result.stdout + result.stderr, described(result=result)
    assert copy.read_bytes() == original, "a refused regeneration writes nothing"


@pytest.mark.usefixtures("tool")
def test_an_unknown_release_tag_exits_two_and_writes_nothing(tmp_path: Path) -> None:
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{ABSENT_TAG}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert probe.returncode != 0, f"{ABSENT_TAG} must not be a tag of this clone"
    copy = tmp_path / "toolchain.json"
    original = COMMITTED.read_bytes()
    copy.write_bytes(original)
    result = run_tool(arguments=[FLAG_RELEASE, ABSENT_TAG, FLAG_INSTALLED, NEW_DATE, FLAG_MANIFEST, str(copy)])
    assert result.returncode == EXIT_TOOL_ERROR, described(result=result)
    assert copy.read_bytes() == original, "a failed git listing writes nothing"


# --- UB-2: deviations and not_installed survive unless the release no longer has their path ------------------------


def test_entries_whose_path_left_the_release_are_dropped_and_reported(tool: ModuleType) -> None:
    deviation = "the installed copy deliberately differs from its source"
    previous = previous_manifest(
        files={
            GITHUB_WRAPPER_INSTALLED: GITHUB_WRAPPER_SOURCE,
            HOOKLIB_INSTALLED: HOOKLIB_SOURCE,
            RUN_TESTS_INSTALLED: RUN_TESTS_SOURCE,
        },
        deviations={
            GITHUB_WRAPPER_INSTALLED: deviation + " (first)",
            HOOKLIB_INSTALLED: deviation + " (dropped)",
            RUN_TESTS_INSTALLED: deviation + " (last)",
        },
        not_installed={
            KIRO_HOOKS: REASON + " (first)",
            MERGE_STEWARD: REASON + " (exact, dropped)",
            CI_PATTERN: REASON + " (pattern, kept)",
            CONFIG_PATTERN: REASON + " (pattern, dropped)",
            GITLAB_WRAPPER: REASON + " (last)",
        },
    )
    release = [GITHUB_WRAPPER_SOURCE, RUN_TESTS_SOURCE, KIRO_HOOKS, CI_TEMPLATES[0], GITLAB_WRAPPER]
    manifest, report = tool.derive(release_paths=release, previous=previous, release_tag=NEW_TAG, installed=NEW_DATE)
    assert list(manifest[KEY_DEVIATIONS].items()) == [
        (GITHUB_WRAPPER_INSTALLED, deviation + " (first)"),
        (RUN_TESTS_INSTALLED, deviation + " (last)"),
    ]
    assert list(manifest[KEY_NOT_INSTALLED].items()) == [
        (KIRO_HOOKS, REASON + " (first)"),
        (CI_PATTERN, REASON + " (pattern, kept)"),
        (GITLAB_WRAPPER, REASON + " (last)"),
    ]
    assert set(report.dropped) == {HOOKLIB_INSTALLED, MERGE_STEWARD, CONFIG_PATTERN}
