"""Fork parity of the GitHub wrapper's golden cases (UB-1.1): the installed fork produces every golden value.

The golden table ``CASES`` of ``src/payload/test/github_wrapper_fixtures.py`` is what the product's entry script must
reproduce (``src/payload/test/test_github_wrapper_compat.py``). Its oracle is the fork this repository runs,
``scripts/github_wrapper.py`` (``config/toolchain.json`` ``deviations``): each case that is neither ``c_only`` (a
deviation UB-1.1 makes on purpose) nor a delivery verb's runs against the fork in the temporary project and with the
fixture token the compatibility test builds, through the same fake GitHub host, comparing standard output, exit code
and the requests other than ``GET``. The fork's ``main()`` takes no ``argv``, so ``sys.argv`` is set.

Parser parity (P, UB-1.1): for each caller-used subcommand of the fork's parser and each nested ``issue …`` spelling,
the subparser the fork's ``_build_parser()`` builds and the one the product's entry script,
``src/payload/scripts/github_wrapper.py``, builds take the same arguments, option by option and positional by
positional: the option strings, and each argument's action kind, ``dest``, ``nargs``, ``const``, ``default``, ``type``,
``choices``, ``required`` and mutually exclusive group, and the parser's ``allow_abbrev``. The fork's ``--token-stdin``
is left out of the fork's side only, so the product carrying it would still be a difference (UB-2.1).

Both the fork and the fixtures exist only in this repository, so this module lives in ``test/`` and is never installed
into a project. No test opens a connection.

Run: ``python scripts/run_tests.py test/test_github_wrapper_fork_parity.py`` (no network).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = ROOT / "src" / "payload" / "test" / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

FORK_SCRIPT = ROOT / "scripts" / "github_wrapper.py"
FORK_MODULE = "github_wrapper_fork"
#: Every golden case the fork can produce: the C-only deviations and the delivery verbs (the steward's) left out.
FORK_CASES = tuple(case for case in fx.CASES if not case.c_only and case.argv[0] not in fx.DELIVERY_SUBCOMMANDS)

PRODUCT_SCRIPT = ROOT / "src" / "payload" / "scripts" / "github_wrapper.py"
PRODUCT_MODULE = "github_wrapper_product"
FORK_NAME = "the fork"
PRODUCT_NAME = "the product"

#: The fork's option no caller passes, which the product does not carry (UB-1.1, UB-2.1): left out of the fork's side.
FORK_ONLY_OPTIONS = frozenset({"--token-stdin"})
NO_OPTIONS: FrozenSet[str] = frozenset()

# UB-1.1's caller-used subcommands of the fork's parser, by group. The delivery verbs only the steward's parser defines
# (`wait-landed`, `check-handoff`, `check-landed`; DL-001) are not in the fork's parser, so they are not compared.
ISSUES_SUBCOMMANDS = (
    "list-issues",
    "get-issue",
    "get-issue-comments",
    "comment-issue",
    "create-issue",
    "update-issue",
    "reopen-issue",
    "checklist",
)
CLAIM_SUBCOMMANDS = ("start-issue", "release-issue", "claim-check", "label-add", "label-remove", "assign")
PULL_REQUEST_SUBCOMMANDS = ("create-pr", "get-pr", "get-pr-checks", "approve-pr", "merge-pr", "delete-remote-branch")
CI_SUBCOMMANDS = ("list-workflows", "list-runs", "get-run", "get-logs", "wait-run")
PARSED_DELIVERY_SUBCOMMANDS = ("enqueue-pr", "dequeue-pr", "queue-status")
#: The fork's nested group and its verbs (`_register_issue_group_subcommands`, routed by `ISSUE_GROUP_DISPATCH`).
ISSUE_GROUP = "issue"
NESTED_ISSUE_VERBS = ("start", "release", "claim-check", "label-add", "label-remove", "assign")
#: Each spelling compared: a flat subcommand, or the `issue` group and one of its verbs.
PARSER_SPELLINGS: Tuple[Tuple[str, ...], ...] = (
    *((name,) for name in ISSUES_SUBCOMMANDS),
    *((name,) for name in CLAIM_SUBCOMMANDS),
    *((name,) for name in PULL_REQUEST_SUBCOMMANDS),
    *((name,) for name in CI_SUBCOMMANDS),
    *((name,) for name in PARSED_DELIVERY_SUBCOMMANDS),
    *((ISSUE_GROUP, verb) for verb in NESTED_ISSUE_VERBS),
)
SPELLING_SEPARATOR = " "
OPTION_SEPARATOR = ", "
POSITIONAL = "positional"
DIFFERENCE_SEPARATOR = "; "
ABSENT = "absent"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def run_fork(*, argv: Any, monkeypatch: pytest.MonkeyPatch) -> int:
    """The exit code of the fork's ``main()`` with ``sys.argv`` set to ``argv``: its return value, or the code of the
    ``SystemExit`` it raises."""
    fork = fx.load_script(path=FORK_SCRIPT, name=FORK_MODULE, monkeypatch=monkeypatch)
    monkeypatch.setattr(target=sys, name="argv", value=[str(FORK_SCRIPT), *argv])
    try:
        result = fork.main()
    except SystemExit as exc:
        return fx.exit_code_of(exc=exc)
    assert isinstance(result, int), f"the fork's main returned {result!r}, not an exit code"
    return result


@pytest.mark.parametrize(argnames="case", argvalues=FORK_CASES, ids=fx.case_name)
def test_the_fork_produces_the_golden_case(
    case: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """UB-1.1's oracle: the fork, run on the case's project and host, writes the golden standard output, exits with the
    golden code and sends the golden requests other than ``GET``."""
    host = fx.enter_project(project=case.project, root=tmp_path, monkeypatch=monkeypatch, routes=case.routes)
    exit_code = run_fork(argv=case.argv, monkeypatch=monkeypatch)
    captured = capsys.readouterr()
    fx.assert_outcome(
        case=case, outcome=fx.Outcome(stdout=captured.out, exit_code=exit_code, requests=tuple(host.requests))
    )
    host.assert_every_request_routed()


@dataclass(frozen=True)
class ExclusiveGroupShape:
    """A mutually exclusive group an argument belongs to: whether one member is required, and its members' keys."""

    required: bool
    members: Tuple[str, ...]


