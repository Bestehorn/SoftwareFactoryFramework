"""GitHub API wrapper for CI/CD, issue, and PR operations.

Usage:
    python scripts/github_wrapper.py list-workflows
    python scripts/github_wrapper.py list-runs --limit 5
    python scripts/github_wrapper.py wait-run <run_id> --timeout-seconds 540   # foreground; re-issue on exit 11
        # BLOCKS until the workflow run completes, polling internally; exit 0 on success,
        # 10 when it completed with any non-success conclusion (failure/cancelled/skipped/
        # timed_out/...), 11 on timeout — distinct from the wrapper's own 1 (API error),
        # 2 (usage), 3 (claim-check unclaimed). Agents run it AFTER the unblocked work, in the
        # FOREGROUND, bounded (parallel-by-default.md) — never `sleep` in a tool call.
    python scripts/github_wrapper.py get-logs <run_id> --failed-only
    python scripts/github_wrapper.py list-issues
    python scripts/github_wrapper.py list-issues --state open --assignee "*" --label in-progress
    python scripts/github_wrapper.py create-issue --title "..." --body "..."
    python scripts/github_wrapper.py start-issue <number>    # claim in-progress (idempotent, verified)
    python scripts/github_wrapper.py claim-check <number>    # read-only; exit 3 if open+unclaimed
    python scripts/github_wrapper.py release-issue <number>  # drop the claim
    python scripts/github_wrapper.py reopen-issue <number>   # undo a premature close
    python scripts/github_wrapper.py create-pr --head <branch> --base main --title "..." --body-file <path>
    python scripts/github_wrapper.py get-pr <pr_number>
    python scripts/github_wrapper.py get-pr-checks <pr_number>
    python scripts/github_wrapper.py approve-pr <pr_number>
    python scripts/github_wrapper.py merge-pr <pr_number> --method squash   # "merge": "direct" only
    python scripts/github_wrapper.py delete-remote-branch <branch>
    python scripts/github_wrapper.py enqueue-pr <pr_number>     # "merge": "steward": hand the PR to the queue
    python scripts/github_wrapper.py dequeue-pr <pr_number> --reason "..."
    python scripts/github_wrapper.py queue-status [--json]
    python scripts/github_wrapper.py wait-landed <pr_number> --timeout-seconds 540  # 0 landed, 10 returned, 11 re-issue
    python scripts/github_wrapper.py check-handoff <issue_number>                   # 0 ready, 4 not (reasons printed)
    python scripts/github_wrapper.py check-landed <pr_number> [<pr_number> ...]     # 0 all landed, 4 not
    python scripts/github_wrapper.py call issues/get --path issue_number=5   # any record, by its operation ID
        # --path NAME=VALUE (owner and repo default to the origin in .git/config); --query NAME=VALUE (a name
        # repeated sends each value; an array parameter is NAME[]; a comma-list filter is one value, labels=bug,ui);
        # -f/--raw-field NAME=TEXT (a string body member); -F/--field NAME=JSON (a number, boolean, array, object,
        # null or quoted string). A list prints as one JSON array of every page's items, a JSON body as indented JSON,
        # an empty body as nothing, any other body as its bytes unchanged. An unknown operation,
        # an undocumented parameter, a missing path parameter, and pulls/merge and issues/create (use merge-pr
        # and create-issue) are refused before any request: exit 2.
    python scripts/github_wrapper.py call markdown/render-raw --input README.md   # a body that is not JSON
        # --input FILE (- reads standard input): the request body, its bytes sent unchanged with the record's media
        # type, for repos/upload-release-asset (sent to uploads.github.com) and markdown/render-raw; --input for any
        # other operation, or together with -f/-F, is refused before any request: exit 2.

Credentials: credentials/github-pat.txt (one-line PAT, gitignored).
The owner/repo are auto-detected from .git/config — do NOT hardcode them.

This wrapper is the project's mandated entry point for all GitHub API
operations (see .kiro/steering/use-git-wrapper-scripts.md). Direct use
of `gh`, `glab`, raw curl, or requests against api.github.com is
forbidden.

Layout: this script is the entry point beside its standard-library package `github_api/` (the two are copied together):
`github_api/transport.py` sends every request, `github_api/registry.py` and `github_api/families/` hold the operation
records, and `github_api/commands/` holds the subcommands, `commands/call.py` (the operation call) among them. A
subcommand is added as a module of `github_api/commands/` that defines `register(subparsers)`: it adds its parsers and
sets each one's `handler` default to a function called as `handler(transport=..., owner=..., repo=..., args=...)`, which
returns None (exit 0) or an exit code. Every module there whose name does not start with `_` is discovered, so no list
names them. The delivery verbs stay in this script and delegate to scripts/merge_steward.py. A `GitHubAPIError` exits 1;
a usage error, a credential refusal, a repository refusal or a refused `call` exits 2.
"""

