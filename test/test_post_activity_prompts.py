"""The post-activity checklist runs only the checks CI does not own (issue #5).

The ``post-activity.md`` steering body that ``prompts/setup-kiro.txt`` installs (section 8.6) runs only the
AFFECTED tests in step 1 because the full suite is CI's, so its step 2 runs ``scripts/run_checks.py`` with the
lint, type and security groups only: a plain ``run_checks.py`` adds the ``tests`` group, the full suite. The
porting guidance and the install self-check of ``prompts/setup-claude.txt`` keep a port of that body from
reintroducing the plain form. The places that deliberately run the whole pipeline (the Rung 3 local mirror, the
run-ci workflow, the "what runs where" tables) keep naming the plain command.

Slicing: a section runs from its heading to the next heading of its level (a line that begins in its first column
with that many ``#`` and a space); phrases are compared whitespace-collapsed, so a wrapped phrase still matches;
commands are compared as stripped lines.

Run: ``python scripts/run_tests.py test/test_post_activity_prompts.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import pytest

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
KIRO_PROMPT = "setup-kiro.txt"
CLAUDE_PROMPT = "setup-claude.txt"

RUN_CHECKS = "python scripts/run_checks.py"
NON_TEST_GROUPS = " --group lint --group types --group security"
NON_TEST_RUN_CHECKS = RUN_CHECKS + NON_TEST_GROUPS
RUN_CHECKS_SCRIPT = "run_checks.py"
GROUP_FLAG = "--group"

# setup-kiro section 8.6, the post-activity steering body, up to the next steering section; its numbered steps.
POST_ACTIVITY_HEADING = "### 8.6 `post-activity.md` (always)"
NEXT_STEERING_HEADING = "### 8."
STEP_1 = "1. **"
STEP_2 = "2. **"
STEP_3 = "3. **"

# AC-2: what step 2 says about the groups it runs, and what the section never says.
STEP_2_PHRASES = (
    "Run the other project checks, locally, in one pass:",
    "the lint, type and security groups",
    "the `tests` group is CI's",
)
FORBIDDEN_SECTION_PHRASES = ("--group tests", "every project check", "and test groups")

# AC-3: the setup-claude porting paragraph for the Kiro bodies, up to the next blank line.
PORTING_PARAGRAPH_OPENING = "When porting `pre-work.md`,"
PORTING_PHRASES = ("`post-activity.md` step 2", "non-test groups", NON_TEST_RUN_CHECKS)

# AC-4: item 6 of the setup-claude install self-check, up to item 7.
SELF_CHECK_ITEM_6 = "6. CLAUDE.md + rules"
SELF_CHECK_ITEM_7 = "7. Settings"
SELF_CHECK_PHRASES = ("plain `python scripts/run_checks.py`", "no `--group`", "`tests` group")

# UB-2: step 1 of the 8.6 body.
STEP_1_PHRASES = (
    "python scripts/run_tests.py <paths or -k expr>",
    "The FULL suite is CI's job, not this checklist's",
)

# UB-1: the sites that deliberately run the whole pipeline.
RUNG_3_HEADING = "## Rung 3 — run the pipeline LOCALLY, as a disclosed workaround"
RUN_CI_HOOK_HEADING = "#### 9.1 `run-ci-workflow.kiro.hook`"
SLASH_COMMANDS_HEADING = "### Part 6.1 — User-invoked workflows → slash commands (.claude/commands/)"
RUN_CI_COMMAND = "`.claude/commands/run-ci.md`"
COMMAND_FILE_PREFIX = "`.claude/commands/"
GIT_HOOKS_HEADING = "### Part 2.2 — Version-controlled git hooks (tracked `.githooks/`) and the check scripts"
WHERE_CHECKS_RUN_HEADING = "### Where checks run"
MANUAL_ROW = "| manual |"
LOCAL_ON_DEMAND_ROW = "| local, on demand |"


def read_prompt(name: str) -> str:
    """A prompt's text with universal newlines, so a CRLF and an LF checkout slice alike."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def collapse(text: str) -> str:
    """The text with every whitespace run collapsed to one space: a phrase wrapped across lines still matches."""
    return " ".join(text.split())


