"""GitLab REST (v4) reference from the docs pages in gitlab-org/gitlab `doc/api`, cross-checked with `openapi_v2.yaml`.

The docs pages are the complete reference (the OpenAPI file covers only part of the API). Each page section that
names an endpoint in a code block (``GET /projects/:id/issues``) becomes one entry; the section's attribute
tables are its parameters. Prose is not copied: from each description cell only facts are extracted (default,
tier, deprecation, mutual exclusions, literal values named in backticks). OpenAPI operations that no docs page
names are added from the OpenAPI file, so the reference is the union of both sources.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from common import Slugger, banner, cell, code, file_slug, table, write

METHOD_LINE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD)\s+(\S+)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
EXPLICIT_ANCHOR = re.compile(r"\s*\{#([\w-]+)\}\s*$")
ATTR_BRACES = re.compile(r"\s*\{[.#][^}]*\}\s*$")
DEFAULT = re.compile(r"\b[Dd]efaults?(?: value)?(?: is| to|:)?\s+`([^`]+)`")
TIER = re.compile(r"\b(Premium and Ultimate|Ultimate|Premium|GitLab\.com|Self-Managed|Dedicated)\s+only\b")
DEPRECATED = re.compile(r"^\W*\[?[Dd]eprecated\b|\b(?:is|was|been|are) deprecated\b|\b[Dd]eprecated in GitLab \d")
DEPRECATED_IN = re.compile(r"[Dd]eprecated in GitLab (\d+\.\d+)")
SUB_TABLE = re.compile(r"^(\S+\[\])\s+attribute$")
NOT_VALUES = {"true", "false", "id", "iid", "ids", "username", "name", "path", "emoji", "null"}
INTRODUCED = re.compile(r"\b[Ii]ntroduced in GitLab (\d+\.\d+)")
EXCLUSIVE = re.compile(r"[Mm]utually exclusive with ((?:`[^`]+`(?:,\s*|\s+(?:and|or)\s+|,\s*(?:and|or)\s+)?)+)")
BACKTICKED = re.compile(r"`([^`\n]{1,60})`")
LITERAL = re.compile(r"^[\w.:+@/-]+$")
PLACEHOLDER = re.compile(r":(\w+)|<(\w+)>|\{(\w+)\}|\*(\w+)")
SKIP_DIRS = ("graphql/", "openapi/")
ROUTE_PREFIX = re.compile(r"^/[\w:./-]+$")
METHOD_ORDER = {m: i for i, m in enumerate(("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"))}


@dataclass
class Param:
    name: str
    type: str
    required: str
    location: str = ""
    default: str = ""
    values: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class Entry:
    title: str
    page: str  # doc/api-relative path, e.g. "issues.md"
    anchor: str
    endpoints: list[tuple[str, str]]
    params: list[Param] = field(default_factory=list)
    headers: list[Param] = field(default_factory=list)
    response: list[tuple[str, str]] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    openapi: bool = False  # True when the entry comes only from the OpenAPI file


@dataclass
class Page:
    path: str
    title: str
    stage: str
    group: str
    details: list[str]
    entries: list[Entry]
    prefixes: list[str] = field(default_factory=list)  # what `<route-prefix>` stands for on this page


@dataclass
class Section:
    level: int
    title: str
    anchor: str
    endpoints: list[tuple[str, str]] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


# ---- Markdown page parsing -------------------------------------------------------------------------------------------
def front_matter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            meta = yaml.safe_load(text[3:end]) or {}
            return (meta if isinstance(meta, dict) else {}), text[end + 4 :]
    return {}, text


def hugo_anchor(title: str, slugger: Slugger) -> str:
    explicit = EXPLICIT_ANCHOR.search(title)
    if explicit:
        return explicit.group(1)
    return slugger.slug(ATTR_BRACES.sub("", title))


def split_row(line: str) -> list[str]:
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") and not body.endswith("\\|") else body
    cells, buf, in_code = [], "", False
    for ch_i, ch in enumerate(body):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code and (ch_i == 0 or body[ch_i - 1] != "\\"):
            cells.append(buf.strip())
            buf = ""
            continue
        buf += ch
    cells.append(buf.strip())
    return cells


def endpoint_lines(lines: list[str]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for line in lines:
        match = METHOD_LINE.match(line.strip())
        if not match:
            continue
        raw = match.group(2).split("?", 1)[0].split("#", 1)[0]
        path = re.sub(r"^https?://[^/]+", "", raw)
        if path != raw and not re.match(r"^/api/v4(?=/)", path):  # an instance-root endpoint such as /oauth/...
            if (match.group(1), "https://HOST" + path) not in found:
                found.append((match.group(1), "https://HOST" + path))
            continue
        path = re.sub(r"^/?api/v4(?=/)", "", path)
        if re.match(r"^[\w:<]", path):  # package pages write `GET projects/:id/...` and `GET <route-prefix>/...`
            path = "/" + path
        if path.startswith("/") and (match.group(1), path) not in found:
            found.append((match.group(1), path))
    templates = [p for p in found if PLACEHOLDER.search(p[1])]
    patterns = [
        (m, re.compile("^" + PLACEHOLDER.sub("[^/]+", re.escape(p).replace("\\:", ":")) + "$")) for m, p in templates
    ]
    concrete = [(m, p) for m, p in found if not PLACEHOLDER.search(p)]
    drop = {(m, p) for m, p in concrete for tm, pat in patterns if tm == m and pat.match(p)}
    return [e for e in found if e not in drop]


class Scanner:
    """Walk one docs page line by line, collecting headings, fenced endpoint lists, tables and details blocks."""

    def __init__(self, title: str) -> None:
        self.slugger = Slugger()
        self.sections = [Section(1, title, "")]
        self.fence: list[str] | None = None
        self.fence_lang = ""
        self.prefixes: list[str] = []
        self.in_details = False
        self.table: list[list[str]] = []

    def flush_table(self) -> None:
        if self.table:
            self.sections[-1].tables.append(list(self.table))
            self.table.clear()

    def close_fence(self) -> None:
        fence = self.fence or []
        if self.fence_lang in ("", "plaintext", "http", "text"):
            current = self.sections[-1].endpoints
            current += [e for e in endpoint_lines(fence) if e not in current]
            bare = [ln.strip() for ln in fence if ROUTE_PREFIX.match(ln.strip())]
            self.prefixes += [b for b in bare if b not in self.prefixes]
        self.fence = None

    def feed(self, line: str) -> None:
        stripped = line.strip()
        if self.fence is not None:
            if stripped.startswith("```"):
                self.close_fence()
            else:
                self.fence.append(line)
            return
        if stripped.startswith("|"):
            self.table.append(split_row(stripped))
            return
        self.flush_table()
        if stripped.startswith("```"):
            self.fence, self.fence_lang = [], stripped[3:].strip().lower()
        elif "{{< details >}}" in stripped or "{{< /details >}}" in stripped:
            self.in_details = "/details" not in stripped
        elif self.in_details and stripped.startswith("- "):
            self.sections[-1].details.append(stripped[2:].strip())
        else:
            heading = HEADING.match(line)
            if heading:
                title = heading.group(2)
                level = len(heading.group(1))
                self.sections.append(Section(level, clean_title(title), hugo_anchor(title, self.slugger)))


def parse_page(root: Path, path: Path) -> Page:
    rel = path.relative_to(root).as_posix()
    meta, text = front_matter(path.read_text(encoding="utf-8"))
    scanner = Scanner(str(meta.get("title", rel)))
    for raw in text.splitlines():
        scanner.feed(raw.rstrip())
    scanner.flush_table()
    entries = sections_to_entries(rel, scanner.sections)
    stage = str(meta.get("stage") or "none")
    stage = "No stage assigned" if stage.lower() in ("none", "") else stage
    uses_prefix = any("<route-prefix>" in p for e in entries for _, p in e.endpoints)
    return Page(
        rel,
        str(meta.get("title", rel)),
        stage,
        str(meta.get("group", "")),
        scanner.sections[0].details,
        entries,
        scanner.prefixes if uses_prefix else [],
    )


def clean_title(title: str) -> str:
    return EXPLICIT_ANCHOR.sub("", ATTR_BRACES.sub("", title)).strip()


def sections_to_entries(rel: str, sections: list[Section]) -> list[Entry]:
    entries: list[Entry] = []
    owner: tuple[Section, Entry] | None = None
    for sec in sections:
        if sec.endpoints:
            entry = Entry(sec.title, rel, sec.anchor, list(sec.endpoints), details=list(sec.details))
            entries.append(entry)
            owner = (sec, entry)
            absorb(entry, sec.tables)
        elif owner and sec.level > owner[0].level:
            absorb(owner[1], sec.tables)  # a subsection (for example "Response attributes") of the endpoint
        else:
            owner = None
    return entries


# ---- tables ----------------------------------------------------------------------------------------------------------
TABLE_KEYS = ("attribute", "parameter", "name", "option", "header", "key", "field")


def absorb(entry: Entry, tables: list[list[list[str]]]) -> None:
    for rows in tables:
        if len(rows) < 3 or not re.fullmatch(r"[\s:|-]+", "|".join(rows[1])):
            continue
        head = [strip_md(h).lower() for h in rows[0]]
        body = [r for r in rows[2:] if any(c.strip() for c in r)]
        sub = SUB_TABLE.match(head[0])  # e.g. "`actions[]` Attribute": the rows are fields of actions[]
        prefix = sub.group(1) + "." if sub else ""
        if sub:
            head[0] = "attribute"
        if head[0] not in TABLE_KEYS:
            continue
        col = {h: i for i, h in enumerate(head)}
        if "required" in col:
            absorb_params(entry.headers if head[0] == "header" else entry.params, body, col, prefix)
        elif "type" in col:
            entry.response += [
                (prefix + strip_md(r[0]), strip_md(r[col["type"]])) for r in body if len(r) > col["type"]
            ]


def absorb_params(target: list[Param], body: list[list[str]], col: dict[str, int], prefix: str) -> None:
    names = {strip_md(r[0]) for r in body if r}
    for row in body:
        param = to_param(row, col, names)
        if param is None:
            continue
        param.name = prefix + param.name
        if param.name not in {p.name for p in target}:
            target.append(param)


def strip_md(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return text.replace("`", "").replace("**", "").replace("\\|", "|").strip()


def to_param(row: list[str], col: dict[str, int], names: set[str]) -> Param | None:
    def get(key: str) -> str:
        i = col.get(key)
        return row[i] if i is not None and i < len(row) else ""

    name = strip_md(row[0]) if row else ""
    if not name:
        return None
    required_raw = strip_md(get("required")).lower()
    required = "yes" if required_raw.startswith("yes") else "" if required_raw in ("no", "") else "conditional"
    desc = get("description")
    param = Param(name, strip_md(get("type")), required)
    param.default = (DEFAULT.search(desc) or [None, ""])[1] or ""
    facts = []
    tier = TIER.search(desc)
    if tier:
        facts.append(f"{tier.group(1)} only")
    if DEPRECATED.search(desc):
        version = DEPRECATED_IN.search(desc)
        facts.append("**deprecated**" + (f" in {version.group(1)}" if version else ""))
    intro = INTRODUCED.search(desc)
    if intro:
        facts.append(f"since {intro.group(1)}")
    excl = EXCLUSIVE.search(desc)
    if excl:
        facts.append("excludes " + ", ".join(code(n) for n in re.findall(r"`([^`]+)`", excl.group(1))))
    if required == "conditional":
        facts.append("conditionally required")
    param.notes = facts
    skip = names | NOT_VALUES | {name, param.default}
    values = (
        []
        if "date" in param.type.lower()
        else [
            v
            for v in dict.fromkeys(BACKTICKED.findall(desc))
            if LITERAL.match(v) and v not in skip and not v.startswith(":")
        ]
    )
    param.values = ", ".join(code(v) for v in values)
    return param


# ---- OpenAPI cross-check ---------------------------------------------------------------------------------------------
def norm(path: str) -> str:
    path = re.sub(r"^/api/v4", "", path)
    return PLACEHOLDER.sub("*", path).rstrip("/") or "/"


def variants(path: str) -> list[str]:
    """Expand Grape's optional segments: `/groups/:id/(-/)search` is both `/groups/:id/search` and `.../-/search`."""
    match = re.search(r"\(([^()]*)\)", path)
    if not match:
        return [path]
    head, tail = path[: match.start()], path[match.end() :]
    return variants(head + tail) + variants(head + match.group(1) + tail)


