# Prompt — issue #63: GitLab wrapper rewrite, part 2 slice: request forms the records lack

Tier: M — six request forms across the GitLab registry, transport, `call` and the contract test, each a design choice (issue #63 "Tier: M"; DL-001).

Kind: FEATURE.

## Goal

#15 AC-3 needs every GitLab family's `PENDING` empty. The keys this issue names stay pending because each needs a request form the record layer does not build. Build the forms, and give each key its record.

## The forms (issue #63, as filed on origin/main 7ec47d1)

- F1 several endpoints under one Reference: `registry.lookup` refuses an ID declared twice. 37 keys plus #43's Conan v1 and NuGet `/v2` keys (#43 DL-003).
- F2 one name, two meanings: `expand` writes one value at every `:id`. 5 keys (`/groups/:id/ssh_certificates/:id`, `/groups/:id/manage/*_access_tokens/:id`).
- F3 `[.format]`: `PLACEHOLDER` reads `:name` only. 1 key (`/projects/:id/repository/archive[.format]`).
- F4 another origin: `Transport._send` refuses every other origin. `https://HOST/oauth/token/info` and #43's two `${CI_REGISTRY}` keys (#43 DL-002).
- F5 request headers: `_build_request` sends none of a caller's. 1 key ("Set status of an external control"); #40's NuGet symbol records omit `Symbolchecksum`.
- F6 two-level members: the contract test's `PARENT_KEY` reads one `parent[key]` level. 1 key (`POST /projects/remote-import-s3`).

## Scope

The six forms, the records for the keys above, the usage docstring and `docs/forLLMConsumption.md`. Out of scope: the gated kept IDs (#15's `None` gate slice), #40's path forms, #43's route prefix, the real-forge run (#10).

## Depends on

#40 (PR #62: `PLACEHOLDER` sigil, `OPTIONAL_GROUP`, `expand`, `Transport.request_raw`, `call --input`) and #43 (the package records, the route prefix). Implementation starts after both land on the trunk; this branch is rebased then.