def stripped_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines()]


def line_block(text: str, start: str, stop: str) -> str:
    """From the one line beginning with ``start`` up to, not including, the next line beginning with ``stop``."""
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith(start)]
    assert len(starts) == 1, f"expected exactly one line beginning {start!r}, found {len(starts)}"
    first = starts[0]
    end = next((index for index in range(first + 1, len(lines)) if lines[index].startswith(stop)), len(lines))
    return "\n".join(lines[first:end])


def heading_section(text: str, heading: str) -> str:
    """A heading's section, up to the next heading of its level (that many ``#`` and a space in column 1)."""
    level = len(heading) - len(heading.lstrip("#"))
    return line_block(text=text, start=heading, stop="#" * level + " ")


def paragraph(text: str, opening: str) -> str:
    """From the one occurrence of ``opening`` up to the next blank line."""
    assert text.count(opening) == 1, f"expected exactly one {opening!r}, found {text.count(opening)}"
    lines = text[text.index(opening) :].splitlines()
    end = next((index for index, line in enumerate(lines) if not line.strip()), len(lines))
    return "\n".join(lines[:end])


def missing_phrases(text: str, phrases: tuple[str, ...]) -> list[str]:
    collapsed = collapse(text=text)
    return [phrase for phrase in phrases if collapse(text=phrase) not in collapsed]


def present_phrases(text: str, phrases: tuple[str, ...]) -> list[str]:
    collapsed = collapse(text=text)
    return [phrase for phrase in phrases if collapse(text=phrase) in collapsed]


def kiro_post_activity_section() -> str:
    return line_block(text=read_prompt(name=KIRO_PROMPT), start=POST_ACTIVITY_HEADING, stop=NEXT_STEERING_HEADING)


@dataclass(frozen=True)
class FullRunSite(ABC):
    """A place that deliberately runs the whole pipeline, so it names a plain ``run_checks.py`` (UB-1)."""

    site_id: str
    prompt: str
    heading: str

    def section(self) -> str:
        return heading_section(text=read_prompt(name=self.prompt), heading=self.heading)

    @abstractmethod
    def assert_stays_plain(self) -> None:
        """Fail unless the site still names the plain command."""


@dataclass(frozen=True)
class FullRunCommandSite(FullRunSite):
    """A command site: a line of it that, stripped, is exactly the plain command."""

    block_start: str = ""
    block_stop: str = ""

    def block(self) -> str:
        if not self.block_start:
            return self.section()
        return line_block(text=self.section(), start=self.block_start, stop=self.block_stop)

    def assert_stays_plain(self) -> None:
        assert RUN_CHECKS in stripped_lines(text=self.block()), f"{self.site_id}: no line that is `{RUN_CHECKS}`"


@dataclass(frozen=True)
class FullRunTableRowSite(FullRunSite):
    """A "what runs where" table row: it names ``run_checks.py`` and no ``--group``."""

    row_prefix: str

    def row(self) -> str:
        rows = [line for line in stripped_lines(text=self.section()) if line.startswith(self.row_prefix)]
        assert len(rows) == 1, f"{self.site_id}: expected one {self.row_prefix!r} row, found {len(rows)}"
        return rows[0]

    def assert_stays_plain(self) -> None:
        row = self.row()
        assert RUN_CHECKS_SCRIPT in row, f"{self.site_id}: the row no longer names `{RUN_CHECKS_SCRIPT}`: {row}"
        assert GROUP_FLAG not in row, f"{self.site_id}: the row narrows the whole pipeline to groups: {row}"