@dataclass(frozen=True)
class ArgumentShape:
    """What argparse does with one argument: its action kind, where it stores, how many values it takes, its constant,
    default, type (by name), choices, whether it is required, and its mutually exclusive group."""

    action: str
    dest: str
    nargs: Any
    const: Any
    default: Any
    value_type: Optional[str]
    choices: Optional[Tuple[Any, ...]]
    required: bool
    exclusive_group: Optional[ExclusiveGroupShape]


@dataclass(frozen=True)
class ParserShape:
    """The arguments one subparser takes, keyed by their option strings (an option) or by their place (a positional),
    and whether it accepts an unambiguous prefix of an option."""

    allow_abbrev: bool
    arguments: Mapping[str, ArgumentShape]


def _subcommands(*, parser: argparse.ArgumentParser, wrapper: str, reached: str) -> Mapping[str, Any]:
    """The subparsers of ``parser``'s one subcommand set, by name."""
    found = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    assert len(found) == 1, f"{wrapper}: the parser of {reached!r} has {len(found)} subcommand sets, not one"
    return found[0].choices


def _subparser(*, parser: argparse.ArgumentParser, spelling: Tuple[str, ...], wrapper: str) -> argparse.ArgumentParser:
    """The subparser ``spelling`` names, one subcommand set at a time from ``parser``."""
    current = parser
    for depth, name in enumerate(spelling):
        reached = SPELLING_SEPARATOR.join(spelling[:depth]) or current.prog
        choices = _subcommands(parser=current, wrapper=wrapper, reached=reached)
        named = SPELLING_SEPARATOR.join(spelling[: depth + 1])
        assert name in choices, f"{wrapper}'s parser has no subcommand {named!r}"
        current = choices[name]
    return current


def _type_name(*, value_type: Any) -> Optional[str]:
    """An argument's ``type`` by name, so the same converter defined in two modules compares equal."""
    if value_type is None:
        return None
    return str(getattr(value_type, "__qualname__", repr(value_type)))


