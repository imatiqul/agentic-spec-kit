"""Write the HealthQ reference into a folder, as it goes into the healthcare repository.

    python examples/healthq/export.py <destination folder>

Copies `examples/healthq/project` except two files that would say something untrue there:
- `.specify/init-options.json`, which says Spec Kit is initialised. In the healthcare repository it is not, yet.
- `.github/workflows/agentic-checks.yml`, which runs the kit's checks. The kit is not installed there, so it would fail.
An existing CODEOWNERS file in the destination is kept, and the reference's lines are added to it.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "project"
LEFT_OUT = {".specify/init-options.json", ".github/workflows/agentic-checks.yml"}
README = """# Spec-driven governance for HealthQ Copilot

- **Phase and date:** Phase 7, 2026-11-22. The numbers below are counted from the files beside this one when it is written
- **Upstream and reference:** github/spec-kit `v1.4.3`; this repository
- **Requirement IDs exercised:** GOV-9, GOV-11, MAP-1 to MAP-5, MAP-8, TRC-1, AGT-1 to AGT-3
- **Assumptions:** owners, tiers and classifications in the system map are proposals until a plan is reviewed
- **Unverified:** nothing here is enforced by this repository's pipeline yet

These files were written with [agentic-spec-kit](https://github.com/imatiqul/agentic-spec-kit). Agents draft, build and verify; a named person approves at every gate.

| Path | What it is |
|---|---|
| `.specify/memory/constitution.md` | The constitution: {principles} principles, each checked by a machine or judged by a named role |
| `.specify/agentic/` | Kit settings (Regulated profile, HIPAA pack), who holds which role, what checks each principle, the audit log |
| `.specify/agentic/agents/` | {agents} agent specs: what each agent may read, write and run, and what it never does |
| `system-map/map.yml` | What exists and what depends on what: {nodes} components and {edges} dependencies |
| `specs/` | {specs} specs, one per finding of the review. {planned} have a plan; {tasked} have a task list |
{work_row}
## State

{decisions}

Spec Kit and the kit's extensions are **not installed** in this repository, and no workflow runs the checks. To run them from a checkout of agentic-spec-kit:

```bash
python <agentic-spec-kit>/extensions/agentic/scripts/agentic.py --root . check
```

Until agents have a GitHub identity of their own, an approval under the maintainer's account cannot be told from one made by an agent, and GitHub does not let the author of a pull request approve it.
"""
NO_DECISIONS = ("No gate has been passed by a pull-request review, so the kit holds no decision record. What the owner approved in "
                "conversation is written at the top of each document, in his words, and is marked there as not being a decision record.")


def readme() -> str:
    """The README for the exported folder, with its numbers counted from the reference project."""
    import yaml
    smap = yaml.safe_load((PROJECT / "system-map" / "map.yml").read_text(encoding="utf-8"))
    specs = sorted(d for d in (PROJECT / "specs").iterdir() if (d / "spec.md").is_file())
    constitution = (PROJECT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
    kit = PROJECT / ".specify" / "agentic"
    worked = sorted(d.name for d in (kit / "work").iterdir() if d.is_dir()) if (kit / "work").is_dir() else []
    recorded = sorted((kit / "decisions").rglob("*.yml")) if (kit / "decisions").is_dir() else []
    return README.format(
        principles=sum(1 for line in constitution.splitlines() if line.startswith("### P-")),
        agents=len(list((kit / "agents").glob("*.yml"))) if (kit / "agents").is_dir() else 0,
        nodes=len(smap.get("nodes") or []), edges=len(smap.get("edges") or []),
        specs=len(specs), planned=sum((d / "plan.md").is_file() for d in specs), tasked=sum((d / "tasks.md").is_file() for d in specs),
        work_row=("| `.specify/agentic/work/`, `.specify/agentic/runs/` | What agents did, task by task and step by step, for: "
                  + ", ".join(f"`{w}`" for w in worked) + " |\n") if worked else "",
        decisions=f"{len(recorded)} gate decision(s) are recorded under `.specify/agentic/decisions/`." if recorded else NO_DECISIONS)


def files() -> list[str]:
    return sorted(p.relative_to(PROJECT).as_posix() for p in PROJECT.rglob("*") if p.is_file() and p.relative_to(PROJECT).as_posix() not in LEFT_OUT)


def export(dest: Path) -> list[str]:
    written = []
    for rel in files():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel == ".github/CODEOWNERS" and target.is_file():
            have = target.read_text(encoding="utf-8")
            extra = [line for line in (PROJECT / rel).read_text(encoding="utf-8").splitlines() if line.strip() and line not in have.splitlines()]
            target.write_text(have.rstrip("\n") + "\n" + "\n".join(extra) + "\n", encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(PROJECT / rel, target)
        written.append(rel)
    readme_rel = ".specify/agentic/README.md"
    (dest / readme_rel).write_text(readme(), encoding="utf-8", newline="\n")
    return written + [readme_rel]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = export(Path(sys.argv[1]).resolve())
    print("\n".join(out))
    print(f"{len(out)} file(s) written")
