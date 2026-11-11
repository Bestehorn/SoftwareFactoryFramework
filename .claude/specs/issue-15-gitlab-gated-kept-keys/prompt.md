# Prompt — issue #15: GitLab wrapper rewrite, part 2 — the kept keys

Tier: S — records on the existing record type and the existing `None` gate of `commands/call.py` `GATED_OPERATIONS` (#44's form), so that every GitLab family's `PENDING` is empty (#15 AC-3, completing #11 AC-1).

Kind: FEATURE.

## Goal

After #43 (the package records, PR #65) and #63 (the request forms) land, the keys left in the GitLab families' `PENDING` are the ones each slice kept on purpose: calls that write a branch or an existing project, which no subcommand sends (for example `ai-coding` "Rebase a merge request", the `create` branch writers, the `plan` clone and merge-note writers, the `verify` merge-train add, the `agent-foundations` workflow starts, the `gitlab-dedicated` existing-project imports, `PUT /projects/:id/`), plus `orbit`'s `GET /orbit/skills/:name/*path`, which waited only for #40's glob form. Give each a record; refuse each writer through a `None` entry; send the orbit read.

## Scope

The kept keys and their tests, `PENDING` empty in every GitLab family, the coverage test passing with no pending key. Then #15's checklist is reconciled against its closed children. Out of scope: the real-instance run (#11).

## Depends on

#43 (PR #65) and #63 (its spec is approved; code after #43). This branch rebases onto the trunk after both land; implementation starts then.