from __future__ import annotations

import argparse
import configparser
import importlib
import json
import logging
import pkgutil
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Sequence, Tuple

if str(Path(__file__).resolve().parent) not in sys.path:
    # Run as `python scripts/github_wrapper.py`, the interpreter already put this directory first; loaded by path
    # (`importlib.util.spec_from_file_location`), it did not. Either way the package beside the script imports.
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from github_api.errors import GitHubAPIError
from github_api.transport import Transport

CREDENTIALS_FILE = Path("credentials") / "github-pat.txt"
PLACEHOLDER = "PASTE_YOUR_GITHUB_PAT_HERE"

GIT_CONFIG_FILE = Path(".git") / "config"
ORIGIN_SECTION = 'remote "origin"'
ORIGIN_URL_KEY = "url"
GITHUB_REPOSITORY_PATTERN = re.compile(r"github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?/?$")
#: A remote URL's optional scheme, then its authority (RFC 3986: up to the first `/`, `?` or `#`); an scp-like remote
#: (`git@github.com:o/r.git`) has no scheme and its authority runs to the first `/`.
URL_AUTHORITY_PATTERN = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*://)?([^/?#]*)")
USERINFO_SEPARATOR = "@"

COMMANDS_PACKAGE = "github_api.commands"
MODULE_SEPARATOR = "."
PRIVATE_MODULE_PREFIX = "_"
DEST_COMMAND = "command"
HOST_GITHUB = "github"

STREAM_ENCODING = "utf-8"
STREAM_ERRORS = "replace"
LOG_FORMAT = "%(levelname)s: %(message)s"
JSON_INDENT = 2

EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_REFUSED = 2  # a usage error (argparse's own code), a credential refusal or a repository refusal

logger = logging.getLogger("github_wrapper")


# The delivery verbs (`enqueue-pr`, `dequeue-pr`, `queue-status`) — a REFERENCE IMPLEMENTATION, wired as-is in
# main(); test/test_wrapper_delivery.py (src/payload/test/test_wrapper_delivery.py) pins it.
STEWARD_SCRIPT = Path("scripts") / "merge_steward.py"
DELIVERY_CONFIG = Path("config") / "delivery.json"
DELIVERY_VERBS = {
    "enqueue-pr": "enqueue",
    "dequeue-pr": "dequeue",
    "queue-status": "status",
    "wait-landed": "wait-landed",  # the session's bounded wait for its PR to land (0 landed, 10 returned, 11 re-issue)
    "check-handoff": "check-handoff",  # may the issue be handed off? (0 yes, 4 no — the reasons are printed)
    "check-landed": "check-landed",  # have all these PRs landed? (0 yes, 4 no — one line per PR that has not)
}
EXIT_DELIVERY_ELSEWHERE = 2

CMD_ENQUEUE_PR = "enqueue-pr"
CMD_DEQUEUE_PR = "dequeue-pr"
CMD_QUEUE_STATUS = "queue-status"
#: The delivery verbs whose argv after the subcommand is handed to the steward unparsed, so the steward's parser is
#: their only argument definition (DL-001).
UNPARSED_DELIVERY_VERBS = frozenset({"wait-landed", "check-handoff", "check-landed"})
STEWARD_REASON = "--reason"
STEWARD_JSON = "--json"


def steward_delegate(verb: str, args: list[str], token: str, host: str) -> int:
    """Run the project's merge steward for one delivery verb and return its exit code (0 accepted, 4 refused
    with the reason printed, 1 host error, 2 usage). This wrapper's own token goes to the steward on STDIN —
    never in argv, a URL, an environment variable or a second credential file. The queue lives on ONE host
    (`config/delivery.json` `host`): on any other — a host kept as a read-only archive or mirror — every
    delivery verb refuses, because no PR lands there."""
    primary = "github"
    if DELIVERY_CONFIG.is_file():
        primary = str(json.loads(DELIVERY_CONFIG.read_text(encoding="utf-8")).get("host") or "github")
    if primary != host:
        logger.error(
            "%s: the merge queue lives on %s (config/delivery.json), not on this %s host; enqueue the PR there",
            verb,
            primary,
            host,
        )
        return EXIT_DELIVERY_ELSEWHERE
    import subprocess  # nosec B404  # the project's own steward script, a fixed argv, never a shell

    command = [sys.executable, str(STEWARD_SCRIPT), "--token-stdin", DELIVERY_VERBS[verb], *args]
    return subprocess.run(command, input=token + "\n", text=True, check=False).returncode  # nosec B603  # fixed argv


