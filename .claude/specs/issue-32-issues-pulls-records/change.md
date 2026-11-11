# Change — issue #32: GitHub wrapper rewrite, part 2 slice: issues, pulls, reactions, search, activity, gists

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn"); its D8 names
what a slice edits. Test files: N, V, K, C, P as #28's mapping; F = `src/payload/test/test_github_api_<family>.py`;
G = `src/hooks/tests/test_gate_filing.py`.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."

## Ask

Issue #32: "Cover #14's slice 'Families: issues, pulls, reactions, search, activity, gists'. … Done: each pending ID
has a record transcribed from its `rest/<category>.md` section, called through the generic operation command of #28
…, with fake-host tests, and the six `PENDING` sets empty."

## Acceptance criteria

- AC-1: Every ID on the six family modules' `PENDING` at aafecbb except `pulls/update-branch` (DL-002) SHALL have one
  `RestOperation` in its module whose method and path are its index row and whose path, query and body names are its
  section's, as N reads them (#28 D5).
- AC-2: `pulls.PENDING` SHALL be `{"pulls/update-branch"}` and the other five `PENDING` empty.
- AC-3: Every record of the six modules SHALL carry:
  - `paging` `Paging.LINK` when its section has a `Paging:` line, else `Paging.NONE`; `item_key` the key
    `conventions.md` "Lists wrapped in an object" names for it (`items` for every `search/*` record), else `None`;
    except `issues/get-issue-artifact` (it pages the `versions` inside one artifact): `Paging.NONE`,
    `item_key` `None` (DL-004);
  - `multi_segment` empty;
  - `api_version` `API_VERSION_DEFAULT` and `accept` `ACCEPT_JSON` (`conventions.md` "Headers, media types and API
    versions").
- AC-4: WHEN a `Paging.LINK` record of these families is called as `call <id>` with `--path` for each path parameter
  but `owner` and `repo`, plus `--query per_page=1`, against a host serving two items over two pages under its item
  key, THEN it SHALL exit 0 and print `printed_json` of both items.
- AC-5: WHEN a record of these families outside `GATED_OPERATIONS` is called through `call` with a value for each
  parameter its section documents, THEN it SHALL exit 0 and send one request with the section's method, expanded path,
  query names and body names.
- AC-6: WHEN `call pulls/merge-async` is run, THEN it SHALL exit 2 with no request and log `pulls/merge-async` and
  `merge-pr` (DL-003).
- AC-7: WHEN every `create-issue` and `issue create` in a shell command has a word character, `/`, `.` or `-` directly
  before or after it, as in `call issues/create-issue-artifact`, THEN `gate_filing.run` SHALL allow it with no note
  (DL-005).

## Unchanged behaviour

- UB-1: The compatibility subcommands (`commands/issues.py`, `claim.py`, `pulls.py`, `ci.py`) and `CASES` SHALL CONTINUE
  TO behave as they do, and the existing records SHALL CONTINUE TO be declared as they are.
- UB-2: `call` SHALL CONTINUE TO refuse with exit 2 and no request `pulls/merge` and `issues/create`, naming `merge-pr`
  and `create-issue`, and an ID no record declares, pending or not in the index.
- UB-3: Credentials SHALL CONTINUE TO come only from `credentials/github-pat.txt`, and the package to import only the
  Python 3.9 standard library.
- UB-4: `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and to pass.
- UB-5: `gate_filing.run` SHALL CONTINUE TO block a `create-issue` or `issue create` call whose body lacks the
  provenance lines.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/families/{issues,pulls,reactions,search,activity,gists}.py` | records added to `OPERATIONS`, their IDs removed from `PENDING`; each module docstring describes the records it now holds |
| `src/payload/scripts/github_api/commands/call.py` | `GATED_OPERATIONS` gains `pulls/merge-async` → `merge-pr` (#28 D8's exceptions row; DL-003); its comment, the module docstring and `refuse_gated`'s message name the subcommand to use |
| F, one per family; G | new; G gains two cases |
| `src/payload/test/test_github_api_call.py` (K) | the AC-2.1 pending-ID case calls `pulls/update-branch` in place of `pulls/list`; `_gated_cases` gains `pulls/merge-async` (DL-004) |
| `src/hooks/gate_filing.py` | `CREATE_RE` skips a `create-issue` or `issue create` with a word character, `/`, `.` or `-` directly before or after it (DL-005) |

K and the hook files are outside #28 D8's slice table. Never edited: the rest of #28 D8's "never" row
(`commands/call.py` only by its exceptions row) and `docs/forLLMConsumption.md`.

## Tests

F's IDs, paths and item keys are transcribed from the sections and `conventions.md`, never read from the records.

- AC-1 — N `test_every_record_matches_its_reference_section`; V `test_every_operation_is_covered_or_pending`,
  `test_one_module_per_family_holding_only_its_own_ids` (unchanged).
- AC-2 — F `test_only_the_residual_ids_are_pending` (example).
- AC-3 — F `test_the_records_follow_the_transcription_rules` (example): the `Paging.LINK` IDs equal F's paged-case IDs
  (the `Paging:` sections but `issues/get-issue-artifact`, whose `item_key` it asserts `None`); `multi_segment`,
  `api_version` and `accept` as AC-3 states; the other `item_key`s are judged by AC-4's route.
- AC-4 — F `test_a_paged_record_prints_every_page`: one `GoldenCase` per `Paging.LINK` record of the family in #28
  D8's form, run with `fx.run_product_case`.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents` (unchanged); by D5's rule the `{org}` rows are
  unreachable, so N is their whole proof.
- AC-6 — K `test_a_gated_operation_names_its_subcommand`, new case `pulls-merge-async-is-merge-pr`.
- AC-7 — G `test_a_command_that_creates_nothing_is_allowed_without_a_note`, new case `call-create-issue-artifact`.
- UB-1 — C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`,
  `test_the_parsers_match_option_by_option`; the PR diff edits no existing record and no line of `CASES`.
- UB-2 — K `test_a_gated_operation_names_its_subcommand` (existing cases), `test_an_unknown_operation_is_refused`.
- UB-3 — C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library`.
- UB-4 — `src/payload/test/test_wrapper_delivery.py`; the PR diff names neither file.
- UB-5 — G `test_a_readable_provenance_free_body_is_blocked` (existing cases); new case `quoted-create-word`
  (`create-issue` double-quoted, inline body without provenance).
- E2E — no deployed system; the real-forge check is #10's. N and F call every record through `main`'s argv to
  the API boundary and G runs the gate on a hook payload, in `.github/workflows/ci.yml` job `verify`, leg `tests`
  (`python scripts/run_checks.py --group tests`).

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 to TEST-6, one per family | F | AC-2, AC-3, AC-4 |
| TEST-7 | K | AC-6, UB-2 |
| TEST-8 | G | AC-7, UB-5 |
| IMPL-1 to IMPL-6, one per family | `src/payload/scripts/github_api/families/<family>.py` | AC-1 to AC-5 |
| IMPL-7 | `src/payload/scripts/github_api/commands/call.py` | AC-6 |
| IMPL-8 | `src/hooks/gate_filing.py` | AC-7, UB-5 |

Red after TEST: F's cases exit 2 and its structural tests fail; K's `pulls/merge-async` case logs no `merge-pr`; G's
AC-7 case is blocked. Green after IMPL, N and V included.

## Residuals

- `issues/get-issue-artifact` prints one page of `versions`; paging a list inside an object needs a record field (as
  #27's `repos/get-commit`).
- `pulls/update-branch` stays pending (DL-002); once #27's `None` mapping lands, gating it is one entry and K's
  pending-ID case moves.
- `github_wrapper.py`'s usage names only `pulls/merge` and `issues/create` as refused; #28 D8 bars a slice from it.
