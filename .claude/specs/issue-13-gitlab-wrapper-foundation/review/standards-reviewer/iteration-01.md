# Standards review — iteration 01 — issue #13 (tier M)

### B1 — The UB-2 standard-library test depends on Python 3.10 in a suite held to 3.9
Severity: B
Location: design.md § Correctness Properties, UB-2 (Acceptance Criteria Mapping, UB-2: T `test_standard_library_only`)
Defect: The oracle "modules in `sys.stdlib_module_names`" uses an attribute that exists only from Python 3.10. It sits in
`src/payload/test/test_gitlab_transport.py`, a shipped suite that `tech-stack.md` holds to 3.9 ("The code stays Python
3.9-compatible"; `pyproject.toml` `requires-python = ">=3.9"`, ruff `target-version = "py39"`). On 3.9 the test raises
`AttributeError`, and no file in `src/` or `test/` uses it today.
Material-because: unmaintainable-by-rule tech-stack.md. The design pins the shipped suite to CI's 3.10 instead of the
floor the rule declares.
Proposed-edit: replace "modules in `sys.stdlib_module_names` (CI runs Python 3.10,
https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names)" with "modules in `STDLIB_ALLOWED`, a literal
set in the test of the standard-library modules the package imports (3.9-compatible; `sys.stdlib_module_names` exists
only from 3.10)".

### C1 — Hypothesis in a shipped suite is not flagged
Severity: C
Location: design.md § Testing Strategy, "Transport and records"
Defect: `dependencies.md` rule 1 asks that a third-party import under `src/payload/` be flagged explicitly.
`test_gitlab_transport.py` would be the first file under `src/` to import Hypothesis (today only strings in
`src/hooks/red_for_right_reason.py` and its test mention it). No dependency changes: Hypothesis is in `pyproject.toml`
`[project.optional-dependencies] dev` and in the dev extra the setup prompts give every project
(`prompts/setup-kiro.txt` Part 4, which `prompts/setup-claude.txt` Part 4 defers to). Only the flag is missing.
Proposed-edit: append to the bullet: "This is the first shipped suite to import Hypothesis. It is already in this
repository's `dev` extra and in every project's (`prompts/setup-kiro.txt` Part 4), so no dependency changes
(`dependencies.md`)."

### C2 — No owner named for the shared JSON-key constants
Severity: C
Location: design.md § Existing patterns followed; § Entry script and subcommands
Defect: `_load_config` in the entry script and `Transport.from_config` in `transport.py` both read `hostname`, `token`
and `token_type`. The design requires `FIELD_*` constants for every key but names no module that defines them, so the
layout leaves room for two definitions of `FIELD_HOSTNAME`/`FIELD_TOKEN`. The entry script cannot be the owner, because
the package would then have to import the entry script.
Proposed-edit: append to "Existing patterns followed": "Each JSON-key constant is defined once, in the package module
that reads the key (the config keys in `gitlab_api/transport.py`), and the entry script imports it."

### C3 — Two class names hide their base (`coding-standards.md` rule 9)
Severity: C
Location: design.md § Layout (`errors.py`, `src/payload/test/gitlab_fake_host.py`)
Defect: `ClaimError(GitLabAPIError)` and `FakeHost` (an `urllib.request.HTTPSHandler` subclass) do not show their base
in the name, and rule 9 says "The inheritance hierarchy must be visible from class names". Precedent only keeps the
suffix (`merge_steward.ConfigError(RuntimeError)`, `memory_compile.RowError(ValueError)`), so the rule's reach is
unclear.
Proposed-edit: rename them to `GitLabClaimError(GitLabAPIError)` and `FakeHostHTTPSHandler` throughout design.md.

### C4 — The template's `_comment` does not mention `token_type`
Severity: C
Location: design.md § Entry script and subcommands ("`templates/config/gitlab.json.template` is unchanged")
Defect: The template's `_comment` is where the existing optional key `in_progress_label` is documented, with its
default. The new optional `token_type` would be documented only in the usage docstring, which the operator does not see
while filling in `config/gitlab.json`.
Proposed-edit: replace "`templates/config/gitlab.json.template` is unchanged; the usage docstring documents
`token_type`." with "`templates/config/gitlab.json.template` keeps its keys (UB-2). Its `_comment` and the usage
docstring document the optional `token_type` (`private` default, `bearer`, `job`), as the `_comment` already does for
`in_progress_label`."

### C5 — The design does not say why the steward's GitLab client is not reused
Severity: C
Location: design.md § Existing patterns followed
Defect: `src/payload/scripts/merge_steward.py` already sends GitLab REST calls (`http_json`, `GitLabAPI._call`,
`GitLabAPI._pages`). `design-principles.md` rule 2 says to reuse before adding, yet the design adds a second transport
without saying why. The reason is in the code: `_pages` stops on a short page, `http_json` retries only 5xx, and
`GitLabAPI` always sends `PRIVATE-TOKEN`. AC-2.1, AC-2.5 and AC-3.2–AC-3.4 contradict all three, and the steward is
installed as an independent file.
Proposed-edit: append to "Existing patterns followed": "`merge_steward.http_json`/`GitLabAPI` is not reused. It pages
until a short page, retries only 5xx and always sends `PRIVATE-TOKEN`, which AC-2.1, AC-2.5 and AC-3.2–AC-3.4
contradict, and the steward ships as an independent file that this change leaves untouched."

### C6 — Residual: the delivery verbs with a `bearer` or `job` token
Severity: C
Location: design.md § Entry script and subcommands (the six delivery verbs, "token from `_load_config()`")
Defect: `steward_delegate` hands the steward the `token` value. `merge_steward.GitLabAPI.__init__` always sends it as
`PRIVATE-TOKEN`, but `conventions.md` "Credential types and how to send them" sends an OAuth token as
`Authorization: Bearer` and a job token as `JOB-TOKEN`. So `token_type` `bearer` (OAuth) or `job` cannot drive the
delivery verbs. Fixing that would change the steward, which is scope this change does not have.
Proposed-edit: add to design.md § Residuals: "`token_type` `bearer` (OAuth) or `job` does not reach the steward,
which sends every token as `PRIVATE-TOKEN` (`merge_steward.GitLabAPI`) → conductor to route."

### D1 — "Deviation, flagged" mislabels an established pattern
Severity: D
Location: design.md § Import bootstrap; § Existing patterns followed
Defect: `src/hooks/hooks.py`, `src/hooks/supervisor.py`, `src/hooks/kiro_hooks.py` and
`test/test_gate_toolchain_paths.py` already put their own directory on `sys.path` and import with `# noqa: E402`. The
imports stay absolute, so `coding-standards.md` rule 2 holds.
Proposed-edit: replace "Deviation, flagged: imports after a statement —" with "Precedent: `src/hooks/hooks.py` and
`src/hooks/supervisor.py` bootstrap the same way. Imports follow a statement because"; in "Existing patterns
followed" delete "and the import bootstrap above".

NOT-CLEAN (0 A, 1 B)
