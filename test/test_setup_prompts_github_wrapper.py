"""The setup prompts copy the GitHub wrapper's package with its entry script (UB-1.3, design D8).

The product wrapper `src/payload/scripts/github_wrapper.py` is a thin entry script that imports the package
`src/payload/scripts/github_api/` from its own directory, so a project set up with only the entry script copied gets a
wrapper that cannot start. Each setup prompt's GitHub copy step therefore names the package beside the entry script,
and each prompt's shipped-Python list names `scripts/github_api/` beside `scripts/github_wrapper.py`.

The copy step is the text from the `### Part 5.3 — Git repository wrapper scripts` heading of `setup-claude.txt` and
from the `### Part 6.2 — Stub credentials and wrappers` heading of `setup-kiro.txt` to the next `### Part` heading;
the shipped-Python list is the text from its `### Shipped Python …` heading to the next `###` heading. Both are cut
the way `test/test_setup_prompts_gitignore.py` cuts PART 3.

Run: ``python scripts/run_tests.py test/test_setup_prompts_github_wrapper.py``
"""

from __future__ import annotations

import re
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


SECTIONS = (
    PromptSection(
        prompt=SETUP_CLAUDE, title=CLAUDE_COPY_STEP_TITLE, next_heading=NEXT_PART_HEADING, paths=COPY_STEP_PATHS
    ),
    PromptSection(prompt=SETUP_KIRO, title=KIRO_COPY_STEP_TITLE, next_heading=NEXT_PART_HEADING, paths=COPY_STEP_PATHS),
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


def test_the_setup_prompts_copy_the_package() -> None:
    """UB-1.3 (D8): each GitHub copy step and each shipped-Python list names the package beside the entry script."""
    gaps = [
        f"{section.prompt_file}: the `{section.title}` section does not name `{path}`"
        for section in SECTIONS
        for path in section.missing_paths()
    ]
    assert not gaps, "the setup prompts do not copy the wrapper's package:\n" + "\n".join(gaps)
