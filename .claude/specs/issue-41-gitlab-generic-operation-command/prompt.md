# Prompt — issue #41: GitLab wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M — one design choice (how records reach the command line) across the command layer, its tests and the docs;
the issue's own tier line. It adds no family's records.

Kind: FEATURE.

## Goal

Part 1 (#13, merged 2eb1c9e) built `src/payload/scripts/gitlab_api/`: the transport (REST and GraphQL), the record
layer (`registry.RestOperation`, `GraphQLOperation`, `call`, `pages`, `expand`, `encode`), one family module per
index family holding 19 records and 1,973 pending `(method, path)` keys, an empty `graphql_only.py`, the
compatibility commands under `commands/`, and the coverage test `test/test_gitlab_wrapper_coverage.py`. #15 split the
remaining coverage into nine slices (#35–#40, #42–#44), all blocked by this child, which settles the design they follow
— on the GitHub sibling #28's design wherever the hosts allow, so that both wrappers expose records the same way.

## Scope (the ask — issue #41 AC-1..AC-5, UB-1..UB-3)

- AC-1 a record a family module or `graphql_only.py` declares is exposed as a documented call with its documented
  parameters.
- AC-2 an unknown operation or an undocumented parameter is refused before any request, naming the documented
  parameters, with a non-zero exit.
- AC-3 the spec records how a call is proven for operations a test project cannot reach (admin, instance, Dedicated,
  Geo), and a test exercises that method.
- AC-4 the spec records whether the `/<route-prefix>/...` package-manager protocol keys and the `Status: Experiment`
  GraphQL-only capabilities are covered or excluded by a rule the coverage test applies.
- AC-5 the usage docstring and `docs/forLLMConsumption.md` name how to call an operation, the map under its cap; the
  spec records the target index revision and how a regeneration reaches the coverage test.
- UB-1 every docstring subcommand keeps the argv and exit codes its callers use; UB-2 Python 3.9+ standard library
  only, credentials only from `config/gitlab.json`; UB-3 `src/payload/scripts/github_wrapper.py` and its tests
  untouched.

Decided at CLASSIFY (DL-001):
- The call mechanism follows #28's design (its frozen requirements and its design as approved); GitLab differences
  (path syntax `:id`, `encode`'s array/hash pairs, form and multipart bodies, OFFSET/KEYSET paging, the three token
  types, text responses such as job traces) are restated, not re-decided.
- AC-4: both are covered, not excluded — the operator's request behind #11/#15 is "the complete set of API features
  for both repo hosts"; an experimental capability is documented as such. Reversible: a later issue can exclude by
  rule.

## Out of scope

- Any family's records (the nine slices); the real-instance run (#11); promoting the new wrapper.

## Integration points

- `src/payload/scripts/gitlab_api/registry.py`, `transport.py`, `commands/` and the entry script
  `src/payload/scripts/gitlab_wrapper.py`; `test/test_gitlab_wrapper_coverage.py`;
  `src/payload/test/gitlab_wrapper_fixtures.py` (the fake host); `docs/api-reference/gitlab/`.

## Tests

Fake-host unit tests (no network) for the call path and its refusals; the AC-3 method exercised by a test; the
existing compatibility suites keep passing. E2E: the real-instance run belongs to #11; CI's `tests` group runs the
new suites.
