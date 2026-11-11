"""GitLab API wrapper for CI/CD, issue, merge-request and delivery operations.

Usage:
    python scripts/gitlab_wrapper.py pipeline status [--count N]   # the latest N pipelines (default 1)
    python scripts/gitlab_wrapper.py pipeline log                  # the traces of the latest pipeline's failed jobs
    python scripts/gitlab_wrapper.py pipeline wait <pipeline_id> --timeout-seconds 540   # foreground; re-issue on 11
        # BLOCKS until the pipeline is terminal, polling internally; exit 0 on success,
        # 10 when it ended without success (failed/canceled/skipped/manual), 11 on timeout —
        # distinct from the wrapper's own 1 (API error), 2 (usage), 3 (claim-check unclaimed).
        # Agents run it AFTER the unblocked work, in the FOREGROUND, bounded
        # (parallel-by-default.md) — never `sleep` in a tool call.
    python scripts/gitlab_wrapper.py issue list
    python scripts/gitlab_wrapper.py issue list --state opened --assignee "*" --labels in-progress
        # --state opened|closed|all; --assignee <username>, "*" (any assignee) or none (no assignee)
    python scripts/gitlab_wrapper.py issue show <iid>
    python scripts/gitlab_wrapper.py issue create --title "..." [--description "..."] [--labels "bug"]
    python scripts/gitlab_wrapper.py issue comment <iid> --body "..."
    python scripts/gitlab_wrapper.py issue start <iid>        # claim in-progress (idempotent, verified)
    python scripts/gitlab_wrapper.py issue claim-check <iid>  # read-only; exit 3 if open+unclaimed
    python scripts/gitlab_wrapper.py issue release <iid>      # drop the claim
    python scripts/gitlab_wrapper.py issue label-add <iid> --labels in-progress      # additive: other labels stay
    python scripts/gitlab_wrapper.py issue label-remove <iid> --labels in-progress
    python scripts/gitlab_wrapper.py issue assign <iid> --me | --user <username> | --unassign
    python scripts/gitlab_wrapper.py issue close <iid>
    python scripts/gitlab_wrapper.py issue reopen <iid>       # undo a premature close; exit 0 if already open
    python scripts/gitlab_wrapper.py label list
    python scripts/gitlab_wrapper.py label create --name <name> --color <color> [--description "..."]
    python scripts/gitlab_wrapper.py mr create --source <branch> --target main --title "..."
    python scripts/gitlab_wrapper.py mr get <mr_iid>
    python scripts/gitlab_wrapper.py mr checks <mr_iid>
    python scripts/gitlab_wrapper.py mr approve <mr_iid>
    python scripts/gitlab_wrapper.py mr merge <mr_iid>            # "merge": "direct" only
    python scripts/gitlab_wrapper.py delete-branch <branch>
    python scripts/gitlab_wrapper.py enqueue-pr <mr_iid>          # "merge": "steward": hand the MR to the queue
    python scripts/gitlab_wrapper.py dequeue-pr <mr_iid> --reason "..."
    python scripts/gitlab_wrapper.py queue-status [--json]
    python scripts/gitlab_wrapper.py wait-landed <mr_iid> --timeout-seconds 540     # 0 landed, 10 returned, 11 re-issue
    python scripts/gitlab_wrapper.py check-handoff <iid>                            # 0 ready, 4 not (reasons printed)
    python scripts/gitlab_wrapper.py check-landed <mr_iid> [<mr_iid> ...]           # 0 all landed, 4 not
    python scripts/gitlab_wrapper.py call plan#retrieve-a-project-issue --path issue_iid=5   # any record, by its id
        # --path NAME=VALUE (id defaults to project_id on a /projects/:id path); --query NAME=VALUE (a query
        # attribute as text; repeat it for each item of an array); -f/--raw-field NAME=TEXT (an attribute, a string);
        # -F/--field NAME=JSON (an attribute: a number, boolean, array, object or quoted string); --file NAME=PATH
        # (a file attribute, sent multipart); --input FILE (a raw-body record's body: the bytes of FILE, or of standard
        # input for -, sent unchanged; the record's attributes go in --query; refused beside -f or -F, and for a record
        # that takes no raw body); --route-prefix PREFIX (a protocol route's <route-prefix>, for a record whose path
        # starts with /<route-prefix>/: one of the values its page lists, verbatim, e.g. /groups/:id/-/packages/npm,
        # each :name of it a path parameter given with --path). A GraphQL record takes its variables with -f and -F.
        # The request forms of a REST record, one example each, the last a two-level member, by its full name:
        #   call plan#add-an-emoji-reaction-to-a-resource --path merge_request_iid=5 -f name=thumbsup
        #       --endpoint 'POST /projects/:id/merge_requests/:merge_request_iid/award_emoji'
        #   call create#delete-a-group-ssh-certificate --path id=7 --path id=12345
        #   call create#retrieve-file-archive-from-a-repository --path format=zip
        #   call software-supply-chain-security#set-status-of-an-external-control --path external_control_id=3
        #       -f status=pass --header X-Gitlab-Timestamp=1700000000 --header X-Gitlab-Nonce=n1
        #       --header X-Gitlab-Hmac-Sha256=ab12
        #   -f 'override_params[container_expiration_policy_attributes][cadence]=7d'
        # --endpoint 'METHOD path' (the endpoint of a Reference several records declare: its method, one space and its
        # path as the index writes them; without it, the Reference's first declared endpoint is sent); --path once per
        # place for a name the path holds at more than one place (its values fill the places in command-line order; no
        # default); --path format=VALUE (a [.format] suffix: one of the values its page lists; without it, no suffix
        # is sent); --header NAME=VALUE (a request header the record declares). A member of a form body below its first
        # bracket level is named in full. A container-registry record (package#delete-image-tags-by-reference) obtains
        # its registry token from the configured instance before the registry is sent anything, and the registry
        # request carries that token alone.
        # A list prints as one JSON array of every page's items, a JSON response as indented JSON, an empty body as
        # nothing, any other body as its bytes unchanged. An unknown operation, an undocumented parameter, a missing
        # path parameter, a value of the wrong shape, a route prefix that none of the record's values equals, none for
        # a record whose path starts with /<route-prefix>/ or one for any other record, an --endpoint none of the ID's
        # records is on, a --path format value its page does not list, a header the record does not declare, and a
        # record that writes a branch or a merge request's source branch, merges, writes into an existing project, or
        # creates an issue or another work item (no subcommand sends one but ai-coding#merge-a-merge-request and
        # plan#create-an-issue: use mr merge and issue create) are refused before any request: exit 2.
    python scripts/gitlab_wrapper.py call graphql#Project.workItems -f fullPath=group/project   # a GraphQL record
        # -f NAME=TEXT and -F NAME=JSON give the document's variables; a mutation takes its input object as one,
        # input, but graphql#designManagementUpload, graphql#pipelineCreate and graphql#workItemsCsvImport take each
        # field; --file NAME=PATH gives an Upload variable's file, once per item of a list, in one multipart request.
        # A global ID is an id another GraphQL record printed. A connection prints as one JSON array of every page's
        # nodes, any other result as its data. The "Only in GraphQL" capabilities and their records:
        #   Work items: graphql#workItem graphql#workItemsByReference graphql#Project.workItems graphql#Group.workItems
        #     graphql#Namespace.workItems graphql#workItemCreate graphql#workItemUpdate graphql#workItemDelete
        #     graphql#workItemExport
        #   Epics with new features (assignees, health status, links to other item types): graphql#WorkItem.widgets
        #   Branch rules: graphql#Project.branchRules graphql#branchRuleCreate graphql#branchRuleUpdate
        #     graphql#branchRuleDelete
        #   Group-wide and instance-wide vulnerability lists: graphql#Group.vulnerabilities
        #     graphql#Query.vulnerabilities graphql#Query.vulnerability
        #   Design uploads: graphql#designManagementUpload
        #   Asynchronous pipeline creation: graphql#pipelineCreate graphql#Project.ciPipelineCreationRequest
        #   Work item CSV import: graphql#workItemsCsvImport
        #   Query cost introspection: graphql#queryComplexity
        # graphql#workItemCreate and graphql#workItemsCsvImport are refused before any request: exit 2.

Exit codes: 0 done; 1 a GitLab API error, a refused claim or a refused config/gitlab.json (the reason on standard
error); 2 a usage error or a refused `call`; 3 `issue claim-check` on an open, unclaimed issue; 10 and 11
`pipeline wait` (above). The delivery verbs (`enqueue-pr` to `check-landed`) run the merge steward,
scripts/merge_steward.py, and return its exit code (0 accepted, 4 refused with the reason printed); on a host that is
not the queue's (config/delivery.json `host`) they refuse with 2. Results go to standard output (JSON, or the job
traces of `pipeline log`); diagnostics go to standard error.

Credentials: config/gitlab.json (gitignored; copy config/gitlab.json.template and fill in real values), and nothing
else: no environment variable is read. Its keys:
    hostname           the GitLab host: gitlab.com or a self-hosted instance
    project_id         the numeric project ID (Settings > General)
    token              the access token, with at least the 'api' scope; printable ASCII without the space ('!' to
                       '~'), so a pasted space, line break or invisible character is refused, by key, never echoed
    token_type         optional, how the token is sent: "private" (the default; a personal, project or group access
                       token, as PRIVATE-TOKEN), "bearer" (an OAuth 2.0 access token, as Authorization: Bearer) or
                       "job" (a CI/CD job token, as JOB-TOKEN; GitLab accepts it on a few endpoints only). The merge
                       steward the delivery verbs run sends every token as PRIVATE-TOKEN.
    in_progress_label  optional: the label `issue start` adds and verifies (default "in-progress")

This wrapper is the project's mandated entry point for all GitLab API operations (the use-git-wrapper-scripts rule,
in .claude/rules/ or .kiro/steering/). Direct use of `glab`, `gh`, raw curl, or requests against the GitLab API is
forbidden. The requests are built by the package beside this file, scripts/gitlab_api/: one record per endpoint, one
request path (gitlab_api/transport.py), and the subcommands in gitlab_api/commands/ (`commands/call.py` calls any
record by its id), whose modules this script discovers. If a host requires corporate-SSO cookie auth (e.g.
Midway-protected GitLab), add that handling in gitlab_api/transport.py, the one request path, as a clearly-commented
extension point.
"""

