"""Self-test material for the system extension: extends the core sample project and adds fixtures."""
from __future__ import annotations

from pathlib import Path

from agentic_kit import selftest
from agentic_kit.core import KIT_DIR

from .checks_map import compute_impact, render_impact
from .mapmodel import MAP_PATH, load_map

SPEC = selftest.SPEC
MAP = """schema: agentic-map/1
nodes:
  - id: demo-app
    type: service
    owner: backend
    tier: high
    classification: internal
    origin: derived
    evidence: src/demo/greet.py
  - id: demo-client
    type: frontend
    owner: frontend
    tier: medium
    classification: none
    origin: assumed
edges:
  - {from: demo-client, rel: calls, to: demo-app, origin: assumed}
index:
  - {paths: ["src/demo/*"], node: demo-app}
  - {paths: ["web/*"], node: demo-client}
"""
FINDINGS = """findings:
  - id: F-001
    statement: The greeting does not escape the name
    evidence: [src/demo/greet.py]
"""
OTHER_SPEC = """---
spec: 002-other
tier_declared: high
owner_role: backend
principles: [P-1]
touches: [demo-app]
---
# Other

- **FR-001**: System MUST do something else to the same service.
"""


def extend_sample(root: Path) -> None:
    w, e = selftest._write, selftest._edit
    w(root, MAP_PATH, MAP)
    w(root, f"{KIT_DIR}/findings.yml", FINDINGS)
    e(f"{KIT_DIR}/roles.yml", "  - solutions-architect\n", "  - solutions-architect\n  - backend\n  - frontend\n")(root)
    e(f"specs/{SPEC}/spec.md", 'paths: ["src/demo/*"]\n', 'paths: ["src/demo/*"]\ntouches: [demo-app]\n')(root)
    ctx = selftest.context(root)
    smap = load_map(ctx)
    w(root, f"specs/{SPEC}/impact.md", render_impact(compute_impact(ctx, smap, SPEC), smap))


def _append(rel: str, text: str):
    def go(root: Path) -> None:
        p = root / rel
        p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8", newline="\n")
    return go


SPECFILE = f"specs/{SPEC}/spec.md"
E = selftest._edit


def fixtures() -> dict:
    return {
        "CK-MAP-SCHEMA": ("an edge points at a node that does not exist", E(MAP_PATH, "to: demo-app", "to: ghost"), {}, {}),
        "CK-MAP-OWNER": ("a node has no owner", E(MAP_PATH, "    owner: frontend\n", ""), {}, {}),
        "CK-MAP-EVIDENCE": ("a derived node cites a file that was deleted", E(MAP_PATH, "evidence: src/demo/greet.py", "evidence: src/demo/gone.py"), {}, {}),
        "CK-MAP-DRIFT": ("a new package exists in the code but not in the map",
                         lambda root: selftest._write(root, "services/new/package.json", '{"name": "new-service", "scripts": {"start": "node ."}, "dependencies": {"express": "4"}}'), {}, {}),
        "CK-MAP-FEDERATION": ("a federated map is pinned to a branch name",
                              _append(MAP_PATH, "federated:\n  - {name: other, repo: example/other, ref: main, path: system-map}\n"), {}, {}),
        "CK-TOUCH": ("a change edits a node the spec does not declare", lambda root: None,
                     {"changed_files": ["src/demo/greet.py", SPECFILE]}, {"changed_files": ["web/app.js", SPECFILE]}),
        "CK-IMPACT": ("the map changed after the impact report was generated", E(MAP_PATH, "    owner: frontend\n", "    owner: platform\n"), {}, {}),
        "CK-TIER-RAISE": ("a spec declared high touches a critical node", E(MAP_PATH, "tier: high", "tier: critical"), {}, {}),
        "CK-CROSS-SPEC": ("two in-flight specs touch the same node with no order",
                          lambda root: [selftest._write(root, f"specs/{s}/spec.md", OTHER_SPEC.replace("002-other", s))
                                        for s in ("002-other", "003-another")] and None, {}, {}),
        "CK-PROGRAMME": ("a programme spec has no children or contract",
                         E(SPECFILE, "touches: [demo-app]\n", "touches: [demo-app]\nprogramme: {children: [], rollout: []}\n"), {}, {}),
        "CK-FINDING-EVIDENCE": ("a finding cites a file that does not exist",
                                E(f"{KIT_DIR}/findings.yml", "evidence: [src/demo/greet.py]", "evidence: [src/demo/nowhere.py]"), {}, {}),
    }
