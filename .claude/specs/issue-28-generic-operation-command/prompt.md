# Prompt — issue #28: GitHub wrapper rewrite, part 2a (generic operation command, coverage-proof method, docs)

Tier: M — one design choice (how records reach the command line) across the command layer, its tests and the docs;
the issue's own tier line. It adds no family's records.

Kind: FEATURE.

## Goal

Part 1 (#17, merged 7f2a1a9) built `src/payload/scripts/github_api/`: the transport, the record layer
(`registry.RestOperation`, `call`, `pages`), one family module per index family holding 23 records and 1,249 pending
operation ids, `graphql_only.py` with 13 pending capabilities, the compatibility commands under `commands/`, and the
coverage test `test/test_github_wrapper_coverage.py`. Part 1's Residuals left one thing open for part 2: records no
compatibility command uses do not reach the command line. #14 split the remaining coverage into family slices (#27,
#29, #31, #32, #33) and a GraphQL-only child (#30); all of them are blocked by this child, which settles the design
they follow so that a slice covers its family by adding records and tests, without revisiting the design.

## Scope (the ask — issue #28 AC-1..AC-5, UB-1..UB-3)

- AC-1 a record a family module declares is exposed as a documented call taking the record's documented path, query
  and body parameters.
- AC-2 an unknown operation or an undocumented parameter is refused before any request, naming the documented
  parameters, with a non-zero exit.
- AC-3 the spec records how a call is proven for operations a test repository cannot reach (enterprise,
  organisation, billing, apps), and a test exercises that method.
- AC-4 the usage docstring and `docs/forLLMConsumption.md` name how to call an operation; the map stays under cap.
- AC-5 the spec records which `operations-index.md` revision the slices target and how a regeneration reaches the
  coverage test.
- UB-1 every subcommand `clients/`, `src/hooks/` and `src/payload/` call today keeps its arguments, output and exit
  codes; UB-2 credentials only from `credentials/github-pat.txt`, Python 3.9 standard library only; UB-3
  `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` untouched and passing.

Decided at CLASSIFY (DL-001): the issue's three open questions (generic subcommand vs per-family modules vs a mix,
and how each prints paginated and binary responses; the coverage-proof method; the target index revision) are design
choices with precedent in part 1's design, settled in `design.md` and reviewed there — no operator question.

## Out of scope

- Any family's records (the slices #27, #29, #31, #32, #33); GraphQL-only capabilities (#30); the real-forge run on
  #10's fixture; promoting the new wrapper over the installed fork.

## Integration points

- `src/payload/scripts/github_api/registry.py` (`call`, `pages`, `lookup`, `RestOperation`, `GraphQLOperation`);
  `src/payload/scripts/github_api/transport.py` (`request`, `pages`, `download`, `upload`); `commands/` and the entry
  script's `_build_parser`; `test/test_github_wrapper_coverage.py`; `src/payload/test/github_wrapper_fixtures.py`
  (the fake host); `docs/api-reference/github/` (`conventions.md`, `operations-index.md`, `rest/*.md`).

## Tests

Fake-host unit tests (no network) for the call path and its refusals; the AC-3 method exercised by a test; the
existing compatibility and fork-parity suites keep passing. E2E: the real-forge run belongs to #10's fixture; CI's
`tests` group runs the new suites.
