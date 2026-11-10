# Change — issue #2: anchor the root-only ignore directories in the setup prompts

Tier: S. Kind: BUGFIX. Scope decided in `decisions/decision-log.md` DL-001.

## User Prompts

- The `/auto-work` run: "Work this project's open-issue backlog AUTONOMOUSLY, end to end"
- Issue #2: "Setup prompts recommend an unanchored reports/ ignore that swallows docs/reports/"

## Ask

`## PART 3 — .gitignore` of `prompts/setup-claude.txt` and of `prompts/setup-kiro.txt` recommends the slash-free
line `reports/`. A pattern without a separator at its beginning or middle "may also match at any level below the
`.gitignore` level" (gitignore(5), PATTERN FORMAT, https://git-scm.com/docs/gitignore), so the line also ignores
`docs/reports/`; the reports it is for land only in the root `reports/` (`src/payload/scripts/run_checks.py`
`--reports-dir`, `src/payload/scripts/run_tests.py` `--junit`). Anchor `reports/` in both blocks; anchor the
root-only packaging directories of the setup-kiro block (an unanchored `lib/` also swallows a TypeScript CDK app's
`cdk/lib/` source); and tell an existing project to replace the slash-free form of an anchored entry.

## Acceptance criteria

- AC-1 — The fenced block of `prompts/setup-claude.txt` `## PART 3 — .gitignore` SHALL list `/reports/` and no
  `reports/` line, with a one-line comment stating that the anchor keeps `docs/reports/` tracked.
- AC-2 — The fenced block of `prompts/setup-kiro.txt` `## PART 3 — .gitignore` SHALL list `/reports/` and no
  `reports/` line, with a one-line comment stating that the anchor keeps `docs/reports/` tracked.
- AC-3 — The setup-kiro PART 3 fenced block SHALL list `/lib/`, `/lib64/`, `/var/`, `/downloads/`, `/eggs/`,
  `/develop-eggs/`, `/parts/`, `/sdist/` and `/wheels/` and none of their slash-free forms, with one comment line
  giving the reason: a nested directory of that name, such as `cdk/lib/`, is source.
- AC-4 — IF a project's existing `.gitignore` carries the slash-free form of an entry PART 3 anchors,
  THEN the PART 3 section of each prompt SHALL instruct the project to replace that line with the anchored form.
- AC-5 — WHEN either block is applied as a repository's `.gitignore`, `git check-ignore --no-index` SHALL report
  `reports/junit.xml` and `reports/checks-lint.json` ignored and `docs/reports/x.md` not ignored; WHEN the
  setup-kiro block is applied, it SHALL also report `lib/x.py` ignored and `cdk/lib/stack.ts` not ignored.

## Unchanged behaviour

- UB-1 — Both blocks SHALL CONTINUE TO ignore the root `reports/` that `run_checks.py` and `run_tests.py` write.
- UB-2 — Both PART 3 sections SHALL CONTINUE TO instruct that every entry the block does not anchor is added only
  when missing ("Read existing entries, add only those …").
- UB-3 — The setup-kiro block SHALL CONTINUE TO list `build/`, `dist/`, `venv/`, `.venv/` and `tmp/` slash-free,
  so a nested directory of one of those names stays ignored.

## Files

- `prompts/setup-claude.txt` — `## PART 3 — .gitignore`: the `reports/` line and its comment in the fenced block;
  the replace sentence beside "Apply Rule 1. Read existing entries, add only those missing", worded:
  > Exception to Rule 1's keep-the-existing-value: an existing line that is the slash-free form of an anchored
  > entry — `reports/` below, or `lib/`, `lib64/`, `var/`, `downloads/`, `eggs/`, `develop-eggs/`, `parts/`,
  > `sdist/` or `wheels/` from the Kiro standard — is REPLACED by the same entry with a leading slash (`reports/`
  > → `/reports/`, `lib/` → `/lib/`), not kept beside it: the slash-free form also ignores a nested directory of
  > that name, such as `docs/reports/` or `cdk/lib/`.
- `prompts/setup-kiro.txt` — `## PART 3 — .gitignore`: the `reports/` line and its comment, the AC-3 packaging
  lines and their comment line in the fenced block; the replace sentence beside "Apply Rule 1. Read existing
  entries, add only those that are missing", worded:
  > Exception to Rule 1's keep-the-existing-value: an existing line that is the slash-free form of an entry below
  > that starts with `/` is REPLACED by that entry (`reports/` → `/reports/`, `lib/` → `/lib/`), not kept beside
  > it: the slash-free form also ignores a nested directory of that name, such as `docs/reports/` or `cdk/lib/`.