def _one_token(*, data: bytes, refusal: str) -> str:
    """The token `data` holds, its outer whitespace stripped (the fork's `_one_token`).

    `data` holds one token when it decodes as UTF-8 and, its outer whitespace stripped, holds no whitespace, no
    non-printable and no non-ASCII character, so that a second pasted line or a pair of smart quotes never reaches a
    request's `Authorization` header. Anything else raises `GitHubAPIError(refusal)`, a message that names the source
    and none of `data`; the decode error is raised again `from None`, because its own message names a byte and its
    position. An empty `data` gives the empty string, which the caller refuses in its own words.
    """
    try:
        token = data.decode(encoding="utf-8").strip()
    except UnicodeDecodeError:
        raise GitHubAPIError(message=refusal) from None
    if any(ch.isspace() or not ch.isprintable() or not ch.isascii() for ch in token):
        raise GitHubAPIError(message=refusal)
    return token


def _load_token() -> str:
    """The token in `CREDENTIALS_FILE`, the wrapper's only credential source, refusing a file that is missing, holds
    the placeholder or is not one token (`_one_token`). Each refusal names the file and none of its contents."""
    if not CREDENTIALS_FILE.exists():
        raise GitHubAPIError(
            message=f"Missing credentials file: {CREDENTIALS_FILE}. Create it and paste your GitHub PAT (one line)."
        )
    not_one_token_message = (
        f"{CREDENTIALS_FILE} does not hold a single token. Paste only your GitHub PAT, on one line, into this file."
    )
    token = _one_token(data=CREDENTIALS_FILE.read_bytes(), refusal=not_one_token_message)
    if not token or token == PLACEHOLDER:
        raise GitHubAPIError(
            message=f"{CREDENTIALS_FILE} still contains the placeholder. Paste a real GitHub PAT into this file."
        )
    return token


def _without_userinfo(*, url: str) -> str:
    """`url` with its userinfo removed — the authority's text up to and including its last `@`, a bare token
    included — so a refusal can name a remote URL without the credential it may carry."""
    match = URL_AUTHORITY_PATTERN.match(string=url)
    if match is None or USERINFO_SEPARATOR not in match.group(1):
        return url
    host = match.group(1).rpartition(USERINFO_SEPARATOR)[2]
    return f"{url[: match.start(1)]}{host}{url[match.end(1) :]}"


def _detect_repo() -> Tuple[str, str]:
    """(owner, repo) of the `origin` remote in .git/config, parsed as the fork parses it.

    A missing .git/config, a missing `origin` and an origin URL that names no GitHub repository each raise
    `GitHubAPIError`; the last names .git/config and the URL without its userinfo, never the URL as written. The file
    is read without interpolation: git gives `%` no meaning, and an interpolation error would quote the URL's text.
    """
    if not GIT_CONFIG_FILE.exists():
        raise GitHubAPIError(message="Not a git repository (no .git/config found).")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(filenames=GIT_CONFIG_FILE)
    if ORIGIN_SECTION not in parser:
        raise GitHubAPIError(message="No 'origin' remote configured in .git/config.")
    url = parser[ORIGIN_SECTION][ORIGIN_URL_KEY]
    match = GITHUB_REPOSITORY_PATTERN.search(string=url)
    if not match:
        shown = _without_userinfo(url=url)
        raise GitHubAPIError(message=f"Could not parse GitHub owner/repo from the origin URL in .git/config: {shown}")
    return match.group(1), match.group(2)


