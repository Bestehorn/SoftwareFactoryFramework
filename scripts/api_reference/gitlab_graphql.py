"""Parse GitLab's generated GraphQL reference (doc/api/graphql/reference/*.md) into the shared schema model.

GitLab does not publish its SDL in the repository; the reference pages are generated from the schema by
`rake gitlab:graphql:docs:compile` and are regular: one `##` heading per type, `###` subsections for fields,
arguments, implementations and member types, tables with Name/Type/Description columns, and the arguments of a
field inlined in its description cell. Descriptions are not copied; only facts are kept (deprecation version,
experiment status, introduced-in version, defaults). The reference collapses connection and edge types to one
line ("Paginated collection of X"); their standard fields are restored here.
"""

from __future__ import annotations

import re
from pathlib import Path

from graphql_model import Arg, Field, Schema, TypeDef

H2 = re.compile(r"^## `([^`]+)`")
H3 = re.compile(r"^### `([^`]+)` (fields|arguments|implementations|member types|extra fields)\b")
TYPE_LINK = re.compile(r"\[`([^`]+)`\]\([^)]*\)|^`([^`]+)`$")
ARG_DEF = re.compile(r"<dt>`([^`]+)` \((?:\[`([^`]+)`\]\([^)]*\)|`([^`]+)`)\)</dt>(?:<dd>(.*?)</dd>)?")
DEPRECATED = re.compile(r"\b[Dd]eprecated in GitLab (\d+\.\d+)")
EXPERIMENT = re.compile(r"\[experiment\]\([^)]*\) in GitLab (\d+\.\d+)|Status\W+Experiment", re.I)
BETA = re.compile(r"\bStatus\W+Beta\b")
INTRODUCED = re.compile(r"\bIntroduced in GitLab (\d+\.\d+)")
DEFAULT = re.compile(r"\b[Dd]efaults?(?: value)?(?: is| to|:)\s+(`[^`]+`|[\w.+-]+)")
INPUT_TYPE = re.compile(r"^\*\*Input type:\*\* `([^`]+)`")
RETURNS = re.compile(r"^\*\*Returns:\*\* \[?`([^`]+)`")
IMPLEMENTS = re.compile(r"^\*\*Implements:\*\* (.*)$")
MEMBER = re.compile(r"^- \[`([^`]+)`\]")
NAMES = re.compile(r"\[`([^`]+)`\]")
CONNECTION_OF = re.compile(r"Paginated collection of \[`([^`]+)`\]")
GID_EXAMPLE = re.compile(r'`"(gid://gitlab/[^"]+)"`')
CONNECTION_NOTE = "accepts the four standard pagination arguments"

FILES = {
    "objects.md": "object",
    "interfaces.md": "interface",
    "unions.md": "union",
    "enums.md": "enum",
    "input_objects.md": "input",
    "scalars.md": "scalar",
}


# ---- facts and cells -------------------------------------------------------------------------------------------------
def facts(text: str) -> list[str]:
    notes = []
    dep = DEPRECATED.search(text)
    if dep:
        notes.append(f"**deprecated** in {dep.group(1)}")
    exp = EXPERIMENT.search(text)
    if exp:
        notes.append("experiment" + (f" since {exp.group(1)}" if exp.group(1) else ""))
    elif BETA.search(text):
        notes.append("beta")
    intro = INTRODUCED.search(text)
    if intro and not exp:
        notes.append(f"since {intro.group(1)}")
    return notes


def default_of(text: str) -> str | None:
    match = DEFAULT.search(re.sub(r"<[^>]+>", " ", text or ""))
    return match.group(1).strip("`").rstrip(".") if match else None


def type_of(text: str) -> str:
    match = TYPE_LINK.search(text.strip())
    return (match.group(1) or match.group(2)) if match else text.strip().strip("`")


def pagination() -> list[Arg]:
    return [Arg("after", "String"), Arg("before", "String"), Arg("first", "Int"), Arg("last", "Int")]


def split_row(line: str) -> list[str]:
    cells, buf, in_code = [], "", False
    body = line.strip()[1:]
    body = body[:-1] if body.endswith("|") else body
    for ch in body:
        in_code ^= ch == "`"
        if ch == "|" and not in_code:
            cells.append(buf.strip())
            buf = ""
        else:
            buf += ch
    cells.append(buf.strip())
    return cells


def rows_of(lines: list[str]) -> list[dict[str, str]]:
    """The rows of the first table in `lines`, as dicts keyed by the lower-cased header."""
    table = [ln for ln in lines if ln.startswith("|")]
    if len(table) < 2:
        return []
    header = [h.lower() for h in split_row(table[0])]
    return [dict(zip(header, split_row(row))) for row in table[2:]]


def name_of(row: dict[str, str], key: str = "name") -> str:
    return row.get(key, "").strip("`")


# ---- splitting a page into blocks ------------------------------------------------------------------------------------
def blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split a page at every ``## `Name` `` heading; any other `##` heading (prose sections) ends the block."""
    out: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    for line in lines:
        match = H2.match(line)
        if match:
            current = []
            out.append((match.group(1), current))
        elif line.startswith("## "):
            current = None
        elif current is not None:
            current.append(line)
    return out


