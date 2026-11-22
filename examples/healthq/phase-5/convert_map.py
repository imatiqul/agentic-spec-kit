"""Convert the Phase 1 draft map of HealthQ Copilot into the kit's system-map format (agentic-map/1).

    python convert_map.py <draft.yml> <healthcare repository> <out map.yml>

The healthcare repository is only read. Rules, all of them mechanical:
- owner titles become role ids; tiers become lower case;
- classification becomes one of the HIPAA pack's three values. A node the draft could not classify ("unknown")
  becomes `restricted` until a person says otherwise, so that Security and Compliance is asked whenever it is touched;
- a derived fact must cite a file that exists. Where the draft cited a description, the file is looked up in the
  repository; where none is found the fact is downgraded to `assumed`, which is what it is;
- the path index is built from the files and folders each node cites;
- the kit's own discovery is then run over the repository. A node it finds under a folder the map already indexes becomes an
  alias of that map node, so that the drift check can compare the two. An event topic, or an edge, that discovery finds and the
  draft lacks is added, marked as such. This was added in Phase 6, after a review comment on pull request 72 of the healthcare
  repository showed that the Phase 1 draft had missed publishers: its pattern did not read calls that name their arguments.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[3] / "extensions" / "agentic" / "scripts"

OWNERS = {"Backend": "backend", "Solutions Architect": "solutions-architect", "Platform": "platform", "Data Owner": "data-owner",
          "AI Engineer": "ai-engineer", "Frontend": "frontend", "Security & Compliance": "security-compliance", "DevOps/SRE": "devops-sre"}
INTERNAL = {"identity", "secrets", "clinical reference text"}
NONE = {"none", "synthetic"}
PACKAGES = {"azure-openai": "Microsoft.SemanticKernel.Connectors.OpenAI", "azure-speech": "Microsoft.CognitiveServices.Speech",
            "azure-document-intelligence": "Azure.AI.DocumentIntelligence", "azure-communication": "Azure.Communication"}
SHARED_FILES = {"src/HealthQCopilot.AppHost/Program.cs"}
#: Components the Phase 1 draft did not map and a finding changes. Added in Phase 5, batch 2, for H6: the workflows.
EXTRA_NODES = [{"id": "ci-pipeline", "type": "shared-pipeline", "owner": "devops-sre", "tier": "high", "classification": "none", "origin": "derived",
                "evidence": ".github/workflows", "note": "Not in the Phase 1 draft; added in Phase 5 because finding H6 changes it"}]
EXTRA_NODES += [
    {"id": "repo-config", "type": "infrastructure", "owner": "platform", "tier": "high", "classification": "none", "origin": "derived",
     "evidence": "Directory.Build.props", "note": "Not in the Phase 1 draft; added in Phase 5 because findings M1, M4 and M5 change it"},
    {"id": "dev-apphost", "type": "infrastructure", "owner": "devops-sre", "tier": "medium", "classification": "none", "origin": "derived",
     "evidence": "src/HealthQCopilot.AppHost/Program.cs", "note": "Not in the Phase 1 draft; added in Phase 5 because finding N8 changes it"}]
#: What discovery finds that is deliberately not a component of the map, each with its reason.
IGNORE = {"healthq-copilot-frontend": "the workspace root of the front ends, not a package of its own",
          "servicebus-emulator": "a development-only container the application host starts; the map has it as part of dev-apphost",
          "sql-servicebus": "a development-only container the application host starts; the map has it as part of dev-apphost"}
FOUND_NOTE = "Not in the Phase 1 draft; found by the kit's discovery in Phase 6"
EXTRA_INDEX = [{"paths": [".github/workflows/**", "frontend/e2e/**", "frontend/e2e-cloud/**"], "node": "ci-pipeline"},
               {"paths": ["Directory.Build.props", ".editorconfig", ".gitignore", "global.json", "README.md", "LICENSE"], "node": "repo-config"},
               {"paths": ["src/HealthQCopilot.AppHost/**"], "node": "dev-apphost"}]


def reconcile(repo: Path, nodes: list, edges: list, index: list, stats: Counter) -> None:
    """Bring the map in line with what the kit's discovery finds in the repository. Nothing is removed."""
    sys.path.insert(0, str(KIT))
    from agentic_kit import core
    core.load_plugins(KIT)
    from agentic_kit_system import discover
    from agentic_kit_system.mapmodel import SystemMap

    src = core.Source(repo)
    found = discover.discover(core.Context(src, src, {}))
    smap = SystemMap({"schema": "agentic-map/1", "nodes": nodes, "edges": edges, "index": index})
    by_id = {n["id"]: n for n in nodes}
    resolved: dict[str, str] = {}
    for n in found["nodes"]:
        if n["id"] in IGNORE:
            continue
        if n["id"] in by_id:
            resolved[n["id"]] = n["id"]
        elif n["type"] == "event":
            nodes.append({"id": n["id"], "type": "event", "owner": "solutions-architect", "tier": "high", "classification": "restricted",
                          "origin": "derived", "evidence": n["evidence"],
                          "note": FOUND_NOTE + ". Not classified; treated as restricted until a person classifies it"})
            by_id[n["id"]] = nodes[-1]
            resolved[n["id"]] = n["id"]
            stats["event topic added from discovery"] += 1
        else:
            target = smap.node_for(n["evidence"])
            if target:
                aliases = by_id[target].setdefault("aliases", [])
                if n["id"] not in aliases:
                    aliases.append(n["id"])
                resolved[n["id"]] = target
                stats["discovery id recorded as an alias"] += 1
            else:
                stats["found by discovery and not placed: " + n["id"]] += 1
    have = {(e["from"], e["rel"], e["to"]) for e in edges}
    for e in found["edges"]:
        a, b = resolved.get(e["from"]), resolved.get(e["to"])
        if a and b and a != b and (a, e["rel"], b) not in have:
            edges.append({"from": a, "rel": e["rel"], "to": b, "origin": "derived", "evidence": e["evidence"], "note": FOUND_NOTE})
            have.add((a, e["rel"], b))
            stats[f"{e['rel']} edge added from discovery"] += 1


