# Best-practice review — design, iteration 02 (delta, issue #28)

Sources, read 2026-11-11: docs.python.org/3.9/library/argparse.html (`type`, `allow_abbrev`, "Option value syntax",
`append_const`, `ArgumentParser.error`), cli.github.com/manual/gh_api, `docs/api-reference/README.md` "Body field
paths", `docs/api-reference/github/rest/*.md`. No MCP documentation server covers Python or the GitHub REST API, so the
official web documentation was used.

Fix sites of iteration 01:

- A1 closed. D2 `query_name`, D4 "Documented names" and the D8 `registry.py` row compare a query name without one
  trailing `[]` and send it as written. No `Parameter` row of the pinned `rest/*.md` has `[]` in its name, so the
  stripping cannot hide a documented name.
- B1 closed. `Transport.pages` gains `accept` (default `ACCEPT_JSON`) and `_page_items` sends it on every page;
  `registry.pages` passes the record's. The only callers of `Transport.pages` (`registry.pages`,
  `test_github_api_transport.py`) keep the default. The AC-1.2 paged row's `application/vnd.github.full+json` is a
  type that the `issues/list-comments` section names.
- C1 and C2 applied (D2 grammar, D7 docstring, Sources).

New text checked, with no A or B finding:

- `-f`/`-F` under argparse's default `allow_abbrev`. The `call` subparser's long options (`--path`, `--query`,
  `--raw-field`, `--field`, `--help`) each start with a different letter, so no full spelling or abbreviation is
  ambiguous. The top-level parser (`_build_parser`) defines only `-h/--help`, so it claims no `call` option while it
  classifies the argv. `-fNAME=TEXT` is the documented concatenated short form. Two `append` options sharing one
  `dest` is the documented `append_const` pattern.
- The reader rules for `constraint` rows and variant labels. Every `constraint` row of the reference is `(body)`,
  except `conditions` in `actions/create-repo-actions-policy` and `actions/update-repo-actions-policy`. Each of
  those sections also has a real `conditions` object row, so dropping the constraint row loses no name. Every leading
  variant label is numbered or named (named ones can contain hyphens, as in
  `{review-custom-gates-comment-required}`). None is doubled, and every one is followed by a `.`. The five pinned
  examples read as D5 states. The only top-level name the rule cannot read, `*` in `copilot.md`, is already a
  residual.

### C1 — `-F` is not `gh api`'s typed field for text that is not a literal
Severity: C
Location: design.md § D2 (`-F/--field`: "The two spellings follow `gh api`'s string and typed fields")
Defect: `gh api -F` converts only `true`, `false`, `null` and integers to JSON types, reads `@<path>`, and keeps any
  other text as a string (cli.github.com/manual/gh_api). D2's `-F` runs `json.loads`. So `-F title=Hello` is refused
  with exit 2, and `-F version=1.5` sends a number where `gh api` sends the string `"1.5"`. The sentence claims a
  likeness that the grammar does not have.
Proposed-edit: replace "The two spellings follow `gh api`'s string and typed fields." with "The option names are
  `gh api`'s. Unlike `gh api`, `-F` takes JSON text, so a bare word is refused (exit 2) and a string is given quoted
  (`-F 'title="Hello"'`) or with `-f`."

Verdict: CLEAN
