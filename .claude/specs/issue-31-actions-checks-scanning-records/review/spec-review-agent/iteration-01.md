# spec-review-agent — iteration 01 (tier S, combined: all lenses)

### B1 — The SARIF and zip forms are routed to #46, whose scope excludes them
Severity: B
Location: change.md § Residuals (third bullet); decisions/decision-log.md DL-002, DL-004
Defect: The bullet routes "the other form → #46 per DL-002", and DL-002 and DL-004 rest on "#46 covers non-JSON and
alternative bodies". But #46's title, ACs and work items cover request bodies, uploads and the `307` only, and its
`prompt.md` puts "other request forms" out of scope. Choosing a response `Accept` per call is #28 requirements'
unrouted Residual ("a record sends its one `accept`"), and no open issue covers it (`list-issues`). So the residual
has no owner.
Material-because: unmaintainable-by-rule `issue-filing-discipline.md`: an item not done here is fixed, filed or
ledgered, never dropped. DL-002's Evidence ("issue #46 body") contradicts its claim (`no-guessing.md`).
Proposed-edit: third Residuals bullet → "- `code-scanning/get-analysis` and `code-scanning/get-codeql-database` send
`ACCEPT_JSON` and print JSON; their SARIF\n  and zip forms need a per-call `Accept`, outside #46's request forms →
ledger (DL-005)." Append DL-005, which supersedes the #46 routing of DL-002 and DL-004. Driver: #46's scope; Evidence:
the #46 body and its `prompt.md`, #28 `requirements.md` Residuals. The #31 comment's "routed to #46" is corrected on
the issue. B2's replacement already carries this bullet.

### B2 — `## Residuals` is 14 lines long; the cap is 10
Severity: B
Location: change.md § Residuals
Defect: The section runs to 14 wrapped lines. The 302 bullet alone takes five lines to say that nothing waits on #46.
Material-because: unmaintainable-by-rule `proportionality.md` "Scope freeze" ("recorded in `## Residuals` (≤ 10
lines)").
Proposed-edit: replace everything after the `## Residuals` heading with the block below: 10 lines, at most 120
columns, 209 B shorter (file 7,756 B). It carries B1, C1, C2 and D1.

```
- `code-scanning/commit-autofix` stays pending (DL-003): it commits to `target_ref` and no subcommand sends it; once
  #27's `None` mapping lands, gating it is one entry → ledger; the deferral is recorded on #31.
- The four `302` downloads print the archive's bytes, fetched without the credential (#28 D3). No section here has a
  non-JSON request body or a `307`; `code-scanning/upload-sarif`'s Base64 `sarif` goes on the command line (#46).
- `code-scanning/get-analysis` and `code-scanning/get-codeql-database` send `ACCEPT_JSON` and print JSON; their SARIF
  and zip forms need a per-call `Accept`, outside #46's request forms → ledger (DL-005).
- `dependabot/repository-access-for-org`, `-for-enterprise` drop `default_level`, which no other call returns → ledger.
- Callable, writing no branch (#28 Security "Destructive operations"): `actions/create-workflow-dispatch`,
  `actions/review-pending-deployments-for-run`, `secret-scanning/create-push-protection-bypass`. Secret-scanning
  alerts print each `secret` unless `--query hide_secret=true`; the runner-token records print a live token (#28 D3).
```

### C1 — `code-scanning/upload-sarif` is an upload, and its `sarif` must fit on the command line
Severity: C
Location: change.md § Residuals, second bullet ("an upload … so none waits on #46")
Defect: `conventions.md` "Uploads and binary request bodies" lists `code-scanning/upload-sarif`. Its `sarif` is the
file gzip-compressed and then Base64-encoded, up to 10 MB compressed. `call` takes it only as `-f sarif=…`, and
CreateProcessW caps a Windows command line at 32,767 characters (Microsoft Learn). A larger SARIF cannot be sent.
Taking a JSON body from a file is one of #46's open questions.
Proposed-edit: B2's second bullet.