def _argument_shape(*, action: argparse.Action, group: Optional[ExclusiveGroupShape]) -> ArgumentShape:
    """The shape of ``action``, in ``group`` when it belongs to one."""
    return ArgumentShape(
        action=type(action).__name__,
        dest=action.dest,
        nargs=action.nargs,
        const=action.const,
        default=action.default,
        value_type=_type_name(value_type=action.type),
        choices=None if action.choices is None else tuple(action.choices),
        required=action.required,
        exclusive_group=group,
    )


def _parser_shape(*, parser: argparse.ArgumentParser, excluded: FrozenSet[str]) -> ParserShape:
    """The shape of every argument of ``parser`` except those carrying an option string in ``excluded``."""
    kept = [action for action in parser._actions if not excluded.intersection(action.option_strings)]
    keys: Dict[argparse.Action, str] = {}
    positionals = 0
    for action in kept:
        if action.option_strings:
            keys[action] = OPTION_SEPARATOR.join(action.option_strings)
        else:
            positionals += 1
            keys[action] = f"{POSITIONAL} {positionals}"
    groups: Dict[argparse.Action, ExclusiveGroupShape] = {}
    for group in parser._mutually_exclusive_groups:
        members = [action for action in group._group_actions if action in keys]
        shape = ExclusiveGroupShape(required=group.required, members=tuple(sorted(keys[action] for action in members)))
        for action in members:
            groups[action] = shape
    return ParserShape(
        allow_abbrev=parser.allow_abbrev,
        arguments={keys[action]: _argument_shape(action=action, group=groups.get(action)) for action in kept},
    )


def _shown(*, shape: Optional[ArgumentShape]) -> str:
    """An argument's shape as a failure message names it; an argument one side lacks is ``absent``."""
    return ABSENT if shape is None else repr(shape)


def _differences(*, fork: ParserShape, product: ParserShape) -> List[str]:
    """One line per way ``product`` differs from ``fork``: the parser's ``allow_abbrev``, then each argument, in the
    fork's order and then the product's extra ones."""
    found = []
    if fork.allow_abbrev != product.allow_abbrev:
        found.append(f"allow_abbrev: {FORK_NAME} {fork.allow_abbrev}, {PRODUCT_NAME} {product.allow_abbrev}")
    keys = [*fork.arguments, *(key for key in product.arguments if key not in fork.arguments)]
    for key in keys:
        theirs, ours = fork.arguments.get(key), product.arguments.get(key)
        if theirs != ours:
            found.append(f"{key}: {FORK_NAME} {_shown(shape=theirs)}, {PRODUCT_NAME} {_shown(shape=ours)}")
    return found


@pytest.mark.parametrize(argnames="spelling", argvalues=PARSER_SPELLINGS, ids=SPELLING_SEPARATOR.join)
def test_the_parsers_match_option_by_option(spelling: Tuple[str, ...], monkeypatch: pytest.MonkeyPatch) -> None:
    """UB-1.1 (P): the product's subparser for a caller-used subcommand or nested spelling takes the arguments the
    fork's takes, option by option and positional by positional, the fork's ``--token-stdin`` aside."""
    fork = fx.load_script(path=FORK_SCRIPT, name=FORK_MODULE, monkeypatch=monkeypatch)
    product = fx.load_script(path=PRODUCT_SCRIPT, name=PRODUCT_MODULE, monkeypatch=monkeypatch)
    fork_parser = _subparser(parser=fork._build_parser(), spelling=spelling, wrapper=FORK_NAME)
    product_parser = _subparser(parser=product._build_parser(), spelling=spelling, wrapper=PRODUCT_NAME)
    differences = _differences(
        fork=_parser_shape(parser=fork_parser, excluded=FORK_ONLY_OPTIONS),
        product=_parser_shape(parser=product_parser, excluded=NO_OPTIONS),
    )
    named = SPELLING_SEPARATOR.join(spelling)
    listed = DIFFERENCE_SEPARATOR.join(differences)
    assert not differences, f"{named}: the product's arguments differ from the fork's: {listed}"
