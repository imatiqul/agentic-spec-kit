"""Lineage (TRC-19): from a line of code back to who asked for it and who approved it."""
from __future__ import annotations

import re
import subprocess

from agentic_kit.core import KIT_DIR, Context, match_any
from agentic_kit.lanes import approved_records

from . import common
from .dedupe import origin
from .intake import records
from .living import spec_deltas

_TRAILER = re.compile(r"^(Work-Item|Agent):\s*(.+)$", re.M)


def _git(ctx: Context, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(ctx.src.root), *args], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""


def last_change(ctx: Context, path: str, line: int | None) -> dict:
    """The commit that last changed the file (or the line), with the work item and agent its message names."""
    if line:
        out = _git(ctx, "log", "-1", f"-L{line},{line}:{path}", "--format=%H%n%an%n%ad%n%B", "--date=short", "-s")
    else:
        out = _git(ctx, "log", "-1", "--format=%H%n%an%n%ad%n%B", "--date=short", "--", path)
    parts = out.split("\n", 3)
    if len(parts) < 3 or not parts[0]:
        return {}
    info = {"commit": parts[0], "author": parts[1], "date": parts[2]}
    for name, value in _TRAILER.findall(parts[3] if len(parts) > 3 else ""):
        info[name.lower().replace("-", "_")] = value.strip()
    return info


def specs_for(ctx: Context, path: str) -> list[str]:
    return [s for s in ctx.specs() if match_any(path, [str(g) for g in (common.front(ctx, s).get("paths") or [])])]


def why(ctx: Context, target: str) -> str:
    path, _, raw = target.partition(":")
    line = int(raw) if raw.isdigit() else None
    lines = [f"# Why `{target}` is the way it is", ""]
    change = last_change(ctx, path, line)
    item_spec = item_id = None
    if change:
        lines.append(f"- **Last changed:** {change['date']} in `{change['commit'][:10]}` by {change['author']}"
                     + (f", agent {change['agent']}" if change.get("agent") else ""))
        if change.get("work_item"):
            item_spec, _, item_id = change["work_item"].partition("/")
            lines.append(f"- **Work item:** {change['work_item']}")
    else:
        lines.append("- **Last changed:** not known (no git history for this path)")
    specs = specs_for(ctx, path)
    if item_spec and item_spec in ctx.specs() and item_spec not in specs:
        specs.insert(0, item_spec)
    if not specs:
        lines += ["", "No spec claims this path. It is either older than the kit or changed outside a spec (see CK-DRIFT-SPEC)."]
        return "\n".join(lines) + "\n"
    intake_by_id = {str(r.get("id")): r for _, r in records(ctx)}
    for spec in specs:
        lines += ["", f"## Spec {spec}: {common.spec_title(ctx, spec)}"]
        frs, acs = common.requirements(ctx, spec), common.criteria(ctx, spec)
        carried: list[str] = []
        work = f"{KIT_DIR}/work/{spec}/{item_id}.yml" if item_id and spec == item_spec else ""
        if work and ctx.src.exists(work):
            carried = [str(c) for c in ((ctx.src.yaml(work) or {}).get("carries") or [])]
            lines.append(f"- **Task {item_id} carries:** {', '.join(carried) or 'no acceptance criterion'}")
        wanted = sorted({f for a in carried for f in (acs.get(a) or ([], ""))[0]}) or sorted(frs)
        for fid in wanted:
            lines.append(f"- **{fid}:** {frs.get(fid, '(not in the spec)')}")
        for d in spec_deltas(ctx, spec):
            for r in d.added + d.modified:
                if not wanted or set(r.verifies) & set(wanted):
                    lines.append(f"- **Behaviour:** capability `{d.capability}`, requirement '{r.name}'")
        for rid in [str(i) for i in origin(ctx, spec).get("intake") or []]:
            src = (intake_by_id.get(rid) or {}).get("source") or {}
            lines.append(f"- **Asked for in:** {src.get('platform', 'unknown')} {src.get('key', rid)}" + (f" ({src['url']})" if src.get("url") else ""))
        approvals = approved_records(ctx, spec)
        for gate in sorted(approvals):
            people = ", ".join(f"{a.get('reviewer')} as {a.get('role')} ({a.get('review_ref')})" for a in approvals[gate][1].get("approvals") or [])
            lines.append(f"- **{gate} approved by:** {people or 'nobody recorded'}")
        if not approvals:
            lines.append("- **Approvals:** none recorded yet")
    return "\n".join(lines) + "\n"
