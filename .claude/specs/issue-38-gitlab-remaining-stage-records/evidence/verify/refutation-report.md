# Refutation report: issue #38, the remaining 13 GitLab stage groups (tier S, one wave)

Tree: branch `issue-38-gitlab-remaining-stage-records`, HEAD b7424e9ab9359057791381fd231ce57431f3ab8a  # pragma: allowlist secret
Base: merge base 5c55448, PR #60. CI was read through `scripts/github_wrapper.py` from the main checkout. Every local
run was `scripts/run_tests.py -p no:cacheprovider --color=no <files>` in the worktree, driven by a disposable harness
(now deleted). The harness edits the CRLF working file at the byte level, deletes that module's bytecode, runs the
paired tests, writes the original bytes back and compares sha256. Captures are under `evidence/verify/`.

## The five steps

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | The whole suite is green on this SHA | `get-run 42997031572`, `get-jobs 42997031572` | FAILED-TO-REFUTE: completed/success, head_sha = HEAD, base = merge base, 5 of 5 jobs success | full-suite.txt |
| W1 | The wave's code is what F demands | 13 modules rewritten to their 5c55448 bytes; 13 F + N | FAILED-TO-REFUTE: 124 failed, 11 passed (every F test fails, N passes); restored | mutant-wave-1.txt |
| M | No record mutant survives F/N/V | 60 targeted mutants (table below), paired F + N (+V) | FAILED-TO-REFUTE: 60 of 60 KILLED on assertions, 0 errors; 60 of 60 sha256 restored | mutant-wave-1-records.txt |
| G | Green after restore | the 19 files of `evidence/green/wave-1.txt` (F, N, C, K, V, P, delivery) | FAILED-TO-REFUTE: 317 passed; `git diff --stat` empty | green-after-restore.txt |
| VAC | F is not vacuous | Grep of the 13 F files | FAILED-TO-REFUTE: no skip, xfail, importorskip, deselect or non-parametrize mark; 67 AC assertions, all `==`; no table read from records or pages (no `read_text`, `REST_DIR`, `OPERATIONS`-derived constant); 9 list parametrizations non-empty (W1 failed every case: tenant_scale 31, gitlab_dedicated 13, runtime 8, analytics 6, developer_experience 3, facilitated_functionality 3, fulfillment 2, growth 2, data_access 1); the 4 modules without one have no OFFSET record (AC-5) | grep; mutant-wave-1.txt |
| RED | Red fails for the right reason | Grep of `evidence/red/wave-1.txt` | FAILED-TO-REFUTE: 124 failed, all 124 `E   AssertionError`, 0 collection errors; W1 reproduces 124 failed / 11 passed | red/wave-1.txt; mutant-wave-1.txt |
| COV | Every changed line is exercised | diff of `origin/main...HEAD` | FAILED-TO-REFUTE: each new record is in its F AC-1 table and reached by both of N's discovery tests (reference half, call half); each PENDING entry by F AC-2 and V; the N edit is load-bearing (GD-T1); everything else is docstrings, comments, docs | mutant-wave-1-records.txt |

## Mutants by criterion (all KILLED; killing tests in the capture)

| Criterion | Mutants | Killed by |
|---|---|---|
| AC-1 records and endpoints | TS-I1 (Invitations list to its `/groups/` endpoint), TS-D1 (DL-003 `delete-a-shared-project-link-in-a-group` moved into tenant_scale.py), FU-E1 (second LDAP endpoint), AF-D1 | `test_every_reference_has_its_record`; V `test_every_index_row_is_mapped_or_pending` (TS-I1) |
| AC-2 PENDING | TS-U1 (revoke-PAT key, record declared), GD-U1 (local-archive import, record declared), AF-U1 (`trigger-a-flow`, record declared), OR-U1 (`*path` glob, record declared), DX-U1; TS-U2, GD-U2 (mapped key put back) | `test_only_the_kept_keys_are_pending` (+ AC-1 test, N for declared records) |
| AC-3 Param names and places | TS-N1, GD-N1 (body name dropped), GD-M1 (`upload[url]` its own Param), AN-N1 (`not[author_username]` dropped), FF-N1, GR-B1 | N `test_every_record_matches_its_reference_section` |
| AC-4 Kind | TS-K1 (avatar FILE→SCALAR), TS-K2, TS-K3 (HASH→SCALAR), TS-K4 (ARRAY_OF_HASHES→ARRAY), GD-K1 (`entities`→ARRAY), GD-K2, GD-K3, GD-K4, AN-K1, RT-K1, GR-K1, OR-K1, DX-K1, DX-K2, AI-K1 | `test_every_param_is_typed_as_its_row` |
| AC-4 required | TS-R1 (false→true), TS-R2, GD-R1 (true→false), GD-R2 (`upload` true), RT-R1, FU-R1, GDL-R1, AI-R1 | same |
| AC-4 body, fixed | TS-B1 (JSON→FORM), GR-B1 (`force-a-variant-assignment` FORM→JSON), TS-B2, GD-F1 (a `fixed` pair) | same (+ N both halves for `fixed`, N for GR-B1) |
| AC-5 paging | OFFSET→NONE: TS-P1, GD-P1, RT-P1, FU-P1, GR-P1, DA-P2, DX-P1, FF-P1 (`page`-row rule); NONE→OFFSET: TS-P2, GD-P2; DL-003 one-object lists: AN-P1, AN-P2, GDL-P1, OR-P1, DA-P1, AF-P1 | `test_only_the_list_records_are_paged` |
| AC-6 one request as documented | TS-B2, GD-F1, AF-D1 | N `test_every_record_is_sent_as_its_section_documents` |
| AC-7 every page | each OFFSET→NONE mutant above | its `test_a_list_record_prints_every_page[...]` case |
| AC-8 bytes unchanged | AF-D1; W1 (all three downloads) | `test_a_download_is_written_unchanged` |
| DL-004 N edit | GD-T1 (append instead of replace) | N `test_an_unreachable_call_matches_its_reference_section` |

