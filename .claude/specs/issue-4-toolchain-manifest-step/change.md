# Change — issue #4: Promotion does not maintain config/toolchain.json

Tier: S. Kind: BUGFIX.

## User Prompts

> Work this project's open-issue backlog AUTONOMOUSLY, end to end

(the `/auto-work` run), and the issue title:

> Promotion does not maintain config/toolchain.json

## Ask

The operator's words (issue #4): "make the promotion of this repository reproducible — either teach
`prompts/update.txt` a "manifest" step for projects that keep a toolchain manifest, or commit the manifest
generator as a repository tool (`scripts/`) that the promotion runs, with a test." Route: DL-001.

## Acceptance criteria

- AC-1 WHEN a release is promoted into this repository by the committed procedure (`prompts/update.txt` `## Task`
  step 7, then the command `docs/forLLMConsumption.md` `## Two halves (read this first)` names), the tool SHALL
  rewrite `config/toolchain.json` with `release_tag` = the promoted tag and `installed` = the `--installed` date
  (default: today).
- AC-2 WHEN the release carries a file under an installable tree (`clients/claude`, `clients/common`,
  `src/hooks`, `src/payload`, `templates`), the tool SHALL list it under `files` at its install path with its
  source unless a `not_installed` entry names it (exact path or `fnmatch.fnmatchcase` pattern; every entry
  carries a reason), and SHALL report each `files` entry added or removed against the previous manifest. IF a
  source is neither mapped nor named, or two sources map to one install path, THEN the tool SHALL exit non-zero
  naming them and write nothing. Mapping (`<f>` may span subdirectories):

  | Source | Install path |
  |---|---|
  | `clients/claude/<d>/<f>`, `<d>` one of agents, commands, docs, rules | `.claude/<d>/<f>` |
  | `clients/common/docs/<f>` | `.claude/docs/<f>` |
  | `clients/common/phases/<f>` | `.claude/specs/_workflow/phases/<f>` |
  | `src/hooks/<f>` | `.claude/hooks/<f>` |
  | `src/payload/<f>` | `<f>` |
  | `templates/githooks/<f>` | `.githooks/<f>` |
  | `templates/docs/<f>` | `docs/<f>` |
  | `templates/setup-hooks.sh.template` | `scripts/setup-hooks.sh` |

- AC-3 The manifest step SHALL need no uncommitted tooling: the tool is committed, imports only the standard
  library, and lists the release with `git ls-tree -r -z --name-only refs/tags/<tag> --` over the installable
  trees, run in the repository holding the script — never from a working tree; only the previous manifest
  (`--manifest`) is read from disk.
- AC-4 WHEN the tool regenerates from the committed manifest with `--release` its `release_tag` and `--installed`
  its `installed`, the result SHALL equal the committed `config/toolchain.json` as parsed JSON and as text after
  CRLF-to-LF normalisation (`test/test_toolchain_integrity.py` `normalised`). Written form: UTF-8, `json.dumps`
  indent 2, `ensure_ascii=False`, one trailing newline, LF; top-level keys in the previous order, `comment` and
  other keys verbatim; `files` sorted by install path; `deviations` and `not_installed` in their previous order.
- AC-5 WHEN `--check` is given, the tool SHALL write nothing and exit zero when the regeneration equals the
  `--manifest` file (normalised as in AC-4), non-zero when it differs.

## Unchanged behaviour

- UB-1 `test/test_toolchain_integrity.py` and `.claude/hooks/gate_toolchain_paths.py` `_manifest` SHALL CONTINUE
  TO read `config/toolchain.json` as their single list of the toolchain; neither changes, nor do the `files`
  entries.
- UB-2 Every `deviations` and `not_installed` entry SHALL CONTINUE TO survive a regeneration with its reason
  unless the release no longer contains its path (a `deviations` key absent from the derived `files`, an exact
  `not_installed` path absent from the release, a pattern matching no release source); then it is dropped and
  reported.

## Files