def subsections(body: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """The block's intro lines, and its `###` subsections keyed by kind ("fields", "arguments", ...)."""
    intro: list[str] = []
    subs: dict[str, list[str]] = {}
    target = intro
    for line in body:
        match = H3.match(line)
        if match:
            target = subs.setdefault(match.group(2), [])
        elif line.startswith("#"):
            target = subs.setdefault("other", [])
        else:
            target.append(line)
    return intro, subs


# ---- types -----------------------------------------------------------------------------------------------------------
def field_from_row(kind: str, row: dict[str, str]) -> Field:
    desc = row.get("description", "")
    if kind == "input":
        return Field(name_of(row), type_of(row.get("type", "")), notes=facts(desc), default=default_of(desc))
    args = [
        Arg(name, linked or plain, default_of(text), facts(text or ""))
        for name, linked, plain, text in ARG_DEF.findall(desc)
    ]
    if CONNECTION_NOTE in desc:
        args = pagination() + args
    return Field(name_of(row), type_of(row.get("type", "")), args, facts(desc))


def parse_type(kind: str, name: str, body: list[str]) -> TypeDef:
    intro, subs = subsections(body)
    text = " ".join(intro)
    typedef = TypeDef(kind, name, notes=facts(text))
    for line in intro:
        implements = IMPLEMENTS.match(line)
        if implements:
            typedef.interfaces = NAMES.findall(implements.group(1))
    item = CONNECTION_OF.search(text)
    if item and kind == "object":
        typedef.notes.append(f"connection of `{item.group(1)}`")
        edge = f"[{name.removesuffix('Connection')}Edge]"
        typedef.fields = [Field("edges", edge), Field("nodes", f"[{item.group(1)}]"), Field("pageInfo", "PageInfo!")]
    if kind == "enum":
        typedef.fields = [Field(name_of(r, "value"), "", notes=facts(r.get("description", ""))) for r in rows_of(intro)]
    example = GID_EXAMPLE.search(text) if kind == "scalar" else None
    if example:
        typedef.notes.append(f"global ID, e.g. `{example.group(1)}`")
    typedef.members = [m.group(1) for m in map(MEMBER.match, subs.get("member types", [])) if m]
    for key in ("fields", "arguments", "extra fields"):
        typedef.fields += [field_from_row(kind, row) for row in rows_of(subs.get(key, []))]
    return typedef


# ---- root fields (queries and mutations) -----------------------------------------------------------------------------
def first_match(pattern: re.Pattern, lines: list[str]) -> str | None:
    return next((m.group(1) for m in map(pattern.match, lines) if m), None)


def parse_root_field(name: str, body: list[str], schema: Schema, mutation: bool) -> Field:
    intro, subs = subsections(body)
    text = " ".join(intro)
    fld = Field(name, first_match(RETURNS, intro) or "", notes=facts(text))
    if CONNECTION_NOTE in text:
        fld.args = pagination()
    args = [
        Arg(
            name_of(r),
            type_of(r.get("type", "")),
            r.get("default", "").strip().strip("`") or None,
            facts(r.get("description", "")),
        )
        for r in rows_of(subs.get("arguments", []))
    ]
    if not mutation:
        fld.args += args
        return fld
    stem = name[0].upper() + name[1:]
    input_name = first_match(INPUT_TYPE, intro) or f"{stem}Input"
    schema.add(TypeDef("input", input_name, [Field(a.name, a.type, notes=a.notes, default=a.default) for a in args]))
    schema.mutation_inputs[name] = input_name
    fld.args = [Arg("input", f"{input_name}!")]
    payload = [
        Field(name_of(r), type_of(r.get("type", "")), notes=facts(r.get("description", "")))
        for r in rows_of(subs.get("fields", []))
    ]
    schema.add(TypeDef("object", f"{stem}Payload", payload))
    fld.type = f"{stem}Payload"
    return fld


def restore_edges(schema: Schema) -> None:
    """Edge types are collapsed in the reference too: add the standard edge for every connection without one."""
    for typedef in list(schema.types.values()):
        node = next((n[len("connection of `") : -1] for n in typedef.notes if n.startswith("connection of `")), None)
        edge = f"{typedef.name.removesuffix('Connection')}Edge"
        if node and edge not in schema.types:
            fields = [Field("cursor", "String!"), Field("node", node)]
            schema.add(TypeDef("object", edge, fields, notes=[f"edge of `{node}` (standard edge fields)"]))


def load(reference_dir: Path) -> Schema:
    schema = Schema()
    for fname, kind in FILES.items():
        for name, body in blocks((reference_dir / fname).read_text(encoding="utf-8").splitlines()):
            schema.add(parse_type(kind, name, body))
    for fname, root, mutation in (("queries.md", "Query", False), ("mutations.md", "Mutation", True)):
        typedef = TypeDef("object", root)
        schema.add(typedef)
        for name, body in blocks((reference_dir / fname).read_text(encoding="utf-8").splitlines()):
            typedef.fields.append(parse_root_field(name.split(".", 1)[-1], body, schema, mutation))
    restore_edges(schema)
    return schema
