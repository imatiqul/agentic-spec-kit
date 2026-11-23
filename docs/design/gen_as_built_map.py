"""Generate requirement-map-as-built.md: every requirement in docs/prompts/spec, the checks that enforce it in the code
as it stands, and, where no check does, how it is met. Fails if a requirement has neither, or a note has gone stale.

Run from the repository root:  python docs/design/gen_as_built_map.py
"""
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

#: Requirements that no check cites: (kind, how it is met). Kinds: feature (code with unit tests), document, procedural, not built.
NOTES = {
    "ADP-2": ("procedural", "Reviews are recorded in `docs/design/source-review.md`. Open: the tracker adapters of slice 0.6 were built without reading the source of the community extensions that overlap them"),
    "ADP-4": ("not built", "Tagged `later`. The enforcement adapter is an interface with a GitHub and a file implementation; no GitLab or Azure DevOps adapter exists, so approvals made there are not read"),
    "ADP-7": ("document", "`docs/adapters/engine.md`"),
    "ADP-15": ("document", "`docs/adapters/domain-pack.md`"),
    "ADP-16": ("feature", "Superseded by ADP-18: the tracker adapters of `agentic-connect`"),
    "ADP-19": ("feature", "`agentic-connect` `notify.py`: Slack, Teams and SMTP renderers. Never sent to a live service"),
    "ADP-20": ("feature", "`extensions/agentic-connect/ci/` and `docs/adapters/pipeline.md`. No template has been run by its CI system"),
    "ADP-21": ("feature", "`agentic-team` `tools.py`: eight configuration files"),
    "AGT-12": ("procedural", "A rule in every agent spec. Tested by the planted-instruction tests (AGT-15, CK-INJECTION), so far with a scripted stand-in only"),
    "CHG-12": ("feature", "`agentic-system` `compute_impact`: Platform and the owner of each component one step away join G3"),
    "MAP-16": ("feature", "`agentic.py quality debt`, and the `debt` report view"),
    "NTF-1": ("feature", "`agentic-connect` `notify.detect`"),
    "NTF-4": ("feature", "`agentic-connect` `notify.channels_for`, and the work-item note"),
    "NTF-5": ("feature", "`agentic-connect` `notify.deliver`: the ledger, and the marker looked for before a note is posted"),
    "NTF-6": ("feature", "`agentic-connect` `notify.deliver`: a failed delivery is reported and never fails the checks"),
    "PIP-1": ("feature", "`agentic.py connect run`"),
    "PIP-2": ("feature", "`agentic.py connect run --json`, and `report gates`"),
    "PIP-6": ("feature", "`agentic.py connect mirror`. Never run against a live repository"),
    "PIP-7": ("feature", "The `intake` job of each pipeline template opens a proposed change. Never run"),
    "QLT-2": ("document", "`docs/limits.md` and the verify command (`extensions/agentic/commands/verify.md`)"),
    "TRC-2": ("feature", "`agentic-system` `manifest_hook`: each row of the trace manifest carries the nodes its spec touches"),
    "TRC-7": ("document", "`docs/design/architecture.md` and `docs/limits.md`"),
    "TRC-13": ("feature", "`agentic.py report metrics`: time to decision per gate, approvals by people, agent steps, time and spend"),
    "TRC-15": ("feature", "`agentic.py report <view>`: gates, waivers, trace, metrics, map, debt, spend, capabilities"),
    "TRC-19": ("feature", "`agentic.py why <file>[:<line>]`. With a system map it also names the component, what the spec touches and depends on, and what it reaches"),
}

def build() -> tuple[str, str]:
    """(the document, a one-line summary). Raises SystemExit when the map and the code disagree."""
    reqs = {}
    for f in sorted((ROOT / "docs" / "prompts" / "spec").glob("*.md")):
        for m in re.finditer(r"^- ([A-Z]{3}-\d+) \[([^\]]+)\]\s*((?:.*\n)(?:  .*\n)*)", f.read_text(encoding="utf-8"), re.M):
            reqs[m.group(1)] = (m.group(2), " ".join(m.group(3).split()), f.name)

    by_req: dict[str, list[str]] = {}
    for cid, chk in core.REGISTRY.items():
        for r in chk.requirements:
            by_req.setdefault(r, []).append(cid)

    unknown = sorted(set(by_req) - set(reqs))
    unmet = sorted(r for r in reqs if r not in by_req and r not in NOTES)
    stale = sorted(r for r in NOTES if r in by_req or r not in reqs)
    if unknown or unmet or stale:
        sys.exit(f"checks cite unknown requirements: {unknown}; requirements with no check and no note: {unmet}; notes that are stale: {stale}")


    def key(rid: str):
        return rid.split("-")[0], int(rid.split("-")[1])


    KINDS = ("check", "feature", "document", "procedural", "not built")
    kinds = Counter()
    for r in reqs:
        kinds[(reqs[r][0], "check" if r in by_req else NOTES[r][0])] += 1
    slices = sorted({s for s, _, _ in reqs.values()})
    out = ["# Requirement map, as built", "",
           "- **Phase and date:** Phase 3e, 2026-11-22",
           "- **Requirement IDs covered:** every requirement in `docs/prompts/spec/`",
           "- **Assumptions:** a check enforces a requirement when its registration cites the requirement's id",
           "- **Unverified:** this maps requirements to code. It says nothing about what has been run against live systems; see `docs/limits.md`", "",
           "Generated by `gen_as_built_map.py` from the spec files and the check registry. Do not edit by hand.",
           "`requirement-map.md` is the Phase 2 design and is kept as it was approved.", "",
           "| Slice | Enforced by a check | Feature with unit tests | Document | Procedural | Not built | Total |", "|---|---|---|---|---|---|---|"]
    for s in slices:
        row = [kinds[(s, k)] for k in KINDS]
        out.append(f"| {s} | {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {sum(row)} |")
    total = [sum(kinds[(s, k)] for s in slices) for k in KINDS]
    out.append(f"| **all** | **{total[0]}** | **{total[1]}** | **{total[2]}** | **{total[3]}** | **{total[4]}** | **{sum(total)}** |")
    out += ["", "| ID | Slice | Requirement | Enforced by | Where no check: how it is met |", "|---|---|---|---|---|"]
    for r in sorted(reqs, key=key):
        sl, text, _ = reqs[r]
        short = text if len(text) <= 150 else text[:147].rsplit(" ", 1)[0] + " …"
        checks = ", ".join(sorted(by_req.get(r, []))) or "—"
        note = "" if r in by_req else f"{NOTES[r][0].capitalize()}. {NOTES[r][1]}"
        out.append(f"| {r} | {sl} | {short.replace('|', '/')} | {checks} | {note} |")
    summary = (f"{len(reqs)} requirements; {total[0]} enforced by a check, {total[1]} features, {total[2]} documents, "
               f"{total[3]} procedural, {total[4]} not built; {len(core.REGISTRY)} checks")
    return "\n".join(out) + "\n", summary


if __name__ == "__main__":
    text, line = build()
    (HERE / "requirement-map-as-built.md").write_text(text, encoding="utf-8", newline="\n")
    print(line)
