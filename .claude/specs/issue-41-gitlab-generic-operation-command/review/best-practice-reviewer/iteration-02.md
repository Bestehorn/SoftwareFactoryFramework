# Best-practice review — design.md, iteration 02 (delta)

Sources, read 2026-11-11: Python 3.9 `json` (https://docs.python.org/3.9/library/json.html) and `argparse` `type`
(https://docs.python.org/3.9/library/argparse.html); GitLab REST "Encoding API parameters of array and hash types"
(https://docs.gitlab.com/api/rest/) and commits "Create a commit" (https://docs.gitlab.com/api/commits/);
`docs/api-reference/gitlab/conventions.md` "Arrays, hashes and arrays of hashes"; `rest/*.md`; `gitlab_api/registry.py`
`_pairs`, `encode`, `BodyFormat`. No documentation MCP server covers Python or GitLab, so official web docs were used.

Fix sites checked against the documentation, no finding:

- BP-B1, D5 `attributes`. Every member row of `rest/*.md` written with `[` or `:` has its parent row in the same table
  (`position`, `actions[]`, `files`, `strategies`, `assets`, `granular_scopes`, `test_splits`), so "another row's name
  followed by `[` or `:`" reaches all of them. The JSON form, the member inside the parent's `-F` value, is GitLab's
  (`"override_params": {"visibility": "private"}`; `"variables": [{"key": "VAR1", "value": "hello"}]`). A
  `parent[key]` member declared in a query or form is GitLab's own spelling (`override_params[visibility]=private`).
  D8's slice row and the `create#create-a-commit` pin agree with D5.
- BP-B2, D2 `-F`. `json.loads(s=TEXT, parse_constant=...)` fits the 3.9 signature (`json.loads(s, *, ...,
  parse_constant=None, ...)`) and the documented use ("This can be used to raise an exception if invalid JSON numbers
  are encountered"); the Sources quote is verbatim. Run in the project venv (Python 3.14.2): `NaN`, `Infinity`,
  `-Infinity` and `[1, NaN]` each raise the hook's `ValueError`. H's sketch draws floats with `allow_nan=False,
  allow_infinity=False`, so the property stays outside the refused texts.
- BP-C1: the `HEAD` residual is in `## Residuals`.

### B1 — The member rule lets a form record send `actions[].action`, a name GitLab does not read
Severity: B
Location: design.md § D5 "Reference half", `attributes`, the member-row bullet
Defect: Its last clause, "a query or form record may still declare it, as part 1's `not[labels]` is", covers every
member row, those written `[].key` or `:key` included. A form record that declares `actions[].action` as a `Param` is
sent by `registry._pairs` as the literal pair `actions[].action=create`, while GitLab documents the form field as
`--form "actions[][action]=create"` (commits "Create a commit"; `conventions.md` "Arrays, hashes and arrays of
hashes"). `record_problems` matches that `Param` to its row by name, and `sent_call` reads the sent name as a
documented body name (it equals the row's name, or continues `actions` with `[`), so D5 reports no undocumented name.
Material-because: wrong-behaviour. Every `[].key` and `:key` member row of the reference is `In` body (`create`,
`verify`, `software-supply-chain-security`), so the clause reaches each such record a slice writes as FORM. The design
does not say whether a record whose call is multipart is a JSON-body or a form record, and `create#create-a-commit` is
one: its `form` row `file` makes its body multipart (`BodyFormat`: "any FILE value makes the body multipart
instead"). The clause comes from my iteration-01 proposed edit, which drew it too wide.
Proposed-edit: in D5's member-row bullet, replace "a query or form record may still declare it, as part 1's
`not[labels]` is." with "a query or form record may still declare a member written `parent[key]`, which is GitLab's
query and form spelling of a hash member (part 1's `not[labels]`). A member written `[].key` or `:key` is never a
`Param`, because no request sends that notation: the form spelling is `actions[][action]` (`conventions.md` "Arrays,
hashes and arrays of hashes")."

### C1 — The `parse_constant` refusal is a plain `ValueError`, not a `JSONDecodeError`
Severity: C
Location: design.md § D2 "Parsing", the `ArgumentTypeError` bullet
Defect: The local run shows `isinstance(error, json.JSONDecodeError)` is false for the hook's refusal. So a
`json_member` that converts only `JSONDecodeError` into `ArgumentTypeError` lets the refusal reach argparse. argparse
formats a type function's `ValueError` as "invalid <type> value: '<argument>'" (3.9 `type`; run: `call: error:
argument -F: invalid member value: 'title=NaN'`). The exit is still 2, but the message holds the value, which D2's "it
never holds a value" forbids. K's NaN cases check only exit 2 and that no request is sent.
Proposed-edit: in D2 "Parsing", after "raise `argparse.ArgumentTypeError`", insert "(`json_member` converts every
`ValueError` that `json.loads` raises, the `parse_constant` refusal included; `JSONDecodeError` subclasses
`ValueError`)".

Verdict: NOT-CLEAN (0 A, 1 B)
