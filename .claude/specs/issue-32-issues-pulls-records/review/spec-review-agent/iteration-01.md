# Combined review (tier S), iteration 01 — issue #32

### B1 — `issues/get-issue-artifact` is left pending although `Paging.NONE` already declares it
Severity: B
Location: change.md § Acceptance criteria AC-1, AC-2, AC-3; § Residuals, first item
Defect: The ask's done-line "the six `PENDING` sets empty" is narrowed on a "design choice" that existing machinery settles: the section documents `page` and `per_page` as query rows (`rest/issues.md` "Get an issue artifact"), so a `Paging.NONE` record prints the artifact with one page of `versions` and any page by `--query page=N`; the sibling slice #27 (its AC-4 and Residuals) declares the same class, an object holding a paged list (`conventions.md` "Lists wrapped in an object": `repos/get-commit`, `repos/compare-commits`), exactly so.
Material-because: the ask's AC-2 ("The six `PENDING` sets SHALL be empty") is contradicted where nothing forces it.
Proposed-edit: AC-1 "except `pulls/update-branch`"; AC-2 "`pulls.PENDING` SHALL be `{"pulls/update-branch"}` and the other five `PENDING` empty"; AC-3 first bullet, append "; `issues/get-issue-artifact`, whose `Paging:` line pages the `versions` inside one artifact, SHALL be `Paging.NONE` with `item_key` `None`"; Residuals first item becomes "`issues/get-issue-artifact` prints one page of `versions`; paging a list inside an object needs a record field (as #27's `repos/get-commit`)."

