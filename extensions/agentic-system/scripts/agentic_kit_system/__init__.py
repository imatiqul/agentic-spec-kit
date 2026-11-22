"""agentic-spec-kit system extension (slice 0.2): system map, discovery and impact analysis.

Importing this package registers its checks, commands and self-test fixtures with the core kit.
"""
from __future__ import annotations

import json

import yaml

from agentic_kit import core

from . import checks_map, discover, sample
from .mapmodel import MAP_PATH, load_map

__version__ = "0.2.0"

core.ROLE_HOOKS.append(checks_map.role_hook)
core.MANIFEST_HOOKS.append(checks_map.manifest_hook)
core.SAMPLE_HOOKS.append(sample.extend_sample)
core.FIXTURE_HOOKS.append(sample.fixtures)

MAP_CHECKS = ["CK-MAP-SCHEMA", "CK-MAP-OWNER", "CK-MAP-EVIDENCE", "CK-MAP-DRIFT", "CK-MAP-FEDERATION"]


def _ctx(args):
    from agentic_kit.__main__ import _context
    return _context(args)


def cmd_map(args) -> int:
    from agentic_kit.__main__ import _report
    ctx = _ctx(args)
    if args.action == "discover":
        found = discover.discover(ctx)
        draft = discover.draft_map(found)
        if args.write:
            path = ctx.src.root / "system-map" / "map.draft.yml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(draft, sort_keys=False), encoding="utf-8", newline="\n")
            print(f"wrote system-map/map.draft.yml: {len(draft['nodes'])} nodes, {len(draft['edges'])} edges")
            print("Every node needs an owner, a tier and a classification from a person before it becomes map.yml.")
        elif args.json:
            print(json.dumps(found, indent=2))
        else:
            for n in found["nodes"]:
                print(f"{n['type']:16} {n['id']:40} {n['evidence']}")
            print(f"\n{len(found['nodes'])} nodes, {len(found['edges'])} edges")
        return 0
    return _report([core.run_check(c, ctx) for c in MAP_CHECKS], args.json)


def cmd_impact(args) -> int:
    ctx = _ctx(args)
    smap = load_map(ctx)
    specs = [args.spec] if args.spec else [s for s in ctx.specs() if ctx.src.exists(f"specs/{s}/spec.md")]
    for spec in specs:
        impact = checks_map.compute_impact(ctx, smap, spec)
        text = checks_map.render_impact(impact, smap)
        if args.write:
            (ctx.src.root / "specs" / spec / "impact.md").write_text(text, encoding="utf-8", newline="\n")
            print(f"wrote specs/{spec}/impact.md")
        if args.matrix:
            consumers = sorted({a["node"] for a in impact["affected"] if a["distance"] == 1})
            print(json.dumps({"include": [{"consumer": c} for c in consumers]}))
        elif args.json:
            print(json.dumps(impact, indent=2))
        elif not args.write:
            print(text)
    return 0


def _cli(sub, common) -> None:
    sp = sub.add_parser("map", help="discover, validate and compare the system map")
    common(sp)
    sp.add_argument("action", choices=["discover", "validate"])
    sp.add_argument("--write", action="store_true", help="with discover: write system-map/map.draft.yml")
    sp.set_defaults(fn=cmd_map)
    sp = sub.add_parser("impact", help="compute the blast radius, tier and required approvers for a spec")
    common(sp)
    sp.add_argument("--spec")
    sp.add_argument("--write", action="store_true")
    sp.add_argument("--matrix", action="store_true", help="print the direct consumers as a CI matrix")
    sp.set_defaults(fn=cmd_impact)


core.CLI_HOOKS.append(_cli)