def _force_utf8_output() -> None:
    """Reconfigure stdout and stderr to UTF-8, replacing what cannot be encoded, so a character outside the console's
    code page (an issue title's) never aborts a command (the fork's `_force_utf8_output`). A stream without
    `reconfigure` (a test double) is left as it is."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding=STREAM_ENCODING, errors=STREAM_ERRORS)


def _register_delivery_subcommands(*, subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """The parsed delivery verbs with the fork's `_register_delivery_subcommands` arguments; each delegates to
    scripts/merge_steward.py through `steward_delegate`."""
    parser = subparsers.add_parser(
        name=CMD_ENQUEUE_PR, help="Hand a PR whose own CI is green to the merge queue (exit 4: refused)"
    )
    parser.add_argument("pr_number", type=int)
    parser = subparsers.add_parser(name=CMD_DEQUEUE_PR, help="Take a PR out of the merge queue")
    parser.add_argument("pr_number", type=int)
    parser.add_argument(STEWARD_REASON, required=True, help="Why it leaves the queue; posted on the PR")
    parser = subparsers.add_parser(name=CMD_QUEUE_STATUS, help="Print the merge queue")
    parser.add_argument(STEWARD_JSON, action="store_true", help="The machine-readable form")


def _discover_command_modules() -> List[ModuleType]:
    """Every module of `github_api.commands` whose name does not start with `_`, imported by its absolute name, in
    sorted name order (as `github_api.registry.discover_families` finds the families): a subcommand module is found
    by being in the directory."""
    package = importlib.import_module(name=COMMANDS_PACKAGE)
    names = sorted(
        module.name
        for module in pkgutil.iter_modules(path=package.__path__)
        if not module.name.startswith(PRIVATE_MODULE_PREFIX)
    )
    return [importlib.import_module(name=f"{COMMANDS_PACKAGE}{MODULE_SEPARATOR}{name}") for name in names]


def _build_parser() -> argparse.ArgumentParser:
    """The wrapper's parser: the parsed delivery verbs and every discovered command module's subcommands."""
    parser = argparse.ArgumentParser(description="GitHub API wrapper")
    subparsers = parser.add_subparsers(dest=DEST_COMMAND, required=True)
    _register_delivery_subcommands(subparsers=subparsers)
    for module in _discover_command_modules():
        module.register(subparsers=subparsers)
    return parser


def _steward_arguments(*, args: argparse.Namespace) -> List[str]:
    """What follows the steward verb for a parsed delivery verb, as the fork's handlers pass it (`steward_delegate`
    prepends the steward verb itself); nothing for any other subcommand."""
    if args.command == CMD_ENQUEUE_PR:
        return [str(args.pr_number)]
    if args.command == CMD_DEQUEUE_PR:
        return [str(args.pr_number), STEWARD_REASON, args.reason]
    if args.command == CMD_QUEUE_STATUS:
        return [STEWARD_JSON] if args.json else []
    return []


def _parse(*, arguments: List[str]) -> Tuple[argparse.Namespace, List[str]]:
    """The parsed `arguments` and what a delivery verb hands the steward after its verb. The argv after
    `wait-landed`, `check-handoff` or `check-landed` is not parsed, so the steward's parser is their only argument
    definition (DL-001); everything else is parsed by `_build_parser()`, whose usage error exits 2."""
    if arguments and arguments[0] in UNPARSED_DELIVERY_VERBS:
        return argparse.Namespace(command=arguments[0]), arguments[1:]
    args = _build_parser().parse_args(args=arguments)
    return args, _steward_arguments(args=args)


def _run_command(*, args: argparse.Namespace, token: str, owner: str, repo: str) -> int:
    """Call the parsed subcommand's handler with a `Transport` holding `token`: a `GitHubAPIError` is logged with its
    details and exits 1; otherwise the handler's `None` is 0 and an integer is the exit code (the fork's
    `_exit_code_of`)."""
    transport = Transport(token=token)
    try:
        result = args.handler(transport=transport, owner=owner, repo=repo, args=args)
    except GitHubAPIError as exc:
        logger.error("%s", exc)
        if exc.details is not None:
            logger.error("Details: %s", json.dumps(obj=exc.details, indent=JSON_INDENT))
        return EXIT_API_ERROR
    return EXIT_OK if result is None else int(result)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run one subcommand and return its exit code; `argv` `None` reads `sys.argv[1:]`.

    The output streams become UTF-8 before anything is parsed (`_parse`). The token (`_load_token`) and the
    repository (`_detect_repo`) are then read, a refusal of either logged and exiting 2. A delivery verb returns
    `steward_delegate`'s code; any other subcommand runs its handler (`_run_command`).
    """
    _force_utf8_output()
    args, steward_args = _parse(arguments=list(sys.argv[1:] if argv is None else argv))
    try:
        token = _load_token()
        owner, repo = _detect_repo()
    except GitHubAPIError as exc:
        logger.error("%s", exc)
        return EXIT_REFUSED
    if args.command in DELIVERY_VERBS:
        return steward_delegate(verb=args.command, args=steward_args, token=token, host=HOST_GITHUB)
    return _run_command(args=args, token=token, owner=owner, repo=repo)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    sys.exit(main())
