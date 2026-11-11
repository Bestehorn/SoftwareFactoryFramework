# Prompt — issue #39: GitLab wrapper rewrite, part 2 slice: the plan stage group

Tier: S — data records in the slice's family modules and their fake-host tests on the merged part-2a design (#41); re-tier to M only if a record needs a field or a request form part 1 and #41 do not build.

Kind: FEATURE.

## Goal

The issue's Ask: each pending operation of the slice's families gets a record transcribed from its `docs/api-reference/gitlab/rest/<stage>.md` section, callable through `call <operation-id>` (#41), passing `test/test_gitlab_wrapper_contract.py` and the coverage test, with the modules' `PENDING` emptied but for ids a missing request form keeps pending (routed as #41's design D8 directs).

## Scope

The issue's ACs and UBs (issue body). Out of scope: other families; the real-instance run (#11). The issue's open questions are reversible and decided in the decision log.