## Reference spot-check (13 pages, 47 sections read against the records)

tenant-scale: create an organization, transfer users, list all topics, list all projects (DL-003 record, `topic`
string → SCALAR, `custom_attributes` hash → HASH), add a member (the `/projects/:id/` endpoint taken), revoke a PAT
(two `:id`, pending). gitlab-dedicated: update a Geo site, start a migration (`configuration` Hash, `entities` Array,
both required, members carried), reassign placeholders (FILE, required), export a project (`upload` HASH not required,
`upload[url]` carried), local-archive import (pending). analytics: upload metric image, non-SQL metrics, track events.
runtime: the two member lists, change state, add a member. fulfillment: deprecated LDAP delete, create a license, SCIM
identities, `extern_uid`. growth: create a broadcast message, list experiments, force a variant. gitlab-delivery:
Sidekiq metrics, delete jobs, update override. orbit: grep, context, named query, skill file (pending).
data-access: last 20, mark, pending. developer-experience: path parameters, namespaced paths, file path (two
pending), Sudo (first 7 rows). agent-foundations: trace, privileges, trigger and restart (pending).
facilitated-functionality: the three event sections. ai-clients: generate a chat response. Each record's method,
path, Param names and places, Kind, required and paging match its section; every kept key's reason matches AC-2.

## Unchanged behaviour and ledger

| Id | Command | Result |
|---|---|---|
| UB-1 | C (`test_gitlab_wrapper_compat.py`) in run G | FAILED-TO-REFUTE: green |
| UB-2 | K `test_a_gated_operation_names_its_subcommand`, `test_an_unknown_operation_is_refused` (pending-only and undeclared IDs) in G; `call.py` `GATED_OPERATIONS` holds the two IDs; no `commands/` file in the diff; F asserts the kept IDs have no record | FAILED-TO-REFUTE |
| UB-3 | C `test_load_config_refusals`, `test_environment_token_ignored`, P `test_standard_library_only` in G; the 13 modules import only `__future__`, `typing`, `gitlab_api.registry` | FAILED-TO-REFUTE |
| UB-4 | `git diff --name-only origin/main...HEAD`: no `github_wrapper.py`, `github_api/` or GitHub test; `test_wrapper_delivery.py` green in G | FAILED-TO-REFUTE |
| Ledger | the four added rows, bytes of the committed diff | FAILED-TO-REFUTE: 225, 205, 176, 220 B (each ≤ 240) |

Observation, no criterion: `docs/lessons-learned.md` gains a five-line entry (decision-log timestamps). change.md
"Files" names only `docs/findings-ledger.md` among docs ("no doc"). The entry carries no behaviour, and CI's corpus
budget test passed on this SHA.

## Tree restored

Every mutated file was written back from its saved bytes, and its sha256 equals the original for all 61 mutants (W1:
13 files; 60 targeted: 61 file edits). `git status --porcelain` before and after shows only
`?? .claude/specs/issue-38-gitlab-remaining-stage-records/evidence/verify/`, and `git diff --stat` is empty. The
worktree is byte-identical apart from this report and the four captures. Nothing under `.kiro/` was touched.

Verdict: VERIFIED
