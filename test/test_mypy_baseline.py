"""AC-1 of issue #7: ``pyproject.toml`` carries no mypy baseline.

The baseline was a ``[[tool.mypy.overrides]]`` table with ``ignore_errors = true`` that exempted whole modules from
mypy, so a new finding in one of them was hidden instead of failing the ``types`` check. These tests fail when such
a table comes back. The scan is plain text, split into TOML tables at each header line (a line starting in column 1
with ``[``): the CI Python (3.10) has no ``tomllib``.

Run: ``python scripts/run_tests.py test/test_mypy_baseline.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
OVERRIDES_HEADER = "[[tool.mypy.overrides]]"
ROOT_TABLE = ""
# The key, bare or quoted, at the start of a body line; a commented-out key is not a key.
IGNORE_ERRORS_KEY = re.compile(r"^\s*[\"']?ignore_errors[\"']?\s*=", flags=re.MULTILINE)


def normalised_header(line: str) -> str:
    """The header of a table-header line with its trailing comment and all whitespace removed."""
    return "".join(line.split(sep="#", maxsplit=1)[0].split())


def split_tables(text: str) -> list[tuple[str, str]]:
    """``(header, body)`` for every TOML table in ``text``; the lines before the first header are the root table."""
    tables: list[tuple[str, list[str]]] = [(ROOT_TABLE, [])]
    for line in text.splitlines():
        if line.startswith("["):
            tables.append((normalised_header(line=line), []))
        else:
            tables[-1][1].append(line)
    return [(header, "\n".join(body)) for header, body in tables]


def baseline_tables(text: str) -> list[str]:
    """The bodies of the ``[[tool.mypy.overrides]]`` tables in ``text`` that set ``ignore_errors``."""
    return [
        body
        for header, body in split_tables(text=text)
        if header == OVERRIDES_HEADER and IGNORE_ERRORS_KEY.search(string=body)
    ]


def test_ac1_pyproject_has_no_mypy_overrides_table_that_sets_ignore_errors() -> None:
    found = baseline_tables(text=PYPROJECT.read_text(encoding="utf-8"))
    assert not found, (
        f"{PYPROJECT.name} exempts modules from mypy with a {OVERRIDES_HEADER} table that sets ignore_errors "
        "(fix the findings instead):\n" + "\n---\n".join(found)
    )


@pytest.mark.parametrize(
    ("header", "key_line"),
    [
        ("[[tool.mypy.overrides]]", "ignore_errors = true"),
        ("[[ tool.mypy.overrides ]]  # the baseline", "ignore_errors=true"),
        ("[[tool.mypy.overrides]]", "    ignore_errors   =   false"),
        ("[[tool.mypy.overrides]]", '"ignore_errors" = true'),
    ],
    ids=["plain", "spaced-header-and-comment", "indented-any-value", "quoted-key"],
)
def test_the_scanner_finds_an_overrides_table_that_sets_ignore_errors(header: str, key_line: str) -> None:
    synthetic = "\n".join(
        [
            "[tool.mypy]",
            'python_version = "3.10"',
            "",
            "[[tool.mypy.overrides]]",
            'module = ["clean"]',
            "disallow_untyped_defs = true",
            "",
            header,
            "module = [",
            '    "exempted",',
            "]",
            key_line,
            "",
            "[tool.pytest.ini_options]",
            'addopts = "-ra"',
        ]
    )
    found = baseline_tables(text=synthetic)
    assert len(found) == 1, f"expected exactly the one exempting table, found {len(found)}: {found}"
    assert '"exempted"' in found[0] and '"clean"' not in found[0], f"the wrong table was reported: {found[0]}"
