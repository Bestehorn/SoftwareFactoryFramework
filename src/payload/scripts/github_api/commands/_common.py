"""What the GitHub wrapper's command modules share (design D2, D5): body resolution, standard-output printing, and the
fork's ``FIELD_*`` names that more than one command module reads.

``add_body_arguments`` and ``resolve_body`` are the fork's ``--body``/``--body-file`` pair and its ``_resolve_body``:
the body comes from ``--body`` or from the UTF-8 file ``--body-file`` names (read with ``pathlib``, so what is on disk
is exactly what is posted, past any shell quoting), and supplying both is a ``GitHubAPIError`` rather than a silent
precedence rule. The printers write a command's result to standard output as the fork's ``print`` calls write it:
``print_json`` as ``json.dumps(value, indent=2)`` (how the fork echoes a response), ``print_compact_json`` as
``json.dumps(value)`` (its one-line verdicts), ``print_line`` one line of text. ``print_bytes`` writes a body that is
not a JSON document as its bytes unchanged, with no line end added (issue #28 design D3): ``sys.stdout`` is flushed
first, so the text already written comes before the bytes, which go to ``sys.stdout.buffer``. Diagnostics go to
``logging``, never through these. ``EXIT_REFUSED`` is the exit code of a refusal decided before any request is sent.

Not a command module: the entry script skips every ``_``-prefixed module of ``github_api.commands`` (D6).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from github_api.errors import GitHubAPIError

# The fork's field names that more than one of the issues, claim, pull-request and CI command modules reads.
FIELD_NUMBER = "number"
FIELD_STATE = "state"
FIELD_TITLE = "title"
FIELD_BODY = "body"
FIELD_LABELS = "labels"
FIELD_NAME = "name"
FIELD_STATUS = "status"
FIELD_CONCLUSION = "conclusion"

OPTION_BODY = "--body"
OPTION_BODY_FILE = "--body-file"
#: The ``argparse.Namespace`` attributes the two options are stored under.
ARG_BODY = "body"
ARG_BODY_FILE = "body_file"
#: The fork's ``BODY_FILE_HELP``, verbatim.
BODY_FILE_HELP = "Path to a UTF-8 markdown file holding the body (avoids shell mangling; not with --body)"
BODY_FILE_ENCODING = "utf-8"
BOTH_BODIES_REFUSAL = "pass either --body or --body-file, not both"

JSON_INDENT = 2
LINE_END = "\n"

#: A refusal before any request is sent: the code of argparse's usage error and of the entry script's credential and
#: repository refusals.
EXIT_REFUSED = 2


def add_body_arguments(*, parser: argparse.ArgumentParser) -> None:
    """Register ``--body`` and ``--body-file`` on ``parser`` as the fork registers them on each command that posts a
    body; giving both is ``resolve_body``'s refusal (exit 1), not an argparse usage error."""
    parser.add_argument(OPTION_BODY)
    parser.add_argument(OPTION_BODY_FILE, help=BODY_FILE_HELP)


def resolve_body(*, args: argparse.Namespace) -> Optional[str]:
    """The body from ``--body`` or from the file ``--body-file`` names; ``None`` when neither was given, so a command
    whose body is optional keeps it optional; ``GitHubAPIError`` when both were."""
    body_file = getattr(args, ARG_BODY_FILE, None)
    body = getattr(args, ARG_BODY, None)
    if body_file is not None and body is not None:
        raise GitHubAPIError(message=BOTH_BODIES_REFUSAL)
    if body_file is not None:
        return Path(body_file).read_text(encoding=BODY_FILE_ENCODING)
    return body


def print_line(*, text: str) -> None:
    """Write ``text`` and a line end to standard output, as ``print(text)`` writes it."""
    sys.stdout.write(f"{text}{LINE_END}")


def print_json(*, value: Any) -> None:
    """Write ``value`` as indented JSON and a line end, as the fork's ``print(json.dumps(value, indent=2))``."""
    print_line(text=json.dumps(obj=value, indent=JSON_INDENT))


def print_compact_json(*, value: Any) -> None:
    """Write ``value`` as one line of JSON, as the fork's ``print(json.dumps(value))``."""
    print_line(text=json.dumps(obj=value))


def print_bytes(*, data: bytes) -> None:
    """Write ``data`` to standard output unchanged, with no line end added: ``sys.stdout`` is flushed first, then the
    bytes go to ``sys.stdout.buffer`` (Python docs, ``sys.stdout``: "to write bytes to stdout, use
    ``sys.stdout.buffer.write``")."""
    sys.stdout.flush()
    sys.stdout.buffer.write(data)  # positional: a binary stream's write takes its bytes positional-only
