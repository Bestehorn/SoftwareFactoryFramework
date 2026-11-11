# Review — design iteration 01 (consolidated)

Six lanes. Overall: NOT-CLEAN (0 A, 3 distinct B). Lanes READY: devops-iac-reviewer, security-reviewer,
best-practice-reviewer. Lanes NOT-READY: spec-review-agent, test-architect, standards-reviewer.

## B (gating)

- **B1 — AC-5.2, the map test cannot fail** (spec-review-agent B1 = test-architect B2). The map's `gitlab_api/` bullet
  already holds `--file`. Edit: the test asserts that the bullet holds `call graphql#`, `--file NAME=PATH` and `Upload`.
- **B2 — AC-5.1, the docstring test matches IDs as substrings** (test-architect B1). `graphql#workItem` passes on
  `graphql#workItemsByReference`, and `graphql#Query.vulnerability` passes on `graphql#Query.vulnerabilities`. Edit:
  match each ID whole: not followed by a letter, digit or `_`, nor by `.` and a letter.
- **B3 — D4 repeats `transport.request_body`** (standards-reviewer B1; `design-principles.md` §2). Edit: with files,
  `Transport.graphql`'s body and Content-Type are what `request_body(form=..., json_body=None, files=...)` returns.
  DL-004 is superseded on this point.

## C and D (applied in the same author pass)

- spec C1: D4 says that a `--file` name outside `upload_variables` gets a single `Path`, and step 4 then refuses it
  with exit 2 (no `KeyError`).
- spec C2: D7 claims only what #11's fixture provides for (CI configuration, Git LFS).
- spec D1: D8 credits the environment-text scan to UB-2.2.
- test-architect C1: the AC-1.3 member test also fails when the rows it reads differ from the table, or when a row
  yields no member.
- test-architect C2: the reference-check copies of the edited records are built inside the test body.
- test-architect C3: the AC-3.1 test files hold a byte that is not UTF-8 and a CRLF.
- test-architect C4: the AC-5.1 test fails when `OPERATIONS` is empty.
- standards C1: D8's `registry.py` bullet adds the module docstring and the `GraphQLOperation` docstring (several
  records may serve one capability).
- standards D1: drop the "five roots" count from D1.
- standards D2: D4 says that `files` names a part in `Transport.request` but a variable path in `Transport.graphql`.
- security C1: D6's `GATED_OPERATIONS` comment uses #41's class wording: "commits to or merges into a branch, or
  creates an issue".
- security C2: Security Considerations adds one sentence on `pipelineCreate` `$variables`. They override project
  variables, and GitLab's `pipeline_variables_minimum_override_role` controls who may set them.
- security D1: Residuals says `gate_merge_steward` is the enforcement when the host cannot protect the branch.
- best-practice C1: D1's mutation table notes that `workItemExport` was deprecated in 18.0 and that
  `workItemsCsvExport` is the alternative. Residuals adds one bullet, like the design-management one.
- devops C1: Operability says `gitlab_wrapper.py` is not installed here (`config/toolchain.json`).

Lane files: `review/<lane>/iteration-01.md`.