- `scripts/toolchain_manifest.py` (new) — a repository tool like `scripts/api_reference/`, never listed in
  `files`. CLI `--release <tag>` (required), `--installed <YYYY-MM-DD>`, `--manifest <path>` (default: that
  repository's `config/toolchain.json`), `--check`; exit 1 only when `--check` finds a difference, 2 on any tool
  error, git included. The derivation is a pure function of the release paths
  (a list of strings), the previous manifest, tag and date, returning the manifest and the report; git is read
  by a separate function. The `subprocess` import and the git call carry bandit `# nosec` annotations as in
  `scripts/ci_outage_mode.py`; the CLI configures INFO logging as `scripts/github_wrapper.py` does.
- `config/toolchain.json` — `not_installed` gains, with reasons: `clients/claude/README.md`,
  `templates/README.md`, `templates/docs/README.md` (descriptions of the product trees, not installed files);
  `src/hooks/ruff.toml` (the root `ruff.toml` extends it in place); `templates/pre-commit-config.yaml.template`
  (this repository keeps its own `.pre-commit-config.yaml`).
- `prompts/update.txt` — `## Task` step 7 gains one sentence: a project that keeps a toolchain manifest
  regenerates it in the same commit as the marker, with the command its `docs/forLLMConsumption.md` names.
- `docs/forLLMConsumption.md` — `## Two halves (read this first)` names
  `python scripts/toolchain_manifest.py --release <tag>` as the promotion's manifest step.
- `test/test_toolchain_manifest.py` (new).

## Tests

In `test/test_toolchain_manifest.py` unless named. Test and tool paths name existing files or carry a `<…>`
placeholder (`test/test_layout.py` `test_every_framework_path_named_in_a_live_file_exists`).

- AC-1 example: the derivation sets `release_tag` and `installed` as given; `prompts/update.txt` step 7 names the
  toolchain manifest; `docs/forLLMConsumption.md` names `scripts/toolchain_manifest.py --release`.
- AC-2 example (synthetic list; the CLI case uses git): sources land at their install paths; `templates/ci/*`
  drops its sources; an unmapped unnamed source and a collision each raise, naming the path; added and removed
  entries are reported; the CLI on a copy lacking the `clients/claude/README.md` entry exits 2, the copy unchanged.
- AC-3 example: every module the tool imports (parsed with `ast`) is in `sys.stdlib_module_names`.
- AC-4 integration (git, the real tag): the CLI regenerates a `tmp_path` copy of the committed manifest; the copy
  equals the committed file as parsed JSON and as normalised text; the written bytes hold no CR.
- AC-5 integration (arguments as in AC-4): `--check` on the committed manifest exits zero; with `--installed`
  one day later, on a `tmp_path` copy, it exits non-zero and leaves the copy byte-identical.
- UB-1 regression: `test/test_toolchain_integrity.py` and `test/test_gate_toolchain_paths.py`, unmodified, stay
  green; AC-4 proves `files` unchanged.
- UB-2 example (synthetic): a release lacking `src/payload/scripts/merge_steward.py` drops that `not_installed`
  entry and reports it; a deviation whose install path leaves `files` is dropped and reported; a
  `templates/config/*` matching nothing is dropped; the other entries keep their reasons and order.

E2E: not applicable — repository tooling, no runtime behaviour. CI's `tests` group runs the test;
`.github/workflows/ci.yml` checks out with `fetch-depth: 0`, so the tag is present.

## Tasks

## Wave 1 — the manifest tool

- [ ] 1.1 TEST: the tests above. A fixture asserts the repository's `scripts/toolchain_manifest.py` is a file,
  then loads it with `importlib.util.spec_from_file_location`: the red is that assertion, not an import error at
  module load; the AC-1 text checks are red on the missing sentences. — Files:
  test/test_toolchain_manifest.py — Validates: AC-1–AC-5, UB-1, UB-2
- [ ] 1.2 IMPL: the tool, the five `not_installed` entries, the step 7 sentence, the map pointer. — Files:
  scripts/toolchain_manifest.py, config/toolchain.json, prompts/update.txt, docs/forLLMConsumption.md —
  Validates: AC-1–AC-5, UB-1, UB-2

## Residuals

None.
