"""PART 3 of each setup prompt recommends a `.gitignore` that ignores the root-only directories at the root only.

A gitignore pattern with no slash at its beginning or middle also matches at any level below the `.gitignore`
(gitignore(5), PATTERN FORMAT): a recommended `reports/` also ignores a project's `docs/reports/`, and the Kiro
standard's `lib/` also ignores a TypeScript CDK app's `cdk/lib/` source. So the prompts recommend the anchored form
(`/reports/`, `/lib/`), tell an existing project to replace the slash-free one, and keep the directories that are
generated at any level (`build/`, `tmp/`) slash-free. The section is the text from the `## PART 3 — .gitignore`
heading to the next `## PART` heading, the block is its first fenced block, and the probes apply that block to a
scratch repository and ask git itself which paths it ignores (git-check-ignore(1), EXIT STATUS).

Run: ``python scripts/run_tests.py test/test_setup_prompts_gitignore.py`` (needs git on PATH).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
PROMPT_SUFFIX = ".txt"
SETUP_CLAUDE = "setup-claude"
SETUP_KIRO = "setup-kiro"
SETUP_PROMPTS = (SETUP_CLAUDE, SETUP_KIRO)

PART_3_TITLE = "## PART 3 — .gitignore"
PART_3_HEADING = re.compile(rf"^{re.escape(PART_3_TITLE)}[ \t]*$", re.MULTILINE)
NEXT_PART_HEADING = re.compile(r"^## PART ", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^```[^\n]*\n(?P<body>.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
FENCED_BODY = "body"
COMMENT_PREFIX = "#"
ANCHOR = "/"

ANCHORED_REPORTS = "/reports/"
ANCHORED_LIB = "/lib/"
ANCHORED_PACKAGING_DIRS = (
    ANCHORED_LIB,
    "/lib64/",
    "/var/",
    "/downloads/",
    "/eggs/",
    "/develop-eggs/",
    "/parts/",
    "/sdist/",
    "/wheels/",
)
SLASH_FREE_GENERATED_DIRS = ("build/", "dist/", "venv/", ".venv/", "tmp/")
REPLACE_WORD = "REPLACED"
ADD_ONLY_MISSING = "Read existing entries, add only those"
# Built from its parts, so test/test_layout.py does not read this module as naming a missing framework path.
DOCS_REPORTS_DIR = Path("docs", "reports").as_posix() + "/"
DOCS_REPORT_PROBE = Path("docs", "reports", "x.md").as_posix()
CDK_LIB_DIR = "cdk/lib/"
JUNIT_PROBE = "reports/junit.xml"
CHECKS_PROBE = "reports/checks-lint.json"

GIT_EXIT_OK = 0
CHECK_IGNORE_IGNORED = 0
CHECK_IGNORE_NOT_IGNORED = 1
IGNORED = True
NOT_IGNORED = False

# (prompt, probe, expected verdict): the AC-5 probes, the root-report probes of UB-1 and the nested generated
# directories of UB-3.
IGNORE_PROBES = (
    (SETUP_CLAUDE, JUNIT_PROBE, IGNORED),
    (SETUP_CLAUDE, CHECKS_PROBE, IGNORED),
    (SETUP_CLAUDE, DOCS_REPORT_PROBE, NOT_IGNORED),
    (SETUP_KIRO, JUNIT_PROBE, IGNORED),
    (SETUP_KIRO, CHECKS_PROBE, IGNORED),
    (SETUP_KIRO, DOCS_REPORT_PROBE, NOT_IGNORED),
    (SETUP_KIRO, "lib/x.py", IGNORED),
    (SETUP_KIRO, "cdk/lib/stack.ts", NOT_IGNORED),
    (SETUP_KIRO, "frontend/build/x.js", IGNORED),
    (SETUP_KIRO, "tmp/x", IGNORED),
)


@dataclass(frozen=True)
class GitignoreSection:
    """One prompt's PART 3 section: its whole text, its first fenced block, and the prose outside that block."""

    prompt: str
    text: str
    block: str
    prose: str

    @classmethod
    def load(cls, prompt: str) -> GitignoreSection:
        text = (PROMPTS_DIR / f"{prompt}{PROMPT_SUFFIX}").read_text(encoding="utf-8")
        heading = PART_3_HEADING.search(string=text)
        assert heading is not None, f"{prompt}{PROMPT_SUFFIX} has no `{PART_3_TITLE}` heading in column 1"
        following = NEXT_PART_HEADING.search(string=text, pos=heading.end())
        section = text[heading.start() : len(text) if following is None else following.start()]
        fence = FENCED_BLOCK.search(string=section)
        assert fence is not None, f"{prompt}{PROMPT_SUFFIX}: the `{PART_3_TITLE}` section has no fenced block"
        return cls(
            prompt=prompt,
            text=section,
            block=fence.group(FENCED_BODY),
            prose=section[: fence.start()] + section[fence.end() :],
        )

    @property
    def block_lines(self) -> list[str]:
        return [line.strip() for line in self.block.splitlines()]

    @property
    def comment_lines(self) -> list[str]:
        return [line for line in self.block_lines if line.startswith(COMMENT_PREFIX)]

    @property
    def flat_text(self) -> str:
        """The section with every run of whitespace, line breaks included, collapsed to one space."""
        return " ".join(self.text.split())