FULL_RUN_SITES = (
    FullRunCommandSite(site_id="kiro-rung-3-local-pipeline", prompt=KIRO_PROMPT, heading=RUNG_3_HEADING),
    FullRunCommandSite(site_id="kiro-run-ci-workflow-hook", prompt=KIRO_PROMPT, heading=RUN_CI_HOOK_HEADING),
    FullRunCommandSite(
        site_id="claude-run-ci-command",
        prompt=CLAUDE_PROMPT,
        heading=SLASH_COMMANDS_HEADING,
        block_start=RUN_CI_COMMAND,
        block_stop=COMMAND_FILE_PREFIX,
    ),
    FullRunTableRowSite(
        site_id="kiro-what-runs-where-manual", prompt=KIRO_PROMPT, heading=GIT_HOOKS_HEADING, row_prefix=MANUAL_ROW
    ),
    FullRunTableRowSite(
        site_id="claude-what-runs-where-local-on-demand",
        prompt=CLAUDE_PROMPT,
        heading=GIT_HOOKS_HEADING,
        row_prefix=LOCAL_ON_DEMAND_ROW,
    ),
    FullRunTableRowSite(
        site_id="kiro-where-checks-run-local-on-demand",
        prompt=KIRO_PROMPT,
        heading=WHERE_CHECKS_RUN_HEADING,
        row_prefix=LOCAL_ON_DEMAND_ROW,
    ),
)


def test_kiro_step2_runs_the_non_test_groups() -> None:
    """AC-1: step 2 runs the three non-test groups, and no `run_checks.py` in 8.6 runs without them."""
    section = kiro_post_activity_section()
    step_2 = line_block(text=section, start=STEP_2, stop=STEP_3)
    assert NON_TEST_RUN_CHECKS in stripped_lines(text=step_2), f"step 2 has no line that is `{NON_TEST_RUN_CHECKS}`"
    collapsed = collapse(text=section)
    total = collapsed.count(RUN_CHECKS)
    qualified = collapsed.count(NON_TEST_RUN_CHECKS)
    assert total == qualified, f"{total - qualified} of {total} `{RUN_CHECKS}` in 8.6 lack `{NON_TEST_GROUPS.strip()}`"


def test_kiro_body_never_runs_the_tests_group() -> None:
    """AC-2: step 2 names the groups it runs and leaves `tests` to CI; the section never implies the tests group."""
    section = kiro_post_activity_section()
    step_2 = line_block(text=section, start=STEP_2, stop=STEP_3)
    missing = missing_phrases(text=step_2, phrases=STEP_2_PHRASES)
    assert not missing, f"step 2 of 8.6 lacks {missing}"
    forbidden = present_phrases(text=section, phrases=FORBIDDEN_SECTION_PHRASES)
    assert not forbidden, f"8.6 still says {forbidden}"


def test_claude_porting_paragraph_names_the_non_test_groups() -> None:
    """AC-3: the porting paragraph says the ported post-activity step 2 runs only the non-test groups."""
    porting = paragraph(text=read_prompt(name=CLAUDE_PROMPT), opening=PORTING_PARAGRAPH_OPENING)
    missing = missing_phrases(text=porting, phrases=PORTING_PHRASES)
    assert not missing, f"the porting paragraph lacks {missing}"


def test_claude_self_check_flags_a_plain_run_checks() -> None:
    """AC-4: self-check item 6 greps the ported post-activity.md for a plain run_checks.py, the tests group."""
    item_6 = line_block(text=read_prompt(name=CLAUDE_PROMPT), start=SELF_CHECK_ITEM_6, stop=SELF_CHECK_ITEM_7)
    missing = missing_phrases(text=item_6, phrases=SELF_CHECK_PHRASES)
    assert not missing, f"self-check item 6 lacks {missing}"


@pytest.mark.parametrize("site", FULL_RUN_SITES, ids=[site.site_id for site in FULL_RUN_SITES])
def test_deliberate_full_runs_stay_plain(site: FullRunSite) -> None:
    """UB-1: every deliberate whole-pipeline run keeps the plain `run_checks.py`."""
    site.assert_stays_plain()


def test_kiro_step1_still_runs_only_affected_tests() -> None:
    """UB-2: step 1 of 8.6 still runs the affected tests and leaves the full suite to CI."""
    step_1 = line_block(text=kiro_post_activity_section(), start=STEP_1, stop=STEP_2)
    missing = missing_phrases(text=step_1, phrases=STEP_1_PHRASES)
    assert not missing, f"step 1 of 8.6 lacks {missing}"
