"""Parse GitHub's public GraphQL SDL (schema.docs.graphql) into the shared schema model."""

from __future__ import annotations

import json
import re
from pathlib import Path

from graphql_model import Arg, Directive, Field, Schema, TypeDef

TOKEN = re.compile(
    r'(?P<block>"""(?:\\"""|[^"]|"(?!""))*""")'
    r'|(?P<string>"(?:\\.|[^"\\])*")'
    r"|(?P<comment>#[^\n]*)"
    r"|(?P<spread>\.\.\.)"
    r"|(?P<punct>[!$():=@\[\]{}|&])"
    r"|(?P<number>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|(?P<name>[_A-Za-z][_0-9A-Za-z]*)"
    r"|(?P<space>[\s,\ufeff]+)"
)
REMOVAL = re.compile(r"Removal on (\d{4}-\d{2}-\d{2})")
BACKTICK = re.compile(r"`([^`]+)`")


class Parser:
    def __init__(self, text: str) -> None:
        self.tokens: list[tuple[str, str]] = []
        pos = 0
        while pos < len(text):
            match = TOKEN.match(text, pos)
            if not match:
                raise ValueError(f"unexpected character at offset {pos}: {text[pos : pos + 20]!r}")
            pos = match.end()
            kind = match.lastgroup or ""
            if kind not in ("space", "comment"):
                self.tokens.append((kind, match.group(0)))
        self.i = 0

    # ---- token helpers -------------------------------------------------------------------------------------------
    def peek(self, offset: int = 0) -> tuple[str, str]:
        j = self.i + offset
        return self.tokens[j] if j < len(self.tokens) else ("eof", "")

    def take(self, value: str | None = None) -> str:
        kind, text = self.peek()
        if value is not None and text != value:
            raise ValueError(f"expected {value!r}, got {text!r} (token {self.i})")
        self.i += 1
        return text

    def accept(self, value: str) -> bool:
        if self.peek()[1] == value:
            self.i += 1
            return True
        return False

    def description(self) -> None:
        if self.peek()[0] in ("block", "string"):
            self.i += 1

    # ---- grammar -------------------------------------------------------------------------------------------------
    def type_ref(self) -> str:
        if self.accept("["):
            inner = self.type_ref()
            self.take("]")
            text = f"[{inner}]"
        else:
            text = self.take()
        if self.accept("!"):
            text += "!"
        return text

    def value(self) -> str:
        kind, text = self.peek()
        if text == "[":
            self.take("[")
            items = []
            while not self.accept("]"):
                items.append(self.value())
            return "[" + ", ".join(items) + "]"
        if text == "{":
            self.take("{")
            pairs = []
            while not self.accept("}"):
                key = self.take()
                self.take(":")
                pairs.append(f"{key}: {self.value()}")
            return "{" + ", ".join(pairs) + "}"
        if text == "$":
            self.take("$")
            return "$" + self.take()
        self.i += 1
        if kind == "block":
            return json.dumps(text[3:-3].strip())
        return text

    def directives(self) -> dict[str, dict[str, str]]:
        found: dict[str, dict[str, str]] = {}
        while self.peek()[1] == "@":
            self.take("@")
            name = self.take()
            args: dict[str, str] = {}
            if self.accept("("):
                while not self.accept(")"):
                    key = self.take()
                    self.take(":")
                    args[key] = self.value()
            found[name] = args
        return found

    def input_values(self, close: str) -> list[Arg]:
        args = []
        while not self.accept(close):
            self.description()
            name = self.take()
            self.take(":")
            type_ref = self.type_ref()
            default = self.value() if self.accept("=") else None
            args.append(Arg(name, type_ref, default, notes_from(self.directives())))
        return args

    def fields(self) -> list[Field]:
        out = []
        self.take("{")
        while not self.accept("}"):
            self.description()
            name = self.take()
            args = self.input_values(")") if self.accept("(") else []
            self.take(":")
            type_ref = self.type_ref()
            out.append(Field(name, type_ref, args, notes_from(self.directives())))
        return out

    def implements(self) -> list[str]:
        names: list[str] = []
        if self.accept("implements"):
            self.accept("&")
            names.append(self.take())
            while self.accept("&"):
                names.append(self.take())
        return names

    def definition(self, schema: Schema) -> None:
        self.description()
        keyword = self.take()
        if keyword == "extend":
            keyword = self.take()
        if keyword == "schema":
            self.directives()
            self.take("{")
            while not self.accept("}"):
                op = self.take()
                self.take(":")
                setattr(schema, op if op != "subscription" else "subscription", self.take())
            return
        if keyword == "directive":
            self.take("@")
            name = self.take()
            args = self.input_values(")") if self.accept("(") else []
            self.accept("repeatable")
            self.take("on")
            self.accept("|")
            locations = [self.take()]
            while self.accept("|"):
                locations.append(self.take())
            schema.directives.append(Directive(name, args, locations))
            return
        name = self.take()
        handler = {
            "type": self.object_like,
            "interface": self.object_like,
            "input": self.input_def,
            "enum": self.enum_def,
            "union": self.union_def,
            "scalar": self.scalar_def,
        }[keyword]
        schema.add(handler(keyword, name))

    def object_like(self, keyword: str, name: str) -> TypeDef:
        interfaces = self.implements()
        notes = notes_from(self.directives())
        fields = self.fields() if self.peek()[1] == "{" else []
        return TypeDef("object" if keyword == "type" else "interface", name, fields, interfaces, notes=notes)

    def input_def(self, keyword: str, name: str) -> TypeDef:
        notes = notes_from(self.directives())
        self.take("{")
        fields = [Field(a.name, a.type, notes=a.notes, default=a.default) for a in self.input_values("}")]
        return TypeDef("input", name, fields, notes=notes)

    def enum_def(self, keyword: str, name: str) -> TypeDef:
        notes = notes_from(self.directives())
        values = []
        self.take("{")
        while not self.accept("}"):
            self.description()
            value = self.take()
            values.append(Field(value, "", notes=notes_from(self.directives())))
        return TypeDef("enum", name, values, notes=notes)

    def union_def(self, keyword: str, name: str) -> TypeDef:
        notes = notes_from(self.directives())
        members = []
        if self.accept("="):
            self.accept("|")
            members.append(self.take())
            while self.accept("|"):
                members.append(self.take())
        return TypeDef("union", name, members=members, notes=notes)

    def scalar_def(self, keyword: str, name: str) -> TypeDef:
        return TypeDef("scalar", name, notes=notes_from(self.directives()))

    def parse(self) -> Schema:
        schema = Schema()
        while self.peek()[0] != "eof":
            self.definition(schema)
        return schema


