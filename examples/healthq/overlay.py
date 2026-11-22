"""Lay the HealthQ reference project over a copy of the healthcare repository, and run the kit there.

    python examples/healthq/overlay.py <healthcare repository> <work folder> [kit arguments ...]

The healthcare repository is cloned into the work folder and is never changed. The reference project
(`examples/healthq/project`: kit settings, roles, constitution, system map, specs) is copied on top of the clone,
so that checks which read source files, such as the evidence each map entry cites, have the source to read.
With no kit arguments it runs every check and prints a summary by check.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1] / "extensions" / "agentic" / "scripts" / "agentic.py"


def build(repo: Path, work: Path) -> str:
    if work.exists():
        raise SystemExit(f"{work} already exists; give a folder that does not, so nothing is overwritten")
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(repo), str(work)], check=True)
    commit = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    shutil.copytree(HERE / "project", work, dirs_exist_ok=True)
    return commit


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit(__doc__)
    repo, work, rest = Path(argv[0]).resolve(), Path(argv[1]).resolve(), argv[2:]
    commit = build(repo, work)
    print(f"reference project laid over {repo.name} at {commit[:8]} in {work}")
    if rest:
        return subprocess.run([sys.executable, str(KIT), "--root", str(work), *rest]).returncode
    out = subprocess.run([sys.executable, str(KIT), "--root", str(work), "check", "--json"], capture_output=True, text=True)
    try:
        results = json.loads(out.stdout)
    except ValueError:
        print(out.stdout[-2000:], out.stderr[-2000:])
        return 2
    rows = results.get("results") if isinstance(results, dict) else results
    passed = failed = not_run = 0
    for r in rows:
        findings, why = r.get("findings") or [], r.get("not_run")
        if why:
            not_run += 1
            print(f"NOT RUN  {r['check']}: {str(why)[:110]}")
        elif findings:
            failed += 1
            print(f"FAIL     {r['check']}: {len(findings)} finding(s); first: {str(findings[0] if isinstance(findings[0], str) else findings[0].get('message'))[:130]}")
        else:
            passed += 1
    print(f"{passed} passed, {failed} failed, {not_run} not run")
    return out.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
