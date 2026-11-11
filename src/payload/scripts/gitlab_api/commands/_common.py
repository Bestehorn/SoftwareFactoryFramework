"""What the command modules of ``gitlab_api.commands`` share (issue #13, design.md D6): not a command module itself.

Its name starts with ``_``, so the entry script's discovery (``gitlab_wrapper.command_modules``) skips it. It holds:

- the two output forms of a subcommand's result on standard output (the diagnostics go to standard error through
  ``logging``): ``print_json``, ``json.dumps(..., indent=2)`` and a line end, and ``print_bytes``, a body that is not
  JSON by its ``Content-Type`` written as its bytes unchanged, with no line end added (issue #41, design.md D3):
  ``sys.stdout`` is flushed first, so the text already written comes before the bytes, which go to
  ``sys.stdout.buffer``;
- ``EXIT_REFUSED``, the exit code of a ``call`` refused before any request is sent: 2, the code of argparse's usage
  error (issue #41, design.md D4);
- the argument helpers every module builds its argv group with: ``add_group`` (a group such as ``issue``, whose
  subcommands are required), ``add_command`` (one subcommand and its handler, ``set_defaults(handler=...)`` as the
  entry script reads it) and ``add_iid`` (the ``<iid>`` positional);
- the ``FIELD_*`` keys more than one command module reads or sends, and ``PATH_PROJECT``, the ``:id`` path value of
  every project record (D6: ``:id`` is always the configured ``project``). A key only one module reads is defined in
  that module.

The handler contract (the comment above ``gitlab_wrapper.COMMAND_DEST``): ``handler(transport=, project=,
in_progress_label=, args=)`` returns ``None`` (exit 0) or the exit code; a ``GitLabAPIError`` propagates to ``main``,
which logs it and exits 1.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING, Any, Callable, Optional

# The `:id` path parameter of every `/projects/:id/...` record; its value is the configured project.
PATH_PROJECT = "id"

# Keys more than one command module reads or sends: a user's, pipeline's or job's `id` (`issue`, `pipeline`), and the
# `title` and `description` an `issue create`, `label create` or `mr create` sends (rest/plan.md, rest/ai-coding.md).
FIELD_ID = "id"
FIELD_TITLE = "title"
FIELD_DESCRIPTION = "description"

# The `dest` of a group's subcommand choice. The entry script's top-level choice is `subcommand`
# (`gitlab_wrapper.COMMAND_DEST`), so a group uses another name.
ACTION_DEST = "action"
IID_ARGUMENT = "iid"
JSON_INDENT = 2
LINE_END = "\n"
# A refusal decided before any request is sent; argparse's usage error exits with the same code.
EXIT_REFUSED = 2

# A handler as the entry script calls it (design.md D6).
Handler = Callable[..., Optional[int]]

if TYPE_CHECKING:
    SubParsers = argparse._SubParsersAction[argparse.ArgumentParser]


def print_json(*, value: Any) -> None:
    """Write ``value`` as indented JSON on standard output, the result of a subcommand."""
    sys.stdout.write(json.dumps(obj=value, indent=JSON_INDENT) + LINE_END)


def print_bytes(*, data: bytes) -> None:
    """Write ``data`` on standard output unchanged, with no line end added: ``sys.stdout`` is flushed first, then the
    bytes go to ``sys.stdout.buffer`` (Python docs, ``sys.stdout``: "to write bytes to stdout, use
    ``sys.stdout.buffer.write``")."""
    sys.stdout.flush()
    sys.stdout.buffer.write(data)  # positional: a binary stream's write takes its bytes positional-only


def add_group(*, subparsers: SubParsers, name: str, help_text: str) -> SubParsers:
    """Add the argv group ``name`` (``issue``, ``pipeline``) and return the action its subcommands are added to; a
    group without one of its subcommands is a usage error (exit 2)."""
    group = subparsers.add_parser(name=name, help=help_text, description=help_text)
    return group.add_subparsers(dest=ACTION_DEST, metavar=ACTION_DEST, required=True)


def add_command(*, subparsers: SubParsers, name: str, handler: Handler, help_text: str) -> argparse.ArgumentParser:
    """Add the subcommand ``name`` served by ``handler`` and return its parser, for the subcommand's own arguments."""
    parser = subparsers.add_parser(name=name, help=help_text, description=help_text)
    parser.set_defaults(handler=handler)
    return parser


def add_iid(*, parser: argparse.ArgumentParser, help_text: str) -> None:
    """Add the ``<iid>`` positional: an integer, so a value that is not one is a usage error (exit 2)."""
    parser.add_argument(IID_ARGUMENT, type=int, help=help_text)