from __future__ import annotations

import argparse
import importlib
import io
import json
import logging
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Sequence

# The import bootstrap (design.md D3): `python scripts/gitlab_wrapper.py` puts this directory first on sys.path, a test
# loading the file with importlib.util.spec_from_file_location does not; either way gitlab_api imports absolutely.
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gitlab_api.commands  # noqa: E402
from gitlab_api.errors import GitLabAPIError  # noqa: E402
from gitlab_api.transport import (  # noqa: E402
    FIELD_HOSTNAME,
    FIELD_IN_PROGRESS_LABEL,
    FIELD_PROJECT_ID,
    FIELD_TOKEN,
    FIELD_TOKEN_TYPE,
    TokenType,
    Transport,
    token_type_of,
)

CONFIG_FILE = Path("config") / "gitlab.json"
PLACEHOLDER_MARKER = "PASTE_"
REQUIRED_KEYS = (FIELD_HOSTNAME, FIELD_PROJECT_ID, FIELD_TOKEN)
DEFAULT_IN_PROGRESS_LABEL = "in-progress"
# The characters a token may hold: printable ASCII without the space. A pasted line break, space or zero-width space
# is refused at load, named by its key and never echoed.
PRINTABLE_FIRST = "!"
PRINTABLE_LAST = "~"

