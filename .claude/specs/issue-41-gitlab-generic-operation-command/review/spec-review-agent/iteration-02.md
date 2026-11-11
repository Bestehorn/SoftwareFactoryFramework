# Spec review — issue #41 design, iteration 02 (spec-review-agent, delta)

The fix sites hold. Iteration 01's B1: the restated `attributes` rule reads the pinned reference as written for every section the brief names. `create#create-a-commit`: `actions[]` becomes `actions`, and the `actions[].…` rows are its members. `ai-coding#update-approval-configuration-for-a-project`: `approvals_before_merge`, `require_password_to_approve`. `verify#create-a-feature-flag`: `strategies:name` and `strategies:scopes:environment_scope` are members of `strategies`. `create#add-changelog-data-to-file`: `version[^…]` and `version` are one attribute. The NuGet symbol-file `header` rows are handled as well. No name in `rest/*.md` is read with two `In` values. Iteration 01's B2: the restated D8 rows reach every request form in requirements Residuals through `registry.placeholders`, `sent_call` and `call_problems`. C1–C6, D1 and D2 are applied as proposed. `GitLabAPIError` subclasses `RuntimeError` (`errors.py`), so Y4's two path cases exit 1, as D4 says. The slice check the brief asks for finds one blocker, B1. Its item predates this revision, but the restated D8 "never" row now explicitly bars the fix.

### B1 — `record_problems` names a difference no record can remove: a table that omits a path row
Severity: B
Location: design.md § D5 "Reference half", `record_problems`, the placeholder item
Defect: The item names "a placeholder (`registry.placeholders`) that has no `In` `path` row". The pinned reference omits that row in single-endpoint sections of ten stems:
- `rest/create.md` "Health" (`GET /projects/:id/repository/health`; its table holds only `generate`), "Add changelog data to file" and "Get file metadata only";
- `rest/ai-coding.md` "Retrieve merge request dependencies" (it has no `merge_request_iid` row);
- `rest/verify.md` "Retrieve the latest pipeline";
- the integration sections of `rest/no-stage-assigned.md` ("Set up Asana").

A record's path is its key (V `family_problems`). So every record of such a section fails N `test_every_record_matches_its_reference_section`, and the slice must edit N's reference half. D8's "never" row bars that edit, and its exceptions row does not name it. No part-1 record sits in such a section, so this change's own tree is unaffected.
Material-because: AC-1.1 — D8's list of the files a slice edits is false for #35, whose AC-5 proves every create and ai-coding record by this method, and for every other slice whose family holds such a section.
Proposed-edit: replace "a placeholder (`registry.placeholders`) that has no `In` `path` row, or the reverse;" with "an `In` `path` row that is no placeholder of the record's path (`registry.placeholders`). A placeholder with no `In` `path` row is no difference: the endpoint comparison already fixes the path, and some tables omit the row (`create#health`);".

### C1 — An alternation is not a request form that part 1 does not build
Severity: C
Location: § D5 `attributes`, the `In` item
Defect: The text, which is my iteration-01 wording, calls `name or context` a request form part 1 does not build and keeps its key pending. But `rest/create.md` "Set commit pipeline status" also lists `name` and `context` as body rows of their own, and both are plain strings that `registry.encode` sends. Requirements Residuals name neither an alternation nor a `header` row, so the citation is false, and `POST /projects/:id/statuses/:sha` stays pending with no Residual naming it.
Proposed-edit: "An `In` `header` row is a request form part 1 does not build (`Transport.request` takes no header); such rows sit in `*name`-glob sections (`rest/openapi-only.md` "The NuGet Symbol File Download Endpoint"), pending by requirements Residuals. An alternation row (`name or context`) is not compared; its alternatives are, as the rows the section also lists." Add to the reader pin: "`create#set-commit-pipeline-status` has the body attributes `name` and `context`."

### C2 — The pair-name rule does not say whether it reads multipart part names
Severity: C
Location: § D5 "Call half", `sent_call`
Defect: `create#create-a-commit` has the required `form` row `file`, so its record declares a `FILE` `Param`. N gives that `Param` a value, so `registry.encode` makes the body multipart and sends `actions` as the parts `actions[0][k]` (`registry._pairs`). "A pair name is read as …" names pairs only. If the rule covers only query and form pairs, `actions[0][k]` is an undocumented body name, and N fails a correct record.
Proposed-edit: "A query pair, form pair or multipart part name is read as the longest documented attribute name …".

### C3 — After the Residuals cut, "until a slice settles their IDs" names no file a slice may edit
Severity: C
Location: § Residuals, first item; § D8 "never" row
Defect: `registry.lookup` refuses a second record with the same ID, and V `family_problems` names an ID that no row carries; a slice may edit neither. So only one key per Reference can be mapped. Of `create#generate-changelog-data`'s two keys (`…/changelog`, `…/changelog.txt` in `operations-index.md`), one stays pending, as do all but one of the keys of `plan#list-all-emoji-reactions-for-a-resource`. #35's draft AC-2 asks for an empty `PENDING`. The item names only `software-supply-chain-security`.
Proposed-edit: "**Several keys under one Reference** (`create#generate-changelog-data`, `plan#list-all-emoji-reactions-for-a-resource`, `software-supply-chain-security`) keep all but one key pending, because `registry.lookup` takes one record per ID. A slice whose issue asks for an empty `PENDING` records them as its residual."

### C4 — A bracketed body row with no parent row
Severity: C
Location: § D5 `attributes`, the member item
Defect: The member rule needs a parent row. `rest/growth.md` "Force a variant assignment" has the body rows `context[user]`, `context[namespace]` and `context[project]` and no `context` row, so a record declares each one as a `Param`. In the default JSON body, `registry.encode` then sends the literal top-level key `"context[user]"`. `conventions.md` "Arrays, hashes and arrays of hashes" writes a hash in JSON as a nested object. This is Y1's failure for a row with no parent.
Proposed-edit: append to the member item: "A bracketed body row with no parent row (`context[user]` in `growth#force-a-variant-assignment`) is declared in a FORM-body record; GitLab reads its pair as the hash member (`conventions.md`)."

### D1 — "The line under the heading" is blank
Severity: D
Location: § D5 `endpoints`
Proposed-edit: "every `` `METHOD path` `` span of the first non-empty line under the heading, …".

Slices #35–#40 and #42–#44: once B1 is applied, a slice edits only its family module, `graphql_only.py` and its own tests. D8's exceptions and the Residuals route the request forms, gated records, `header` rows and References with several keys. No other change in this revision contradicts text that iteration 01 passed.

Verdict: NOT-READY (0 A, 1 B)
