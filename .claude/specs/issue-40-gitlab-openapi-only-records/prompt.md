# Prompt — issue #40: GitLab wrapper rewrite, part 2 slice: the OpenAPI-only operations

Tier: M — records for every key the index links to `rest/openapi-only.md` (267 in `families/openapi_only.py`, and the three `ml_models` file keys `families/deploy.py` holds), plus the request forms part 1 left to #15: the `*name` glob, the optional `(*path/)` segment, and the escaped OData parentheses; the raw-body question is answered against #41's `call`.

Kind: FEATURE.

## Goal

The issue's Ask: each pending key gets a `RestOperation` transcribed from its `docs/api-reference/gitlab/rest/openapi-only.md` entry, reachable through `call <operation-id>` (#41), with fake-host tests, and `PENDING` empty; the path forms it needs land in `registry.py` with their tests, so the package slice (#43) can reuse them.

## Scope

The issue's ACs and UBs (issue body). Also in scope (DL-001): the three `ml_models` keys of `families/deploy.py` that link to `rest/openapi-only.md` and need the optional segment, moved here from #38. Out of scope: other families; the package slice's `<route-prefix>` and registry-host forms (#43); the real-instance run (#11). The issue's open questions are decided in the design and the decision log.
