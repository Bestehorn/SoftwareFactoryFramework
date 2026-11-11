# Spec review, iteration 03 (delta), SPEC lane (issue #30, tier M)

Scope: the fix site of iteration 02's B1, which is design.md § D7 "The usage docstring", checked against § Correctness
Properties AC-4.1 `test_the_usage_names_every_graphql_record`. I did not re-open any text that passed iteration 01 or 02.

## Fix site

| Check | Result |
|---|---|
| Edit applied | APPLIED verbatim. D7's third `#` line ends "…record printed. A connection prints as one" and the fourth reads `        # JSON array of every page's nodes, any other result as its data, both as indented JSON. --path, --query and a`, which is the text iteration 02 proposed. |
| Columns | Measured with `pathlib` on design.md: the third `#` line is 111 columns, the fourth 118. The fence carries the module's own indentation (4 spaces before a usage line, 8 before its `#` lines, as in the `call issues/get` entry of `src/payload/scripts/github_wrapper.py`), so the docstring lines have the same widths. Both are within the 120-column limit (`coding-standards.md` rule 7). |
| `-F NAME=JSON` | in the first `#` line ("-f NAME=TEXT and -F NAME=JSON give the document's variables"). |
| `input` | in the usage line (`-F 'input={...}'`) and the first `#` line ("a mutation takes one, input"). |
| `JSON array` | now on one line, at the start of the fourth `#` line. |
| `data` | in the fourth `#` line ("any other result as its data"). |
| `exit 2` | in the fifth `#` line ("are refused: exit 2.") and the last `#` line. |
| AC-3.1's IDs and `merge-pr` | `graphql/enablePullRequestAutoMerge (use merge-pr)`, `graphql/createCommitOnBranch`, `graphql/revertPullRequest` and `graphql/transferIssue` are in the last two `#` lines. These are AC-3.1's four mutations (requirements § AC-3.1), each written as `graphql/` plus its root field. |
| Entry boundary | The entry goes after the `call issues/get` entry, whose last `#` line is followed by the blank line that closes the usage list (`src/payload/scripts/github_wrapper.py` module docstring). So every string above falls in the span the test reads: the `call graphql/` usage line and the `#` lines under it. The `call issues/get` entry's own "one JSON array" stays outside that span, as Y6 requires. |

## Side effects

- The fix moves one word between two adjacent lines. It removes " JSON" from the end of one line and adds "JSON " at the
  start of the next, so design.md's byte count does not change and the file stays within its cap.
- The meaning is unchanged. The sentence still says that a connection prints as one JSON array of every page's nodes,
  which matches requirements § AC-2.2 ("one JSON array in the form `commands/_common.print_json` writes") and
  § AC-4.1 ("how a connection and a result without one print").
- No other line in requirements.md or design.md quotes the old line break. A grep for "prints as one", "JSON array"
  and "every page's nodes" finds only D7's two lines, the AC-4.1 oracle bullet and requirements § AC-2.2.
- Scope freeze holds. The fix adds no AC or UB id, no requirement and no mechanism.

No findings.

Verdict: READY
