# spec-review-agent — iteration 01 (tier S, COMBINED: all six lenses)

Reviewed: `change.md` against `prompts/setup-kiro.txt` 8.6, 8.23, 8.25, 9.1, Part 2.2, "Where checks run";
`prompts/setup-claude.txt` Part 2.2, Part 6.1, Part 8.2, PART 11 item 6; `src/payload/scripts/run_checks.py`
(`GROUP_ORDER`, `--group` is `action="append"`, so three `--group` flags select three groups); installed
`.claude/rules/post-activity.md` step 2; issue #5 body (via `github_wrapper.py get-issue 5`).

Security lens: not engaged (no auth, IAM, secrets or input handling). Operability lens: `E2E: not applicable`
matches `always-test-e2e.md` (no runtime behaviour); `pyproject.toml` `testpaths` includes `test`, so CI's
`tests` group collects the new module. Standards lens: `ROOT = Path(__file__).resolve().parents[1]` matches
`test/test_layout.py`; the change is under the tier-S cap and carries no line numbers or figures.

## A — none

## B — none

## C

### C1 — Two slice rules leave read mode and heading detection open
Severity: C
Location: change.md § Tests (the "Slices:" paragraph)
Defect: The checked-out prompts are CRLF while the index and CI checkout are LF (`git ls-files --eol`:
`i/lf w/crlf`, `core.autocrlf=true`). If the module slices on bytes or on `newline=""` text, the porting
paragraph's "next blank line" is never found locally. Second: setup-kiro Part 2.2 holds an indented
`### Git hooks setup` (the README snippet in its 4-backtick fence) ahead of the "What runs where" table. If
headings are detected on stripped lines, as the "line checks compare stripped lines" sentence invites, that
site stops before its `| manual |` row. Everything else in the slicing holds: every start and end marker
occurs once in its prompt, neither prompt has a whitespace-only line, `### 8.7` follows 8.6 directly, the
`1. **`/`2. **`/`3. **` markers are unique inside 8.6, and the porting paragraph contains no blank line.
Material-because: not gating. Both failures show up at T1's capture, because the UB-1 tests have to be green
before I1. Neither one lets a test pass silently.
Proposed-edit: after `reading the prompts from \`Path(__file__).resolve().parents[1] / "prompts"\`` insert
`with \`read_text(encoding="utf-8")\` (universal newlines, so CRLF and LF checkouts slice alike)`; after
"a heading-bounded UB-1 site runs to the next heading of its level" insert "(a heading is a line that begins
in its first column with that many `#` and a space)".

### C2 — Two pinned phrases are looser than their criterion
Severity: C
Location: change.md § Tests, AC-2 and AC-4 entries
Defect: AC-2 fixes the whole lead "Run the other project checks, locally, in one pass:", but its test pins
only the prefix "Run the other project checks". AC-4 requires the reason ("that form runs the `tests` group,
which is CI's"), but its test pins only "plain `python scripts/run_checks.py`" and "no `--group`". Item 6
does not contain "`tests` group" today, so pinning it would make the reason falsifiable too. Both tests
are red before I1 (none of these phrases is in the prompts today), so each criterion can already fail. This
finding is about partial coverage of the criterion's text, nothing more.
Material-because: not gating. The coverage is partial, not missing.
Proposed-edit: in the AC-2 test entry replace `"Run the other project checks"` with `"Run the other project
checks, locally, in one pass:"`; in the AC-4 test entry replace `and "no \`--group\`"` with `, "no
\`--group\`" and "\`tests\` group"`.

### C3 — 8.23 still describes the checklist as "plus `run_checks.py`"
Severity: C
Location: change.md § Residuals (out-of-scope list) / § Files
Defect: The setup-kiro 8.23 procedures body, `## Integration`, says "`post-activity.md`: the post-activity
checklist runs the affected tests plus `run_checks.py`". After I1, that is the only description of the
checklist left that names the script without its groups. setup-claude's porting paragraph names Kiro 8.23
as a port source, and the installed `.claude/rules/tests-must-not-fail-procedures.md` already reads "plus
the non-test `run_checks.py` groups". The Residuals list neither names this site nor gives a reason for
leaving it.
Material-because: not gating. The text is outside the 8.6 section that AC-2 bounds.
Proposed-edit: append to § Files under `prompts/setup-kiro.txt`: "8.23 procedures `## Integration`: 'runs
the affected tests plus `run_checks.py`' becomes 'runs the affected tests plus the non-test `run_checks.py`
groups' (the installed Claude companion's wording)."

## D

### D1 — Step 2 keeps a pointer to a setup-prompt rule
Severity: D
Location: change.md § Files, `prompts/setup-kiro.txt` entry
Defect: "Apply Rule 3 (no output shortening)" points to the setup prompt's `### Rule 3: Read complete
output`, and an installed project has no such rule. The target wording, installed
`.claude/rules/post-activity.md` step 2, reads "Read all of it (`no-output-shortening.md`)", and DL-001's
driver is that the two clients read the same.
Proposed-edit: replace "The Rule 3 sentence and the fix-every-failure sentences stay." with "'Apply Rule 3
(no output shortening).' becomes 'Read all of it (`no-output-shortening.md`).'; the fix-every-failure
sentences stay."

## Coverage (criterion → test; state checked against the current prompts)

| Criterion | Test | Before I1 | Falsifiable by |
|---|---|---|---|
| AC-1 | `test_kiro_step2_runs_the_non_test_groups` | red: step 2's only command line is plain | stripped-line equality + every-occurrence suffix |
| AC-2 | `test_kiro_body_never_runs_the_tests_group` | red: lead absent; "every project check", "and test groups" present | 3 positive pins, 3 forbidden phrases (C2 tightens the lead) |
| AC-3 | `test_claude_porting_paragraph_names_the_non_test_groups` | red: none of the 3 phrases is in the paragraph | 3 phrase pins, whitespace-collapsed |
| AC-4 | `test_claude_self_check_flags_a_plain_run_checks` | red: neither phrase is in item 6 | 2 phrase pins (C2 adds the reason) |
| UB-1 (6 sites) | `test_deliberate_full_runs_stay_plain` | green: Rung 3, 9.1, `run-ci.md` each have a plain command line; the 3 rows hold `run_checks.py`, no `--group` | equality fails if `--group` is added |
| UB-2 | `test_kiro_step1_still_runs_only_affected_tests` | green: both phrases in step 1 | phrase pins |

Property-based tests: none required. No criterion quantifies over an input domain.

Verdict: CLEAN (0 A, 0 B) — READY
