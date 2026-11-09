# No Ad-Hoc Temporary Variables in CLI Commands

When you run a shell command, do NOT introduce per-command temporary variables with descriptive
names (`$touched`, `$f`, `$pyFiles`, `$logPath`, `$matches`, etc.).

In Claude Code this is a CLEANLINESS rule, not an approval workaround: Claude Code does not
re-prompt on new shell variable names (that motivation was Kiro's, whose approval system matches
the literal command text). A one-off variable still splits one readable step into fragments and
hides the data you should be reading.

## Decision flow

1. **Eliminate the variable.** Most temp variables exist because a pipeline was broken up mentally.
   Stitch it back into one pipeline, or split the work into independent commands and read each
   output in full (`no-output-shortening.md`), reasoning about the combination in your own response
   — the shell is not the place to compute intersections of structured data. A single-use variable
   that merely holds a literal (a path, a filename) is the same violation: inline the literal at
   every use site.
   - WRONG: `sha=$(git rev-parse HEAD); git tag "release-$sha"`
   - RIGHT: `git tag "release-$(git rev-parse HEAD)"`
2. **Genuinely unavoidable** (an expensive command's result reused in two places that cannot be one
   pipeline)? Use ONLY the canonical names: `$v1`, `$v2`, `$v3` for single values, `$l1`, `$l2`,
   `$l3` for lists. Any other name is forbidden inline — `$f`, `$file`, `$path`, `$result`,
   `$output`, `$tmp`, `$line`, `$data`, `$count`, `$items` included.
3. **More than three variables?** The command is too complex for the shell. Write a disposable
   script in `tmp/` (`tmp/<name>.py`) and invoke it as one command. Inside the script descriptive
   names are encouraged (`coding-standards.md`): code files and CLI invocations follow intentionally
   opposite naming policies, because the constraints differ.
