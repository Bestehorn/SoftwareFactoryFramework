# Change — issue #31: GitHub wrapper rewrite, part 2 slice: actions, checks, code-scanning, dependabot, secret-scanning

Tier: S. Kind: FEATURE. Follows `.claude/specs/issue-28-generic-operation-command/design.md` ("#28 Dn").

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Backlog run: #28 landed (aafecbb); #31 selected, `prompt.md` from its body; no interview (`qa_log.md`).

## Ask

Issue #31: "Done: each pending ID has a `RestOperation` transcribed from its
`docs/api-reference/github/rest/<category>.md` section, called through the call mechanism of #28 …, with fake-host
tests, and the five `PENDING` sets empty." Open questions, DL-002: a secret write's `encrypted_value` and `key_id` are
`-f` values sent as given; `code-scanning/get-analysis` is one record, default media type.

## Acceptance criteria

- AC-1 Every ID on the `PENDING` of `families/{actions,checks,code_scanning,dependabot,secret_scanning}.py` at aafecbb
  SHALL have one `RestOperation` in its module's `OPERATIONS`, except `code-scanning/commit-autofix`:
  `code_scanning.PENDING` SHALL be exactly `{"code-scanning/commit-autofix"}` and the other four empty (DL-003).
- AC-2 Each new record's `method`, `path`, `query_params` and `body_params` SHALL be its section's as N's
  `reference_sections` reads it.
- AC-3 Each new record's `multi_segment` SHALL hold exactly the path parameters whose `Parameter` row reads "may contain
  `/` (multi-segment path)"; its `api_version` SHALL be `API_VERSION_DEFAULT` and its `accept` `ACCEPT_JSON`.
- AC-4 A new record SHALL be `Paging.LINK` when its section has a `Paging:` line, with `item_key` the key that line
  names after "items in", or `None` where it reads "the response body is the array". Every other record SHALL be
  `Paging.NONE` with `item_key` `None`, `actions/get-actions-cache-usage-for-org` and
  `actions/get-hosted-runner-for-org` included (a `Link` header on one object).
