"""Discovery adapters (MAP-5, ADP-9): derive candidate nodes and edges from the codebase.

Every fact cites the file that proves it. Discovery is heuristic: it finds what these adapters know
how to read and nothing else. A human confirms the map; discovery then guards it against drift.
"""
from __future__ import annotations

import fnmatch
import json
import re

from agentic_kit.core import Context

SKIP = ("node_modules/", "bin/", "obj/", "dist/", ".git/", ".specify/", "specs/")
IMAGES = [  # image-name fragment -> (node type, engine)
    ("postgres", "data-store", "postgresql"), ("pgvector", "data-store", "postgresql"), ("mysql", "data-store", "mysql"),
    ("mariadb", "data-store", "mariadb"), ("mssql", "data-store", "sqlserver"), ("mongo", "data-store", "mongodb"),
    ("redis", "data-store", "redis"), ("qdrant", "data-store", "qdrant"), ("elasticsearch", "data-store", "elasticsearch"),
    ("opensearch", "data-store", "opensearch"), ("rabbitmq", "event-bus", "rabbitmq"), ("kafka", "event-bus", "kafka"),
    ("servicebus", "event-bus", "servicebus"), ("nats", "event-bus", "nats"),
]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _files(ctx: Context) -> list[str]:
    return [f for f in ctx.src.files() if not any(f"/{s}" in f"/{f}" for s in SKIP)]


def _image(image: str):
    for frag, kind, engine in IMAGES:
        if frag in image.lower():
            return kind, engine
    return None


def dotnet(ctx: Context, files: list[str], nodes: dict, edges: list) -> None:
    projects = {}
    for rel in files:
        if not rel.endswith(".csproj"):
            continue
        text = ctx.src.read(rel)
        stem = rel.rsplit("/", 1)[-1][:-7]
        if re.search(r"<IsTestProject>\s*true", text, re.I) or re.search(r"(^|[.\-_])tests?($|[.\-_])", stem, re.I) \
                or "Microsoft.NET.Test.Sdk" in text:
            continue
        kind = "service" if "Microsoft.NET.Sdk.Web" in text else "shared-library"
        if "Aspire.AppHost" in text or stem.lower().endswith("apphost"):
            kind = "infrastructure"
        projects[stem] = (rel, text, kind)
    for stem, (rel, text, kind) in projects.items():
        nodes[_slug(stem)] = {"id": _slug(stem), "type": kind, "evidence": rel, "adapter": "dotnet"}
        if kind == "infrastructure":
            continue
        for ref in re.findall(r'ProjectReference\s+Include="([^"]+)"', text):
            other = ref.replace("\\", "/").rsplit("/", 1)[-1][:-7]
            if other in projects:
                edges.append({"from": _slug(stem), "rel": "builds-with", "to": _slug(other), "evidence": rel, "adapter": "dotnet"})


def node(ctx: Context, files: list[str], nodes: dict, edges: list) -> None:
    packages = {}
    for rel in files:
        if rel.rsplit("/", 1)[-1] != "package.json":
            continue
        try:
            data = json.loads(ctx.src.read(rel))
        except json.JSONDecodeError:
            continue
        if data.get("name") and not data.get("workspaces"):
            packages[data["name"]] = (rel, data)
    for name, (rel, data) in packages.items():
        deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {}), **(data.get("peerDependencies") or {})}
        runnable = any(k in (data.get("scripts") or {}) for k in ("dev", "start", "serve"))
        server = any(d in deps for d in ("express", "fastify", "koa", "@nestjs/core", "hono"))
        ui = any(d in deps for d in ("react", "vue", "@angular/core", "svelte", "next"))
        kind = "service" if runnable and server else ("frontend" if runnable and ui else "shared-package")
        nid = _slug(name.lstrip("@"))
        nodes[nid] = {"id": nid, "type": kind, "evidence": rel, "adapter": "node"}
        for dep in deps:
            if dep in packages and dep != name:
                edges.append({"from": nid, "rel": "builds-with", "to": _slug(dep.lstrip("@")), "evidence": rel, "adapter": "node"})