# This wrapper's host as config/delivery.json names it (`steward_delegate`'s `host`).
DELIVERY_HOST = "gitlab"
TEXT_ENCODING = "utf-8"
STREAM_ERRORS = "replace"
EXIT_OK = 0
EXIT_API_ERROR = 1

# The command-module contract (design.md D6). Every module of gitlab_api.commands whose name does not start with `_`
# (`_common` is a helper) defines `register(subparsers)`: it adds its argv group to `subparsers`, the top-level
# parser's `add_subparsers` action, and gives each subcommand's parser `set_defaults(handler=<function>)`. `main` calls
# `handler(transport=…, project=…, in_progress_label=…, args=…)`; it returns None (exit 0) or the exit code.
COMMAND_DEST = "subcommand"
HANDLER = "handler"
PRIVATE_MODULE_PREFIX = "_"

logger = logging.getLogger("gitlab_wrapper")


# --- config/gitlab.json -------------------------------------------------------------------------------------------


def _read_config() -> Dict[str, Any]:
    """The JSON object of config/gitlab.json; a missing file, invalid JSON or another top-level value raises."""
    if not CONFIG_FILE.is_file():
        raise GitLabAPIError(
            f"Missing credentials file: {CONFIG_FILE}. Copy config/gitlab.json.template and fill in real values."
        )
    try:
        config = json.loads(s=CONFIG_FILE.read_text(encoding=TEXT_ENCODING))
    except json.JSONDecodeError as error:
        # The position only: the error's text never quotes the file, which holds the token.
        raise GitLabAPIError(
            f"{CONFIG_FILE} is not valid JSON: {error.msg} at line {error.lineno}, column {error.colno}."
        ) from None
    if not isinstance(config, dict):
        raise GitLabAPIError(f"{CONFIG_FILE} must hold one JSON object.")
    return config


