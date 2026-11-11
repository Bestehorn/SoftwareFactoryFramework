# Review latest — issue #41 design

## Iteration 01 (consolidated by the conductor)

Lanes: test-architect NOT-CLEAN (0 A, 2 B), standards CLEAN, best-practice NOT-CLEAN (0 A, 2 B), security CLEAN, devops
CLEAN, spec-review NOT-READY (0 A, 2 B). Root causes Y1 (reference reader), Y2 (`-F` NaN), Y3 (D8 slice files), Y4
(AC-1.7 registry error), Y5 (AC-5.3 removed row), plus the C/D list — all applied by the author (see the lane files).

## Iteration 02 (delta, consolidated by the conductor)

Lanes: test-architect NOT-CLEAN (0 A, 1 B; 27 COVERED, 0 GAP), best-practice NOT-CLEAN (0 A, 1 B), spec-review
NOT-READY (0 A, 1 B), standards CLEAN, security CLEAN, devops CLEAN. Every Y1–Y5 fix site APPLIED.

### Root causes (B), 3 findings → 3 causes

- **Z1 — the `NaN` test cannot fail.** `test_a_field_that_is_not_json_is_refused` omits `--path issue_iid`, so a build
  without `parse_constant` is refused at step 4 with the same exit 2. Fix: add `--path issue_iid=5`, and the oracle
  requires argparse's usage message on standard error naming `-F/--field` and `"title"` and not holding the text after
  the first `=`; D2 "Parsing" says `json_member` converts every `ValueError` from `json.loads` (incl. the plain
  `ValueError` `parse_constant` raises) into the usage error. [TA2-B1, BP2-C1, SEC2-C2]
- **Z2 — the member rule is too wide for form records.** Only a `parent[key]` member may be declared in a query or
  form record; a `[].key` or `:key` member is never a parameter of its own; `create#create-a-commit` (multipart, a
  `file` row) sends `actions` through the parent's value. A bracketed body row with no parent row
  (`growth#force-a-variant-assignment` `context[user]`) is declared in a FORM-body record. [BP2-B1, SR2-C4]
- **Z3 — `record_problems` demands a path row tables omit.** Restate as SR2-B1 proposes: an `In` `path` row that is no
  placeholder of the record's path is a difference; a placeholder with no `In` `path` row is not (`create#health`).
  [SR2-B1]

### C/D — apply in the same pass, no new round

- TA2-C1 a footnote-form reader pin (`create#add-changelog-data-to-file` has `version` and `from`). TA2-C2 cases for the
  `/geo/` and `/hooks/` arms (`openapi-only#determine-if-a-geo-site-should-proxy-requests`,
  `openapi-only#update-a-custom-header`). TA2-C3 AC-1.7's two path errors carry no `details`.
- SR2-C1 an alternation row is not compared; its alternatives are; pin `create#set-commit-pipeline-status` has `name`
  and `context`; `header` rows are request forms part 1 does not build. SR2-C2 `sent_call` reads multipart part names
  too. SR2-C3 the several-keys residual names `create#generate-changelog-data` and
  `plan#list-all-emoji-reactions-for-a-resource` and says a slice records them as its residual. SR2-D1 "the first
  non-empty line under the heading".
- SEC2-C1 the gated-records class reads "commits to or merges into a branch, or creates an issue"
  (`verify#add-a-merge-request-to-a-merge-train` merges).
- ST2-C4 N imports neither `verify.py` nor `common.py` `Slugger` and checks the pages independently of the generator.
  ST2-D2 `print_bytes(*, data)` as #28's.
- DV2-D1 "Lines inside fenced code blocks are not headings."

Next: one author pass over Z1–Z3 and every C/D above; delta review in iteration 03 (cap 4).

## Iterations 03–04 (delta)

Iteration 03: best-practice CLEAN, spec-review READY (1 C), test-architect NOT-CLEAN (1 B: the member rule checked by no test). The B fixed by a `record_problems` arm and a `granular_scopes[].access` rejection case. Iteration 04 (cap): test-architect CLEAN, TEST-READY 27/27; spec-review READY. The C items applied in one pass. Approved (DL-003).
