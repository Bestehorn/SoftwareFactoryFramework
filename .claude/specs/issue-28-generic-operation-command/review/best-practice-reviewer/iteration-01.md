# Best-practice review — design, iteration 01 (issue #28)

Sources, read 2026-11-11: docs.python.org/3.9 (`argparse`, `sys`, `http.client`), docs.github.com/en/rest/activity/starring,
cli.github.com/manual/gh_api, `docs/api-reference/github/conventions.md`. No MCP documentation server covers Python or
the GitHub REST API, so the official web documentation was used.

### A1 — A `NAME[]` query name passes D4's check and is then refused by `send` and `pages`
Severity: A
Location: design.md § D2 (`--query`; "Registry additions", `send`) and § D4 ("Documented names")
Defect: D4 checks a query name that ends in `[]` without the `[]`. But `send` keeps "`_check_names` for query and body"
  as `call` does today, and `registry.pages` is unchanged. `_check_names` compares each given name verbatim with
  `query_params`, which holds the reference's bare names: array parameters are listed without brackets (`rest/orgs.md`
  `token_id`, `rest/migrations.md` `exclude`, typed `array of string`). So D2's own AC-1.2 example `--query state[]=open`,
  and every array parameter spelled the way `conventions.md` "Query strings" requires (`repository_ids[]=1&repository_ids[]=2`),
  raises `ValueError` inside the handler. The design maps that error to no exit code, because `_run_command` catches only
  `GitHubAPIError`. The result is a traceback, no request, and no exit 2.
Material-because: AC-1.2. A documented query parameter given in the documented array form is never sent
  (wrong-behaviour).
Proposed-edit: in § D2 "Registry additions" add the bullet "`_check_names` checks a query name that ends in `[]` by the
  name without the `[]`, as D4 does, so `send` and `pages` accept every query name D4 accepts and send it as written.";
  in § D8 change the `registry.py` row to "adds `path_parameters` and `send`; `_check_names` checks a query name without
  its trailing `[]`; `call` becomes `send(...).json()`".

### B1 — A `Paging.LINK` record's `accept` is never sent
Severity: B
Location: design.md § D2 step 5 and "Registry additions"; § D3 `Paging.LINK`; § D8
Defect: D2 sends a `Paging.LINK` record through `registry.pages`. That function passes `Transport.pages` no media type,
  and `Transport._page_items` sends `Accept: application/vnd.github+json` on every page. GitHub documents Link-paged
  lists whose custom media type changes the items: `application/vnd.github.star+json` on "List stargazers" adds the
  time each star was created (docs.github.com/en/rest/activity/starring), `text-match+json` does the same on the
  `search/*` lists, and the `raw`/`text`/`html`/`full` types apply to the issue, pull request and comment lists
  (`conventions.md` "Custom media types"). A slice's list record that carries one of these types is therefore sent
  with the default type. D8 bars the slice from `commands/*` and allows `transport.py` only for the exceptions it names,
  so the slice has no edit that fixes it. The AC-1.2 oracle ("`Accept` equal to the record's `accept`") cannot catch
  this, because every #17 record's `accept` is `ACCEPT_JSON`.
Material-because: AC-1.2 (the record's `accept` is not sent for a `Paging.LINK` record). AC-1.1 is also affected: D8
  does not name the files a slice would have to edit to make such a record callable.
Proposed-edit: § D2 step 5 → "A `Paging.LINK` record goes through `registry.pages(...)`, which passes the record's
  `accept` to `Transport.pages`; any other record goes through `registry.send(...)`. Output is as in D3."; in § D8 add
  the row "`src/payload/scripts/github_api/transport.py` | `pages` and `_page_items` take `accept` (default
  `ACCEPT_JSON`, so every existing caller is unchanged) and send it on every page", and extend the `registry.py` row
  with "`pages` passes `accept=operation.accept`"; in § Correctness Properties AC-1.2 add "R
  `test_pages_sends_the_record_accept`: a synthetic `Paging.LINK` record with `application/vnd.github.star+json` sends
  that `Accept` on both pages."

### C1 — `--field` means the opposite of `gh api`'s `--field`
Severity: C
Location: design.md § D2 (grammar); § D7
Defect: GitHub's own CLI uses `-f/--raw-field` for "static string parameters" and `-F/--field` for typed values (`true`,
  `false`, `null`, integers) (cli.github.com/manual/gh_api). D2's `--field` is the string form. A caller who knows
  `gh api` will write `--field draft=true`, which sends the string `"true"` and gets an HTTP error (exit 1) instead of
  the typed call.
Proposed-edit: rename `--field NAME=TEXT` to `--raw-field NAME=TEXT` in § D2, § D5, § D7 (the docstring lines and the
  map sentence) and the Correctness Properties examples, and leave `--json-field` as it is.

### C2 — The docstring suggests repeating a parameter that GitHub takes as one comma-separated value
Severity: C
Location: design.md § D7 (usage docstring)
Defect: `conventions.md` "Query strings" says array parameters are spelled `NAME[]`, and that many list filters are one
  comma-separated string (`labels=bug,ui,@high` on `issues/list-for-repo`). The docstring's "a name repeated sends
  each value" names neither, so a caller is likely to repeat `labels`, and the reference does not document how GitHub
  handles a repeated plain name.
Proposed-edit: in § D7 replace "(a name repeated sends each value; NAME[] as the reference spells an array)" with "(a
  name repeated sends each value; an array parameter is NAME[], and a comma-list filter is one value, labels=bug,ui)".

Verdict: NOT-CLEAN (1 A, 1 B)
