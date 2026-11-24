# Test architect — design review, iteration 01

## Findings

### B1 — AC-4.1's refused values let a containment or first-slash guard through
Severity: B
Location: design.md § Correctness Properties AC-4.1
Defect: every refused `project_id` holds at most one `/` and no `sff-test-` inside a segment, so a guard testing `"sff-test-" in` the last segment, or the part after the FIRST `/` (`partition`), passes every W case while serving `Bestehorn/x-sff-test-y` or `Bestehorn/sff-test-x/SoftwareFactoryFramework` (#10's W refuses inner and trailing prefixes for this reason).
Material-because: AC-4.1 (refuse unless the configured project's path starts with `sff-test-`) is untested for near misses.
Proposed-edit: in AC-4.1's `project_id` list, after `"sff-test-x"` add `"Bestehorn/x-sff-test-y"` and `"bestehorn-sff-test/sff-test-x/other"`.

### B2 — The non-private creation that must still be deleted has no test
Severity: B
Location: design.md § Correctness Properties AC-1.4; § D9 step 6
Defect: D9 step 6 refuses a creation answered with a `visibility` other than `private` and hands the record to step 8 through the error's `details`; no S case scripts that answer, so a provision that loses the record there (step 8 sees `None`) passes every listed test and leaves the project to a sweep a day later (#10 tests this path: `test_a_repository_created_other_than_private_is_refused_and_deleted`).
Material-because: AC-1.4 (the project is deleted whether the run passed, failed or raised an error).
Proposed-edit: append to Correctness Properties AC-1.4 and the mapping row AC-1.4: "Parametrized example, S `test_a_project_created_other_than_private_is_refused_and_deleted`: a creation answered with `visibility` `internal` or `public` makes `provision` raise `ForgeSetupError` without entering the body; exactly one `tenant-scale#delete-a-project` of that project is recorded and the workspace no longer exists."

### B3 — Two of AC-9.1's items pass on today's GitHub text
Severity: B
Location: design.md § Correctness Properties AC-9.1
Defect: `docs/forge-suite.md` already holds `bestehorn-sff-test` ("in the organization `bestehorn-sff-test`") and "Only a machine that runs the forge suite locally needs the file", so G's checks for the test group and the local-only sentence pass with no GitLab section at all.
Material-because: AC-9.1 (the GitLab setup names the test group, and that only a machine running the GitLab suite locally needs the file) is not tested.
Proposed-edit: replace "`docs/forge-suite.md` names" with "the GitLab section of `docs/forge-suite.md` (from its heading naming GitLab to the next heading of that level) names `gitlab.com`,", and "and that only a machine" with "and, in a sentence of that section, that only a machine".

### B4 — AC-5.3's message is checked on the function, not on the step
Severity: B
Location: design.md § Correctness Properties AC-5.3
Defect: S checks the text of `write_test_credential`'s exception and that `write_credential.main` returns 1, so a `main` that returns 1 after logging nothing or another text passes while the job log never says the secret is unavailable.
Material-because: AC-5.3 ("SHALL fail with a message saying that the secret `SFF_GITLAB_TEST_TOKEN` is unavailable").
Proposed-edit: replace "`write_credential.main` returns 1 on the refusal" with "`write_credential.main`, with `SFF_GITLAB_TEST_TOKEN` empty and unset (`monkeypatch`), logs one record holding that text, writes nothing and returns 1; with a token it writes the file and returns 0".

### C1 — AC-5.1: name the scope of "no `continue-on-error`"
Proposed-edit: "no `continue-on-error` on the job or on any of its steps" (L checks both).

### C2 — AC-8.6: "with its reason" has no oracle
Proposed-edit: "names each record D6 lists as not called and, beside it, D6's reason (its tier, `administrator credentials`, no documented answer, or `call`'s refusal)".

### C3 — F `test_no_leftover_survives_the_sweep` judges through the code under test
Its selection is `is_leftover`, and its oracle rests on `marked_for_deletion_on` in a Free group's listing items, which D9 cites no documentation for (`docs/api-reference/gitlab/rest/tenant-scale.md` marks the listing's `marked_for_deletion_on` query attribute "Premium and Ultimate only").
Proposed-edit: "selects inline: namespace `TEST_GROUP`, path starting `sff-test-`, `created_at` over a day before `swept_at`"; cite the item attribute's documentation, or also accept D4's `-deletion_scheduled-` path as marked.

### C4 — UB-2: the read half has no oracle (#10's clause dropped)
Proposed-edit: append "; the sentinel holds another token and a `token_type`, and the clone's `config/gitlab.json` holds exactly `hostname`, `project_id` and the test token".

### C5 — AC-9.2: `test/forge_gitlab` is a substring of the local command
Proposed-edit: "names `test/forge_gitlab` beside the local command (L's `beside_the_command`)".

### C6 — AC-3.1 to AC-3.3: the property's "other" values are unnamed
Proposed-edit: "the other paths and namespaces include near misses, as #10's `UNPREFIXED_NAMES` and `OTHER_OWNERS`: `sff-test-` inside a path, `sff-test` without the dash, `bestehorn-sff-test-archive`, a subgroup `bestehorn-sff-test/sub`".

### C7 — AC-4.2 covers the handler branch only
Proposed-edit: add "`enqueue-pr 1` reaches the steward recorder once with the same arguments with and without the marker".

### C8 — AC-4.1's subprocess example names no argv
Proposed-edit: "runs `call plan#create-an-issue`, which `call` refuses before any request, so the child sends nothing whichever refusal comes first and only the message tells them apart" (#10's choice; UB-1).

## Residuals

- L's map checks (`test/forge`, `python scripts/run_tests.py --workers 1 test/forge`) are substrings of the GitLab path and command, so after this change they no longer fail on removal of the GitHub text; nothing in this ask edits them.

## Coverage

Legend as design.md's mapping (W, S, G, L, H, F, C, A, K, V, P, I, B).

| Criterion | Tests | State |
|---|---|---|
| AC-1.1 | F fixture; S provisioning, distributed run; G session fixture | OK |
| AC-1.2 | S run id | OK |
| AC-1.3 | F fixture, no pipeline, repository records; S provisioning | OK |
| AC-1.4 | S provisioning; G session fixture | GAP (B2) |
| AC-2.1 | S teardown deletes | OK |
| AC-2.2 | S teardown refuses | OK |
| AC-2.3 | S no creation | OK |
| AC-3.1 | S sweep property, boundaries; F sweep | OK |
| AC-3.2 | S sweep property, boundaries | OK |
| AC-3.3 | S sweep property, boundaries | OK |
| AC-4.1 | W refuses, W entry script | GAP (B1) |
| AC-4.2 | W ephemeral through; every F | OK |
| AC-4.3 | S marker argv; W values, without marker; G | OK |
| AC-5.1 | G job beside verify | OK |
| AC-5.2 | G secret step, nothing keeps | OK |
| AC-5.3 | S missing secret | GAP (B4) |
| AC-5.4 | G report; L report | OK |
| AC-6.1 | S credential lookup | OK |
| AC-6.2 | S bad credential | OK |
| AC-6.3 | S written only to clone, commits none, helper; G secret step | OK |
| AC-7.1 | G default collects none | OK |
| AC-7.2 | G path collects all | OK |
| AC-7.3 | G nothing keeps | OK |
| AC-8.1 | G ephemeral only; every F | OK |
| AC-8.2 | F subcommands (4) | OK |
| AC-8.3 | F records (3); F fixture | OK |
| AC-8.4 | F graphql | OK |
| AC-8.5 | F request forms (2); G uncalled forms | OK |
| AC-8.6 | G uncalled forms | OK |
| AC-8.7 | G ephemeral only | OK |
| AC-9.1 | G setup note | GAP (B3) |
| AC-9.2 | G map; B | OK |
| UB-1 | W, S, G in `verify` on doubles; fake-host suites unedited | OK |
| UB-2 | S sentinel | OK |
| UB-3 | C, A, K, V, P unedited; W without marker | OK |
| UB-4 | H, L; diff under `test/forge/` empty | OK |
| UB-5 | I; the PR diff | OK |

33 OK, 4 GAP.

NOT-CLEAN (0 A, 4 B) — NOT-TEST-READY