def notes_from(directives: dict[str, dict[str, str]]) -> list[str]:
    notes = []
    if "deprecated" in directives:
        reason = unquote(directives["deprecated"].get("reason", ""))
        extra = []
        date = REMOVAL.search(reason)
        if date:
            extra.append(f"removal {date.group(1)}")
        names = [n for n in BACKTICK.findall(reason) if re.fullmatch(r"[\w.]+", n)]
        if names:
            extra.append("see " + ", ".join(f"`{n}`" for n in dict.fromkeys(names)))
        notes.append("**deprecated**" + (f" ({'; '.join(extra)})" if extra else ""))
    if "preview" in directives:
        notes.append(f"preview `{unquote(directives['preview'].get('toggledBy', ''))}`")
    if "possibleTypes" in directives:
        concrete = directives["possibleTypes"].get("concreteTypes", "")
        abstract = unquote(directives["possibleTypes"].get("abstractType", ""))
        kinds = re.findall(r'"([^"]+)"', concrete)
        label = ", ".join(kinds) if kinds else abstract
        if label:
            notes.append(f"ID of: {label}" + (f" (any `{abstract}`)" if abstract and kinds else ""))
    if "docsCategory" in directives:
        notes.append(f"category `{unquote(directives['docsCategory'].get('name', ''))}`")
    for name, args in directives.items():
        if name not in ("deprecated", "preview", "possibleTypes", "docsCategory"):
            notes.append(f"@{name}" + (f"({', '.join(f'{k}: {v}' for k, v in args.items())})" if args else ""))
    return notes


def unquote(text: str) -> str:
    try:
        return json.loads(text) if text.startswith('"') else text
    except json.JSONDecodeError:
        return text.strip('"')


def load(path: Path) -> Schema:
    schema = Parser(path.read_text(encoding="utf-8")).parse()
    mutation = schema.types.get(schema.mutation)
    for fld in mutation.fields if mutation else []:
        for arg in fld.args:
            if arg.name == "input":
                schema.mutation_inputs[fld.name] = arg.type.rstrip("!")
    return schema
