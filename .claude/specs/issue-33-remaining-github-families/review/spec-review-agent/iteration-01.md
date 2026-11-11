# spec-review-agent — iteration 01 (tier S, combined: all lenses) — issue #33

### C1 — DL-003 and DL-004 are not on #33, so two of its items cannot close over them
Severity: C
Location: decisions/decision-log.md DL-003, DL-004; issue #33
Defect: The only comment on #33 (6786847717) records the `markdown/render-raw` deferral alone. DL-004 keeps
`copilot/set-copilot-content-exclusion-for-organization` pending against the Ask ("leaving each module's `PENDING`
empty") and the item "Copilot and agent families", and DL-003 makes seven records refused by `call`. Neither is on the
issue, and `issue-tracking.md` "Closing" requires the deferral there, recorded when it is decided.
Proposed-edit: none in change.md. Post on #33: "DL-004: `copilot/set-copilot-content-exclusion-for-organization` stays
pending: its body is a map of any key, which `call` cannot send; a findings-ledger row records it. That defers the item
'Copilot and agent families' for that one ID. DL-003: the seven records whose call writes a branch or creates issues are
declared and refused by `call` (`GATED_OPERATIONS`, no subcommand)."

### C2 — The media-type residual has no route
Severity: C
Location: change.md § Residuals, third bullet
Defect: The bullet cites #28's requirements residual, which no issue covers (#31 review iteration 01, B1). On f374b3d
`docs/findings-ledger.md` has no per-call `Accept` row (#31's DL-005 row is on its unmerged branch), and only the first
bullet is marked "→ ledger", so the Files row's "the Residuals' ledger rows" does not include this one. Left like
this, it is dropped (`issue-filing-discipline.md` "The findings ledger").
Proposed-edit: "not their named `raw`/`html` types (#28's\n  requirements residual)." → "not their `raw`/`html` types
(#28's\n  requirements residual) → ledger." (+5 B)

### D1 — The Files closing line misplaces `commands/call.py` and leaves out the ledger
Severity: D
Location: change.md § Files, closing line
Defect: The `GATED_OPERATIONS` edit falls under #28 D8's exceptions row, not outside D8. The ledger is a doc, and this
change edits it.
Proposed-edit: "Outside #28 D8's slice table only N and `commands/call.py` are edited; no other doc is." →
"Beyond #28 D8's slice table and exceptions row only N is edited; no doc but the ledger." (0 B)

### D2 — Not every structural test in F is red after TEST
Severity: D
Location: change.md § Tasks, red line
Defect: 11 families have no paged ID: `agent_merge`, `classroom`, `codes_of_conduct`, `credentials`, `emojis`,
`gitignore`, `interactions`, `markdown`, `meta`, `oidc`, `rate_limit`. In these, `OPERATIONS` is empty and both
`Paging.LINK` sets are empty, so `test_the_records_follow_the_transcription_rules` passes. The pending test is the only
one that fails in all 31 families.
Proposed-edit: "F's structural tests fail" → "F's pending tests fail" (−3 B)

With all four edits applied, change.md is 7,993 B.

## Checked, no finding

- **Gating (AC-6).** Of the 379 sections, these seven write a branch or create issues:
  - `agent-tasks/create-task-in-repo`: its body has `create_pull_request`, `base_ref` and `head_ref`.
  - `agent-merge/put-agent-merge-enrollment`: `allowed_actions` takes `fix_ci` and `resolve_merge_conflicts`.
  - The three automation writes: they carry `write_scope` `repository`, or run the automation.
  - `codespaces/export-for-authenticated-user`: GitHub's docs say "If changes cannot be pushed to the codespace's
    repository, they will be pushed to a new or previously-existing fork", and the export details have a `branch`.
  - `campaigns/create-campaign`: it has `generate_issues`, which `campaigns/update-campaign` lacks.

  The records left callable, correctly:
  - `codespaces/publish-for-authenticated-user` creates a repository ("allowing the user to push").
  - `security-advisories/create-fork` and the `start_private_fork` bodies create a fork.
  - The Source Imports records were removed on 2024-04-12.
  - `pull-request-stacks/*` take only PR numbers.

  No ID holds `create-issue`. `refuse_gated` tests membership and runs before `lookup`, and K and C read no
  `GATED_OPERATIONS` entry.
- **Pending (AC-2).** `markdown/render-raw` is the only non-JSON request body in the 31 families. #46's AC-5 and its
  work item name it. The content-exclusion `PUT` is the only `*` body. A `{"*"}` record would pass N and still send a
  member named `*`, so DL-004 holds.
- **Paging (AC-3, AC-4).**
  - 62 sections have a `Paging:` line. All are `GET`, all name `per_page`, and their keys match `conventions.md` "Lists
    wrapped in an object".
  - 12 sections have a `Link` header and no `Paging:` line. Only `dependency-graph/diff-range` answers an array; the
    other 11 answer one object.
  - No section has paging parameters without a `Paging:` line.
  - Paged IDs occur in 20 families. `diff-range` has no `per_page`, so its case is one page of two items.
- **Record fields.** No row reads "may contain `/`", so `multi_segment` stays empty. The only "Media types named" are
  the two in the third Residuals bullet. Every section's method and path equal its index row, and its placeholders equal
  its path rows. The three `302` IDs are #28 D3's archive form, and no section answers `307`.
- **N edit (DL-005).** The edit is needed. With billing declaring `billing/update-budget-org`, step 3 makes
  `registry.lookup` fail with "declared 2 times", so the call exits 2. No other test of the three suites relies on an
  ID of these families being pending; N's `projects/add-field-for-org` pin reads a section only. N is not toolchain.
- **F shape.**
  - `pyproject.toml` does not set `empty_parameter_set_mark`, so an empty parametrization is a skip, and DL-006's
    absence rule is needed.
  - Every family has at least one record, so the transcription test is never empty.
  - `--import-mode=importlib` means the new file names cannot clash.
- **Security.**
  - No credential path changes (UB-4).
  - `agents/update-*-variable` documents `name` in both the path and the body, and `check_call` accepts both.
  - `credentials/revoke` takes plaintext tokens as `-F credentials=[…]`. That is #28 Residuals' command-line class, and
    no edit is owed.

## Coverage

| Criterion | Test | Fails when | Red after TEST |
|---|---|---|---|
| AC-1 | N record test; V covered-or-pending, one-module | a method, path or name differs; an ID neither declared nor pending, or both | no (F AC-2 is) |
| AC-2 | F `test_only_the_residual_ids_are_pending` | a `PENDING` holds more or less than its AC-2 IDs | yes, 31 files |
| AC-3 | F `test_the_records_follow_the_transcription_rules`; AC-4 routes | the LINK set differs from F's paged IDs; `multi_segment` is set; another version or media type; a NONE record has an `item_key`; a wrong `item_key` exits 1 | 20 families; vacuous in 11 (D2) |
| AC-4 | F `test_a_paged_record_prints_every_page` | an item or page is missing; `per_page` is refused | yes (exit 2) |
| AC-5 | N every-record test; N unreachable test (edited) | exit not 0, a refusal, or the names differ; a double declaration | no |
| AC-6 | F `test_a_branch_writing_record_is_refused`, literal IDs in 5 families | an ID is sent, exits other than 2, is undeclared, or its log lacks the ID or the refusal | yes (no record) |
| UB-1 | C golden cases; P parity | a subcommand's output, exit code or parser changes | n/a |
| UB-2 | K gated and unknown cases; F AC-2 test + V; #27's F refusal tests | a gated, pending or unknown ID is sent | n/a |
| UB-3 | K non-JSON case; AC-3 keeps the three text records NONE | the body is re-encoded; one of them becomes LINK | n/a |
| UB-4 | C credential test; V stdlib test | `environ`/`getenv`, a token option, or a non-stdlib import | n/a |
| UB-5 | `test_wrapper_delivery.py`; the PR diff | either file is touched or fails | n/a |
| E2E | N and F through `main` to the API boundary (CI `verify`/`tests`); the real-forge check is #10's | — | — |

Verdict: READY
