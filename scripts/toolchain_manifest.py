#!/usr/bin/env python
"""Regenerate config/toolchain.json from a release tag: the manifest step of a promotion.

WHY THIS EXISTS
    This repository runs on an installed release of the framework it develops. config/toolchain.json lists every
    installed toolchain file with its product source, and the integrity test and the toolchain-paths gate read it
    as the single list of the toolchain. A promotion (prompts/update.txt) must rewrite it for the promoted release;
    written by hand it drifts from the release. This tool derives it from the release itself.

WHAT IT DOES
    1. Lists the release with `git ls-tree -r -z --name-only refs/tags/<tag> --` over the installable trees, run in
       the repository holding this script: the release is read from git, never from a working tree.
    2. Maps every listed source to its install path (LAYOUT), unless a `not_installed` entry of the previous
       manifest names it (an exact path or an `fnmatch.fnmatchcase` pattern). A source that is neither mapped nor
       named, or two sources of one install path, is refused and nothing is written.
    3. Carries `deviations` and `not_installed` forward in their order, dropping an entry whose path the release
       no longer has; every other top-level key is kept verbatim, in its place.
    4. Writes UTF-8 JSON, indent 2, no ASCII escaping, LF, one trailing newline; `files` sorted by install path.

USAGE
    python scripts/toolchain_manifest.py --release <tag>                  # rewrite config/toolchain.json
    python scripts/toolchain_manifest.py --release <tag> --installed <YYYY-MM-DD>
    python scripts/toolchain_manifest.py --release <tag> --check          # write nothing; exit 1 when it differs

    Exit 0: written, or (--check) up to date. Exit 1: --check found a difference. Exit 2: any tool error, git
    included; nothing is written.

A repository tool, like scripts/api_reference/: it is never listed under `files`.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import logging
import subprocess  # nosec B404 — runs git with a fixed argv, never a shell
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

logger = logging.getLogger(__name__)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "config" / "toolchain.json"

KEY_RELEASE_TAG = "release_tag"
KEY_INSTALLED = "installed"
KEY_FILES = "files"
KEY_DEVIATIONS = "deviations"
KEY_NOT_INSTALLED = "not_installed"
# Written even when the previous manifest lacks them; `deviations` and `not_installed` only where it has them.
REQUIRED_KEYS = (KEY_RELEASE_TAG, KEY_INSTALLED, KEY_FILES)

EXIT_OK = 0
EXIT_DIFFERS = 1
EXIT_TOOL_ERROR = 2

INSTALLABLE_TREES = ("clients/claude", "clients/common", "src/hooks", "src/payload", "templates")
# (source, install path). A row ending in "/" is a prefix: `<source><f>` installs at `<install path><f>`, where
# `<f>` is non-empty and may span subdirectories. Any other row maps exactly one source.
LAYOUT = (
    ("clients/claude/agents/", ".claude/agents/"),
    ("clients/claude/commands/", ".claude/commands/"),
    ("clients/claude/docs/", ".claude/docs/"),
    ("clients/claude/rules/", ".claude/rules/"),
    ("clients/common/docs/", ".claude/docs/"),
    ("clients/common/phases/", ".claude/specs/_workflow/phases/"),
    ("src/hooks/", ".claude/hooks/"),
    ("src/payload/", ""),
    ("templates/githooks/", ".githooks/"),
    ("templates/docs/", "docs/"),
    ("templates/setup-hooks.sh.template", "scripts/setup-hooks.sh"),
)
PREFIX_MARK = "/"

ENCODING = "utf-8"
JSON_INDENT = 2
CRLF = b"\r\n"
LF = b"\n"


class ManifestError(Exception):
    """Base of every refusal of this tool: the CLI exits 2 on any of them and writes nothing."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details


class ManifestReadError(ManifestError):
    """The previous manifest cannot be read or parsed."""


class ManifestFormatError(ManifestError):
    """The previous manifest parses, but a section of it is not an object of non-empty strings."""


class ManifestGitError(ManifestError):
    """git could not list the release."""


class ManifestUnmappedSourceError(ManifestError):
    """A release source that no LAYOUT row maps and no `not_installed` entry names."""


class ManifestCollisionError(ManifestError):
    """Two or more release sources map to one install path."""


