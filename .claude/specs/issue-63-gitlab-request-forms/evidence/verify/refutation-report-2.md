# Refutation report, round 2 (delta) - issue #63 (tier M, PR #66, head 583fbbd on 43ba0f1)

Scope: the rework of DL-010 (tests only) against round 1's RF-1..RF-6. `git diff 43ba0f1 583fbbd --stat --
src/payload/scripts` printed nothing; the sha256 of each mutated product file before mutation equals round 1's.
Method: a detached worktree of 583fbbd under `tmp/verify2/` (removed after); each mutant replaced one exact text,
ran its paired tests through `scripts/run_tests.py`, restored the bytes (28 restore lines, all `match=True`); each
survivor then ran against every GitLab suite (957 tests, the rework-1.txt Run line). Captures `evidence/verify/round2-*`.
F = test_gitlab_api_package.py, G = _container_registry, T = _transport, R = _registry.

| # | Claim | Command / mutant | Result | Capture |
|---|---|---|---|---|
| 1 | Whole suite green on the head | `wait-run`/`get-run`/`get-jobs` 43087628208: head_sha 583fbbd; security, lint, types, tests, report success; 3694 passed (+31), hook suite 1053 | FAILED-TO-REFUTE | round2-full-suite.txt |
| 2 | Detached tree green before mutants | the four rework files: 237 passed | FAILED-TO-REFUTE | round2-baseline-green.txt |
| 3 | RF-1: host with `?` refused | `?` dropped from `REFUSED_IN_HOST`: killed by F `test_no_registry_token_sends_nothing_to_the_registry[image-prefix-host-with-a-query]` | FAILED-TO-REFUTE | round2-sec-step2-query-allowed.txt |
| 4 | RF-1: `\` refused, `?` still refused | `\` dropped: killed by F [image-prefix-host-with-a-backslash] (the fake host's unscripted DELETE to the registry) | FAILED-TO-REFUTE | round2-sec-step2-backslash-allowed.txt |
| 5 | RF-1: white space refused | `\s` dropped: killed by F [image-prefix-host-with-white-space] | FAILED-TO-REFUTE | round2-sec-step2-whitespace-allowed.txt |
| 6 | RF-1 near-variant: white space other than U+0020 | `\s` narrowed to a space (tab, LF, CR admitted): 71 passed paired, 957 passed every GitLab suite | REFUTED R2-1 | round2-sec-step2-only-space-refused[-full].txt |
| 7 | RF-2: `GET /user` without a username raises | `_answer_text` bypassed: killed by G `test_a_user_answer_without_a_username_sends_nothing_further` [no-username], [a-username-that-is-not-a-string], F [user-answer-without-a-username], [...-not-a-string] | FAILED-TO-REFUTE | round2-ac53-username-unchecked.txt |
| 8 | RF-2 near-variant: non-string username | any truthy username accepted: killed by G and F [...-not-a-string] | FAILED-TO-REFUTE | round2-ac53-username-type-unchecked.txt |
| 9 | RF-2 near-variant: empty-string username | any string username accepted: 71 passed paired, 957 passed every GitLab suite | REFUTED R2-2 | round2-ac53-username-empty-accepted[-full].txt |
| 10 | RF-3: refused `/jwt/auth` body never in the message | `{response.body!r}` in the message: 11 failed, T `test_a_registry_token_answer_without_a_token_is_never_quoted` x5, G `test_a_refused_registry_token_answer_is_never_quoted` x3, F `test_a_refused_jwt_auth_answer_is_never_reported` x3 | FAILED-TO-REFUTE | round2-sec-jwt-refusal-quotes-body.txt |
| 11 | RF-3 near: body kept as `details`, message unchanged | `details=response.text`: the same 11 failed | FAILED-TO-REFUTE | round2-sec-jwt-body-in-details.txt |
| 12 | RF-3 near: body in a log record | `LOGGER.debug` of the body before the raise: the same 11 failed | FAILED-TO-REFUTE | round2-sec-jwt-body-logged.txt |
| 13 | RF-3: non-JSON answer's body not carried as details | `answer = None` -> `raise`: 3 failed, [claims-json-but-is-not-json] in T, G, F | FAILED-TO-REFUTE | round2-sec-jwt-non-json-answer-reraised.txt |
| 14 | RF-3 near: non-JSON body quoted in a new error | raise quoting `response.text`: the same 3 failed | FAILED-TO-REFUTE | round2-sec-jwt-non-json-body-in-message.txt |
| 15 | RF-4: `pages` refuses a non-REST base | check off: R `test_pages_refuses_a_record_not_under_the_api` [host-root], [container-registry] | FAILED-TO-REFUTE | round2-f4-pages-any-base.txt |
| 16 | RF-4 near: one base admitted | host root admitted: [host-root] failed; container registry admitted: [container-registry] failed | FAILED-TO-REFUTE | round2-f4-pages-admits-*.txt |
| 17 | RF-4: `pages` refuses a request header | `or encoded.headers` dropped: R `test_pages_refuses_a_request_header` | FAILED-TO-REFUTE | round2-f5-pages-headers-accepted.txt |
| 18 | RF-5: DL-009 refusal | check off: 5 failed, R `test_send_refuses_a_registry_record_anything_but_a_query` [json-body, form-body, file, header, raw-bytes] | FAILED-TO-REFUTE | round2-dl009-registry-body-accepted.txt |
| 19 | RF-5 near: each disjunct | data, form, files, json_body, headers each dropped: each killed by its own case alone | FAILED-TO-REFUTE | round2-dl009-{raw-bytes,form,file,json,header}-accepted.txt |
| 20 | RF-6 484 `_described` | "no value" -> "nothing": R `test_a_positional_name_given_no_value_is_refused` [absent], [none] | FAILED-TO-REFUTE | round2-rf6-described-no-value-changed.txt |
| 21 | RF-6 499 `_place_values` | `if not places: continue` removed: R `test_a_positional_name_in_a_left_out_group_takes_no_value` | FAILED-TO-REFUTE | round2-rf6-left-out-group-not-skipped.txt |
| 22 | RF-6 774 `_scope` | no token_scope sent as "": R `test_send_refuses_a_registry_scope_it_cannot_write[no-token-scope]` | FAILED-TO-REFUTE | round2-rf6-missing-token-scope-sent-empty.txt |
| 23 | RF-6 779 `_scope` | `${NAME}` given no value left literal: R [scope-name-given-no-value] | FAILED-TO-REFUTE | round2-rf6-scope-name-left-literal.txt |
| 24 | RF-6 coverage | CI 43087628208: registry.py misses 457, 932 only (git blame 678c076b, 140bbe44, ancestors of base 6beeb77); 484, 499, 774, 779, 805, 935, 945 and transport.py 289-291 now executed | FAILED-TO-REFUTE | round2-full-suite.txt |
| 25 | Vacuity of the new tests | diff: 10 new test functions, 5 new `NO_TOKEN_CASES` params; markers only `parametrize`; no removed assert, raises, param or test; no pyproject/conftest change; every new function failed under at least one mutant | FAILED-TO-REFUTE | diff |
| 26 | Red for the right reason | every kill: AssertionError, `DID NOT RAISE`, or the fake host's unscripted-request AssertionError; the one ValueError is the refusal row 21's test proves absent; no collection or import error | FAILED-TO-REFUTE | round2-*.txt |
| 27 | Restored tree green | four rework files after every mutant: 237 passed; mutant tree `git status --porcelain` empty | FAILED-TO-REFUTE | round2-restored-green.txt |

## Refutations

- R2-1 AC-5.3 / D4 step 2 (residue of RF-1): "hold none of ... white space" is pinned for U+0020 alone. A mutant
  refusing only the space survives 957 tests; under it a host holding a tab or LF passes step 2 and step 3 is sent,
  where D4 raises `GitLabAPIError` before step 3.
- R2-2 AC-5.3 / D4 step 1 (residue of RF-2): "an answer whose field is absent or not a non-empty string" is pinned for
  absent and non-string usernames, not for `""`. A mutant accepting any string username survives 957 tests; under it
  steps 2 to 4 are sent, where `container_registry.login` raises before step 2.

All nine of round 1's survivors are killed. 15 of 17 near-variants are killed; R2-1 and R2-2 are the two survivors.
RF-3, RF-4, RF-5 and RF-6 are closed. RF-1 and RF-2 are closed except for R2-1 and R2-2.

## Tree

The temporary worktree is removed and pruned (`git worktree list` names main, issue-15, issue-63). `tmp/` is empty, and
pytest's basetemp and the temp dir were scoped under the issue-63 tree's `tmp/` and removed. `git status --porcelain`
lists only `evidence/verify/round2-*` and this report. HEAD is 583fbbd. Nothing was committed and nothing was written
outside the issue-63 worktree. detect-secrets-hook against `.secrets.baseline` exits 0 on the captures.

Refuted: R2-1 R2-2
Verdict: REFUTED
