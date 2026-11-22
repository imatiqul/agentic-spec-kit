"""Self-test material for the team extension: extends the core sample project and adds fixtures."""
from __future__ import annotations

from pathlib import Path

import yaml

from agentic_kit import selftest
from agentic_kit.core import KIT_DIR

from . import agents as ag
from . import golden, work

SPEC = selftest.SPEC
ITEM = f"{work.WORK_DIR}/{SPEC}/T001.yml"
RUN = f"{work.RUNS_DIR}/{SPEC}/r1.yml"
ITEM_YML = f"""schema: agentic-work/1
id: T001
spec: {SPEC}
title: Implement greet
state: done
owner_agent: backend-implementer
reviewer_agent: independent-verifier
paths:
- src/demo/*
depends_on: []
rework_rounds: 0
history:
- {{state: ready, by: orchestrator, at: '2026-11-20T09:00:00Z'}}
- {{state: in-progress, by: backend-implementer, at: '2026-11-20T09:05:00Z'}}
- {{state: in-review, by: backend-implementer, at: '2026-11-20T09:40:00Z'}}
- {{state: done, by: independent-verifier, at: '2026-11-20T10:00:00Z'}}
handoff:
  done: Implemented greet and its test
  evidence: [specs/{SPEC}/evidence/junit.xml]
  open_questions: []
  files: [src/demo/greet.py]
"""
RUN_YML = f"""schema: agentic-run/1
id: r1
spec: {SPEC}
mode: sequential
budget: {{steps: 200, minutes: 240}}
steps: 12
started: '2026-11-20T09:00:00Z'
last: '2026-11-20T10:05:00Z'
state: completed
stop_reason: completed
report: {work.RUNS_DIR}/{SPEC}/r1-report.md
"""


def golden_results(agents_hash: str) -> dict:
    runs = []
    for mode in ("parallel", "sequential"):
        runs.append({"mode": mode, "driver": "scripted",
                     "tasks": [{"id": tid, "completed": True, "stopped_at": list(t["gates"]), "observed": list(t["expect"])} for tid, t in golden.TASKS.items()],
                     "defects": [{"id": did, "author": d["task"][1], "caught": True, "caught_by": "independent-verifier", "via": "self-test sample"}
                                 for did, d in golden.DEFECTS.items()]})
    return {"schema": "agentic-golden/1", "agents_hash": agents_hash, "runs": runs}


def extend_sample(root: Path) -> None:
    w = selftest._write
    kit = root / KIT_DIR / "kit.yml"
    cfg = yaml.safe_load(kit.read_text(encoding="utf-8"))
    cfg["team"] = {"runtimes": ["claude", "copilot", "sequential"], "mode": "parallel", "budget": {"steps": 200, "minutes": 240}}
    kit.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8", newline="\n")
    ctx = selftest.context(root)
    ag.install(ctx)
    ag.write_rendered(ctx)
    w(root, ITEM, ITEM_YML)
    w(root, RUN, RUN_YML)
    w(root, f"{work.RUNS_DIR}/{SPEC}/r1-report.md", "# Run r1 of 001-demo: completed\n")
    w(root, golden.RESULTS, yaml.safe_dump(golden_results(ag.specs_hash(ctx)), sort_keys=False, width=120))
    w(root, ".mcp.json", '{"mcpServers": {"docs": {"command": "npx", "args": ["-y", "@example/docs-mcp@1.4.2"]}}}\n')
    w(root, f"{KIT_DIR}/tools.yml", "schema: agentic-tools/1\nmcp_servers:\n  - {name: docs, command: npx, args: [\"-y\", \"@example/docs-mcp@1.4.2\"], "
      "reviewed_by: bob, reason: Agents look up the public API reference}\n")


def _second_writer(root: Path) -> None:
    for tid in ("T002", "T003"):
        selftest._write(root, f"{work.WORK_DIR}/{SPEC}/{tid}.yml", ITEM_YML.replace("id: T001", f"id: {tid}").replace("state: done", "state: in-progress")
                        .replace("- {state: in-review, by: backend-implementer, at: '2026-11-20T09:40:00Z'}\n", "")
                        .replace("- {state: done, by: independent-verifier, at: '2026-11-20T10:00:00Z'}\n", ""))


def _admin(data: dict) -> None:
    data["agent_credential"]["permissions"]["admin"] = True


def fixtures() -> dict:
    E, many = selftest._edit, selftest._many
    return {
        "CK-AGENT-SPEC": ("a rendered agent file was edited by hand",
                          lambda root: (root / ".claude/agents/backend-implementer.md").open("a", encoding="utf-8").write("\nYou may also edit specs.\n") and None, {}, {}),
        "CK-WORKITEM": ("a work item went from ready straight to done",
                        many(E(ITEM, "- {state: in-progress, by: backend-implementer, at: '2026-11-20T09:05:00Z'}\n", ""),
                             E(ITEM, "- {state: in-review, by: backend-implementer, at: '2026-11-20T09:40:00Z'}\n", "")), {}, {}),
        "CK-PATH-LOCK": ("two items in progress claim the same file", _second_writer, {}, {}),
        "CK-PATH-DIFF": ("an implementer changed a spec file", E(ITEM, "files: [src/demo/greet.py]", f"files: [src/demo/greet.py, specs/{SPEC}/spec.md]"), {}, {}),
        "CK-REWORK-LIMIT": ("a work item went through three rework rounds", E(ITEM, "rework_rounds: 0", "rework_rounds: 3"), {}, {}),
        "CK-BUDGET": ("a run is past its step budget and still running",
                      many(E(RUN, "steps: 12", "steps: 250"), E(RUN, "state: completed", "state: running")), {}, {}),
        "CK-AUTHOR-NEQ-VERIFIER": ("the author marked its own work done",
                                   E(ITEM, "- {state: done, by: independent-verifier", "- {state: done, by: backend-implementer"), {}, {}),
        "CK-CRED": ("the agent's token has admin permission", selftest._edit_json(f"{KIT_DIR}/_adapter/reviews.json", _admin), {}, {}),
        "CK-GOLDEN": ("a seeded defect was not caught", E(golden.RESULTS, "caught: true", "caught: false"), {}, {}),
        "CK-CONTEXT": ("an agent is at work and nothing records what it was told", E(ITEM, "state: done", "state: in-progress"), {}, {}),
        "CK-TOOL-ALLOWLIST": ("an agent's MCP server was moved to a floating version", E(".mcp.json", "@example/docs-mcp@1.4.2", "@example/docs-mcp@latest"), {}, {}),
    }