@dataclass(frozen=True)
class DerivationReport:
    """What a regeneration changed: install paths added to and removed from `files`, and the `deviations` keys
    and `not_installed` entries dropped because the release no longer has their path."""

    added: tuple[str, ...]
    removed: tuple[str, ...]
    dropped: tuple[str, ...]


def install_path(source: str) -> str:
    """The install path of a release source under LAYOUT; raises ManifestUnmappedSourceError when no row maps it."""
    for row_source, row_install in LAYOUT:
        if row_source.endswith(PREFIX_MARK):
            if source.startswith(row_source) and len(source) > len(row_source):
                return row_install + source[len(row_source) :]
        elif source == row_source:
            return row_install
    raise ManifestUnmappedSourceError(f"no install layout row maps {source}", details=[source])


def names(entry: str, source: str) -> bool:
    """A `not_installed` entry names a source: the exact path, or an `fnmatch.fnmatchcase` pattern matching it."""
    return entry == source or fnmatch.fnmatchcase(name=source, pat=entry)


def string_section(previous: Mapping[str, Any], key: str) -> dict[str, str]:
    """A section of the previous manifest (absent: empty) as an object of non-empty strings, in its order."""
    section = previous.get(key, {})
    if not isinstance(section, dict) or not all(
        isinstance(name, str) and isinstance(value, str) and value for name, value in section.items()
    ):
        raise ManifestFormatError(f"`{key}` must be an object whose every entry is a non-empty string", details=key)
    return dict(section)


def installed_files(sources: Sequence[str], not_installed: Mapping[str, str]) -> dict[str, str]:
    """`files` for the release: install path -> source, sorted by install path, without the named sources."""
    by_install: dict[str, list[str]] = {}
    unmapped: list[str] = []
    for source in sorted(set(sources)):
        if any(names(entry=entry, source=source) for entry in not_installed):
            continue
        try:
            by_install.setdefault(install_path(source=source), []).append(source)
        except ManifestUnmappedSourceError:
            unmapped.append(source)
    if unmapped:
        raise ManifestUnmappedSourceError(
            "release sources neither mapped by the install layout nor named under `not_installed` (add an entry "
            f"with its reason): {', '.join(unmapped)}",
            details=unmapped,
        )
    collisions = {path: found for path, found in by_install.items() if len(found) > 1}
    if collisions:
        listed = "; ".join(f"{path} <- {', '.join(found)}" for path, found in sorted(collisions.items()))
        raise ManifestCollisionError(f"two sources map to one install path: {listed}", details=collisions)
    return {path: found[0] for path, found in sorted(by_install.items())}


def derive(
    *, release_paths: Sequence[str], previous: Mapping[str, Any], release_tag: str, installed: str
) -> tuple[dict[str, Any], DerivationReport]:
    """The manifest of a release and its report: a pure function of the release paths, the previous manifest, the
    tag and the date. Raises a ManifestError subclass naming what it refuses."""
    if not isinstance(previous, dict):
        raise ManifestFormatError("the previous manifest must be a JSON object", details=type(previous).__name__)
    previous_files = string_section(previous=previous, key=KEY_FILES)
    deviations = string_section(previous=previous, key=KEY_DEVIATIONS)
    not_installed = string_section(previous=previous, key=KEY_NOT_INSTALLED)
    files = installed_files(sources=release_paths, not_installed=not_installed)
    kept_deviations = {path: reason for path, reason in deviations.items() if path in files}
    kept_not_installed = {
        entry: reason
        for entry, reason in not_installed.items()
        if any(names(entry=entry, source=source) for source in release_paths)
    }
    derived: dict[str, Any] = {
        KEY_RELEASE_TAG: release_tag,
        KEY_INSTALLED: installed,
        KEY_FILES: files,
        KEY_DEVIATIONS: kept_deviations,
        KEY_NOT_INSTALLED: kept_not_installed,
    }
    manifest = {key: derived[key] if key in derived else copy.deepcopy(x=value) for key, value in previous.items()}
    for key in REQUIRED_KEYS:
        manifest.setdefault(key, derived[key])
    report = DerivationReport(
        added=tuple(sorted(set(files) - set(previous_files))),
        removed=tuple(sorted(set(previous_files) - set(files))),
        dropped=tuple(
            [path for path in deviations if path not in kept_deviations]
            + [entry for entry in not_installed if entry not in kept_not_installed]
        ),
    )
    return manifest, report