### C2 — Responses that carry a secret go to standard output
Severity: C
Location: change.md § Residuals, last bullet
Defect: These responses print a credential through #28 D3:
- `secret-scanning/list-alerts-for-org`, `-for-repo` and `get-alert` document `hide_secret` with default `false`, so
  each alert prints its `secret`.
- `actions/create-registration-token-*` and `create-remove-token-*` answer `authentication-token`.
- `generate-runner-jitconfig-*` answers a runner configuration.
None of these values is logged: `call` logs names only, and no query value in these sections is a secret. Guarding
the output would add a mechanism, so this is a Residual.
Proposed-edit: B2's last bullet.

### D1 — The dependabot residual's reason
Severity: D
Location: change.md § Residuals, fourth bullet
Defect: "keeping both needs a record field" leaves out the fact the reader needs: GitHub's page documents no other
read of `default_level`, so `call` cannot return it at all.
Proposed-edit: B2's fourth bullet.

## Checked, no finding

- **Paging (AC-4).** Every `Paging:` section in the five files is a `GET`, and its line names either "items in
  `<key>`" or "the response body is the array". The 40 wrapped keys equal `conventions.md` "Lists wrapped in an object"
  for these families. Every section with a `page`, `per_page`, `before` or `after` row has a `Paging:` line. Every
  `(headers: Link)` outside one is one of AC-4's two single objects; as `Paging.LINK`, `_items_of` would reject either
  one (exit 1). `test_every_list_record_has_a_case` and AC-6's routes both fail on a wrong key or a wrong set.
- **The `302` records.** With `download-workflow-run-logs` they are the only `302` sections. `registry.send` →
  `_send` follows through `CredentialStrippingRedirectHandler`, which drops `Authorization` off-origin; K's AC-1.6
  case proves the path, and `Response.url` never holds the signed target.
- **UB-1.** No existing record changes. K, C and `commands/ci.py` name only the six existing IDs, and K's pending case
  is `pulls/list`.
- **Branch, merge, issue.** Only `commit-autofix` writes. Its `target_ref` is the "target branch for the commit", and
  "Branch needs to already exist". `create-autofix` "Creates an autofix" and commits nothing. `rerequest-*` and
  `create-workflow-dispatch` start runs; the fork's `dispatch-workflow` already does that, and no gate judges it. No
  record here creates an issue or merges.
- **Secrets.** `encrypted_value` is ciphertext, sent as given (DL-002); command-line values are #28 Residuals'.
- **Siblings.** The ACs follow #27 and #32; AC-4 rightly drops #27's `Link`-header arm. V's "covered and pending"
  check with F makes UB-2's `commit-autofix` refusal falsifiable.

## Coverage

| Criterion | Test | Fails when |
|---|---|---|
| AC-1 | F `test_nothing_is_pending` (4), `test_only_the_branch_writing_record_is_pending`; V covered-or-pending, one-module | an ID stays pending, `commit-autofix` is declared, or an ID has no record |
| AC-2 | N `test_every_record_matches_its_reference_section` | a method, path or name differs |
| AC-3 | F default version and media type; F multi-segment table; the `checks/list-suites-for-ref` `/` case | another version or media type; a `ref` name is missing or extra; `/` is sent as `%2F` |
| AC-4 | F `test_every_list_record_has_a_case` + AC-6 routes | the LINK set differs from the `Paging:` sections; a wrong `item_key` exits 1 |
| AC-5 | N `test_every_record_is_sent_as_its_section_documents` | a call is refused, exits non-0 or sends other names |
| AC-6 | F `test_a_list_record_prints_every_item` | an item or a page is missing (red: exit 2) |
| UB-1 | C golden cases; P parity; diff | a subcommand's output, parser or exit code changes |
| UB-2 | K gated and unknown cases; F pending test + V | a gated or undeclared ID sends |
| UB-3 | C credential; V stdlib | `environ`/`getenv`, a token option, a non-stdlib import |
| UB-4 | `test_wrapper_delivery.py`; diff | either file is touched or fails |
| E2E | N, F through `main` to the API boundary, CI `verify`/`tests`; the real-forge check is #10's | — |

Verdict: NOT-READY (0 A, 2 B)