### B2 — the change's choices between alternatives are not in the decision log
Severity: B
Location: decisions/decision-log.md (DL-001 only); change.md § Files (`call.py`, K rows), § Residuals
Defect: Three choices between alternatives — `pulls/update-branch` pending against the ask's done-line (vs declared ungated, or hook-gated), `pulls/merge-async` gated to `merge-pr` (vs a hook gate), K edited outside #28 D8's slice table — are unlogged; the log holds only the tier call.
Material-because: unmaintainable-by-rule `agent-state-convention.md` §2 rule 4 (an entry is owed for a design choice between alternatives).
Proposed-edit: append, in the §2 schema: DL-002 `pulls/update-branch` stays pending (it commits to the head branch; `GATED_OPERATIONS: Mapping[str, str]` has no subcommand to name; ungated contradicts #28 Residuals); DL-003 `pulls/merge-async` → `merge-pr` (its body carries `merge_action` `direct_merge` and `bypass_rules`, `rest/pulls.md` "Merge a pull request asynchronously"); DL-004 K's pending-ID case moves to `pulls/update-branch` because this slice declares `pulls/list`.

### C1 — the `pulls/update-branch` residual names a choice #27 is settling
Severity: C
Location: change.md § Residuals, second item
Defect: #27's AC-7 maps every record "whose call commits to, creates, moves or renames a branch" to `None`; `pulls/update-branch` is of that class, so after #27 lands its gate is one entry, not DESIGN-OPTIONS. No other semantic conflict: #27's `None` wording and this change's "use the <subcommand>" wording are disjoint branches of `refuse_gated`; #27 leaves K unedited.
Proposed-edit: "`pulls/update-branch` stays pending: it commits to the pull request's head branch and no subcommand sends it; once #27's `Optional[str]` `GATED_OPERATIONS` lands it is declared and mapped to `None` (#27 AC-7's class), and K's pending-ID case moves."

### C2 — the installed issue-filing gate refuses `call issues/create-issue-artifact`
Severity: C
Location: change.md § Residuals (new line); AC-5 for `issues/create-issue-artifact`
Defect: `src/hooks/gate_filing.py` `CREATE_RE` `(create-issue|issue\s+create)` is a substring search: this review's Bash call naming `issues/create-issue-artifact` was refused, "BLOCKED by issue-filing-gate: this issue body is missing required provenance line(s): Origin: Subject: Filing-rationale:". The record passes AC-5 on the fake host and is refused in every hooked session.
Proposed-edit: Residuals line "`gate_filing.CREATE_RE` matches inside `issues/create-issue-artifact` and blocks its `call` (observed in review); small and clear (a word-bounded pattern, one `src/hooks/tests/test_gate_filing.py` case) → fixed per `issue-filing-discipline.md` branch 2, outside this slice's files."

### C3 — the usage still names two refused IDs
Severity: C
Location: change.md § Residuals (new line)
Defect: The entry script's usage (#28 D7) lists `pulls/merge` and `issues/create` as the refused IDs; this change refuses `pulls/merge-async` too, and #28 D8 bars a slice from `github_wrapper.py`.
Proposed-edit: Residuals line "The usage docstring names only `pulls/merge` and `issues/create` as refused; #28 D8 bars a slice from it." (#27's line.)

### C4 — F's oracle source is implied, not bound
Severity: C
Location: change.md § Tests AC-3, AC-4
Defect: AC-3's test compares the module's `Paging.LINK` IDs with F's paged cases and AC-4's routes judge `item_key`; both prove the transcription only while F's IDs and item keys come from the sections, not from the records.
Proposed-edit: Tests preamble, append "F's IDs, paths and item keys are transcribed from the sections and `conventions.md`, never read from the records."

### D1 — "Never edited" contradicts the `call.py` row
Severity: D
Location: change.md § Files, closing line
Defect: `commands/*` is in #28 D8's "never" row; the table edits `commands/call.py` through D8's exceptions row.
Proposed-edit: "Never edited: the rest of #28 D8's "never" row (`commands/call.py` only by its exceptions row) and `docs/forLLMConsumption.md`."

### D2 — docstrings that go stale beyond "every ID is pending"
Severity: D
Location: change.md § Files, family-module and K rows
Defect: `pulls.py` says "none of them pages" and names only the compatibility records; `issues.py` says "both list operations return a bare array"; K's `_gated_cases` says "the two records" and `OP_PULLS_LIST`'s comment calls it pending.
Proposed-edit: family row "…; each module docstring describes the records it now holds"; K row, append "; the `_gated_cases` docstring and the pending-ID constant's comment follow".

### D3 — headroom under the cap
Severity: D
Location: change.md § Residuals
Defect: The file is just under its cap and B1, C1–C3 add text.
Proposed-edit: delete "Choosing a section's custom media type per call stays #28's requirements residual." (#28's own residual).

## Coverage (all lenses)

| Criterion | Test | Fails when | Red after TEST |
|---|---|---|---|
| AC-1 | N record test; V covered-or-pending, one-module | a name, method or path differs; an ID neither declared nor pending | no (unchanged); F AC-2 is red |
| AC-2 | F `test_only_the_residual_ids_are_pending` | a `PENDING` differs from the residual set | yes |
| AC-3 | F `test_the_records_follow_the_transcription_rules`; AC-4 routes | LINK set differs from F; non-empty `multi_segment`; non-default version or media type; wrong `item_key` exits 1 | yes |
| AC-4 | F `test_a_paged_record_prints_every_page` | an item or page missing; `--query per_page=1` refused (every `Paging:` line of the six files is page-based with `per_page`) | yes (exit 2) |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | method, path or names differ; a refusal | no (unchanged) |
| AC-6 | K gated case `pulls-merge-async-is-merge-pr` | the refusal lacks `merge-pr`; an ungated `PUT` is unrouted | yes |
| UB-1 | C golden cases; P; diff | a subcommand's output or parser changes | n/a |
| UB-2 | K gated and unknown cases (pending case on `pulls/update-branch`) | a gated ID sends; a pending ID sends | n/a |
| UB-3 | C credential; V stdlib | `environ`/`getenv` or a non-stdlib import | n/a |
| UB-4 | `test_wrapper_delivery.py`; diff | either file edited | n/a |

Security: gating `pulls/merge-async` keeps the gates' guarantee (`refuse_gated` runs before `lookup`); `pulls/update-branch` pending is the safer reading (nothing is sent). No path parameter of the six files is multi-segment; AC-5's three unreachable IDs are every `{org}` row of these families.

Verdict: NOT-READY (0 A, 2 B)
