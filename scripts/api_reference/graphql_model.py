"""A GraphQL schema model shared by both parsers, and the Markdown renderer for it."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from common import Slugger, banner, code, table, write

BUILT_IN_SCALARS = ("Boolean", "Float", "ID", "Int", "String")
KIND_FILES = {
    "object": "objects",
    "interface": "interfaces",
    "union": "unions",
    "enum": "enums",
    "input": "input-objects",
    "scalar": "scalars",
}
KIND_TITLES = {
    "object": "Objects",
    "interface": "Interfaces",
    "union": "Unions",
    "enum": "Enums",
    "input": "Input objects",
    "scalar": "Scalars",
}
SPLIT_BYTES = 450_000


@dataclass
class Arg:
    name: str
    type: str
    default: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class Field:
    name: str
    type: str
    args: list[Arg] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    default: str | None = None  # input fields only


@dataclass
class TypeDef:
    kind: str
    name: str
    fields: list[Field] = field(default_factory=list)  # object/interface fields, input fields, enum values
    interfaces: list[str] = field(default_factory=list)
    members: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class Directive:
    name: str
    args: list[Arg]
    locations: list[str]


@dataclass
class Schema:
    types: dict[str, TypeDef] = field(default_factory=dict)
    query: str = "Query"
    mutation: str = "Mutation"
    subscription: str | None = None
    directives: list[Directive] = field(default_factory=list)
    mutation_inputs: dict[str, str] = field(default_factory=dict)  # mutation name -> its input type name

    def add(self, typedef: TypeDef) -> None:
        self.types[typedef.name] = typedef


def chunked(items: list, weights: list[int]) -> list[list]:
    """Split items into the fewest runs that keep each under SPLIT_BYTES, with the runs about equally large."""
    total = sum(weights)
    target = total / max(1, -(-total // SPLIT_BYTES))
    chunks: list[list] = [[]]
    size = 0
    for item, weight in zip(items, weights):
        if chunks[-1] and size + weight > target * 1.02:
            chunks.append([])
            size = 0
        chunks[-1].append(item)
        size += weight
    return chunks


def base_type(type_ref: str) -> str:
    return re.sub(r"[\[\]!]", "", type_ref)


class Renderer:
    def __init__(self, schema: Schema, out: Path, title: str, source: str) -> None:
        self.schema = schema
        self.out = out
        self.title = title
        self.source = source
        self.inlined = self.mutation_owned_types()
        self.home: dict[str, str] = {}  # type name -> "file.md#anchor"
        self.root_pages: dict[str, list[tuple[str, int, str]]] = {}  # "queries"/"mutations" -> (file, count, span)

    # ---- which types appear where -------------------------------------------------------------------------------
    def mutation_owned_types(self) -> set[str]:
        """Input and payload types used by exactly one mutation are documented with that mutation only."""
        mutation = self.schema.types.get(self.schema.mutation)
        if not mutation:
            return set()
        uses: dict[str, int] = {}
        for typedef in self.schema.types.values():
            for fld in typedef.fields:
                for name in [base_type(fld.type), *(base_type(a.type) for a in fld.args)]:
                    uses[name] = uses.get(name, 0) + 1
        owned = set()
        for fld in mutation.fields:
            payload = base_type(fld.type)
            if uses.get(payload) == 1 and payload in self.schema.types:
                owned.add(payload)
            input_name = self.schema.mutation_inputs.get(fld.name)
            if input_name and uses.get(input_name, 0) <= 1 and input_name in self.schema.types:
                owned.add(input_name)
        return owned

    def listed(self, kind: str) -> list[TypeDef]:
        roots = {self.schema.query, self.schema.mutation, self.schema.subscription}
        return sorted(
            (
                t
                for t in self.schema.types.values()
                if t.kind == kind and t.name not in roots and t.name not in self.inlined
            ),
            key=lambda t: t.name.lower(),
        )

    # ---- links -------------------------------------------------------------------------------------------------
    def link(self, type_ref: str, here: str) -> str:
        name = base_type(type_ref)
        target = self.home.get(name)
        if not target:
            return code(type_ref)
        page, anchor = target.split("#", 1)
        return f"[{code(type_ref)}]({'' if page == here else page}#{anchor})"

    @staticmethod
    def args_inline(args: list[Arg]) -> str:
        parts = []
        for arg in args:
            text = f"{arg.name}: {arg.type}"
            if arg.default is not None:
                text += f" = {arg.default}"
            if arg.notes:
                text += " (" + "; ".join(arg.notes) + ")"
            parts.append(text)
        return ", ".join(code(p) for p in parts)

    # ---- sections ------------------------------------------------------------------------------------------------
    def type_section(self, typedef: TypeDef, here: str, level: str = "##") -> list[str]:
        lines = [f"{level} `{typedef.name}`", ""]
        facts = []
        if typedef.interfaces:
            facts.append("Implements: " + ", ".join(self.link(i, here) for i in typedef.interfaces))
        if typedef.kind == "interface":
            impl = sorted(t.name for t in self.schema.types.values() if typedef.name in t.interfaces)
            if impl:
                facts.append("Implemented by: " + ", ".join(self.link(i, here) for i in impl))
        if typedef.members:
            facts.append("Members: " + ", ".join(self.link(m, here) for m in typedef.members))
        if typedef.notes:
            facts.append("Notes: " + "; ".join(typedef.notes))
        lines += [f"- {f}" for f in facts] + ([""] if facts else [])
        lines += self.fields_table(typedef, here)
        return lines

    def fields_table(self, typedef: TypeDef, here: str) -> list[str]:
        if not typedef.fields:
            return []
        if typedef.kind == "enum":
            if any(f.notes for f in typedef.fields):
                return [*table(["Value", "Notes"], [[code(f.name), "; ".join(f.notes)] for f in typedef.fields]), ""]
            return ["Values: " + ", ".join(code(f.name) for f in typedef.fields), ""]
        if typedef.kind == "input":
            rows = [
                [code(f.name), self.link(f.type, here), f.default or "", "; ".join(f.notes)] for f in typedef.fields
            ]
            return [*table(["Field", "Type", "Default", "Notes"], rows), ""]
        rows = [
            [code(f.name), self.link(f.type, here), self.args_inline(f.args), "; ".join(f.notes)]
            for f in typedef.fields
        ]
        return [*table(["Field", "Type", "Arguments", "Notes"], rows), ""]

    def root_section(self, fld: Field, here: str, mutation: bool) -> list[str]:
        lines = [f"## `{fld.name}`", ""]
        sig = f"{fld.name}" + (f"({', '.join(a.name + ': ' + a.type for a in fld.args)})" if fld.args else "")
        lines.append(f"{code(sig)} → {self.link(fld.type, here)}")
        lines.append("")
        if fld.notes:
            lines += ["- Notes: " + "; ".join(fld.notes), ""]
        input_name = self.schema.mutation_inputs.get(fld.name) if mutation else None
        input_type = self.schema.types.get(input_name or "")
        if input_type and input_name in self.inlined:
            rows = [
                [code(f.name), self.link(f.type, here), f.default or "", "; ".join(f.notes)] for f in input_type.fields
            ]
            lines += [f"Input `{input_name}`:", "", *table(["Input field", "Type", "Default", "Notes"], rows), ""]
        elif fld.args:
            rows = [[code(a.name), self.link(a.type, here), a.default or "", "; ".join(a.notes)] for a in fld.args]
            lines += [*table(["Argument", "Type", "Default", "Notes"], rows), ""]
        payload = self.schema.types.get(base_type(fld.type))
        if mutation and payload and payload.name in self.inlined:
            rows = [[code(f.name), self.link(f.type, here), "; ".join(f.notes)] for f in payload.fields]
            lines += [f"Payload `{payload.name}`:", "", *table(["Payload field", "Type", "Notes"], rows), ""]
        return lines

    # ---- files ---------------------------------------------------------------------------------------------------
    def head(self, heading: str, slugger: Slugger) -> list[str]:
        slugger.slug(heading)
        return [
            banner(self.source),
            "",
            f"# {heading}",
            "",
            "Index: [README](README.md) · Mechanics (endpoint, auth, paging, limits): [conventions](conventions.md) · "
            "Notation: [reading the tables](../../README.md#reading-the-generated-tables)",
            "",
        ]

    def plan_files(self) -> dict[str, list[TypeDef]]:
        """Assign every listed type to a file; split a kind alphabetically when its file would be too large."""
        files: dict[str, list[TypeDef]] = {}
        provisional = {
            t.name: f"{KIND_FILES[t.kind]}-x-y.md#{t.name.lower()}"
            for t in self.schema.types.values()
            if t.kind in KIND_FILES
        }
        self.home = {**provisional, **dict.fromkeys(BUILT_IN_SCALARS, "scalars.md#built-in-scalars")}
        for kind, stem in KIND_FILES.items():
            types = self.listed(kind)
            if kind == "scalar":
                files[f"{stem}.md"] = types
                continue
            est = [len("\n".join(self.type_section(t, "")).encode("utf-8")) + 1 for t in types]
            chunks = chunked(types, est)
            if len(chunks) == 1:
                files[f"{stem}.md"] = chunks[0]
            else:
                for chunk in chunks:
                    first, last = chunk[0].name[0].lower(), chunk[-1].name[0].lower()
                    name = f"{stem}-{first}.md" if first == last else f"{stem}-{first}-{last}.md"
                    if name in files:
                        name = f"{stem}-{chunk[0].name[:3].lower()}-{chunk[-1].name[:3].lower()}.md"
                    files[name] = chunk
        return files

    def render(self) -> dict:
        files = self.plan_files()
        self.home = {}
        for page, types in files.items():
            for typedef in types:
                self.home[typedef.name] = f"{page}#{Slugger().slug(typedef.name)}"
        for builtin in BUILT_IN_SCALARS:
            self.home.setdefault(builtin, "scalars.md#built-in-scalars")
        sizes = {}
        for page, types in files.items():
            sizes[page] = self.render_types(page, types)
        sizes["queries.md"] = self.render_root(self.schema.query, "queries.md", "Queries", mutation=False)
        sizes["mutations.md"] = self.render_root(self.schema.mutation, "mutations.md", "Mutations", mutation=True)
        if self.schema.subscription and self.schema.subscription in self.schema.types:
            sizes["subscriptions.md"] = self.render_root(
                self.schema.subscription, "subscriptions.md", "Subscriptions", mutation=False
            )
        sizes["directives.md"] = self.render_directives()
        counts = {k: len(self.listed(k)) for k in KIND_FILES}
        counts["query fields"] = len(self.schema.types.get(self.schema.query, TypeDef("object", "")).fields)
        counts["mutations"] = len(self.schema.types.get(self.schema.mutation, TypeDef("object", "")).fields)
        counts["documented with their mutation"] = len(self.inlined)
        counts["directives"] = len(self.schema.directives)
        return {"files": files, "sizes": sizes, "counts": counts}

    def render_types(self, page: str, types: list[TypeDef]) -> int:
        kind = types[0].kind if types else "scalar"
        slugger = Slugger()
        span = f" ({types[0].name} … {types[-1].name})" if types and page[:-3] != KIND_FILES[kind] else ""
        lines = self.head(f"{self.title} — {KIND_TITLES[kind]}{span}", slugger)
        if kind == "scalar":
            lines += ["## Built-in scalars", ""]
            slugger.slug("Built-in scalars")
            lines += [", ".join(code(s) for s in BUILT_IN_SCALARS) + " (GraphQL specification).", ""]
        for typedef in types:
            slugger.slug(typedef.name)
            lines += self.type_section(typedef, page)
        return write(self.out / page, lines)

    def render_root(self, root: str, page: str, label: str, mutation: bool) -> int:
        """Write the root fields (queries or mutations), split alphabetically into several files when large."""
        typedef = self.schema.types.get(root)
        fields = sorted(typedef.fields, key=lambda f: f.name.lower()) if typedef else []
        stem = page[:-3]
        sections = [(fld, self.root_section(fld, page, mutation)) for fld in fields]
        weights = [len("\n".join(lines).encode("utf-8")) + len(fld.name) * 2 + 8 for fld, lines in sections]
        chunks = chunked(sections, weights)
        total = 0
        self.root_pages[stem] = []
        for chunk in chunks:
            name = page
            span = ""
            if len(chunks) > 1:
                first, last = chunk[0][0].name[0].lower(), chunk[-1][0].name[0].lower()
                name = f"{stem}-{first}-{last}.md"
                span = f", {chunk[0][0].name} … {chunk[-1][0].name}"
            self.root_pages[stem].append((name, len(chunk), span.lstrip(", ")))
            out = self.head(f"{self.title} — {label} ({len(chunk)} of {len(fields)}{span})", Slugger())
            out += ["## Contents", "", ", ".join(f"[{f.name}](#{f.name.lower()})" for f, _ in chunk), ""]
            for _, lines in chunk:
                out += lines
            total += write(self.out / name, out)
        return total

    def render_directives(self) -> int:
        lines = self.head(f"{self.title} — Directives ({len(self.schema.directives)})", Slugger())
        rows = [[code("@" + d.name), self.args_inline(d.args), ", ".join(d.locations)] for d in self.schema.directives]
        return write(self.out / "directives.md", [*lines, *table(["Directive", "Arguments", "Locations"], rows)])
