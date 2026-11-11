# spec-review-agent — iteration 01 (tier S, combined: all lenses)

### B1 — AC-2's "`Kind.SCALAR` for every other" has no test that can fail
Severity: B
Location: change.md § Tests, AC-2
Defect: F `test_every_param_is_typed_as_its_row` compares only the `ARRAY` names and the required names, so a record
that declares `Kind.HASH`, `ARRAY_OF_HASHES` or `FILE` for a `string`, `boolean`, `integer` or `number` row leaves
both tables unchanged. N compares names and `In` only (#41 Residuals "D5 compares names and `In` only"), and its call
half gives each `Param` a value of its DECLARED `Kind` (`typed_argument`), so that call still exits 0 with the same
body names. AC-6 pins four names of one record.
Material-because: AC-2 (the issue's AC-1 "`Param`s (location, `Kind`, required) match") is not tested; built wrong,
`call … -F use_inherited_settings=true` is refused with exit 2 (`registry.KIND_ACCEPTS`) while every listed test passes.
Proposed-edit: in § Tests, replace the AC-2 parenthesis "(`{operation_id: ARRAY names}` and … with no `fixed`)" with:

```
  (`{operation_id: {name: Kind}}` of every `Param` not `SCALAR`, and `{operation_id: required names}`, over the records
  with any, equal F's tables: the `array of strings` rows as `ARRAY`, and the `yes` rows; every record JSON-bodied with
  no `fixed`).
```

### C1 — AC-5's two path clauses rest on "routed by the fake host"
Severity: C
Location: change.md § Tests, AC-5
Defect: AC-5 requires `/groups/g%2Fsub/integrations` and `/projects/<project_id>/integrations`. An answer queued with
`FakeGitLab.script_next` serves any URL, so a wrong path fails the test only when each page is scripted at its exact
URL, as K `test_a_list_prints_every_page_as_one_array` scripts `…?per_page=100` and `…?per_page=100&page=2` and
asserts the sent list.
Proposed-edit: the AC-5 bullet becomes:

```
- AC-5 — F `test_a_list_record_prints_every_page`, one case per AC-3 record (#41 D8): each page scripted at its URL
  (`FakeGitLab.script`) and the sent `(method, URL)` list asserted (K `test_a_list_prints_every_page_as_one_array`).
```

### D1 — The destructive-operations residual leaves out two `PUT`s
Severity: D
Location: change.md § Residuals, third bullet
Defect: "every `Disable …` `DELETE` and `Set up …` `PUT`" omits "Update integration for a group" and "Update
integration for a project" (`PUT …/integrations/jira-cloud-app`), the two `PUT` sections not titled "Set up".
Proposed-edit:

```
- Callable, gated by none (#41 Security "Destructive operations"): every `DELETE` and every `PUT`; a `/projects/:id`
  record acts on the configured project when `id` is not given.
```

## Checked, no finding

- **AC-1.** The `PENDING` at 3beba95 equals the family's index keys; each key's Reference is distinct and names a
  section whose one endpoint is that key, the two `GET …/integration/google-cloud-platform-workload-identity-federation`
  included. No Reference carries two keys, so an empty `PENDING` is reachable.
- **AC-2's mapping is exact.** N's reader finds every row `In` `body`; Types are `string`, `boolean`, `integer`,
  `number` and `array of strings` (only `project_keys` of `set-up-jira` and `set-up-jira-issues`); Required is `yes` or
  empty. No member, alternation, `header`, `form` or footnoted row; "in OpenAPI only" and `**deprecated**` sit in Notes,
  so N demands those rows (DL-002). Only the `PUT` sections carry a table.
- **AC-3 (DL-004).** `conventions.md` "Pagination": offset "is the default and works on every list endpoint except where
  a page says otherwise"; neither list section says otherwise; precedent `ai-coding#list-merge-request-pipelines`. The
  list sections have no table, and N's `documented_paging` admits the `per_page` that `Transport.pages` adds.
- **AC-5, AC-6 are implementable.** `call.takes_project` defaults only a `/projects/:id` path; `registry.expand` sends
  `g%2Fsub`; `Transport._next_page_url` builds `page=2` from `x-next-page`. `KIND_ACCEPTS` takes `1` and `true` as
  `SCALAR`, `["A"]` as `ARRAY`, and `registry.encode` sends the four values as the JSON body.
- **No gated record (UB-2).** Every section configures, reads or disables an integration; none commits, merges or
  creates an issue, so `GATED_OPERATIONS` and `commands/call.py` stay untouched (#41 D8).
- **Secrets (DL-003, security lens).** The family has no query row, so no value reaches a URL (the `429` retry warning
  logs the URL). Refusals carry names and types only (`_split`, `json_member`, `check_parameters`, `_declared_values`);
  `--file` cannot reach a `SCALAR`. The command-line exposure is the ledgered residual; no ledger row on it exists yet
  (`memory_compile.py search secret`).
- **Reachability, E2E.** Both pages' Offering names GitLab.com and no path is under `/admin/`, `/geo/` or `/hooks/`, so
  #11's run covers them; `ci.yml` job `verify` has the `tests` leg.
- **Files and Tasks.** TEST-1 and IMPL-1 name exactly the three Files rows; every named test exists at 3beba95; no
  GitLab test reads this module's docstring or IDs. change.md stays under 8,000 B with B1, C1 and D1 applied.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_nothing_is_pending`; V `test_every_index_row_is_mapped_or_pending`, `test_every_declared_key_is_in_its_family` | a key stays pending; an ID is missing or extra; a record's method or path is not its row's |
| AC-2 | N `test_every_record_matches_its_reference_section`; F `test_every_param_is_typed_as_its_row` | a name or `In` differs; an `array of strings` row is not `ARRAY`, a `yes` row not required, a FORM body or `fixed` pair; any other non-`SCALAR` `Kind` only after B1 |
| AC-3 | F `test_only_the_list_records_are_paged` | a list is not `OFFSET`, or another record is paged |
| AC-4 | N `test_every_record_is_sent_as_its_section_documents` | a call is refused, exits non-0, or sends another method, path or body names |
| AC-5 | F `test_a_list_record_prints_every_page` (two cases) | a page or item is missing (red: exit 2); a wrong path only with C1's exact-URL scripting |
| AC-6 | F `test_a_settings_write_sends_its_typed_body` | `project_keys` is not `ARRAY` (exit 2); another method or path; the body differs from the four values |
| UB-1 | C, unedited; PR diff | a compatibility subcommand's argv or exit code changes |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused`; PR diff | a gated or undeclared ID sends; `GATED_OPERATIONS` is edited |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`; K `test_call_takes_no_token_option`; P `test_standard_library_only` | an environment token, a token option, a non-stdlib import |
| UB-4 | `src/payload/test/test_wrapper_delivery.py`; PR diff | a GitHub wrapper file is touched or the delivery test fails |
| E2E | N and F through `main` to the API boundary, CI `verify`/`tests`; the real-instance run is #11's | — |

Verdict: NOT-READY (0 A, 1 B)
