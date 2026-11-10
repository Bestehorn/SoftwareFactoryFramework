"""The setup prompts install the GitLab wrapper's entry script together with its `gitlab_api/` package.

Design D2 (install path) ships the GitLab wrapper as the entry script `src/payload/scripts/gitlab_wrapper.py` plus the
package `src/payload/scripts/gitlab_api/` that the entry script imports (D3), both copied into a project's `scripts/`,
and callers keep invoking `scripts/gitlab_wrapper.py` (UB-1). So the GitLab copy step of each setup prompt
(`setup-claude` Part 5.3, `setup-kiro` Part 6.2) names both sources, the copy instruction in it that copies the entry
script copies the package too, and each prompt's "Shipped Python" list names `scripts/gitlab_api/` beside
`scripts/gitlab_wrapper.py`.

A section is the text from its heading in column 1 to the next `###` heading (a `##` heading ends it too), as
`test/test_setup_prompts_gitignore.py` cuts PART 3. A path counts only where no path character adjoins it, so the
`scripts/gitlab_api/` inside `src/payload/scripts/gitlab_api/` does not satisfy a list.

The copy instruction is the unit of the copy step that copies the entry script, in the prompt's own wording: in
`setup-claude.txt` the sentence `copy `<source>` to `<destination>` and …`, in `setup-kiro.txt` the GitLab top-level
bullet whose nested bullets read `` `<destination>`: copy from `<source>` ``. The package must be copied in that same
unit, so a pointer to the package elsewhere in the copy step does not stand in for the copy. The GitHub wrapper's
paths are not checked here.

Run: ``python scripts/run_tests.py test/test_setup_prompts_gitlab_wrapper.py``.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
PROMPT_SUFFIX = ".txt"
SETUP_CLAUDE = "setup-claude"
SETUP_KIRO = "setup-kiro"

CLAUDE_COPY_STEP = "### Part 5.3 — Git repository wrapper scripts"
KIRO_COPY_STEP = "### Part 6.2 — Stub credentials and wrappers"
CLAUDE_SHIPPED_PYTHON = (
    "### Shipped Python (shared with the Kiro prompt, under src/payload/, laid out like the project)"
)
KIRO_SHIPPED_PYTHON = "### Shipped Python referenced by this prompt"
SECTION_END = re.compile(pattern=r"^###? ", flags=re.MULTILINE)

PARAGRAPH_BOUNDARY = re.compile(pattern=r"\n[ \t]*\n")
SENTENCE_BOUNDARY = re.compile(pattern=r"(?<=[.!?])\s+")
TOP_LEVEL_BLOCK_BOUNDARY = re.compile(pattern=r"\n[ \t]*\n|\n(?=- )")
COPY_VERB = re.compile(pattern=r"\bcopy\b", flags=re.IGNORECASE)
WHITESPACE_RUN = re.compile(pattern=r"\s+")
SENTENCE = "sentence"
TOP_LEVEL_BULLET = "top-level bullet"

SOURCE_ENTRY = "src/payload/scripts/gitlab_wrapper.py"
SOURCE_PACKAGE = "src/payload/scripts/gitlab_api/"
INSTALLED_ENTRY = "scripts/gitlab_wrapper.py"
INSTALLED_PACKAGE = "scripts/gitlab_api/"
COPY_STEP_PATHS = (SOURCE_PACKAGE, SOURCE_ENTRY)
SHIPPED_PYTHON_PATHS = (INSTALLED_PACKAGE, INSTALLED_ENTRY)
NO_PATH_CHARACTER_BEFORE = r"(?<![\w./-])"
NO_PATH_CHARACTER_AFTER = r"(?![\w-])"


@dataclass(frozen=True)
class PromptSection:
    """One section of one setup prompt and the GitLab wrapper paths it must name."""

    prompt: str
    heading: str
    paths: tuple[str, ...]

    @property
    def prompt_file(self) -> str:
        return f"{self.prompt}{PROMPT_SUFFIX}"

    def text(self) -> str:
        """The text from this section's heading (column 1, the whole line) to the next `###` or `##` heading."""
        prompt_text = (PROMPTS_DIR / self.prompt_file).read_text(encoding="utf-8")
        heading_line = re.compile(pattern=rf"^{re.escape(pattern=self.heading)}[ \t]*$", flags=re.MULTILINE)
        heading = heading_line.search(string=prompt_text)
        assert heading is not None, f"{self.prompt_file}: no `{self.heading}` heading in column 1"
        following = SECTION_END.search(string=prompt_text, pos=heading.end())
        return prompt_text[heading.start() : len(prompt_text) if following is None else following.start()]

    def missing(self) -> list[str]:
        """One failure line per path the section does not name."""
        section_text = self.text()
        return [
            f"{self.prompt_file}, section `{self.heading}`: does not name `{path}`"
            for path in self.paths
            if not self._names(section_text=section_text, path=path)
        ]

    @staticmethod
    def _names(section_text: str, path: str) -> bool:
        """Whether the section names the path with no path character adjoining it on either side."""
        pattern = rf"{NO_PATH_CHARACTER_BEFORE}{re.escape(pattern=path)}{NO_PATH_CHARACTER_AFTER}"
        return re.search(pattern=pattern, string=section_text) is not None


