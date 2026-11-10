# Change — issue #5: Kiro post-activity step 2 runs the full suite it says CI owns

Tier: S. Kind: BUGFIX. Scope decided in `decisions/decision-log.md` DL-001.

## User Prompts

- The `/auto-work` run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end"
- Issue #5: "Kiro post-activity step 2 runs the full suite it says CI owns"

## Ask

The steering body `post-activity.md` that `prompts/setup-kiro.txt` installs (`### 8.6 \`post-activity.md\` (always)`)
contradicts itself: step 1 runs only the AFFECTED tests because "The FULL suite is CI's job, not this checklist's";
step 2 runs plain `python scripts/run_checks.py`, whose default groups (`src/payload/scripts/run_checks.py`
`GROUP_ORDER`: `lint`, `types`, `security`, `tests`) include the full suite, and says "It runs lint, type, security
and test groups". Step 2 runs only `--group lint --group types --group security`, the form of this repository's
installed `.claude/rules/post-activity.md` step 2 (DL-001: the groups are named; `run_checks.py` gains no
selection). The `prompts/setup-claude.txt` porting guidance and install self-check keep a port of the Kiro body
from reintroducing the plain invocation.

## Acceptance criteria

- AC-1 — Step 2 of the 8.6 body SHALL run `python scripts/run_checks.py --group lint --group types --group
  security`, and every `python scripts/run_checks.py` in the 8.6 section SHALL carry those three `--group`
  arguments.
- AC-2 — The 8.6 body SHALL NOT state or imply that the checklist runs the `tests` group: step 2's lead SHALL read
  "Run the other project checks, locally, in one pass:", its explanatory text SHALL name "the lint, type and
  security groups" and state that "the `tests` group is CI's" (a plain `run_checks.py` adds it), and the section
  SHALL contain none of `--group tests`, "every project check", "and test groups".
- AC-3 — The setup-claude paragraph that begins "When porting `pre-work.md`, `use-lessons-learned.md`,
  `no-guessing.md`," SHALL state that the ported `post-activity.md` step 2 runs only the non-test groups,
  `python scripts/run_checks.py --group lint --group types --group security`.
- AC-4 — The setup-claude install self-check item "6. CLAUDE.md + rules" SHALL instruct the installer to grep the
  ported `post-activity.md` for a plain `python scripts/run_checks.py` (no `--group`) and flag it, because that form
  runs the `tests` group, which is CI's.

## Unchanged behaviour

- UB-1 — These deliberate full runs SHALL CONTINUE TO name plain `run_checks.py` (no `--group`):
  - setup-kiro `## Rung 3 — run the pipeline LOCALLY, as a disclosed workaround` step 1 (the
    `docs/ci-capacity-ladder.md` body under 8.25);
  - setup-kiro `#### 9.1 \`run-ci-workflow.kiro.hook\``;
  - setup-claude `` `.claude/commands/run-ci.md` `` under `### Part 6.1 — User-invoked workflows → slash commands
    (.claude/commands/)`;
  - the "What runs where" table under each prompt's `### Part 2.2 — Version-controlled git hooks (tracked
    \`.githooks/\`) and the check scripts`: setup-kiro's `| manual |` row, setup-claude's `| local, on demand |` row;
  - setup-kiro `### Where checks run`, the `| local, on demand |` row.
- UB-2 — Step 1 of the 8.6 body SHALL CONTINUE TO run `python scripts/run_tests.py <paths or -k expr>` and to say
  "The FULL suite is CI's job, not this checklist's".

## Files

- `prompts/setup-kiro.txt` — `### 8.6`, step 2 only: the lead (AC-2), the fenced command (AC-1), and the
  explanatory text, which becomes "These are the SAME commands CI runs, so the two cannot drift apart. They run the
  lint, type and security groups; the `tests` group is CI's (a plain `run_checks.py` adds it, the full suite). The
  script continues past a failure instead of stopping at the first one and ends with a consolidated
  `=== FAILED CHECKS (n) ===` block." "Apply Rule 3 (no output shortening)." becomes "Read all of it
  (`no-output-shortening.md`)."; the fix-every-failure sentences stay. In `### 8.23`, the procedures body's
  `## Integration` line "runs the affected tests plus `run_checks.py`" becomes "runs the affected tests plus the
  non-test `run_checks.py` groups", the installed `.claude/rules/tests-must-not-fail-procedures.md` wording.
