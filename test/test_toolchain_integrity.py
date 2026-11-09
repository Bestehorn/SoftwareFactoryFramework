"""The toolchain integrity check: every installed toolchain file equals its product source at the pinned release.

This repository develops the framework AND runs on an installed copy of one of its releases
(docs/reports/self-hosting-proposal-2026-11-07.md). config/toolchain.json lists each installed file with its
source; .claude/FRAMEWORK_COMMIT names the release commit. A hand edit of an installed file would make
development run on code no release contains, and the next promotion would silently overwrite it — so it fails
here, naming the product file to change instead. A deliberate difference is listed under `deviations` with its
reason. Line endings are compared normalised (git stores LF; a core.autocrlf checkout may carry CRLF).

Run: ``python scripts/run_tests.py test/test_toolchain_integrity.py`` (needs git and the full history: CI checks
out with fetch-depth 0).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "config" / "toolchain.json").read_text(encoding="utf-8"))
FILES: dict = MANIFEST["files"]
DEVIATIONS: dict = MANIFEST.get("deviations", {})


def pinned_commit() -> str:
    line = (ROOT / ".claude" / "FRAMEWORK_COMMIT").read_text(encoding="utf-8").split()
    return line[0] if line else ""


def framework_blob(source: str) -> bytes:
    result = subprocess.run(["git", "show", f"{pinned_commit()}:{source}"], cwd=ROOT, capture_output=True, check=False)
    assert result.returncode == 0, (
        f"cannot read {source} at the pinned commit {pinned_commit()[:12]}: "
        f"{result.stderr.decode(errors='replace').strip()} (a shallow clone lacks it: fetch the full history)"
    )
    return result.stdout


def normalised(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def test_the_pin_is_the_commit_of_the_release_tag() -> None:
    # The sha lives in .claude/FRAMEWORK_COMMIT only: quoted in JSON it reads as a high-entropy secret.
    assert re.fullmatch(r"[0-9a-f]{40}", pinned_commit()), ".claude/FRAMEWORK_COMMIT must start with a full sha"
    tag = MANIFEST["release_tag"]
    assert re.fullmatch(r"v\d{4}\.\d{2}\.\d{2}(\.\d+)?", tag), "release tags are vYYYY.MM.DD[.N]"
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"release tag {tag} is not in this clone (fetch the tags)"
    named = result.stdout.strip()
    assert named == pinned_commit(), (
        f"release tag {tag} names {named[:12]}, but .claude/FRAMEWORK_COMMIT pins {pinned_commit()[:12]}"
    )


def test_every_deviation_is_an_installed_file_with_a_reason() -> None:
    for path, reason in DEVIATIONS.items():
        assert path in FILES, f"deviation {path} is not an installed toolchain file"
        assert isinstance(reason, str) and len(reason) >= 40, f"deviation {path} needs a stated reason"


@pytest.mark.parametrize("installed", sorted(FILES), ids=str)
def test_an_installed_file_equals_its_source_at_the_release(installed: str) -> None:
    path = ROOT / installed
    assert path.is_file(), f"toolchain file {installed} is missing (source: {FILES[installed]})"
    if installed in DEVIATIONS:
        return
    assert normalised(path.read_bytes()) == normalised(framework_blob(FILES[installed])), (
        f"{installed} differs from {FILES[installed]} at release {MANIFEST['release_tag']}. The toolchain is never "
        f"edited by hand: change {FILES[installed]} and promote a release, or record a deviation with its reason."
    )
