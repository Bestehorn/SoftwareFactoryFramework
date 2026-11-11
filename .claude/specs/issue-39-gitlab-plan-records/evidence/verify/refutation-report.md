# Refutation report: issue #39, the plan GitLab records (tier S, wave 1)

Tree `.claude/worktrees/issue-39`, branch `issue-39-gitlab-plan-records`, HEAD e09f2ad (merges origin/main d30d022),
PR #54. Under test: `git diff origin/main...HEAD`, which covers `families/plan.py`, the new F, K's DL-004 lines and the ledger rows.
Paired tests: F `src/payload/test/test_gitlab_api_plan.py`, K `src/payload/test/test_gitlab_api_call.py`, N
`test/test_gitlab_wrapper_contract.py`, V `test/test_gitlab_wrapper_coverage.py`. Every mutant ran
`python scripts/run_tests.py F K N V` (152 tests). Each edit was a byte-level replacement in the CRLF working file,
checked to occur exactly once. The original bytes were written back and checked by sha256, never by `git checkout` or `git stash`.

## 1. Whole-suite verdict

`github_wrapper.py wait-run 42977947467` exited 0 with conclusion `success`. `get-run` reports head_sha e09f2ad, which is the worktree HEAD.
`get-jobs`: verify (lint), verify (security), verify (types), verify (tests), report: all `success`. Capture: `full-suite.txt`.

## 2. Mutants (all restored; every capture ends `matches original: True`)

| id | mutation | failing tests (message) | capture |
|---|---|---|---|
| W1 | plan.py replaced by origin/main (wave reverted) | F pending, typed, required, list-set + 54 new list cases; 58 failed, 94 passed | mutant-wave-1.txt |
| m01 | `create-an-upload` `file` (In form) FILE->SCALAR | F typed: missing (create-an-upload, file) | mutant-wave-1-m01.txt |
| m02 | `list-all-group-issues` `iids` ARRAY->SCALAR | F typed: missing (.., iids) | -m02 |
| m03 | `create-a-wiki-page` `front_matter` HASH->SCALAR | F typed: missing (.., front_matter) | -m03 |
| m04 | `create-a-milestone` `title` required->optional | F required: missing | -m04 |
| m05 | `create-a-milestone` `description` optional->required | F required: not expected | -m05 |
| m06 | `list-group-labels` OFFSET->NONE | F list-set + case [list-group-labels] | -m06 |
| m07 | "Get a single group label" NONE->OFFSET | F list-set: not expected | -m07 |
| m08 | `clone-an-issue` given a section-faithful record, key off PENDING | F pending (missing clone key), F required; N, V, K pass | -m08 |
| m09 | `create-a-merge-request-note` likewise | F pending, F required | -m09 |
| m10 | `retrieve-notification-settings` on its `/groups/` endpoint, PENDING swapped | F pending only | -m10 |
| m11 | `not[labels]` dropped from `retrieve-issues-statistics-for-a-group` | F typed; N reference: "the query row 'not[labels]' is not declared" | -m11 |
| m12 | body row `description` dropped from `create-a-milestone` | N reference: "the body row 'description' is not declared" | -m12 |
| m13 | K `OP_PENDING_ONLY` back to `plan#create-an-upload` | K [only-on-a-pending-list]: "a refused call exits 2, got 0" | -m13 |
| m14 | `render-markdown-content` `text` BODY->QUERY | N reference + N send: "query name 'text' ... not documented in the query" | -m14 |

Re-confirmed green after the last restore: plan.py, K and F have their pre-run sha256 (8f3f81ed, f70082d2, fbd310dc),
`git diff --stat` is empty, and the green set (F, K, N, V, C, P, `test_wrapper_delivery.py`) shows 254 passed (`restored-green.txt`).

Observation, not a refutation: under m08, K's `only-on-a-pending-list` case passes. `call` refuses the declared
clone record because the required `to_project_id` is missing: exit 2, no request, and the ID is named. F's AC-1 test kills m08, and
change.md maps UB-2 to that test too.

## 3. Vacuity