def _refuse_incomplete(*, config: Dict[str, Any]) -> None:
    """An absent, empty or `PASTE_` value of `hostname`, `project_id` or `token` raises, naming the key."""
    for key in REQUIRED_KEYS:
        value = config.get(key)
        if not value or str(value).startswith(PLACEHOLDER_MARKER):
            raise GitLabAPIError(f"{CONFIG_FILE} is incomplete: fill in '{key}'.")


def _refuse_token_characters(*, token: str) -> None:
    """A token holding a character outside `!` to `~` raises, naming the key and the character's code point, never
    the token's value (design.md D7)."""
    refused = next((character for character in token if not PRINTABLE_FIRST <= character <= PRINTABLE_LAST), None)
    if refused is not None:
        raise GitLabAPIError(
            f"{CONFIG_FILE}: '{FIELD_TOKEN}' holds the character U+{ord(refused):04X}, and a token holds printable "
            f"ASCII without the space only ('{PRINTABLE_FIRST}' to '{PRINTABLE_LAST}'): paste it again without spaces, "
            "line breaks or invisible characters."
        )


def _token_type(*, config: Dict[str, Any]) -> TokenType:
    """The configured `token_type`: absent or empty is `private` (as `Transport.from_config` reads it); a value other
    than `private`, `bearer` and `job` raises."""
    configured = config.get(FIELD_TOKEN_TYPE)
    if configured is None or configured == "":
        return TokenType.PRIVATE
    try:
        return token_type_of(value=configured)
    except GitLabAPIError as refusal:
        raise GitLabAPIError(f"{CONFIG_FILE}: {refusal}") from None


def _load_config() -> Dict[str, Any]:
    """config/gitlab.json, checked, with `token_type` and `in_progress_label` filled in (design.md D7).

    It is the only source of the credential: nothing reads an environment variable, and `token` stays the key
    `merge_steward.read_token` reads. Every refusal is a `GitLabAPIError` that names the key."""
    config = _read_config()
    _refuse_incomplete(config=config)
    _refuse_token_characters(token=str(config[FIELD_TOKEN]))
    config[FIELD_TOKEN_TYPE] = _token_type(config=config).value
    config[FIELD_IN_PROGRESS_LABEL] = str(config.get(FIELD_IN_PROGRESS_LABEL) or DEFAULT_IN_PROGRESS_LABEL)
    return config


