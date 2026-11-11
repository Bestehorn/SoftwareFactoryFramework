# Prompt — issue #43: GitLab wrapper rewrite, part 2 slice: the package stage group

Tier: M — records for every pending key of `families/package.py` plus the request forms part 1 lacks that only this group needs: the `/<route-prefix>` paths (Debian, npm, NuGet), the hyphenated placeholder (`:module-name`) and the container-registry host paths; the `*name` glob is #40's form, reused here (#40 DL-001).

Kind: FEATURE.

## Goal

The issue's Ask: each pending key gets a `RestOperation` from its `docs/api-reference/gitlab/rest/package.md` attribute table, or is excluded by the rule #41 records; each record is reachable through `call <operation-id>` (#41) with a fake-host test; `PENDING` is empty.

## Scope

The issue's ACs and UBs (issue body). Depends on #40 for the glob form: the design reuses #40's registry change, and this branch rebases onto it once #40 lands. Out of scope: other families; the real-instance run (#11). The issue's open questions are decided in the design and the decision log.
