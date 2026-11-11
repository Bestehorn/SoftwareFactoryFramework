# Standards review — design iteration 02, delta (issue #41)

Fix sites S-C1, S-C2, S-C3 and S-D1 are applied as proposed. Checked against the code: `commands/mr.py` `OP_MERGE_MR`
and `commands/issue.py` `OP_CREATE_ISSUE` exist with the IDs D1 names; C defines `load_wrapper`, `write_json` and
`main_exit_code`; `FakeGitLab.script_next` takes the same keyword-only `status`, `headers` and `body` as
`FakeGitLab.script`; design.md no longer contains `cmd_call`.

### S-C4 — The restated anchor rule gives a reason that covers `verify.py` only
Severity: C
Location: design.md § D5 "Reference half", "The anchor" bullet
Defect: The DV-C3 text restates the rule because `verify.py` imports PyYAML. But `scripts/api_reference/common.py`
`Slugger.slug` holds the same rule using the standard library only, and the generator's Reference anchors come from it
(`gitlab_rest.py` `hugo_anchor`). The design does not say why N restates the rule instead of reusing that copy. An
implementer looking to reuse code could import `common` by putting `scripts/api_reference/` on `sys.path`. No suite
does that today, and `common` is a flat top-level module name.
Proposed-edit: replace "restated (N never imports `verify.py`, which imports PyYAML):" with "restated: N imports neither
`verify.py`, which imports PyYAML, nor the generator's `common.Slugger`, so N checks the pages independently of the
generator, as `verify.py` does:".

### S-D2 — `print_bytes`'s parameter name departs from the sibling's
Severity: D
Location: design.md § D8 "This change", `commands/_common.py` row
Defect: my iteration-01 S-C3 edit named the parameter `body`. The parity source implements it as
`github_api.commands._common.print_bytes(*, data: bytes)` on the #28 branch, and "Differences from #28" does not list
the change.
Proposed-edit: in the row, replace "`print_bytes(*, body)`" with "`print_bytes(*, data)`".

Verdict: CLEAN