- `test/test_setup_prompts_gitignore.py` — new framework test module.
- `test/test_layout.py` — `HISTORICAL` also matches `\.claude/specs/`, and the module docstring lists it: a committed spec directory is a historical
  record like `.kiro/specs/`, and its probe paths are not framework references.

## Tests

All in `test/test_setup_prompts_gitignore.py`; example tests, parametrized over the two prompts where both apply,
no property-based test. The section is the text from the
`## PART 3 — .gitignore` heading to the next `## PART` heading; the block is the first fenced block after the
heading. A probe writes the block as `.gitignore` of a repository created with `git init` under pytest's
`tmp_path` and runs `git check-ignore --no-index -q <path>` with `cwd=` that repository: exit 0 is ignored, exit 1
is not ignored, any other exit fails the test (git-check-ignore(1), EXIT STATUS and `-q` "only valid with a single
pathname", https://git-scm.com/docs/git-check-ignore). The module builds the `docs/reports/x.md` probe from its
parts (`Path("docs", "reports", "x.md").as_posix()`), so `test/test_layout.py`
`test_every_framework_path_named_in_a_live_file_exists` does not read it as a framework path.

- AC-1, AC-2 — `test_reports_line_is_anchored_with_its_comment[setup-claude]`, `[setup-kiro]`: the block has a
  `/reports/` line, no `reports/` line, and a `#` line naming `docs/reports/`. Example.
- AC-3 — `test_root_only_packaging_dirs_are_anchored`: every AC-3 anchored line is present, none of its slash-free
  forms is a line of the block (whole-line comparison), and a `#` line names `cdk/lib/`. Example.
- AC-4 — `test_section_says_to_replace_a_slash_free_entry[setup-claude]`, `[setup-kiro]`: the section text outside
  the fenced block holds "is REPLACED by", "not kept beside it" and the arrows `reports/` → `/reports/`,
  `lib/` → `/lib/`, and neither reversed arrow nor "never REPLACED". Example.
- AC-5 — `test_applied_block_ignores_only_the_root_dirs`, parametrized by prompt, probe and expected verdict:
  `reports/junit.xml` and `reports/checks-lint.json` ignored, `docs/reports/x.md` not ignored, for both blocks;
  `lib/x.py` ignored and `cdk/lib/stack.ts` not ignored for the setup-kiro block. Integration (runs `git`).
- UB-1 — the `reports/junit.xml` and `reports/checks-lint.json` probes of the AC-5 test.
- UB-2 — `test_section_still_adds_only_missing_entries[setup-claude]`, `[setup-kiro]`: the section text contains
  "Read existing entries, add only those". Example.
- UB-3 — `test_generated_dirs_stay_slash_free`: the setup-kiro block has the lines `build/`, `dist/`, `venv/`,
  `.venv/` and `tmp/`; plus AC-5 test probes `frontend/build/x.js` and `tmp/x`, both ignored under the setup-kiro
  block. Example and integration.

Red before I1: the AC-1 to AC-4 tests and the `docs/reports/x.md` and `cdk/lib/stack.ts` probes. Green before and
after I1: the UB-1 to UB-3 tests and probes.

E2E: not applicable — prompt text; no runtime behaviour of a running system changes. CI's `tests` group runs the
module (`pyproject.toml` `testpaths` includes `test`).

## Tasks (one wave)

- [x] T1 TEST: write the module described under Tests; capture it red before I1 — Files:
  `test/test_setup_prompts_gitignore.py` — Validates: AC-1, AC-2, AC-3, AC-4, AC-5, UB-1, UB-2, UB-3
- [x] I1 IMPL: edit both PART 3 sections per AC-1 to AC-4 and § Files;
  add `\.claude/specs/` to `test/test_layout.py` `HISTORICAL` — Files: `prompts/setup-claude.txt`,
  `prompts/setup-kiro.txt`, `test/test_layout.py` — Validates: AC-1, AC-2, AC-3, AC-4, AC-5

## Residuals

None. Out of scope: this repository's own `.gitignore` (already anchored) and the `run_checks.py` /
`run_tests.py` defaults.
