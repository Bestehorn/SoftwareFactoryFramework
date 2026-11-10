"""The setup prompts copy the GitHub wrapper's package with its entry script (UB-1.3, design D8).

The product wrapper `src/payload/scripts/github_wrapper.py` is a thin entry script that imports the package
`src/payload/scripts/github_api/` from its own directory, so a project set up with only the entry script copied gets a
wrapper that cannot start. Each setup prompt's GitHub copy instruction therefore copies the package beside the entry
script, each copy step names both, and each prompt's shipped-Python list names `scripts/github_api/` beside
`scripts/github_wrapper.py`.

The copy step is the text from the `### Part 5.3 — Git repository wrapper scripts` heading of `setup-claude.txt` and
from the `### Part 6.2 — Stub credentials and wrappers` heading of `setup-kiro.txt` to the next `### Part` heading;
the shipped-Python list is the text from its `### Shipped Python …` heading to the next `###` heading. Both are cut
the way `test/test_setup_prompts_gitignore.py` cuts PART 3.

The copy instruction is the unit of the copy step that copies the entry script, in the prompt's own wording: in
`setup-claude.txt` the sentence `copy `<source>` to `<destination>` and …`, in `setup-kiro.txt` the GitHub top-level
bullet whose nested bullets read `` `<destination>`: copy from `<source>` ``. The package must be copied in that same
unit, so a pointer to the package elsewhere in the copy step does not stand in for the copy.

Run: ``python scripts/run_tests.py test/test_setup_prompts_github_wrapper.py``
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

CLAUDE_COPY_STEP_TITLE = "### Part 5.3 — Git repository wrapper scripts"
KIRO_COPY_STEP_TITLE = "### Part 6.2 — Stub credentials and wrappers"
CLAUDE_SHIPPED_PYTHON_TITLE = (
    "### Shipped Python (shared with the Kiro prompt, under src/payload/, laid out like the project)"
)
KIRO_SHIPPED_PYTHON_TITLE = "### Shipped Python referenced by this prompt"

NEXT_PART_HEADING = re.compile(pattern=r"^### Part ", flags=re.MULTILINE)
NEXT_SUBSECTION_HEADING = re.compile(pattern=r"^### ", flags=re.MULTILINE)

PARAGRAPH_BOUNDARY = re.compile(pattern=r"\n[ \t]*\n")
SENTENCE_BOUNDARY = re.compile(pattern=r"(?<=[.!?])\s+")
TOP_LEVEL_BLOCK_BOUNDARY = re.compile(pattern=r"\n[ \t]*\n|\n(?=- )")
COPY_VERB = re.compile(pattern=r"\bcopy\b", flags=re.IGNORECASE)
WHITESPACE_RUN = re.compile(pattern=r"\s+")
SENTENCE = "sentence"
TOP_LEVEL_BULLET = "top-level bullet"

PRODUCT_ENTRY_SCRIPT = "src/payload/scripts/github_wrapper.py"
PRODUCT_PACKAGE = "src/payload/scripts/github_api/"
INSTALLED_ENTRY_SCRIPT = "scripts/github_wrapper.py"
INSTALLED_PACKAGE = "scripts/github_api/"
COPY_STEP_PATHS = (PRODUCT_ENTRY_SCRIPT, PRODUCT_PACKAGE)
SHIPPED_PYTHON_PATHS = (INSTALLED_ENTRY_SCRIPT, INSTALLED_PACKAGE)


@dataclass(frozen=True)
class PromptSection:
    """One section of one setup prompt: its heading line, where it ends, and the paths it must name."""

    prompt: str
    title: str
    next_heading: re.Pattern[str]
    paths: tuple[str, ...]

    @property
    def prompt_file(self) -> str:
        return f"{self.prompt}{PROMPT_SUFFIX}"

    def text(self) -> str:
        """The text from this section's heading (column 1, the whole line) to the next heading `next_heading` finds."""
        prompt_text = (PROMPTS_DIR / self.prompt_file).read_text(encoding="utf-8")
        heading_line = re.compile(pattern=rf"^{re.escape(pattern=self.title)}[ \t]*$", flags=re.MULTILINE)
        heading = heading_line.search(string=prompt_text)
        assert heading is not None, f"{self.prompt_file} has no `{self.title}` heading in column 1"
        following = self.next_heading.search(string=prompt_text, pos=heading.end())
        return prompt_text[heading.start() : len(prompt_text) if following is None else following.start()]

    def missing_paths(self) -> list[str]:
        section_text = self.text()
        return [path for path in self.paths if path not in section_text]


@dataclass(frozen=True)
class CopyInstruction(ABC):
    """A prompt's GitHub copy instruction: the copy-step unit copying the entry script copies the package."""

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
        entry_copy = self.copy_phrase(source=PRODUCT_ENTRY_SCRIPT, destination=INSTALLED_ENTRY_SCRIPT)
        package_copy = self.copy_phrase(source=PRODUCT_PACKAGE, destination=INSTALLED_PACKAGE)
        entry_units = [unit for unit in self.units() if entry_copy.search(string=unit) is not None]
        where = f"{self.section.prompt_file}: the `{self.section.title}` section"
        entry_copied = f"copies `{PRODUCT_ENTRY_SCRIPT}` to `{INSTALLED_ENTRY_SCRIPT}`"
        if not entry_units:
            return [f"{where} has no {self.unit_kind} that {entry_copied}"]
        return [
            f"{where}: the {self.unit_kind} that {entry_copied} does not copy `{PRODUCT_PACKAGE}` to "
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


CLAUDE_COPY_STEP = PromptSection(
    prompt=SETUP_CLAUDE, title=CLAUDE_COPY_STEP_TITLE, next_heading=NEXT_PART_HEADING, paths=COPY_STEP_PATHS
)
KIRO_COPY_STEP = PromptSection(
    prompt=SETUP_KIRO, title=KIRO_COPY_STEP_TITLE, next_heading=NEXT_PART_HEADING, paths=COPY_STEP_PATHS
)

SECTIONS = (
    CLAUDE_COPY_STEP,
    KIRO_COPY_STEP,
    PromptSection(
        prompt=SETUP_CLAUDE,
        title=CLAUDE_SHIPPED_PYTHON_TITLE,
        next_heading=NEXT_SUBSECTION_HEADING,
        paths=SHIPPED_PYTHON_PATHS,
    ),
    PromptSection(
        prompt=SETUP_KIRO,
        title=KIRO_SHIPPED_PYTHON_TITLE,
        next_heading=NEXT_SUBSECTION_HEADING,
        paths=SHIPPED_PYTHON_PATHS,
    ),
)

COPY_INSTRUCTIONS = (
    SentenceCopyInstruction(section=CLAUDE_COPY_STEP),
    BulletCopyInstruction(section=KIRO_COPY_STEP),
)


def test_the_setup_prompts_copy_the_package() -> None:
    """UB-1.3 (D8): each GitHub copy instruction copies the package, and each section names it beside the entry."""
    instruction_gaps = [gap for instruction in COPY_INSTRUCTIONS for gap in instruction.gaps()]
    section_gaps = [
        f"{section.prompt_file}: the `{section.title}` section does not name `{path}`"
        for section in SECTIONS
        for path in section.missing_paths()
    ]
    gaps = instruction_gaps + section_gaps
    assert not gaps, "the setup prompts do not copy the wrapper's package:\n" + "\n".join(gaps)