def main(draft: Path, repo: Path, out: Path) -> None:
    src = yaml.safe_load(draft.read_text(encoding="utf-8"))
    tracked = subprocess.run(["git", "-C", str(repo), "ls-files"], capture_output=True, text=True, check=True).stdout.splitlines()
    tracked_set = set(tracked)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()

    def exists(path: str) -> bool:
        path = path.rstrip("/")
        return path in tracked_set or any(t.startswith(path + "/") for t in tracked)

    def paths_in(evidence) -> list[str]:
        found = []
        for part in str(evidence or "").split(";"):
            token = re.sub(r":[0-9,\- ]+$", "", part.strip().split(" ")[0])
            if token and exists(token):
                found.append(token.rstrip("/"))
        return found

    def grep(pattern: str, under: str = "src") -> str | None:
        """First tracked file under a folder whose text matches, in path order, so the result is repeatable."""
        rx = re.compile(pattern)
        for rel in sorted(t for t in tracked if t.startswith(under.rstrip("/") + "/") and t.endswith((".cs", ".csproj", ".ts", ".tsx", ".yaml", ".yml", ".json"))):
            try:
                if rx.search((repo / rel).read_text(encoding="utf-8", errors="replace")):
                    return rel
            except OSError:
                continue
        return None

    stats = Counter()
    folders: dict[str, str] = {}
    nodes, index = [], []
    for n in src["nodes"]:
        nid, origin = n["id"], n["origin"]
        cited = paths_in(n.get("evidence"))
        note = None
        if origin == "derived" and not cited:
            found = None
            if nid in PACKAGES:
                found = grep(re.escape(PACKAGES[nid]))
            elif nid.startswith("topic-"):
                found = grep(r'"' + re.escape(nid[len("topic-"):]) + r'"')
            if found:
                cited, note = [found], f"Phase 1 cited: {n.get('evidence')}"
                stats["node evidence looked up"] += 1
            else:
                origin, note = "assumed", f"Phase 1 cited no file that could be found: {n.get('evidence')}"
                stats["node downgraded to assumed"] += 1
        cls = str(n.get("classification", "")).strip()
        if cls in NONE:
            new_cls = "none"
        elif cls in INTERNAL:
            new_cls = "internal"
        elif cls == "unknown":
            new_cls, note = "restricted", ((note + ". ") if note else "") + "Not classified in Phase 1; treated as restricted until a person classifies it"
            stats["unknown classification treated as restricted"] += 1
        else:
            new_cls = "restricted"
        node = {"id": nid, "type": n["type"], "owner": OWNERS[n["owner"]], "tier": str(n["tier"]).lower(), "classification": new_cls, "origin": origin}
        if cls not in ("none", "unknown", new_cls):
            node["holds"] = cls
        if cited:
            node["evidence"] = "; ".join(cited)
        if note:
            node["note"] = note
        nodes.append(node)
        globs = []
        for p in cited:
            if p in SHARED_FILES or not n["type"] in ("service", "frontend", "shared-library", "shared-package", "ai-component", "api-contract", "schema-object",
                                                       "data-store", "event-bus", "event-stream", "external-service"):
                continue
            if nid in PACKAGES or nid.startswith("topic-"):
                continue  # a file that mentions a package or a topic is not the node's own file
            is_dir = p not in tracked_set
            if is_dir:
                globs.append(p + "/**")
            elif p.rsplit("/", 1)[-1] in ("Program.cs", "package.json") or p.endswith(".csproj"):
                globs.append(p.rsplit("/", 1)[0] + "/**")
            else:
                globs.append(p)
        if globs:
            index.append({"paths": sorted(set(globs)), "node": nid})
            folder = next((g[:-3] for g in globs if g.endswith("/**")), None)
            if folder:
                folders[nid] = folder

    edges = []
    for e in src["edges"]:
        edge = {"from": e["from"], "rel": e["rel"], "to": e["to"], "origin": e["origin"]}
        cited = paths_in(e.get("evidence"))
        if e["origin"] == "derived" and not cited and e["rel"] in ("publishes", "subscribes") and e["from"] in folders:
            found = grep(r'"' + re.escape(e["to"][len("topic-"):]) + r'"', folders[e["from"]]) if e["to"].startswith("topic-") else None
            if found:
                cited = [found]
                stats["edge evidence looked up"] += 1
        if e["origin"] == "derived" and not cited:
            edge["origin"] = "assumed"
            edge["note"] = "Phase 1 cited no file for this"
            stats["edge downgraded to assumed"] += 1
        if cited:
            edge["evidence"] = "; ".join(cited)
        edges.append(edge)

    nodes += [dict(n) for n in EXTRA_NODES if exists(n["evidence"])]
    index += [dict(i) for i in EXTRA_INDEX]
    reconcile(repo, nodes, edges, index, stats)
    doc = {"schema": "agentic-map/1", "discovery": {"ignore": sorted(IGNORE)}, "nodes": nodes, "edges": edges, "index": index}
    header = (f"# System map of HealthQ Copilot, in agentic-spec-kit's format.\n"
              f"# Converted by examples/healthq/phase-5/convert_map.py from the Phase 1 draft, against the repository at commit {commit}.\n"
              "# Owners, tiers and classifications are an agent's proposals from Phase 1. A person confirms them when a plan is reviewed (G3).\n"
              "# `holds` keeps what Phase 1 wrote where the HIPAA pack's three classes are coarser. Not mapped: " + "; ".join(src.get("not_mapped") or []) + "\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + yaml.safe_dump(doc, sort_keys=False, width=160), encoding="utf-8", newline="\n")
    print(f"{len(nodes)} nodes ({sum(n['origin'] == 'assumed' for n in nodes)} assumed), {len(edges)} edges ({sum(e['origin'] == 'assumed' for e in edges)} assumed), {len(index)} index entries")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