def compose(ctx: Context, files: list[str], nodes: dict, edges: list) -> None:
    import yaml
    for rel in files:
        name = rel.rsplit("/", 1)[-1]
        if not (fnmatch.fnmatch(name, "docker-compose*.y*ml") or fnmatch.fnmatch(name, "compose*.y*ml")):
            continue
        try:
            doc = yaml.safe_load(ctx.src.read(rel)) or {}
        except yaml.YAMLError:
            continue
        for sid, svc in (doc.get("services") or {}).items():
            found = _image(str((svc or {}).get("image", "")))
            if found:
                nodes[_slug(sid)] = {"id": _slug(sid), "type": found[0], "engine": found[1], "evidence": rel, "adapter": "compose"}


def aspire(ctx: Context, files: list[str], nodes: dict, edges: list) -> None:
    for rel in files:
        if not rel.endswith(".cs") or "apphost" not in rel.lower():
            continue
        text = ctx.src.read(rel)
        for m in re.finditer(r'\.Add(Postgres|Redis|SqlServer|MongoDB|RabbitMQ|Kafka)\(\s*"([^"]+)"', text):
            kind = "event-bus" if m.group(1) in ("RabbitMQ", "Kafka") else "data-store"
            engine = {"Postgres": "postgresql", "SqlServer": "sqlserver", "MongoDB": "mongodb"}.get(m.group(1), m.group(1).lower())
            nodes[_slug(m.group(2))] = {"id": _slug(m.group(2)), "type": kind, "engine": engine, "evidence": rel, "adapter": "aspire"}
        for m in re.finditer(r'\.AddDatabase\(\s*"([^"]+)"', text):
            nodes[_slug(m.group(1))] = {"id": _slug(m.group(1)), "type": "schema", "evidence": rel, "adapter": "aspire"}
        for m in re.finditer(r'\.AddContainer\(\s*"([^"]+)"\s*,\s*"([^"]+)"', text):
            found = _image(m.group(2))
            if found:
                nodes[_slug(m.group(1))] = {"id": _slug(m.group(1)), "type": found[0], "engine": found[1], "evidence": rel, "adapter": "aspire"}


def contracts(ctx: Context, files: list[str], nodes: dict, edges: list) -> None:
    for rel in files:
        name = rel.rsplit("/", 1)[-1].lower()
        stem = name.rsplit(".", 1)[0]
        if name.endswith((".graphql", ".graphqls", ".proto")) or \
                (name.endswith((".yaml", ".yml", ".json")) and ("openapi" in name or "swagger" in name or "asyncapi" in name or "/contracts/" in f"/{rel}")):
            nodes[f"contract-{_slug(stem)}"] = {"id": f"contract-{_slug(stem)}", "type": "api-contract", "evidence": rel, "adapter": "contracts"}


ADAPTERS = {"dotnet": dotnet, "node": node, "compose": compose, "aspire": aspire, "contracts": contracts}


def discover(ctx: Context) -> dict:
    files = _files(ctx)
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    for fn in ADAPTERS.values():
        fn(ctx, files, nodes, edges)
    seen, unique = set(), []
    for e in edges:
        key = (e["from"], e["rel"], e["to"])
        if key not in seen and e["from"] in nodes and e["to"] in nodes:
            seen.add(key)
            unique.append(e)
    return {"nodes": [nodes[k] for k in sorted(nodes)], "edges": sorted(unique, key=lambda e: (e["from"], e["rel"], e["to"]))}


def draft_map(found: dict) -> dict:
    """A map draft from discovery: every node still needs an owner, tier and classification from a human."""
    return {
        "schema": "agentic-map/1",
        "nodes": [{"id": n["id"], "type": n["type"], **({"engine": n["engine"]} if n.get("engine") else {}),
                   "owner": "", "tier": "", "classification": "", "origin": "derived", "evidence": n["evidence"]}
                  for n in found["nodes"]],
        "edges": [{"from": e["from"], "rel": e["rel"], "to": e["to"], "origin": "derived", "evidence": e["evidence"]}
                  for e in found["edges"]],
        "index": [{"paths": [n["evidence"].rsplit("/", 1)[0] + "/*"], "node": n["id"]}
                  for n in found["nodes"] if "/" in n["evidence"] and n["type"] not in ("data-store", "schema", "event-bus", "api-contract")],
    }