def list_release(*, tag: str, repository: Path) -> list[str]:
    """Every file of the release tag under the installable trees, read from git in the given repository."""
    command = ["git", "ls-tree", "-r", "-z", "--name-only", f"refs/tags/{tag}", "--", *INSTALLABLE_TREES]
    try:
        result = subprocess.run(  # nosec B603 — git ls-tree, fixed argv, no shell
            args=command,
            cwd=repository,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ManifestGitError(f"cannot run git: {error}", details=command) from error
    if result.returncode != 0:
        stderr = result.stderr.decode(encoding=ENCODING, errors="replace").strip()
        raise ManifestGitError(
            f"git ls-tree of refs/tags/{tag} failed (exit {result.returncode}): {stderr}", details=command
        )
    paths = [path for path in result.stdout.decode(encoding=ENCODING).split(sep="\0") if path]
    if not paths:
        raise ManifestGitError(f"refs/tags/{tag} holds no file under {', '.join(INSTALLABLE_TREES)}", details=command)
    return paths


def read_manifest(*, path: Path) -> tuple[bytes, dict[str, Any]]:
    """The previous manifest's bytes and its parsed object."""
    try:
        raw = path.read_bytes()
        parsed = json.loads(s=raw.decode(encoding=ENCODING))
    except (OSError, ValueError) as error:  # ValueError: UnicodeDecodeError and json.JSONDecodeError
        raise ManifestReadError(f"cannot read the manifest {path}: {error}", details=str(path)) from error
    if not isinstance(parsed, dict):
        raise ManifestFormatError(f"the manifest {path} is not a JSON object", details=str(path))
    return raw, parsed


def serialised(manifest: Mapping[str, Any]) -> bytes:
    """The written form: UTF-8, indent 2, no ASCII escaping, LF, one trailing newline."""
    return (json.dumps(obj=manifest, indent=JSON_INDENT, ensure_ascii=False) + "\n").encode(encoding=ENCODING)


def normalised(data: bytes) -> bytes:
    """Line endings normalised to LF, as test/test_toolchain_integrity.py compares them."""
    return data.replace(CRLF, LF)


def log_report(*, report: DerivationReport) -> None:
    for path in report.added:
        logger.info("files: added %s", path)
    for path in report.removed:
        logger.info("files: removed %s", path)
    for entry in report.dropped:
        logger.info("dropped (path no longer in the release): %s", entry)


def regenerate(*, release: str, installed: str, manifest_path: Path, check: bool) -> int:
    """Derive the manifest of the release from the one at manifest_path; write it, or (check) compare it."""
    current, previous = read_manifest(path=manifest_path)
    release_paths = list_release(tag=release, repository=REPOSITORY_ROOT)
    manifest, report = derive(release_paths=release_paths, previous=previous, release_tag=release, installed=installed)
    rendered = serialised(manifest=manifest)
    log_report(report=report)
    if check:
        if normalised(data=rendered) == normalised(data=current):
            logger.info("%s is current for %s (installed %s)", manifest_path, release, installed)
            return EXIT_OK
        logger.info("%s differs from the regeneration for %s (installed %s)", manifest_path, release, installed)
        return EXIT_DIFFERS
    try:
        manifest_path.write_bytes(data=rendered)
    except OSError as error:
        raise ManifestError(
            f"cannot write the manifest {manifest_path}: {error}", details=str(manifest_path)
        ) from error
    logger.info("wrote %s: %s, installed %s, %d files", manifest_path, release, installed, len(manifest[KEY_FILES]))
    return EXIT_OK


def iso_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate config/toolchain.json from a release tag (the promotion's manifest step)."
    )
    parser.add_argument("--release", required=True, help="the promoted release tag, vYYYY.MM.DD[.N]")
    parser.add_argument(
        "--installed", type=iso_date, default=date.today().isoformat(), help="the install date (default: today)"
    )
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST, help="the previous manifest, rewritten in place"
    )
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when the manifest differs")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(args=argv)
    try:
        return regenerate(release=args.release, installed=args.installed, manifest_path=args.manifest, check=args.check)
    except ManifestError as error:
        logger.error("%s", error)
        return EXIT_TOOL_ERROR
    except Exception:  # exit 1 means "--check found a difference" only, so an unforeseen failure is a tool error
        logger.exception("unexpected failure")
        return EXIT_TOOL_ERROR


if __name__ == "__main__":
    sys.exit(main())