class ScratchRepository:
    """A `git init` repository under pytest's tmp_path whose `.gitignore` is the given text.

    Every git call names an empty `core.excludesFile`, so a developer's global ignore file cannot decide a verdict.
    """

    def __init__(self, parent: Path, gitignore: str) -> None:
        self.path = parent / "repo"
        self.path.mkdir()
        self._excludes_file = parent / "empty-global-excludes"
        self._excludes_file.write_bytes(b"")
        self._git(arguments=["init", "--quiet"], accepted=(GIT_EXIT_OK,))
        (self.path / ".gitignore").write_bytes(gitignore.encode("utf-8"))

    def is_ignored(self, probe: str) -> bool:
        """`git check-ignore --no-index -q`: exit 0 is ignored, exit 1 is not, any other exit fails the test."""
        result = self._git(
            arguments=["check-ignore", "--no-index", "-q", probe],
            accepted=(CHECK_IGNORE_IGNORED, CHECK_IGNORE_NOT_IGNORED),
        )
        return result.returncode == CHECK_IGNORE_IGNORED

    def _git(self, arguments: list[str], accepted: tuple[int, ...]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args=["git", "-c", f"core.excludesFile={self._excludes_file.as_posix()}", *arguments],
            cwd=self.path,
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
        )
        if result.returncode not in accepted:
            pytest.fail(f"`git {' '.join(arguments)}` exited {result.returncode}: {result.stderr.strip()}")
        return result


def _slash_free(entry: str) -> str:
    return entry.lstrip(ANCHOR)


def _verdict(ignored: bool) -> str:
    return "ignored" if ignored else "not-ignored"


@pytest.mark.parametrize("prompt", SETUP_PROMPTS)
def test_reports_line_is_anchored_with_its_comment(prompt: str) -> None:
    """AC-1 (setup-claude), AC-2 (setup-kiro): the block lists `/reports/`, no `reports/`, and says why."""
    section = GitignoreSection.load(prompt=prompt)
    lines = section.block_lines
    assert ANCHORED_REPORTS in lines, f"{prompt}: the PART 3 block has no `{ANCHORED_REPORTS}` line"
    slash_free = _slash_free(entry=ANCHORED_REPORTS)
    assert slash_free not in lines, (
        f"{prompt}: the PART 3 block still lists `{slash_free}`, which also ignores `{DOCS_REPORTS_DIR}`"
    )
    assert any(DOCS_REPORTS_DIR in line for line in section.comment_lines), (
        f"{prompt}: no comment line of the PART 3 block says the anchor keeps `{DOCS_REPORTS_DIR}` tracked"
    )


def test_root_only_packaging_dirs_are_anchored() -> None:
    """AC-3: the setup-kiro block anchors the root-only packaging directories and names `cdk/lib/` as the reason."""
    section = GitignoreSection.load(prompt=SETUP_KIRO)
    lines = section.block_lines
    missing = [entry for entry in ANCHORED_PACKAGING_DIRS if entry not in lines]
    assert not missing, f"{SETUP_KIRO}: the PART 3 block lacks the anchored lines {missing}"
    slash_free = [_slash_free(entry=entry) for entry in ANCHORED_PACKAGING_DIRS if _slash_free(entry=entry) in lines]
    assert not slash_free, f"{SETUP_KIRO}: the PART 3 block still lists the slash-free lines {slash_free}"
    assert any(CDK_LIB_DIR in line for line in section.comment_lines), (
        f"{SETUP_KIRO}: no comment line of the PART 3 block names `{CDK_LIB_DIR}` as the reason for the anchors"
    )


@pytest.mark.parametrize("prompt", SETUP_PROMPTS)
def test_section_says_to_replace_a_slash_free_entry(prompt: str) -> None:
    """AC-4: the prose outside the block tells an existing project to replace a slash-free line by the anchored one."""
    section = GitignoreSection.load(prompt=prompt)
    missing = [phrase for phrase in (REPLACE_WORD, ANCHORED_REPORTS, ANCHORED_LIB) if phrase not in section.prose]
    assert not missing, f"{prompt}: the PART 3 text outside the fenced block lacks {missing}"


@pytest.mark.parametrize(
    ("prompt", "probe", "expected"),
    [
        pytest.param(prompt, probe, expected, id=f"{prompt}:{probe}:{_verdict(ignored=expected)}")
        for prompt, probe, expected in IGNORE_PROBES
    ],
)
def test_applied_block_ignores_only_the_root_dirs(prompt: str, probe: str, expected: bool, tmp_path: Path) -> None:
    """AC-5, UB-1, UB-3: applied as a repository's `.gitignore`, the block gives git the expected verdict."""
    repository = ScratchRepository(parent=tmp_path, gitignore=GitignoreSection.load(prompt=prompt).block)
    actual = repository.is_ignored(probe=probe)
    assert actual is expected, (
        f"{prompt}: with the PART 3 block as `.gitignore`, git reports `{probe}` {_verdict(ignored=actual)}, "
        f"expected {_verdict(ignored=expected)}"
    )


@pytest.mark.parametrize("prompt", SETUP_PROMPTS)
def test_section_still_adds_only_missing_entries(prompt: str) -> None:
    """UB-2: every entry the block does not anchor is still added only when it is missing."""
    section = GitignoreSection.load(prompt=prompt)
    assert ADD_ONLY_MISSING in section.flat_text, f"{prompt}: the PART 3 section lacks `{ADD_ONLY_MISSING}`"


def test_generated_dirs_stay_slash_free() -> None:
    """UB-3: the setup-kiro block keeps the generated directories slash-free, so a nested one stays ignored."""
    section = GitignoreSection.load(prompt=SETUP_KIRO)
    missing = [entry for entry in SLASH_FREE_GENERATED_DIRS if entry not in section.block_lines]
    assert not missing, f"{SETUP_KIRO}: the PART 3 block lacks the slash-free lines {missing}"
