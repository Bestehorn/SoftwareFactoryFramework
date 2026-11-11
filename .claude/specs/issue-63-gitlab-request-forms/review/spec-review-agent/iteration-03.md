# spec-review-agent — design iteration 03, delta (issue #63, tier M)

Reviewed: `git diff 8fe5ae0 dfeae41` of `design.md` (`requirements.md` has no change), the iteration-02 fix sites and
the other edits of the same diff, against the worktree's `src/payload/` and `test/` and `origin/main` 70c4dba.

## Iteration-02 findings

| ID | Status | Evidence |
|---|---|---|
| B1 | resolved | AC-9.2's N `test_the_map_names_the_request_forms` now holds "AC-9.1's spellings: `--endpoint`, two `--path id=`, `--path format=`, `--header` and `override_params[container_expiration_policy_attributes]`"; D11 names "the repeated `--path` (two `--path id=`)" and "the two-level member's full name", whose `…[cadence]` spelling contains the asserted text |
| C1 | resolved | Security "What stays callable" reads "every record of D8 but the S3 import (Gates), none gated" |
| C2 | resolved | D7 reads "fail only through `header_problems` and #43's `test_only_the_upload_module_path_holds_a_hyphenated_name` as D9 restates it"; D9 restates no other N test ("Every other existing test of … P, N and V passes unedited") |

## Other edits of the diff, checked and holding

- D7 `IN_HEADER` "beside `IN_PATH`": `test/test_gitlab_wrapper_contract.py` holds `IN_PATH = "path"` beside `IN_QUERY`,
  `IN_BODY` and `IN_FORM`, and no `IN_HEADER`, so the constant is new as stated.
- D12's `D7, D9` row for N names the rule edit of D9's last bullet.
- AC-1.2 "so it is red on the base": the worktree's `families/plan.py` and `families/verify.py` each declare
  `plan#add-an-emoji-reaction-to-a-resource` and `verify#get-the-latest-release` once (the latter's comment: "the
  first of its three endpoints, the others pending"), so an assertion that the judged IDs include both fails on the
  base and passes once D8's F1 records exist.
- AC-5.2's G `test_a_job_token_logs_in_as_gitlab_ci_token`: the `gitlab-ci-token` login and the `Authorization: Basic`
  of `<login>:<token>` match D4 steps 1 and 3 and the Sources' `lib/gitlab/auth.rb` `find_for_git_client`.
- AC-5.3's exact-request oracle matches D4 and the code it builds on: `bearer` raises at step 1 before any request;
  `transport.py` `_send` retries only a `429`, so a `401` at step 1 or 3 is one recorded request; `prepare_call` and
  `send_call` in `commands/call.py` send nothing before `registry.send`; `Transport`'s config loading reads an absent
  `token_type` as `private`, so the non-`bearer` cases send step 1. AC-8.3's "(to the registry, for AC-5.3)" and
  UB-2's oracle stay consistent with it; requirements AC-5.3 ("send nothing to the registry and exit 1") is met.
- D11 "under its cap": `docs/forLLMConsumption.md` is 7,358 bytes (`wc -c`) against the 40,000-byte cap.
- #43's N test is not on `origin/main` 70c4dba; the design's rebase precondition (DL-001) already covers that.

## New findings

None.

CLEAN
Verdict: READY
