# Prompt — issue #5: Kiro post-activity step 2 runs the full suite it says CI owns

Tier: S — a wording and command change in one prompt section, plus the matching setup-claude porting guidance
and self-check; no new interface.

Kind: BUGFIX.

## Goal

The Kiro steering body `post-activity.md` that `prompts/setup-kiro.txt` installs (section
`### 8.6 \`post-activity.md\` (always)`) contradicts itself: step 1 runs only the AFFECTED tests because "The
FULL suite is CI's job, not this checklist's"; step 2 runs plain `python scripts/run_checks.py`, whose default
groups (`run_checks.GROUP_ORDER`: `lint`, `types`, `security`, `tests`) include the full suite. Step 2 must run
only `--group lint --group types --group security`, as this repository's installed `.claude/rules/post-activity.md`
already does, and the setup-claude porting guidance must not reintroduce the plain invocation.

## Scope (the ask)

- `prompts/setup-kiro.txt` 8.6 step 2: the command becomes
  `python scripts/run_checks.py --group lint --group types --group security`; its explanatory sentence names
  those groups and says the `tests` group is CI's (and that a plain `run_checks.py` adds it). Decided (DL-001):
  the groups are named explicitly — the installed Claude rule's form — rather than a new named selection in
  `run_checks.py` (the issue's open question): no new interface, and both clients then read the same.
- `prompts/setup-claude.txt`, the porting paragraph that begins "When porting `pre-work.md`, …" ("port the
  CURRENT bodies (Kiro 8.2, 8.18, 8.21, 8.6, 8.23, 8.22)"): one sentence saying the ported `post-activity.md`
  step 2 runs only the non-test groups.
- `prompts/setup-claude.txt`, the install self-check item `6. CLAUDE.md + rules`: also grep the ported
  `post-activity.md` for a plain `python scripts/run_checks.py` (no `--group`) and flag it.
- A test under `test/` that pins the 8.6 body's step 2 to the three non-test groups, asserts no sentence of the
  8.6 body says the checklist runs the `tests` group, and asserts the two setup-claude additions.

## Out of scope

- The deliberate full runs (UB-1): setup-kiro's capacity-ladder Rung 3 step, `run-ci-workflow.kiro.hook`, the
  setup-claude `/run-ci` command, and the "local, on demand" rows of both prompts' tables.
- `src/payload/scripts/run_checks.py` (unchanged).

## Tests

Every acceptance criterion and unchanged-behaviour clause is pinned by a test in the new module.
E2E: not applicable — prompt text; no runtime behaviour of a deployed system changes. CI's `tests` group runs
the new test.