- AC-5 WHEN a record of these families is called with `call <id>` and a value for every parameter its section
  documents, THE wrapper SHALL send one request with the section's method, expanded path, query names and body names
  and exit 0, reachable or not (#28 D5).
- AC-6 WHEN a `Paging.LINK` record of these families is called with #28 D8's argv against a host serving two items
  under its `item_key` (one per page where it documents `per_page`), THE wrapper SHALL exit 0 and print `printed_json`
  of both.

## Unchanged behaviour

- UB-1 `commands/ci.py`'s subcommands, `get-pr-checks` and `CASES` SHALL CONTINUE TO behave as they do, on the
  records part 1 declared (#17), unchanged.
- UB-2 `call` SHALL CONTINUE TO refuse with exit 2 and no request `pulls/merge` and `issues/create`, naming `merge-pr`
  and `create-issue`, and an ID no record declares, `code-scanning/commit-autofix` included.
- UB-3 Credentials SHALL CONTINUE TO come only from `credentials/github-pat.txt`, imports only from the Python 3.9
  standard library.
- UB-4 `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` SHALL CONTINUE TO be untouched and to pass.

## Files

| File | Change |
|---|---|
| `src/payload/scripts/github_api/families/{actions,checks,code_scanning,dependabot,secret_scanning}.py` | records added to `OPERATIONS`, their IDs removed from `PENDING` per AC-1; each module docstring describes the records it now holds |
| F: `src/payload/test/test_github_api_{actions,checks,code_scanning,dependabot,secret_scanning}.py` | new |
| `docs/findings-ledger.md` | the Residuals' ledger rows, via `memory_compile.py ledger add` |

Nothing else: no file of #28 D8's "never" row (`commands/call.py` included: no record here is gated), no other doc.

## Tests

Example tests. F's IDs, paths, item keys and multi-segment names are literal tables transcribed from the sections,
never read from the records. In `src/payload/test/`: C = `test_github_wrapper_compat.py`, K =
`test_github_api_call.py`. N = `test/test_github_wrapper_contract.py`, P = `test/test_github_wrapper_fork_parity.py`,
V = `test/test_github_wrapper_coverage.py`; C, K, N, P, V unedited.

- AC-1 — F `test_nothing_is_pending` (four families), `test_only_the_branch_writing_record_is_pending`
  (`code_scanning`); V `test_every_operation_is_covered_or_pending`,
  `test_one_module_per_family_holding_only_its_own_ids`.
- AC-2 — N `test_every_record_matches_its_reference_section`.
- AC-3 — F `test_every_record_sends_the_default_version_and_media_type`,
  `test_the_multi_segment_parameters_are_the_sections` (`{operation_id: multi_segment}` over the family's records with
  one equals F's table of the "may contain `/`" rows: `checks/list-for-ref`, `checks/list-suites-for-ref` → `{"ref"}`;
  empty in the other four), plus AC-6's `checks/list-suites-for-ref` case with a `ref` holding `/`.
- AC-4 — F `test_every_list_record_has_a_case` (the family's `Paging.LINK` IDs equal F's case IDs, the `Paging:`
  sections) and AC-6's cases, which exit 1 on a wrong `item_key`.
- AC-5 — N `test_every_record_is_sent_as_its_section_documents`, the whole proof of the unreachable `{enterprise}` and
  `{org}` rows (#28 D5).
- AC-6 — F `test_a_list_record_prints_every_item`: #28 D8's one `GoldenCase` per `Paging.LINK` record, run with
  `fx.run_product_case`.
- UB-1 — C `test_a_subcommand_matches_its_golden_case`; P `test_the_fork_produces_the_golden_case`,
  `test_the_parsers_match_option_by_option`; the PR diff edits no existing record and no line of `CASES`.
- UB-2 — K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; F
  `test_only_the_branch_writing_record_is_pending`.
- UB-3 — C `test_the_credential_comes_only_from_the_file`; V `test_the_wrapper_imports_only_the_standard_library`.
- UB-4 — `src/payload/test/test_wrapper_delivery.py`; the PR diff names neither file.
- E2E — no deployed system; the real-forge check is #10's, on an `sff-test-*` repository. N and F run `call` through
  the product's `main` to the API boundary in `.github/workflows/ci.yml` job `verify`, leg `tests`.

## Tasks (one wave)

| Task | Files | Validates |
|---|---|---|
| TEST-1 to TEST-5, one per family | the family's F | AC-1, AC-3, AC-4, AC-6 |
| IMPL-1 to IMPL-5, one per family | `src/payload/scripts/github_api/families/<module>.py` | AC-1 to AC-6, UB-1 |

Red after TEST: F's cases of new records exit 2 and its structural tests fail. Green after IMPL: F, C, K, N, P and V.

## Residuals

- `code-scanning/commit-autofix` stays pending (DL-003): it commits to `target_ref` and no subcommand sends it; once
  #27's `None` mapping lands, gating it is one entry → ledger; the deferral is recorded on #31.
- The `actions` `302` downloads print the archive's bytes, fetched without the credential (#28 D3). No section here has
  a non-JSON request body or a `307`; `code-scanning/upload-sarif`'s Base64 `sarif` goes on the command line (#46).
- `code-scanning/get-analysis` and `code-scanning/get-codeql-database` send `ACCEPT_JSON` and print JSON; their SARIF
  and zip forms need a per-call `Accept`, outside #46's request forms → ledger (DL-005).
- `dependabot/repository-access-for-org`, `-for-enterprise` drop `default_level`, which no other call returns → ledger.
- Callable, writing no branch (#28 Security "Destructive operations"): `actions/create-workflow-dispatch`,
  `actions/review-pending-deployments-for-run`, `secret-scanning/create-push-protection-bypass`. Secret-scanning
  alerts print each `secret` unless `--query hide_secret=true`; the runner-token records print a live token (#28 D3).