- `prompts/setup-claude.txt` — one sentence in the "When porting `pre-work.md`, …" paragraph of `### Part 8.2 —
  .claude/rules/ (the detailed rules)` (AC-3); one sentence in item "6. CLAUDE.md + rules" of `## PART 11 — FINAL
  VERIFICATION AND REPORT` `### Verification checklist` (AC-4).
- `test/test_post_activity_prompts.py` — new framework test module.

## Tests

All in `test/test_post_activity_prompts.py`, reading the prompts from `Path(__file__).resolve().parents[1] /
"prompts"` with `read_text(encoding="utf-8")` (universal newlines, so CRLF and LF checkouts slice alike); example
tests only (no criterion quantifies over an input domain). Slices: the 8.6 section runs from its heading to the
next `### 8.` heading; within it step 1 runs from `1. **` to `2. **` and step 2 from `2. **` to `3. **`; the
porting paragraph runs from "When porting `pre-work.md`," to the next blank line; item 6 runs from "6. CLAUDE.md +
rules" to "7. Settings"; a heading-bounded UB-1 site runs to the next heading of its level (a heading is a line
that begins in its first column with that many `#` and a space); the `run-ci.md` site runs to the next line
beginning `` `.claude/commands/ ``. Phrase checks compare whitespace-collapsed text, so a wrapped phrase still
matches; line checks compare stripped lines.

- AC-1 — `test_kiro_step2_runs_the_non_test_groups`: step 2 has a line that, stripped, is
  `python scripts/run_checks.py --group lint --group types --group security`, and every
  `python scripts/run_checks.py` in the section is followed by ` --group lint --group types --group security`.
- AC-2 — `test_kiro_body_never_runs_the_tests_group`: step 2 contains "Run the other project checks, locally, in
  one pass:", "the lint, type and security groups" and "the `tests` group is CI's"; the section contains none of
  `--group tests`, "every project check", "and test groups".
- AC-3 — `test_claude_porting_paragraph_names_the_non_test_groups`: the paragraph contains "`post-activity.md`
  step 2", "non-test groups" and the three-group command.
- AC-4 — `test_claude_self_check_flags_a_plain_run_checks`: item 6 contains "plain `python scripts/run_checks.py`",
  "no `--group`" and "`tests` group".
- UB-1 — `test_deliberate_full_runs_stay_plain`, parametrized over the six UB-1 sites: each of the three command
  sites has a line that, stripped, is `python scripts/run_checks.py`; each of the three table rows holds
  `run_checks.py` and no `--group`.
- UB-2 — `test_kiro_step1_still_runs_only_affected_tests`: step 1 contains
  `python scripts/run_tests.py <paths or -k expr>` and "The FULL suite is CI's job, not this checklist's".

Red before I1: the AC-1 to AC-4 tests. Green before and after I1: the UB-1 and UB-2 tests.

E2E: not applicable — prompt text; no runtime behaviour of a running system changes. CI's `tests` group runs the
module (`pyproject.toml` `[tool.pytest.ini_options]` `testpaths` includes `test`).

## Tasks (one wave)

- [ ] T1 TEST: write the module described under Tests; capture it red before I1 — Files:
  `test/test_post_activity_prompts.py` — Validates: AC-1, AC-2, AC-3, AC-4, UB-1, UB-2
- [ ] I1 IMPL: edit 8.6 step 2 per AC-1, AC-2 and the Files text; restate the 8.23 `## Integration` line; add the
  AC-3 and AC-4 sentences — Files:
  `prompts/setup-kiro.txt`, `prompts/setup-claude.txt` — Validates: AC-1, AC-2, AC-3, AC-4

## Residuals

None. Out of scope: `src/payload/scripts/run_checks.py`; the other plain `run_checks.py` mentions, which describe or
verify the whole pipeline — setup-kiro `### \`docs/forLLMConsumption.md\`` common commands and the "Checks" items of
both prompts' verification checklists.
