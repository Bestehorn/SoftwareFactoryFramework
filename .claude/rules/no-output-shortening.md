# Read Complete Command Output (CRITICAL)

When you run a shell command, you MUST read its complete, unabbreviated output. Truncating, tailing,
or paginating output causes two failure modes:

1. **Stalled commands.** A command that prompts for input (a credential, a confirmation, a missing
   parameter) holds the terminal until input arrives. If the prompt is in lines you discarded, you
   wait forever while the command waits for you.
2. **Hidden errors and warnings.** The relevant error is rarely on the last 30 lines. Truncation
   hides root causes and forces blind retries.

## Forbidden patterns (PowerShell, cmd, bash, zsh, fish)

- `| Select-Object -Last <N>` / `| Select-Object -First <N>` / `| Select -Last|-First <N>`
- `| tail [-n <N>]` / `| tail -<N>`, `| head [-n <N>]` / `| head -<N>`
- `| more`, `| less`, `| Out-Host -Paging`
- `| sed -n '1,30p'` or any `sed`/`awk` invocation that drops lines
- `2>&1 > /dev/null`, `2>&1 > NUL`, `*> $null`, `2>&1 | Out-Null`
- Redirecting stderr/stdout to a file you then read partially
- Any wrapper that limits output by line count, byte count, or page

Forbidden shapes, for example:

```bash
python scripts/run_tests.py src/hooks/tests 2>&1 | tail -50
```

```powershell
python tmp\local_build_test.py 2>&1 | Select-Object -Last 30
```

## Required behavior

1. Run the command without any output filter.
2. Wait for the command to complete (exit code returned).
3. Read 100% of stdout and stderr — relevant errors are often in the middle, not the tail. Search
   the captured output rather than truncating it.

## When the output really is enormous

Megabytes of output usually mean a missing log level or a debug flag left on. Reduce verbosity at
the source (a log-level flag, `--quiet`, `-v` removed), or write the FULL output to a file in `tmp/`
and read that file with Read/Grep (`native-tools-over-shell.md`): the file is the COMPLETE output;
you just choose where to look. Never write a truncated file, and never use a truncating pipe to
"make output more manageable" — it discards information you have not yet decided is irrelevant.

## Why the shell level is different

Claude Code's own tools may cap what they DISPLAY; that is fine, because nothing was discarded and
you can ask for more. The patterns above operate at the SHELL level and discard data before any
tool sees it. Once shell-level truncation happens, the data is gone.
