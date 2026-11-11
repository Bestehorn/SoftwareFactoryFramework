# Refutation report: issue #46 (PR #57, head 10a2223, merge base 52403f8)

Adversarial verifier, 2026-11-11. Every mutant was a byte edit applied by a harness kept outside the worktree (the main
checkout's `tmp/verify-46/`). The harness recorded each touched file's sha256 before the edit, after it and after the
restore, and restored the file's mtime. All 42 restores read `identical=True`. Paired tests ran through
`scripts/run_tests.py --workers 1 <files> -k <paired tests> -pno:cacheprovider --tb=line --color=no`.

| Id | Claim | Command | Result | Capture |
|---|---|---|---|---|
| S1 | Whole suite green on the pushed SHA | `github_wrapper.py get-run 42982400640`, `get-jobs 42982400640` | FAILED-TO-REFUTE: completed/success, head_sha = worktree HEAD 10a2223; lint, tests, types, security, report all success | full-suite.txt |
| W1 | Transport and registry (AC-1.2, AC-2.2, AC-3.1, AC-3.2, UB-2.2) | `mutate.py wave 1` over T, R, K (23 tests) | FAILED-TO-REFUTE: 19/19 killed; 23 passed after restore | mutant-wave-1.txt |
| W2 | `--input`, its refusals, the upload record, N's host (AC-1.1, AC-1.3, AC-2.1, AC-2.2, AC-4.1, AC-4.2) | `mutate.py wave 2` over K, H, G, N, V (17 tests) | FAILED-TO-REFUTE: 12/12 killed; 17 passed after restore | mutant-wave-2.txt |
| W3 | Usage docstring (AC-5.1) | `mutate.py wave 3` over C, B (3 tests) | FAILED-TO-REFUTE: 6/6 killed; 3 passed after restore | mutant-wave-3.txt |
| W4 | render-raw record, stdin bytes (AC-1.2, AC-4.1, AC-4.3) | `mutate.py wave 4` over K, M, N, V (9 tests) | FAILED-TO-REFUTE: 4/4 killed; 9 passed after restore | mutant-wave-4.txt |
| VAC | No vacuous test in the change | grep of the test diff for skip/xfail/importorskip/deselect/commented tests; config diff | FAILED-TO-REFUTE | this report |
| RED | Each red capture failed for the right reason | Read of `evidence/red/wave-1..4.txt` | FAILED-TO-REFUTE | evidence/red/ |
| F.2 | No existing line of C, P, K or fx `CASES` changed; C gains one test | `git diff --numstat` and `-U0` against origin/main | FAILED-TO-REFUTE | this report |
| F.3 | The map holds D6's parenthesis under its cap | Grep of the map; B in the wave-3 re-run | FAILED-TO-REFUTE | mutant-wave-3.txt |
| RB | The rebase merge in `commands/call.py` kept trunk's gating | Read of `call.py`; diff hunks | FAILED-TO-REFUTE | this report |
| COV | No new or changed line goes unexercised | mutant kills plus inspection | FAILED-TO-REFUTE | mutant-wave-1..4.txt |

## Mutants (every one KILLED on a test failure, none survived, none killed only by an error)

- W1-01 `request_raw` sends to the API root: T raw[asset], R. W1-02 raw body CRLF to LF: T raw[markdown], R.
  W1-03 a byte that is not UTF-8 replaced: T raw x2, R. W1-04 Content-Type dropped: T raw x2, R. W1-05 Content-Type
  sent with `data=None`: T raw x2.
- W1-06 the 307 re-send drops the body: T re-send x3, K 307. W1-07 the re-send's method becomes POST: T re-send x4,
  second-307 x2, K. W1-08 the re-send drops the headers (credential, Content-Type): T re-send x4, K. W1-09 the 307
  branch disabled: T re-send x4, second-307 x2, K.
- W1-10 the branch without its origin comparison (task 1.1's named mutant): T cross-origin-307 x4. W1-11 the
  cross-origin strip removed: T `test_a_cross_origin_redirect_drops_the_credential` x5. W1-12 `REST_ROOTS` admits
  another host: T raw x2. W1-13 the `REST_ROOTS` check removed: T raw x2. W1-14 the once guard removed: T second-307
  x2. W1-15 DELETE out of `RESENT_METHODS`: T re-send[delete], second-307[delete].
- W1-16 `send` ignores `root`, W1-17 ignores `content_type`, W1-18 accepts `data` for a JSON record, W1-19 ignores
  the raw path: R in each.
- W2-01 `refuse_both_bodies` removed, W2-02 moved after the request: K AC-1.3 x2. `check_call` still exits 2, but
  its message does not name `--input`.
- W2-03 `refuse_raw_body` removed, W2-04 moved after the request, W2-05 removed with the registry guard: K AC-1.1
  [input-for-a-json-record] in each.
- W2-06 the file read as text: K upload, H x2. W2-07 `OSError` not converted, W2-08 the path not rendered with
  `json.dumps`: K AC-1.1[input-file-that-does-not-exist] in each.
- W2-09 the upload's root set to the API root: K upload, N every-record. W2-10 the upload's media type changed: K
  upload. W2-11 the upload back on `PENDING`: G no-pending. W2-12 N's reader keeping the default host (task 2.4's
  named mutant): N read[repos/upload-release-asset], N every-record.
- W3-01..06: each usage phrase dropped in turn (`call markdown/render-raw --input`, `--input FILE`, `standard input`,
  `repos/upload-release-asset`, `uploads.github.com`, `with -f/-F`): C `test_the_usage_names_the_raw_body_input`.
- W4-01 render-raw sends `text/x-markdown`: K markdown. W4-02 render-raw rooted at uploads: K markdown, N every-record.
  W4-03 render-raw back on `PENDING`: M residual. W4-04 standard input read through the text layer: K markdown.

## Findings

- VAC: the added test lines hold no skip, xfail, importorskip or deselect marker and no commented-out test. The only
  `pytest.mark` other than parametrize is `usefixtures`. No pytest config or conftest is in the diff. Every new test
  asserts directly or through `fx.assert_outcome` and `fx.assert_log`.
- RED: no capture has a collection error.
  - wave-1, 10 failed of 943: a `TypeError` in R's body (`RestOperation` has no `root`); an `AttributeError` in T's
    body (`REST_ROOTS`); `GitHubAPIError` HTTP 307 raised by `transport.request` in T's re-send bodies; and
    `AssertionError`s (T second-307, K 307 exit 1).
  - wave-2, 9 of 951: `AssertionError` x7 (K, G); an `AttributeError` on `read_input` in H's body, x2.
  - wave-3, 1 of 562: an `AssertionError` naming the six missing texts.
  - wave-4, 3 of 1085: `AssertionError` x3, among them K exiting 2 on "No GitHub operation record declares".
- F.2: numstat gives K +364/-0 and C +21/-0, and P is not in the diff. fx's three hunks are the `CONTENT_TYPE_JSON`
  constant and `NonGetRequest`; `CASES` is untouched. C's only new def is `test_the_usage_names_the_raw_body_input`,
  with its `USAGE_RAW_BODY_TEXTS`.
- F.3: lines 37-38 of `docs/forLLMConsumption.md` hold D6's parenthesis. B `test_llm_map_within_cap` passed in the
  wave-3 re-run.
- RB: `GATED_OPERATIONS` holds all 17 trunk entries: pulls/merge, pulls/merge-async, issues/create, repos/merge,
  repos/merge-upstream, repos/rename-branch, repos/create-or-update-file-contents, repos/delete-file, git/create-ref,
  git/update-ref, agent-tasks/create-task-in-repo, agent-merge/put-agent-merge-enrollment,
  agent-automations/create-repo-automation, agent-automations/edit-repo-automation,
  agent-automations/create-repo-automation-task, codespaces/export-for-authenticated-user and
  campaigns/create-campaign. The diff has no hunk in it or in `refuse_gated`, whose three forms are intact: "no
  subcommand sends it", "use the X subcommand", and "use the X subcommand, which sends it". `--input` sits beside them.
- COV: a mutant kill covers every new behavioural line except straight-line code that the paired tests run on every
  pass: `cmd_call`'s `data=raw_body` (K upload and K markdown judge the bytes it carries), the `--input`
  `add_argument`, and `ResentRequest`'s `origin_req_host`/`unverifiable`. C's UB-2.1 scan reads the docstrings. AC-1.2's
  media types are the sections' own: `releases.md` gives the upload `Request body (application/octet-stream...)`, and
  `markdown.md` gives render-raw `Request body (text/plain...)`.

## Tree restored

`git diff --quiet HEAD` exits 0 at 10a2223, and `git status --porcelain` lists only `evidence/verify/`. The harness's
crash-backup directory is empty. Only gitignored caches lie outside this comparison.

Verdict: VERIFIED
