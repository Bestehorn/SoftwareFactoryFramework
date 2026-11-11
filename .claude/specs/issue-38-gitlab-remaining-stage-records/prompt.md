# Prompt — issue #38: GitLab wrapper rewrite, part 2 slice: the remaining 14 stage groups

Tier: S — data records and their fake-host tests in 13 family modules on part 1's record type and #41's `call`; deploy's three `ml_models` keys, the only ones needing the optional `(*path/)` segment, move to #40, which owns that form (DL-001).

Kind: FEATURE.

## Goal

The issue's Ask: each pending key of the slice's family modules gets a record transcribed from its `docs/api-reference/gitlab/rest/<stage>.md` section, callable through `call <operation-id>` (#41), passing `test/test_gitlab_wrapper_contract.py` and the coverage test, with the modules' `PENDING` emptied but for keys a missing request form keeps pending (routed as #41's design D8 directs).

## Scope

The issue's ACs and UBs (issue body), for tenant_scale, gitlab_dedicated, analytics, runtime, fulfillment, growth, gitlab_delivery, orbit, data_access, developer_experience, agent_foundations, facilitated_functionality and ai_clients. Out of scope: `families/deploy.py`'s three keys (#40, DL-001); other families; the real-instance run (#11).