def load_openapi(path: Path) -> dict[tuple[str, str], dict]:
    """Every OpenAPI operation by (method, normalized path); one with optional segments has several keys."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    ops = {}
    for raw_path, item in doc.get("paths", {}).items():
        for method, op in item.items():
            if method.upper() in METHOD_ORDER and isinstance(op, dict):
                op["_path"] = re.sub(r"\{(\w+)\}", r":\1", re.sub(r"^/api/v4", "", raw_path))
                op["_definitions"] = doc.get("definitions", {})
                for variant in variants(op["_path"]):
                    ops[(method.upper(), norm(variant))] = op
    return ops


def openapi_params(op: dict) -> list[Param]:
    params = []
    for raw in op.get("parameters", []):
        if raw.get("in") == "body":
            ref = raw.get("schema", {}).get("$ref", "")
            schema = op["_definitions"].get(ref.rsplit("/", 1)[-1], raw.get("schema", {}))
            required = set(schema.get("required", []))
            for name, prop in schema.get("properties", {}).items():
                params.append(openapi_param(name, prop, "body", name in required))
            continue
        params.append(openapi_param(raw["name"], raw, raw.get("in", ""), bool(raw.get("required"))))
    return params


def openapi_param(name: str, spec: dict, location: str, required: bool) -> Param:
    kind = spec.get("type", "object" if "properties" in spec else "")
    if kind == "array":
        kind = f"array of {spec.get('items', {}).get('type', 'object')}"
    if spec.get("format"):
        kind += f" ({spec['format']})"
    values = spec.get("enum") or spec.get("items", {}).get("enum") or []
    loc = {"formData": "form", "query": "query", "path": "path", "body": "body", "header": "header"}.get(
        location, location
    )
    if spec.get("type") == "file":
        loc = "form"
    param = Param(name, kind, "yes" if required else "", loc)
    param.default = str(spec["default"]) if "default" in spec else ""
    param.values = ("one of: " + ", ".join(code(v) for v in values)) if values else ""
    if spec.get("type") == "file":
        param.notes.append("file upload (multipart/form-data)")
    return param


def enrich(entry: Entry, ops: list[dict]) -> None:
    """Add what the OpenAPI file knows (enums, defaults, file uploads, missing parameters) to a docs entry."""
    known = {p.name: p for p in entry.params}
    for op in ops:
        for extra in openapi_params(op):
            mine = known.get(extra.name) or known.get(extra.name.removesuffix("[]")) or known.get(extra.name + "[]")
            if mine is None:
                if extra.location != "path":
                    extra.notes.append("in OpenAPI only")
                    entry.params.append(extra)
                    known[extra.name] = extra
                continue
            if extra.values.startswith("one of"):
                mine.values = extra.values
            if not mine.default and extra.default:
                mine.default = extra.default
            if extra.type.startswith("file") and not any("file upload" in n for n in mine.notes):
                mine.notes.append("file upload (multipart/form-data)")


# ---- locations -------------------------------------------------------------------------------------------------------
def locate(entry: Entry) -> None:
    path_names = {g for _, p in entry.endpoints for m in PLACEHOLDER.finditer(p) for g in m.groups() if g}
    methods = {m for m, _ in entry.endpoints}
    default = (
        "query" if methods <= {"GET", "HEAD", "DELETE"} else "body" if not methods & {"GET", "HEAD"} else "query/body"
    )
    for param in entry.params:
        if param.location:
            continue
        param.location = "path" if param.name in path_names else default
        uploads = param.type.lower().startswith("file") or any("file upload" in n for n in param.notes)
        if uploads and param.location in ("body", "query/body"):
            param.location = "form"
            if not any("file upload" in n for n in param.notes):
                param.notes.append("file upload (multipart/form-data)")


# ---- rendering -------------------------------------------------------------------------------------------------------
def docs_url(page: str, anchor: str) -> str:
    stem = page[:-3]
    stem = stem[: -len("_index")].rstrip("/") if stem.endswith("_index") else stem
    return f"https://docs.gitlab.com/api/{stem}/" + (f"#{anchor}" if anchor else "")


def render_entry(entry: Entry, page_details: list[str]) -> list[str]:
    lines = [f"### {entry.title}", ""]
    lines += [", ".join(f"`{m} {p}`" for m, p in entry.endpoints)]
    link = f"[docs]({docs_url(entry.page, entry.anchor)})" if not entry.openapi else "source: `openapi_v2.yaml` only"
    lines[-1] += f" · {link}"
    lines.append("")
    facts = []
    details = [d for d in entry.details if d not in page_details]
    if details:
        facts.append("Availability: " + "; ".join(cell(strip_md(d)) for d in details))
    if entry.headers:
        facts.append(
            "Request headers: "
            + ", ".join(code(h.name) + (" (required)" if h.required == "yes" else "") for h in entry.headers)
        )
    if entry.response:
        facts.append(
            "Response attributes: " + ", ".join(f"{code(n)} ({t})" if t else code(n) for n, t in entry.response)
        )
    lines += [f"- {f}" for f in facts] + ([""] if facts else [])
    if entry.params:
        rows = [
            [
                code(p.name),
                p.location,
                p.type,
                p.required,
                code(p.default) if p.default else "",
                p.values,
                "; ".join(p.notes),
            ]
            for p in entry.params
        ]
        lines += table(["Attribute", "In", "Type", "Required", "Default", "Values", "Notes"], rows) + [""]
    return lines


def build(docs_root: Path, openapi_path: Path, out: Path, pin: str) -> dict:
    pages = []
    for path in sorted(docs_root.rglob("*.md")):
        rel = path.relative_to(docs_root).as_posix()
        if rel.startswith(SKIP_DIRS):
            continue
        page = parse_page(docs_root, path)
        if page.entries:
            pages.append(page)
    ops = load_openapi(openapi_path)
    matched: set[int] = set()
    for page in pages:
        for entry in page.entries:
            hits = list({id(o): o for o in (ops.get((m, norm(p))) for m, p in entry.endpoints) if o}.values())
            matched |= {id(o) for o in hits}
            enrich(entry, hits)
            locate(entry)
    extra_by_tag: dict[str, list[Entry]] = defaultdict(list)
    done: set[int] = set()
    for key, op in sorted(ops.items(), key=lambda kv: (kv[1]["_path"], METHOD_ORDER[kv[0][0]])):
        if id(op) in matched or id(op) in done:
            continue
        done.add(id(op))
        entry = Entry(op.get("summary") or op.get("operationId", ""), "", "", [(key[0], op["_path"])], openapi=True)
        entry.params = openapi_params(op)
        locate(entry)
        extra_by_tag[(op.get("tags") or ["untagged"])[0]].append(entry)
    total = len({id(o) for o in ops.values()})
    return render_all(pages, extra_by_tag, out, pin, (total, len(matched)))


NAV = (
    "Index: [README](../README.md) · Mechanics (auth, encoding, paging, uploads, errors): "
    "[conventions](../conventions.md) · Notation: [reading the tables](../../README.md#reading-the-generated-tables)"
)


def render_stage(stage: str, stage_pages: list[Page], out: Path, pin: str, index_rows: list) -> tuple[list, int]:
    """One file per DevOps stage; one `##` per docs page; one `###` per endpoint section."""
    fname = f"{file_slug(stage)}.md"
    stage_pages = sorted(stage_pages, key=lambda p: p.title.lower())
    slugger = Slugger()
    n_entries = sum(len(p.entries) for p in stage_pages)
    n_endpoints = sum(len(e.endpoints) for p in stage_pages for e in p.entries)
    title = f"GitLab REST API — stage “{stage}” ({len(stage_pages)} pages, {n_endpoints} endpoints)"
    slugger.slug(title)
    slugger.slug("Contents")
    lines = [banner(f"gitlab-org/gitlab doc/api ({pin})"), "", f"# {title}", "", NAV, "", "## Contents", ""]
    body: list[str] = []
    for page in stage_pages:
        lines.append(f"- [{page.title}](#{slugger.slug(page.title)}) — {len(page.entries)} sections")
        availability = "; ".join(cell(strip_md(d)) for d in page.details)
        body += [f"## {page.title}", "", f"Docs page: {docs_url(page.path, '')}"]
        body[-1] += f" · Availability: {availability}" if availability else ""
        body.append("")
        if page.prefixes:
            body += ["`<route-prefix>` on this page is one of: " + ", ".join(code(p) for p in page.prefixes), ""]
        for entry in page.entries:
            body += render_entry(entry, page.details)
            anchor = slugger.slug(entry.title)
            index_rows += [
                [m, code(p), f"[{page.title}: {entry.title}](rest/{fname}#{anchor})"] for m, p in entry.endpoints
            ]
    size = write(out / "rest" / fname, [*lines, "", *body])
    row = [
        f"[{stage}](rest/{fname})",
        str(len(stage_pages)),
        str(n_entries),
        str(n_endpoints),
        ", ".join(p.title for p in stage_pages),
    ]
    return row, size


def render_openapi_only(extra: dict[str, list[Entry]], out: Path, pin: str, index_rows: list) -> int:
    fname = "openapi-only.md"
    slugger = Slugger()
    title = f"GitLab REST API — operations only in openapi_v2.yaml ({sum(len(v) for v in extra.values())})"
    slugger.slug(title)
    lines = [
        banner(f"gitlab-org/gitlab doc/api/openapi/openapi_v2.yaml ({pin})"),
        "",
        f"# {title}",
        "",
        "These operations are in GitLab's OpenAPI file but no docs page names them: mostly legacy `/services/` "
        "aliases of the integrations endpoints, package-manager protocol routes, `authorize` pre-upload hooks and "
        "internal endpoints. Parentheses mark optional path segments. Index: [README](../README.md).",
        "",
    ]
    for tag, entries in sorted(extra.items()):
        slugger.slug(tag)
        lines += [f"## {tag}", ""]
        for entry in entries:
            lines += render_entry(entry, [])
            anchor = slugger.slug(entry.title)
            index_rows += [
                [m, code(p), f"[OpenAPI only: {entry.title}](rest/{fname}#{anchor})"] for m, p in entry.endpoints
            ]
    return write(out / "rest" / fname, lines)


def render_all(pages: list[Page], extra: dict[str, list[Entry]], out: Path, pin: str, counts: tuple[int, int]) -> dict:
    by_stage: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        by_stage[page.stage].append(page)
    stage_rows, index_rows, sizes = [], [], {}
    for stage, stage_pages in sorted(by_stage.items()):
        row, sizes[f"{file_slug(stage)}.md"] = render_stage(stage, stage_pages, out, pin, index_rows)
        stage_rows.append(row)
    if extra:
        sizes["openapi-only.md"] = render_openapi_only(extra, out, pin, index_rows)
    index_rows.sort(key=lambda r: (r[1], METHOD_ORDER.get(r[0], 9)))
    write(
        out / "operations-index.md",
        [
            banner(f"gitlab-org/gitlab doc/api + openapi_v2.yaml ({pin})"),
            "",
            f"# GitLab REST API — every endpoint ({len(index_rows)})",
            "",
            "Sorted by path; paths are relative to `https://HOST/api/v4` unless they start with `https://HOST`. "
            "Back to the [README](README.md).",
            "",
            *table(["Method", "Path", "Reference"], index_rows),
        ],
    )
    docs_endpoints = {(m, p) for page in pages for e in page.entries for m, p in e.endpoints}
    return {
        "stages": stage_rows,
        "endpoints": len(index_rows),
        "docs_endpoints": len(docs_endpoints),
        "pages": len(pages),
        "openapi_ops": counts[0],
        "openapi_matched": counts[1],
        "openapi_only": sum(len(v) for v in extra.values()),
        "sizes": sizes,
        "entries": sum(len(p.entries) for p in pages),
    }