# Issue metadata and checklist subcommands, not served yet (#15 builds them; see the issue-tracking rule,
# .claude/rules/issue-tracking.md). A project that needs one sooner adds a module to scripts/gitlab_api/commands/
# defining register(subparsers). All paths are under /projects/{project_id} (URL-encode the id if it is a
# namespace/path rather than a numeric id); GitLab supports most of these natively:
#   - set_due_date / start: PUT /issues/{iid} {"due_date": "<YYYY-MM-DD>"}
#     for a target/end date; GitLab has no first-class "start date" on plain
#     issues (it exists on epics), so record the start as a dated note unless
#     the project uses epics.
#   - time tracking: POST /issues/{iid}/add_spent_time {"duration":"3h"}
#     (equivalent to the /spend quick action) to record time-spent; optional
#     POST /issues/{iid}/time_estimate.
#   - set_parent(iid, parent): for an epic parent use the Epic-Issues API
#     (PUT /groups/{g}/epics/{epic_iid}/issues/{issue_id}); for a parent/child
#     issue link use POST /issues/{iid}/links. If neither applies, record the
#     link as a note and report the limitation.
#   - checklist items live in the issue DESCRIPTION as "- [ ]" / "- [x]"
#     lines: toggle_checklist_item(iid, item_text, checked) by GET-ing the
#     description, flipping the matching line, and PUT-ing it back. (GitLab
#     renders these as "N of M checklist items completed".) NOT best-effort:
#     this is how a task item is marked done, and the task-item gate in
#     @close-session is satisfied by the resulting description. Consider a
#     --count mode that reports ticked/total and lists the unticked items, so
#     the gate needs no description parsing of its own.
# For every field the host or this issue does not support, return a clear
# "unsupported" result so the caller can fall back to a note and continue.


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


# --- The command line ---------------------------------------------------------------------------------------------


def command_modules(*, package: ModuleType) -> List[ModuleType]:
    """Every command module of ``package``, sorted by name, found by scanning it with ``pkgutil.iter_modules`` (the
    pattern of ``registry.discover_families``); a module whose name starts with ``_`` is a helper and is skipped."""
    names = sorted(
        info.name
        for info in pkgutil.iter_modules(path=package.__path__)
        if not info.name.startswith(PRIVATE_MODULE_PREFIX)
    )
    return [importlib.import_module(name=f"{package.__name__}.{name}") for name in names]


def build_parser() -> argparse.ArgumentParser:
    """The parser of every discovered command module; no file lists the modules."""
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest=COMMAND_DEST, metavar=COMMAND_DEST, required=True)
    for module in command_modules(package=gitlab_api.commands):
        module.register(subparsers=subparsers)
    return parser


def _utf8_streams() -> None:
    """Standard output and standard error write UTF-8: on Windows a pipe otherwise uses the ANSI code page, which
    cannot print every character of a job trace or an issue."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding=TEXT_ENCODING, errors=STREAM_ERRORS)


def _report(*, error: GitLabAPIError) -> int:
    """Log a refusal or an API error, its message and then its details, and return the API-error exit code."""
    logger.error("%s", error)
    if error.details:
        logger.error("%s", error.details)
    return EXIT_API_ERROR


def _run(*, argv: List[str]) -> int:
    """A delivery verb goes to the merge steward with the rest of argv unparsed; anything else is parsed before the
    config is read, so a usage error exits 2 whatever the config, then served by its command module's handler."""
    if argv and argv[0] in DELIVERY_VERBS:
        config = _load_config()
        return steward_delegate(verb=argv[0], args=argv[1:], token=str(config[FIELD_TOKEN]), host=DELIVERY_HOST)
    parser = build_parser()
    args = parser.parse_args(args=argv)
    handler = getattr(args, HANDLER, None)
    if not callable(handler):
        parser.error(message=f"'{getattr(args, COMMAND_DEST)}' needs one of its subcommands (see --help)")
    config = _load_config()
    result = handler(
        transport=Transport.from_config(config=config),
        project=str(config[FIELD_PROJECT_ID]),
        in_progress_label=str(config[FIELD_IN_PROGRESS_LABEL]),
        args=args,
    )
    return EXIT_OK if result is None else int(result)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run one subcommand (``None``: ``sys.argv[1:]``) and return its exit code; a ``GitLabAPIError`` of any kind is
    logged and returns 1 (design.md D7)."""
    _utf8_streams()
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        return _run(argv=arguments)
    except GitLabAPIError as error:
        return _report(error=error)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
