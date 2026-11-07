"""GitHub REST reference: one Markdown file per OpenAPI `x-github.category`, plus an index of every operation."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from common import Slugger, banner, code, file_slug, literal, table, write

METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
MAX_DEPTH = 8
MEDIA_TYPE = re.compile(r"application/vnd\.github[\w.+-]*")
CONSTRAINT_KEYS = (
    ("minimum", "min"),
    ("maximum", "max"),
    ("exclusiveMinimum", "exclusive min"),
    ("exclusiveMaximum", "exclusive max"),
    ("minLength", "min length"),
    ("maxLength", "max length"),
    ("minItems", "min items"),
    ("maxItems", "max items"),
    ("minProperties", "min properties"),
    ("maxProperties", "max properties"),
    ("pattern", "pattern"),
)


@dataclass
class Row:
    name: str
    type: str
    required: bool
    default: str
    constraints: str


class Spec:
    def __init__(self, path: Path) -> None:
        self.doc = json.loads(path.read_text(encoding="utf-8"))

    # ---- $ref handling -------------------------------------------------------------------------------------------
    def lookup(self, ref: str) -> object:
        node: object = self.doc
        for part in ref.lstrip("#/").split("/"):
            node = node[part.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
        return node

    def res(self, node: object) -> dict:
        return self.named(node)[0]

    def named(self, node: object) -> tuple[dict, str | None]:
        """Resolve a $ref chain; return the schema and the component name it came from (if any)."""
        name = None
        while isinstance(node, dict) and "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            node = self.lookup(node["$ref"])
        return (node if isinstance(node, dict) else {}), name

    def merged(self, schema: dict) -> dict:
        """Fold allOf members into one schema (properties and required lists are unioned)."""
        if "allOf" not in schema:
            return schema
        out = {k: v for k, v in schema.items() if k != "allOf"}
        props = dict(out.get("properties", {}))
        req = list(out.get("required", []))
        for part in schema["allOf"]:
            sub = self.merged(self.res(part))
            props.update(sub.get("properties", {}))
            req += sub.get("required", [])
            for key, value in sub.items():
                if key not in ("properties", "required"):
                    out.setdefault(key, value)
        if props:
            out["properties"] = props
        if req:
            out["required"] = req
        return out

    # ---- type strings --------------------------------------------------------------------------------------------
    def type_of(self, node: object, depth: int = 0, show_names: bool = False) -> str:
        schema, name = self.named(node)
        schema = self.merged(schema)
        if depth > MAX_DEPTH:
            return "…"
        if show_names and name and (schema.get("type") == "object" or "properties" in schema):
            text = code(name)
        elif show_names and name and schema.get("type") == "array":
            text = f"{code(name)} (array of {self.type_of(schema.get('items', {}), depth + 1, show_names)})"
        else:
            text = self._bare_type(schema, depth, show_names)
        if schema.get("format"):
            text += f" ({schema['format']})"
        if schema.get("nullable") and "null" not in text:
            text += " | null"
        return text

    def _bare_type(self, schema: dict, depth: int, show_names: bool) -> str:
        for key in ("oneOf", "anyOf"):
            if key in schema and "properties" not in schema:
                parts: list[str] = []
                for variant in schema[key]:
                    label = self.type_of(variant, depth + 1, show_names)
                    if label not in parts:
                        parts.append(label)
                return " | ".join(parts)
        kind = schema.get("type")
        if isinstance(kind, list):
            return " | ".join(kind)
        if kind == "array":
            inner = self.type_of(schema.get("items", {}), depth + 1, show_names)
            return f"array of ({inner})" if " | " in inner else f"array of {inner}"
        if kind is None:
            return "object" if "properties" in schema or "additionalProperties" in schema else "any"
        return str(kind)

    @staticmethod
    def allowed_values(schema: dict) -> list[str]:
        parts = []
        if "enum" in schema:
            parts.append("one of: " + ", ".join(literal(v) for v in schema["enum"]))
        if "const" in schema:
            parts.append("const " + literal(schema["const"]))
        items = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        if items and "enum" in items:
            parts.append("items one of: " + ", ".join(literal(v) for v in items["enum"]))
        return parts

    @staticmethod
    def constraints(schema: dict) -> str:
        parts = Spec.allowed_values(schema)
        for key, label in CONSTRAINT_KEYS:
            if key in schema:
                parts.append(f"{label} {code(schema[key])}")
        if schema.get("uniqueItems"):
            parts.append("unique items")
        if schema.get("x-multi-segment"):
            parts.append("may contain `/` (multi-segment path)")
        if schema.get("deprecated"):
            parts.append("**deprecated**")
        if schema.get("readOnly"):
            parts.append("read-only")
        if schema.get("writeOnly"):
            parts.append("write-only")
        return "; ".join(parts)

    def scalar_constraints(self, schema: dict) -> str:
        """Constraints of a schema, including the enums of scalar oneOf/anyOf variants."""
        text = self.constraints(schema)
        extra = []
        for key in ("oneOf", "anyOf"):
            for variant in schema.get(key, []):
                sub = self.res(variant)
                if "properties" not in sub and self.constraints(sub):
                    extra.append(self.constraints(sub))
        return "; ".join([t for t in [text, *extra] if t])

    # ---- flattening of object schemas into dotted rows -----------------------------------------------------------
    def flatten(self, node: object, prefix: str, rows: list[Row], depth: int = 0, stack: tuple = ()) -> None:
        schema, name = self.named(node)
        schema = self.merged(schema)
        if depth > MAX_DEPTH or (name and name in stack):
            if prefix:
                rows.append(Row(prefix + ".…", "(recursive)", False, "", f"see {code(name or 'parent')}"))
            return
        stack = (*stack, name) if name else stack
        required = set(schema.get("required", []))
        for prop, sub_node in schema.get("properties", {}).items():
            sub = self.merged(self.res(sub_node))
            path = f"{prefix}.{prop}" if prefix else prop
            default = literal(sub["default"]) if "default" in sub else ""
            rows.append(Row(path, self.type_of(sub_node), prop in required, default, self.scalar_constraints(sub)))
            self.descend(sub, path, rows, depth, stack)
        extra = schema.get("additionalProperties")
        if isinstance(extra, dict) and extra:
            path = f"{prefix}.*" if prefix else "*"
            rows.append(Row(path, self.type_of(extra), False, "", "any key; " + self.constraints(self.res(extra))))
            self.descend(self.merged(self.res(extra)), path, rows, depth, stack)
        self.variants(schema, prefix, rows, depth, stack)

    def descend(self, sub: dict, path: str, rows: list[Row], depth: int, stack: tuple) -> None:
        if "properties" in sub or isinstance(sub.get("additionalProperties"), dict) or self.object_variants(sub):
            self.flatten(sub, path, rows, depth + 1, stack)
        items = sub.get("items")
        if sub.get("type") == "array" and isinstance(items, dict):
            item = self.merged(self.res(items))
            if "properties" in item or self.object_variants(item):
                self.flatten(items, path + "[]", rows, depth + 1, stack)

    def object_variants(self, schema: dict) -> list[tuple[str, object]]:
        out = []
        for key in ("oneOf", "anyOf"):
            for i, variant in enumerate(schema.get(key, []), 1):
                sub, name = self.named(variant)
                sub = self.merged(sub)
                if "properties" in sub:
                    out.append((self.variant_label(sub, name, i), variant))
        return out

    @staticmethod
    def variant_label(schema: dict, name: str | None, index: int) -> str:
        if name:
            return name
        for prop in schema.get("properties", {}).values():
            if isinstance(prop, dict) and len(prop.get("enum", [])) == 1:
                return str(prop["enum"][0])
        return str(schema.get("title") or f"variant {index}")

    def variants(self, schema: dict, prefix: str, rows: list[Row], depth: int, stack: tuple) -> None:
        for label, variant in self.object_variants(schema):
            self.flatten(variant, f"{prefix}{{{label}}}", rows, depth + 1, stack)
        for key in ("oneOf", "anyOf"):
            sets = [self.res(v).get("required") for v in schema.get(key, []) if "properties" not in self.res(v)]
            sets = [s for s in sets if s]
            if sets:
                word = "exactly one" if key == "oneOf" else "at least one"
                alts = " / ".join("{" + ", ".join(s) + "}" for s in sets)
                rows.append(Row(f"{prefix or '(body)'}", "constraint", False, "", f"{word} of: {alts}"))


# ---- per-operation rendering -----------------------------------------------------------------------------------------
def param_rows(spec: Spec, op: dict, path_item: dict) -> list[list[str]]:
    seen: dict[tuple[str, str], dict] = {}
    for raw in [*path_item.get("parameters", []), *op.get("parameters", [])]:
        param = spec.res(raw)
        seen[(param["in"], param["name"])] = param
    rows = []
    order = {"path": 0, "query": 1, "header": 2, "cookie": 3}
    for (loc, name), param in sorted(seen.items(), key=lambda kv: order.get(kv[0][0], 9)):
        schema = spec.merged(spec.res(param.get("schema", {})))
        if param.get("x-multi-segment"):
            schema = {**schema, "x-multi-segment": True}
        default = literal(schema["default"]) if "default" in schema else ""
        flags = spec.scalar_constraints(schema)
        if param.get("deprecated"):
            flags = "; ".join(filter(None, [flags, "**deprecated**"]))
        style = ""
        if param.get("style") or "explode" in param:
            style = f"style {param.get('style', 'form')}, explode {str(param.get('explode', True)).lower()}"
        required = "yes" if param.get("required") or loc == "path" else ""
        rows.append(
            [
                code(name),
                loc,
                spec.type_of(param.get("schema", {})),
                required,
                default,
                "; ".join(filter(None, [flags, style])),
            ]
        )
    return rows


def paging(spec: Spec, op: dict, names: set[str]) -> str:
    kinds = []
    if "page" in names:
        kinds.append("page-based (`page`, `per_page`)")
    elif "per_page" in names:
        kinds.append("`per_page`")
    cursors = sorted(names & {"before", "after", "cursor"})
    if cursors:
        kinds.append("cursor-based (" + ", ".join(code(c) for c in cursors) + ")")
    if not kinds:
        return ""
    where = ""
    ok = spec.res(op.get("responses", {}).get("200", {}))
    schema = spec.merged(spec.res(ok.get("content", {}).get("application/json", {}).get("schema", {})))
    if schema.get("type") == "array":
        where = "items: the response body is the array"
    elif "properties" in schema:
        arrays = [k for k, v in schema["properties"].items() if spec.merged(spec.res(v)).get("type") == "array"]
        total = " (with `total_count`)" if "total_count" in schema["properties"] else ""
        if arrays:
            where = "items in " + " or ".join(code(a) for a in arrays) + total
    link = any("link" in {h.lower() for h in spec.res(r).get("headers", {})} for r in op.get("responses", {}).values())
    return "; ".join(filter(None, [" + ".join(kinds), where, "`Link` header" if link else ""]))


def responses(spec: Spec, op: dict) -> str:
    parts = []
    for status in sorted(op.get("responses", {}), key=str):
        resp = spec.res(op["responses"][status])
        bodies = []
        for media, body in resp.get("content", {}).items():
            shape = spec.type_of(body.get("schema", {}), show_names=True) if body.get("schema") else ""
            bodies.append(f"{media}" + (f" {shape}" if shape and shape != "any" else ""))
        headers = sorted(resp.get("headers", {}))
        text = code(status)
        if bodies:
            text += ": " + "; ".join(bodies)
        if headers:
            text += " (headers: " + ", ".join(code(h) for h in headers) + ")"
        parts.append(text)
    return " · ".join(parts)


def summarize_patch(patch: object) -> list[str]:
    out: list[str] = []
    if isinstance(patch, list):  # RFC 6902 JSON Patch
        return [f"{step.get('op')} {code(short_path(step.get('path', '').strip('/').split('/')))}" for step in patch]

    def walk(node: object, path: list[str]) -> None:
        if isinstance(node, dict) and node and "$ref" not in node:
            for key, value in node.items():
                walk(value, [*path, key])
        elif node is None:
            out.append(f"removes {code(short_path(path))}")
        else:
            out.append(f"sets {code(short_path(path))}")

    walk(patch, [])
    return out


def short_path(parts: list[str]) -> str:
    text = ".".join(p.replace("~1", "/") for p in parts)
    text = text.replace("requestBody.content.application/json.schema.properties.", "body.")
    text = re.sub(r"responses\.(\d+)\.content\.application/json\.schema", r"response \1", text)
    return text.replace(".properties.", ".")


def flags(op: dict) -> list[str]:
    xg = op.get("x-github", {})
    out = []
    if op.get("deprecated"):
        dates = ", ".join(f"{k} {xg[k]}" for k in ("deprecationDate", "removalDate") if xg.get(k))
        out.append("**deprecated**" + (f" ({dates})" if dates else ""))
    if xg.get("enabledForGitHubApps") is False:
        out.append("not available to GitHub App installation tokens")
    if xg.get("triggersNotification"):
        out.append("triggers notifications (content-creation secondary rate limits)")
    for preview in xg.get("previews") or []:
        out.append(f"preview {code(preview.get('name'))}" + (" required" if preview.get("required") else ""))
    if xg.get("requestBodyParameterName"):
        out.append(f"the body may be a bare JSON array (documented as {code(xg['requestBodyParameterName'])})")
    return out


def body_section(spec: Spec, op: dict) -> list[str]:
    body = spec.res(op.get("requestBody", {}))
    if not body:
        return []
    lines: list[str] = []
    need = "required" if body.get("required") else "optional"
    for media, content in body.get("content", {}).items():
        schema = spec.merged(spec.res(content.get("schema", {})))
        rows: list[Row] = []
        spec.flatten(content.get("schema", {}), "", rows)
        top = spec.type_of(content.get("schema", {}))
        lines.append(f"Request body ({code(media)}, {need}): {top}")
        if schema.get("type") == "array" or (not rows and schema):
            extra = spec.scalar_constraints(schema)
            if extra:
                lines[-1] += f" — {extra}"
        if rows:
            lines += [""] + table(
                ["Field", "Type", "Required", "Default", "Allowed values / constraints"],
                [[code(r.name), r.type, "yes" if r.required else "", r.default, r.constraints] for r in rows],
            )
        lines.append("")
    return lines


def render_op(spec: Spec, method: str, path: str, op: dict, path_item: dict, host: str) -> list[str]:
    lines = [f"### {op.get('summary') or op['operationId']}", ""]
    docs = op.get("externalDocs", {}).get("url")
    head = f"`{method.upper()} {path}` · operationId {code(op['operationId'])}"
    lines.append(head + (f" · [docs]({docs})" if docs else ""))
    lines.append("")
    servers = op.get("servers")
    names = {spec.res(p)["name"] for p in [*path_item.get("parameters", []), *op.get("parameters", [])]}
    facts = []
    if servers:
        facts.append("Host: " + ", ".join(code(s["url"]) for s in servers) + f" (not {code(host)})")
    page = paging(spec, op, names)
    if page:
        facts.append("Paging: " + page)
    facts.append("Responses: " + responses(spec, op))
    media = sorted(set(MEDIA_TYPE.findall(op.get("description", ""))))
    if media:
        facts.append("Media types named in the docs: " + ", ".join(code(m.rstrip(".")) for m in media))
    flagged = flags(op)
    if flagged:
        facts.append("Notes: " + "; ".join(flagged))
    for change in op.get("x-github-breaking-changes", []):
        facts.append(
            f"API version {code(change['version'])} ({code(change['changeset'])}): "
            + "; ".join(summarize_patch(change.get("patch")))
        )
    lines += [f"- {f}" for f in facts] + [""]
    params = param_rows(spec, op, path_item)
    if params:
        lines += table(["Parameter", "In", "Type", "Required", "Default", "Allowed values / constraints"], params)
        lines.append("")
    lines += body_section(spec, op)
    return lines


# ---- files -----------------------------------------------------------------------------------------------------------
def collect(spec: Spec) -> dict[str, list[tuple[str, str, dict, dict]]]:
    cats: dict[str, list] = defaultdict(list)
    for path, item in spec.doc["paths"].items():
        for method in METHODS:
            if method in item:
                op = item[method]
                cats[op.get("x-github", {}).get("category") or (op.get("tags") or ["misc"])[0]].append(
                    (method, path, op, item)
                )
    order = {m: i for i, m in enumerate(METHODS)}
    for ops in cats.values():
        ops.sort(key=lambda t: (t[2].get("x-github", {}).get("subcategory", ""), t[1], order[t[0]]))
    return dict(sorted(cats.items()))


def build(source: Path, out: Path, pin: str) -> dict:
    spec = Spec(source)
    host = spec.doc.get("servers", [{}])[0].get("url", "https://api.github.com")
    cats = collect(spec)
    index_rows: list[list[str]] = []
    cat_rows: list[list[str]] = []
    sizes = {}
    for cat, ops in cats.items():
        fname = f"{file_slug(cat)}.md"
        slugger = Slugger()
        subs: dict[str, int] = defaultdict(int)
        for _, _, op, _ in ops:
            subs[op.get("x-github", {}).get("subcategory", "(none)")] += 1
        lines = [banner(f"api.github.com.json ({pin})"), "", f"# GitHub REST API — `{cat}` ({len(ops)} operations)", ""]
        slugger.slug(f"GitHub REST API — `{cat}` ({len(ops)} operations)")
        lines += [
            f"Official docs: https://docs.github.com/rest/{cat} · Index: [README](../README.md) · "
            "Mechanics (auth, paging, uploads, errors): [conventions](../conventions.md) · "
            "Notation: [reading the tables](../../README.md#reading-the-generated-tables)",
            "",
            "## Contents",
            "",
        ]
        slugger.slug("Contents")
        sub_anchor = {}
        body: list[str] = []
        current = None
        for method, path, op, item in ops:
            sub = op.get("x-github", {}).get("subcategory", "(none)")
            if sub != current:
                current = sub
                sub_anchor[sub] = slugger.slug(sub)
                body += [f"## {sub}", ""]
            body += render_op(spec, method, path, op, item, host)
            anchor = slugger.slug(op.get("summary") or op["operationId"])
            index_rows.append([method.upper(), code(path), code(op["operationId"]), f"[{cat}](rest/{fname}#{anchor})"])
        lines += [f"- [{s}](#{sub_anchor[s]}) ({n})" for s, n in subs.items()] + [""] + body
        sizes[fname] = write(out / "rest" / fname, lines)
        cat_rows.append([f"[{cat}](rest/{fname})", str(len(ops)), ", ".join(subs)])
    index_rows.sort(key=lambda r: (r[1], r[0]))
    write(
        out / "operations-index.md",
        [
            banner(f"api.github.com.json ({pin})"),
            "",
            f"# GitHub REST API — every operation ({len(index_rows)})",
            "",
            "Sorted by path. Back to the [README](README.md).",
            "",
            *table(["Method", "Path", "Operation ID", "Reference"], index_rows),
        ],
    )
    return {
        "categories": cat_rows,
        "operations": len(index_rows),
        "paths": len(spec.doc["paths"]),
        "sizes": sizes,
        "version": spec.doc["info"].get("version"),
        "openapi": spec.doc.get("openapi"),
        "schemas": len(spec.doc.get("components", {}).get("schemas", {})),
        "webhooks": len(spec.doc.get("x-webhooks", {})),
    }