@dataclass(frozen=True)
class CopyInstruction(ABC):
    """A prompt's GitLab copy instruction: the copy-step unit copying the entry script copies the package."""

    section: PromptSection

    @property
    @abstractmethod
    def unit_kind(self) -> str:
        """What one unit of this prompt's copy step is called in a failure message."""

    @abstractmethod
    def units(self) -> list[str]:
        """The copy step cut into the units this prompt writes one copy instruction in."""

    @abstractmethod
    def copy_phrase(self, source: str, destination: str) -> re.Pattern[str]:
        """The phrase that, in this prompt's wording, copies `source` to `destination`."""

    def gaps(self) -> list[str]:
        """One line per copy instruction that copies the entry script without the package, or none copies it at all."""
        entry_copy = self.copy_phrase(source=SOURCE_ENTRY, destination=INSTALLED_ENTRY)
        package_copy = self.copy_phrase(source=SOURCE_PACKAGE, destination=INSTALLED_PACKAGE)
        entry_units = [unit for unit in self.units() if entry_copy.search(string=unit) is not None]
        where = f"{self.section.prompt_file}, section `{self.section.heading}`"
        entry_copied = f"copies `{SOURCE_ENTRY}` to `{INSTALLED_ENTRY}`"
        if not entry_units:
            return [f"{where}: has no {self.unit_kind} that {entry_copied}"]
        return [
            f"{where}: the {self.unit_kind} that {entry_copied} does not copy `{SOURCE_PACKAGE}` to "
            f"`{INSTALLED_PACKAGE}`: {WHITESPACE_RUN.sub(repl=' ', string=unit).strip()}"
            for unit in entry_units
            if package_copy.search(string=unit) is None
        ]


class SentenceCopyInstruction(CopyInstruction):
    """A copy step written as prose (`setup-claude.txt`): one sentence `copy `<source>` to `<destination>` and …`."""

    @property
    def unit_kind(self) -> str:
        return SENTENCE

    def units(self) -> list[str]:
        """The copy step's sentences that use the verb `copy`; a sentence never spans two paragraphs."""
        return [
            sentence
            for paragraph in PARAGRAPH_BOUNDARY.split(string=self.section.text())
            for sentence in SENTENCE_BOUNDARY.split(string=paragraph)
            if COPY_VERB.search(string=sentence) is not None
        ]

    def copy_phrase(self, source: str, destination: str) -> re.Pattern[str]:
        return re.compile(pattern=rf"`{re.escape(pattern=source)}`\s+to\s+`{re.escape(pattern=destination)}`")


class BulletCopyInstruction(CopyInstruction):
    """A copy step written as a list (`setup-kiro.txt`): a host's top-level bullet, a nested bullet per copied path."""

    @property
    def unit_kind(self) -> str:
        return TOP_LEVEL_BULLET

    def units(self) -> list[str]:
        """The copy step's paragraphs and top-level bullets, each top-level bullet with its nested bullets."""
        return TOP_LEVEL_BLOCK_BOUNDARY.split(string=self.section.text())

    def copy_phrase(self, source: str, destination: str) -> re.Pattern[str]:
        return re.compile(pattern=rf"`{re.escape(pattern=destination)}`:\s+copy\s+from\s+`{re.escape(pattern=source)}`")


CLAUDE_COPY_SECTION = PromptSection(prompt=SETUP_CLAUDE, heading=CLAUDE_COPY_STEP, paths=COPY_STEP_PATHS)
KIRO_COPY_SECTION = PromptSection(prompt=SETUP_KIRO, heading=KIRO_COPY_STEP, paths=COPY_STEP_PATHS)

SECTIONS = (
    CLAUDE_COPY_SECTION,
    KIRO_COPY_SECTION,
    PromptSection(prompt=SETUP_CLAUDE, heading=CLAUDE_SHIPPED_PYTHON, paths=SHIPPED_PYTHON_PATHS),
    PromptSection(prompt=SETUP_KIRO, heading=KIRO_SHIPPED_PYTHON, paths=SHIPPED_PYTHON_PATHS),
)

COPY_INSTRUCTIONS = (
    SentenceCopyInstruction(section=CLAUDE_COPY_SECTION),
    BulletCopyInstruction(section=KIRO_COPY_SECTION),
)


def test_both_prompts_copy_the_package_with_the_entry() -> None:
    """UB-1: each GitLab copy instruction copies `gitlab_api/` with the entry script, and each section names both."""
    instruction_gaps = [gap for instruction in COPY_INSTRUCTIONS for gap in instruction.gaps()]
    section_gaps = [line for section in SECTIONS for line in section.missing()]
    gaps = instruction_gaps + section_gaps
    assert not gaps, (
        "the setup prompts do not install the GitLab wrapper's package with its entry script:\n" + "\n".join(gaps)
    )
