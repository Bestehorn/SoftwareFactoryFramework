# Combined review (tier S), iteration 02 (delta) — issue #32

### B1 — the create-word rule leaves UB-5 unprotected and, read as shell words, contradicts it
Severity: B
Location: change.md § Acceptance criteria AC-7; § Unchanged behaviour UB-5; § Files, `src/hooks/gate_filing.py` row; § Tests UB-5
Defect: Three spellings that the worktree's `gate_filing.run` refuses today (probe, exit 2) diverge under the readings of "whole shell words" / "only inside a longer word". (1) `python scripts/github_wrapper.py "create-issue" --title t --body plain`: a blank-delimited token match skips it. (2) `bash -c "python scripts/github_wrapper.py create-issue --title t --body plain"`: a shell-word match skips it (the one word holds `create-issue` inside a longer word), so AC-7 as worded requires allowing it while UB-5 requires blocking it. The gate docstring lists wrapper-shell create calls as RULE-only residuals, but the gate refuses this one today. (3) `gh issue` + bare newline + `create`: a shell-word match skips it, and the `DELIBERATE DIFFERENCES` comment ("`\s+` also spans a bare line break") goes stale. No G case writes the create words quoted or inside a wrapper shell, so TEST-8 and UB-5's "existing cases" pass under every reading, including the one that drops spelling (1), a direct create call. A boundary form (no word character, `/`, `.` or `-` directly before or after the match) still matches (1), (2) and (3), the after-`&&`, flags-first and unsplittable spellings, and skips `call issues/create-issue-artifact`. Over the 53 rendered ALLOW/BLOCK/creates-nothing commands of `test_gate_filing.py`, it changes the match of only `create-issue-inside-a-longer-word-reads-all-words`, which then exits 0 with no note, as its `assert_verified_allow` accepts (probe against `gate_filing.CREATE_RE`).
Material-because: regression — UB-5 is contradicted by AC-7 under the Files row's reading and is unprotected against the reading that drops the quoted create word.
Proposed-edit: Files row → "`CREATE_RE` skips a `create-issue` or `issue create` with a word character, `/`, `.` or `-` directly before or after it (DL-005)"; AC-7 → "WHEN every `create-issue` and `issue create` in a shell command has a word character, `/`, `.` or `-` directly before or after it, as in `call issues/create-issue-artifact`, THEN `gate_filing.run` SHALL allow it with no note (DL-005)."; Tests UB-5 append "; new case `quoted-create-word` (`create-issue` double-quoted, inline body without provenance)"; Files "G gains one case" → "G gains two cases"; Tasks red line "G's new case is blocked" → "G's AC-7 case is blocked". D1 offsets the growth.

### D1 — AC-3 credits `versions` to the `Paging:` line
Severity: D
Location: change.md § Acceptance criteria AC-3, first bullet
Defect: The `Paging:` line of `rest/issues.md` "Get an issue artifact" names only `page` and `per_page`. `versions` is the item key in `conventions.md` "Lists wrapped in an object", which the bullet's general rule already cites.
Proposed-edit: "(its `Paging:` line pages `versions` inside one artifact)" → "(it pages the `versions` inside one artifact)".

Verdict: NOT-READY (0 A, 1 B)
