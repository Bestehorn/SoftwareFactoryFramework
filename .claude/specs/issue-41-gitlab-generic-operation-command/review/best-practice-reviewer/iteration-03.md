# Best-practice review — design.md, iteration 03 (delta)

Sources, read 2026-11-11: GitLab REST "Encoding API parameters of array and hash types" (https://docs.gitlab.com/api/rest/),
commits "Create a commit" (https://docs.gitlab.com/api/commits/), experiments "Force a variant assignment"
(https://docs.gitlab.com/api/experiments/); Python 3.9 `json` (https://docs.python.org/3.9/library/json.html); Python
3.12 `cgi` deprecation notice (https://docs.python.org/3.12/library/cgi.html); `docs/api-reference/gitlab/conventions.md`
"Arrays, hashes and arrays of hashes"; `rest/create.md`, `growth.md`, `ai-coding.md`, `gitlab-dedicated.md`, `verify.md`,
`openapi-only.md`; `gitlab_api/registry.py` `_pairs`, `encode`, `BodyFormat`; `gitlab_api/transport.py`
`multipart_body`, `multipart_name`. No documentation MCP server covers Python or GitLab, so official web docs were used.

Fix sites checked against the documentation, no finding:

- BP2-B1, D5 member-row bullet. A declared member is now only `parent[key]`, in a query or form record. That is
  GitLab's query and form spelling of a hash member (`--form "override_params[visibility]=private"`, REST "Hash";
  `conventions.md` row `hash`). No `[].key` or `:key` member is a `Param`, so no request sends that notation.
  `create#create-a-commit`: `rest/create.md` holds the row `file` (In `form`, "in OpenAPI only"), so a call that gives it
  is multipart (`BodyFormat`: "any FILE value makes the body multipart instead"). `actions` then goes through `_pairs` as
  `actions[0][action]`, the indexed array-of-hashes form GitLab documents (`variables[0][key]=VAR1&variables[0][value]=
  hello`, REST "Array of hashes"; `conventions.md`). Without the file the body is JSON, and `actions` is the native array
  of GitLab's JSON example.
- BP2-B1 / SR2-C4, D5 FORM ruling for a bracketed body row with no parent row. GitLab's example for "Force a variant
  assignment" sends `--data "variant=candidate" --data "context[user]=sidney-jones"`, the form pair a FORM record sends.
  Of every body row written `name[key]` in `rest/*.md`, only the three `context[...]` rows of
  `growth#force-a-variant-assignment` lack a parent row. `position[...]` (`ai-coding.md`, `create.md`),
  `configuration[...]`, `entities[...]`, `upload[...]` (`gitlab-dedicated.md`) and `platform_kubernetes_attributes[...]`
  (`verify.md`) each sit under their parent row, so the member rule reaches them, not the FORM ruling.
  The deeper `override_params[...][...]` rows are `form` rows.
- `sent_call` reads multipart part names with `email.parser.BytesParser` (SR2-C2's text). For POST bodies, Python's
  `cgi` notice names the `email.message` module as the replacement (`cgi` was removed in 3.13). I ran the product's
  `encode` and `multipart_body` in the project venv (Python 3.14.2) and parsed the body with
  `BytesParser(policy=email.policy.HTTP)`, behind the request's `Content-Type`. It read the part names `branch`,
  `actions[0][action]`, `actions[0][file_path]`, `context[user]` and `file`, which D5's longest-match rule reads as
  `branch`, `actions`, `actions`, `context[user]` and `file`. The probe was deleted.
- BP2-C1, D2 "Parsing". "`json_member` converts every `ValueError` of `json.loads`, the plain one `parse_constant`
  raises included" covers both refusals. `JSONDecodeError` is a "Subclass of ValueError" (3.9 `json`), and the hook's
  refusal is a plain `ValueError` (iteration-02 run).
- The revision's new citations match the reference:
  - `create#health` (`GET /projects/:id/repository/health`) has no `id` path row.
  - `create#set-commit-pipeline-status` has the row `name or context` and its own `name` and `context` rows.
  - `create#add-changelog-data-to-file` has `version[^version-attribute-include]` and
    `from[^unspecified-automatically-finds]`.
  - The `header` rows (`Symbolchecksum`) sit in the two `rest/openapi-only.md` "The NuGet Symbol File Download Endpoint"
    sections, whose paths carry `*file_name` globs.

Verdict: CLEAN
