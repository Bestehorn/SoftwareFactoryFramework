"""Verify the generated API reference against the raw sources, independently of the generator's parsers.

    python -I scripts/api_reference/verify.py --sources tmp/api-sources --out docs/api-reference

Checks, each with its own simple scan of the source rather than the generator's code:
- GitHub REST: every operation of the OpenAPI file, each of its parameters and top-level body fields.
- GitHub GraphQL: every named definition, every Query and Mutation field, every enum value of the SDL.
- GitLab REST: every `METHOD /path` line in a plain code block of the docs pages, every OpenAPI operation.
- GitLab GraphQL: every type, query and mutation heading of the reference pages.
- Every relative link and #anchor in the reference resolves (GitHub's heading-anchor rule).
Exit status 1 when anything is missing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD")
LINK = re.compile(r"\]\(([^)\s]+)\)")
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def read_tree(folder: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(folder.rglob("*.md")))


# ---- GitHub REST -----------------------------------------------------------------------------------------------------
class OpenAPI:
    def __init__(self, path: Path) -> None:
        self.doc = json.loads(path.read_text(encoding="utf-8"))

    def res(self, node: object) -> dict:
        while isinstance(node, dict) and "$ref" in node:
            cur: object = self.doc
            for part in node["$ref"][2:].split("/"):
                cur = cur[part]  # type: ignore[index]
            node = cur
        return node if isinstance(node, dict) else {}

    def operations(self):
        for path, item in self.doc["paths"].items():
            for method, op in item.items():
                if method.upper() in METHODS:
                    yield method.upper(), path, op, item

    def body_fields(self, op: dict) -> list[str]:
        names: list[str] = []
        for content in self.res(op.get("requestBody", {})).get("content", {}).values():
            schema = self.res(content.get("schema", {}))
            names += list(schema.get("properties", {}))
            for part in schema.get("allOf", []):
                names += list(self.res(part).get("properties", {}))
        return names


def check_github_rest(src: Path, out: Path, problems: list[str]) -> str:
    spec = OpenAPI(src / "github-openapi/api.github.com.json")
    pages = {p.name: p.read_text(encoding="utf-8") for p in (out / "github/rest").glob("*.md")}
    n_ops = n_params = n_fields = 0
    for method, path, op, item in spec.operations():
        n_ops += 1
        text = pages.get(f"{op['x-github']['category']}.md", "")
        start = text.find(f"`{method} {path}` · operationId `{op['operationId']}`")
        if start < 0:
            problems.append(f"GitHub REST: {method} {path} missing")
            continue
        block = text[start : text.find("\n### ", start)]
        for raw in [*item.get("parameters", []), *op.get("parameters", [])]:
            n_params += 1
            param = spec.res(raw)
            if f"| `{param['name']}` | {param['in']} |" not in block:
                problems.append(f"GitHub REST: {op['operationId']} parameter {param['name']} missing")
        for name in spec.body_fields(op):
            n_fields += 1
            if f"| `{name}` |" not in block:
                problems.append(f"GitHub REST: {op['operationId']} body field {name} missing")
    index = (out / "github/operations-index.md").read_text(encoding="utf-8")
    rows = len(re.findall(r"^\| (?:GET|POST|PUT|PATCH|DELETE|HEAD) \|", index, re.M))
    if rows != n_ops:
        problems.append(f"GitHub REST: the index has {rows} rows for {n_ops} operations")
    return f"GitHub REST: {n_ops} operations, {n_params} parameters, {n_fields} top-level body fields"


# ---- GitHub GraphQL --------------------------------------------------------------------------------------------------
def check_github_graphql(src: Path, out: Path, problems: list[str]) -> str:
    sdl = re.sub(r'"""[\s\S]*?"""', "", (src / "github-graphql/schema.docs.graphql").read_text(encoding="utf-8"))
    text = read_tree(out / "github/graphql")
    headed = set(re.findall(r"^## `(\w+)`", text, re.M)) | set(re.findall(r"^(?:Input|Payload) `(\w+)`:", text, re.M))
    defs = re.findall(r"^(?:type|interface|input|enum|union|scalar) (\w+)", sdl, re.M)
    problems += [f"GitHub GraphQL: type {n} missing" for n in defs if n not in headed | {"Query", "Mutation"}]
    n_roots = 0
    for root in ("Query", "Mutation"):
        body = re.search(r"^type " + root + r"(?: [^{]*)?\{(.*?)^\}", sdl, re.M | re.S)
        for name in re.findall(r"^  (\w+)", body.group(1) if body else "", re.M):
            n_roots += 1
            if f"## `{name}`" not in text:
                problems.append(f"GitHub GraphQL: {root}.{name} missing")
    n_values = 0
    for enum, values in re.findall(r"^enum (\w+)[^{]*\{(.*?)^\}", sdl, re.M | re.S):
        section = text[text.find(f"## `{enum}`") :]
        section = section[: section.find("\n## ", 5)]
        for value in re.findall(r"^  (\w+)", values, re.M):
            n_values += 1
            if f"`{value}`" not in section:
                problems.append(f"GitHub GraphQL: enum value {enum}.{value} missing")
    return f"GitHub GraphQL: {len(defs)} definitions, {n_roots} root fields, {n_values} enum values"


# ---- GitLab REST -----------------------------------------------------------------------------------------------------
def plain_fences(text: str) -> list[list[str]]:
    fences: list[list[str]] = []
    current: list[str] | None = None
    lang = ""
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if current is None:
                current, lang = [], line.strip()[3:].strip()
            else:
                if lang in ("", "plaintext", "http", "text"):
                    fences.append(current)
                current = None
        elif current is not None:
            current.append(line.strip())
    return fences


def docs_endpoints(docs: Path) -> set[tuple[str, str]]:
    found = set()
    for page in docs.rglob("*.md"):
        if page.relative_to(docs).as_posix().startswith(("graphql/", "openapi/")):
            continue
        for fence in plain_fences(page.read_text(encoding="utf-8")):
            for line in fence:
                match = re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD)\s+(\S+)", line)
                if not match or re.match(r"^(https?:|\$|-)", match.group(2)):
                    continue  # curl-style examples with a host, shell variables or options are not endpoint templates
                path = re.sub(r"^/?api/v4(?=/)", "", match.group(2).split("?")[0])
                path = path if path.startswith("/") else "/" + path
                if re.search(r"[:<{*]", path) or not re.search(r"/\d+(/|$)", path):
                    found.add((match.group(1), path))
    return found


def norm(path: str) -> str:
    return re.sub(r":\w+|\{\w+\}|<[\w-]+>|\*\w+", "*", re.sub(r"^/api/v4", "", path)).rstrip("/")


def path_variants(path: str) -> set[str]:
    return {norm(re.sub(r"\([^()]*\)", "", path)), norm(re.sub(r"[()]", "", path)), norm(path)}


def check_gitlab_rest(src: Path, out: Path, problems: list[str]) -> str:
    index = (out / "gitlab/operations-index.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| (\w+) \| `([^`]+)` \|", index, re.M))
    wanted = docs_endpoints(src / "gitlab-docs/doc/api")
    problems += [f"GitLab REST: {m} {p} missing" for m, p in sorted(wanted - listed)]
    listed_norm = {(m, v) for m, p in listed for v in path_variants(p)}
    spec = yaml.safe_load((src / "gitlab-openapi/openapi_v2.yaml").read_text(encoding="utf-8"))
    n_ops = 0
    for path, item in spec["paths"].items():
        for method in (m.upper() for m in item if m.upper() in METHODS):
            n_ops += 1
            if not any((method, v) in listed_norm for v in path_variants(path)):
                problems.append(f"GitLab OpenAPI: {method} {path} missing")
    return f"GitLab REST: {len(wanted)} docs endpoint lines, {n_ops} OpenAPI operations"


# ---- GitLab GraphQL --------------------------------------------------------------------------------------------------
def check_gitlab_graphql(src: Path, out: Path, problems: list[str]) -> str:
    ref = src / "gitlab-docs/doc/api/graphql/reference"
    text = read_tree(out / "gitlab/graphql")
    headed = set(re.findall(r"^## `([^`]+)`", text, re.M)) | set(
        re.findall(r"^(?:Input|Payload) `([^`]+)`:", text, re.M)
    )
    total = 0
    for page in ("objects", "interfaces", "unions", "enums", "input_objects", "scalars", "queries", "mutations"):
        names = re.findall(r"^## `([^`]+)`", (ref / f"{page}.md").read_text(encoding="utf-8"), re.M)
        total += len(names)
        problems += [f"GitLab GraphQL: {page} {n} missing" for n in names if n.split(".", 1)[-1] not in headed]
    return f"GitLab GraphQL: {total} reference headings"


# ---- links -----------------------------------------------------------------------------------------------------------
def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    found = set()
    for line in re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S).splitlines():
        match = HEAD.match(line)
        if not match:
            continue
        text = re.sub(r"`|\*\*|\[|\]\([^)]*\)", "", match.group(2)).strip().lower()
        base = re.sub(r"[^\w\- ]", "", text).replace(" ", "-")
        seen[base] = seen.get(base, -1) + 1
        found.add(base if seen[base] == 0 else f"{base}-{seen[base]}")
    return found


def check_links(out: Path, problems: list[str]) -> str:
    cache: dict[Path, set[str]] = {}
    total = 0
    for page in sorted(out.rglob("*.md")):
        for match in LINK.finditer(re.sub(r"```.*?```", "", page.read_text(encoding="utf-8"), flags=re.S)):
            target = match.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            total += 1
            file_part, _, anchor = target.partition("#")
            dest = (page.parent / file_part).resolve() if file_part else page
            if not dest.exists():
                problems.append(f"link: {page.relative_to(out)} -> {target}: no such file")
            elif anchor and dest.suffix == ".md" and anchor not in cache.setdefault(dest, anchors(dest)):
                problems.append(f"link: {page.relative_to(out)} -> {target}: no such anchor")
    return f"links: {total} relative links"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    problems: list[str] = []
    for check in (check_github_rest, check_github_graphql, check_gitlab_rest, check_gitlab_graphql):
        print(check(args.sources, args.out, problems))
    print(check_links(args.out, problems))
    print(f"{len(problems)} problems")
    for problem in problems[:200]:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