A Grep of F and K finds no skip, xfail, importorskip, deselect, mark other than parametrize, or commented-out test or assert. All six F
functions assert. The F parametrization holds 56 cases (W1: 54 failed + 2 part-1 passed). F's tables are literals,
audited against `rest/plan.md` by Grep:
- 55 rows whose In is `form` or whose Type holds array/Hash/object: F's 55 `TYPED_ATTRIBUTES`, the same names per section.
- 59 non-path Required `yes` rows, less those of Clone an issue, Create a merge request note and Promote an issue to an epic,
  the 3 sections with no record of their own: F's 56 `REQUIRED_ATTRIBUTES`.
- 56 `###` headings beginning "List" or "Get all", every one a `GET`: F's 56 `LIST_ENDPOINTS`, paths equal.

## 4. Red for the right reason

`evidence/red/wave-1.txt` shows 58 failed, 70 passed. Every failure is an AssertionError: either a set difference naming the keys or IDs, or
`call ... exits 0, got 2` with `unknown operation id`. There is no collection or import error. W1 regenerates the same 58 F failures, and K, N and V
pass.

## 5. Coverage of the change

The changed executable lines are the plan.py records, PENDING and K's `OP_PENDING_ONLY`. N's reference test reads every record, and N's
send test calls every record outside `GATED_OPERATIONS` (only `ai-coding#merge-a-merge-request` and
`plan#create-an-issue`); m14 shows the send test flags a new plan record. F's AC-1 test and V read PENDING, and K's case reads
its line (m13). The docstring and ledger rows execute nothing. No changed line goes unexercised.

## 6. Spot-check and UB-1

I compared 15 records field by field with their `rest/plan.md` sections (method, path, every row and its In, Kind, required,
paging), and all match: list-all-group-epics, execute-a-glql-query, list-all-group-iterations, upload-a-file-to-a-group,
list-all-uploads-for-a-group, move-an-issue, create-a-related-epic-link, render-markdown-content, create-an-upload,
list-uploads, unregister-a-device, list-all-issue-notes, create-new-pages-domain, get-a-single-group-label,
retrieve-notification-settings.
UB-1: plan.py's diff has two hunks. `@@ -2,11 +2,26 @@` is the docstring, and the first three lines of `@@ -179,230 +194,1989 @@` are context. Part 1's seven
records (base lines 22-181) fall outside both hunks, so they are byte-identical. The diff touches no part of C, `test/`, `commands/` or
`github_wrapper.py`. K's only change is `OP_PENDING_ONLY` and its comment (DL-004).

## Claims

| claim | command | result | capture |
|---|---|---|---|
| AC-1 | run_tests.py F K N V: F `test_only_the_kept_keys_are_pending`, V | FAILED-TO-REFUTE | W1, m08, m09, m10 |
| AC-2 | N `test_every_record_matches_its_reference_section` | FAILED-TO-REFUTE | m11, m12, m14 |
| AC-3 | F typed, required, body tests; Grep audit | FAILED-TO-REFUTE | m01-m05 |
| AC-4 | F `test_every_list_record_has_a_case`; Grep audit | FAILED-TO-REFUTE | m06, m07 |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | FAILED-TO-REFUTE | m14, restored-green.txt |
| AC-6 | F `test_a_list_record_prints_every_item`, 56 cases | FAILED-TO-REFUTE | W1, m06 |
| UB-1 | C in CI and locally; plan.py diff hunks | FAILED-TO-REFUTE | full-suite.txt, restored-green.txt |
| UB-2 | K gated + unknown cases; F AC-1 | FAILED-TO-REFUTE | m08, m09, m13 |
| UB-3 | C config tests; P `test_standard_library_only` | FAILED-TO-REFUTE | full-suite.txt, restored-green.txt |
| UB-4 | `test_wrapper_delivery.py`; diff names | FAILED-TO-REFUTE | restored-green.txt |

## Tree restoration

Every mutation was restored byte for byte (sha256 checked). The harness under `tmp/verify/` is deleted. `git status` lists only
`evidence/verify/`. No code or test was edited.

Verdict: VERIFIED
