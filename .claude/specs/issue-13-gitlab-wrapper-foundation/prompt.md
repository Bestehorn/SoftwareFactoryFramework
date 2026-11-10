# Prompt — issue #13: GitLab wrapper rewrite, part 1 (design, core transport, today's subcommands, coverage test)

Tier: M — one wrapper with an open design choice, a transport, the subcommands and a coverage test; the issue's own
tier line. Re-tier to L only if the layer becomes a generated package.

Kind: FEATURE.

## Goal

The product GitLab wrapper `src/payload/scripts/gitlab_wrapper.py` is a skeleton (`main` raises
`NotImplementedError`; `_api_request`, `_load_config`, `GitLabAPIError`, `pipeline_wait`, `steward_delegate` exist;
the module docstring lists the caller-facing subcommands). Part 1 builds the foundation of #11: the operation-layer
decision, the REST v4 and GraphQL transport, the docstring subcommands served from it, and the coverage test part 2
(#15) drives to green. Workers use `docs/api-reference/gitlab/` (`conventions.md`, `graphql/conventions.md`,
`operations-index.md`, `rest/*.md`) and the official GitLab page each entry links.

## Scope (the ask — issue #13 AC-1..AC-5, UB-1..UB-3)

- AC-1 the operation-layer decision and a layout in which each part-2 endpoint family is added without editing a
  file another family edits; any shared file named with its reason.
- AC-2 REST v4: the configured token type's header (`PRIVATE-TOKEN`, `Authorization: Bearer`, `JOB-TOKEN`),
  URL-encoded path parameters, documented array/hash encoding, multipart files, offset pagination (keyset where only
  keyset exists).
- AC-3 no `PRIVATE-TOKEN`/`JOB-TOKEN` to another host on redirect; `429` waits `Retry-After` and backs off when
  GitLab.com omits the rate-limit headers; each documented error shape raises `GitLabAPIError`.
- AC-4 GraphQL: POST `/api/graphql`, cursor paging, `GitLabAPIError` for errors returned with HTTP 200.
- AC-5 a coverage test that fails for any `operations-index.md` endpoint neither mapped nor on an explicit pending
  list.
- UB-1 every docstring subcommand keeps the argv and exit codes its callers use, now on the new transport; UB-2
  standard library only, credentials only from `config/gitlab.json`; UB-3 `github_wrapper.py` and its tests
  untouched.

Decided at CLASSIFY (DL-001), the issue's open questions:
- The pending list is split per endpoint family (one file per family), so part-2 workers never edit a shared file.
- Callers outside the docstring: the requirements author greps `clients/`, `src/hooks/`, `src/payload/`,
  `prompts/` and `templates/` for every `gitlab_wrapper.py` invocation; any subcommand a caller uses that the
  docstring omits is added to UB-1 (a found caller, not new scope).
- The operation-layer structure SHOULD match the GitHub sibling's (#17, worked in parallel in this run) where the
  forges allow, so the two wrappers stay one design; the design records any deliberate difference.

## Out of scope

- Part 2's remaining endpoints (#15); the GitLab real-instance test target (stays on #11); promotion.

## Integration points

- `src/payload/scripts/gitlab_wrapper.py`; `src/hooks/hooklib.py` (wrapper discovery);
  `src/hooks/gate_merge_steward.py` `SCRIPT_KINDS`; `src/payload/test/test_wrapper_delivery.py` (the delivery verbs);
  `templates/config/gitlab.json.template`.

## Tests

Fake-host unit tests (no network) for the transport and every docstring subcommand; the AC-5 coverage test reads
`operations-index.md`. E2E: not applicable here — no deployed runtime behaviour; the real-instance run stays on #11.
CI's `tests` group runs the new suites.
