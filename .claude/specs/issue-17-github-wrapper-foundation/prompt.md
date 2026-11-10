# Prompt — issue #17: GitHub wrapper rewrite, part 1 (design, core transport, today's subcommands, coverage test)

Tier: M — a design choice (the operation layer and its layout) plus a transport, a subcommand migration and a
coverage test across modules; the issue's own tier line. Re-tier to L only if the layer becomes a generated package.

Kind: FEATURE.

## Goal

The product wrapper `src/payload/scripts/github_wrapper.py` is a skeleton (`main` raises `NotImplementedError`;
`_api_request` pins `X-GitHub-Api-Version: 2022-11-28` and sets `Authorization` with `add_header`, which urllib
copies to a redirect target). Sessions here run an adopted fork installed as `scripts/github_wrapper.py`
(`config/toolchain.json` `deviations`). Part 1 builds the foundation of #12: the structure decision, the REST and
GraphQL transport, today's caller-facing subcommands on that transport, and the coverage test that part 2 (#14)
drives to green. Workers use `docs/api-reference/github/` (`conventions.md`, `graphql/conventions.md`, `rest/*.md`,
`operations-index.md`) and the official GitHub page each entry links.

## Scope (the ask — issue #17 AC-1..AC-5, UB-1..UB-3)

- AC-1 the operation-layer decision (generic reference-driven, hand-written, or a mix) and a layout under which part
  2's families are added without editing one shared file wherever possible.
- AC-2/AC-3 REST transport: `X-GitHub-Api-Version` on every request; `Link` pagination incl. lists wrapped under an
  item key; uploads via `upload_url`; no `Authorization` to another host on redirect; bounded rate-limit retry on
  `403`/`429` per `retry-after` / `x-ratelimit-reset`, then an error naming the limit; other errors raise
  `GitHubAPIError` with status and documented body.
- AC-4 GraphQL: POST `query` + `variables`, follow `pageInfo` cursors, raise on a top-level `errors` array even with
  HTTP 200.
- AC-5 a test that fails for any `operations-index.md` operation or "Only in GraphQL" capability neither covered by a
  wrapper call nor on an explicit pending list.
- UB-1 every subcommand that `clients/`, `src/hooks/` and `src/payload/` call today keeps the arguments, output and
  exit codes of the installed fork; UB-2 credentials only from `credentials/github-pat.txt`, Python 3.9 standard
  library only; UB-3 `gitlab_wrapper.py` and `src/payload/test/test_wrapper_delivery.py` untouched and passing.

Decided at CLASSIFY (DL-001), the issue's open questions:
- `wait-landed`, `check-handoff`, `check-landed` are called by `clients/` (the steward delivery verbs) and are not in
  the fork: UB-1 covers them as they behave today in the product skeleton (its `DELIVERY_VERBS` delegation to
  `merge_steward.py`), not as fork behaviour.
- The default API version stays `2022-11-28` (what the skeleton and the fork send today — no caller-visible change);
  `2026-03-10` is selectable.
- The pending list is split per operation family (one file per family), so part-2 workers never edit a shared file;
  any file that stays shared is named with its reason (AC-1).

## Out of scope

- Part 2's remaining operations (#14); the real-forge test on the #10 fixture (blocked on the operator's token —
  its work item stays open on this issue until #10 lands); promoting the new wrapper over the fork.

## Integration points

- `src/payload/scripts/github_wrapper.py` (`main`, `_api_request`, `_load_token`, `GitHubAPIError`,
  `DELIVERY_VERBS`); `scripts/github_wrapper.py` `_build_parser` (read only — the reference behaviour);
  `src/hooks/hooklib.py` `project_wrapper`; every caller in `clients/`, `src/hooks/`, `src/payload/`, `prompts/`.

## Tests

Fake-host unit tests (no network) for the transport and every migrated subcommand; the AC-5 coverage test reads
`operations-index.md`. E2E: the real-forge run belongs to #10's fixture; this change adds no deployed runtime
behaviour, and CI's `tests` group runs the new suites.
