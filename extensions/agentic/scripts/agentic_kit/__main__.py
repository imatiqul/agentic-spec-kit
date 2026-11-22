"""Command line for the kit. Every command works without an agent.

Exit codes: 0 all good, 1 a check failed, 2 a check could not run or the command was misused.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

from . import __version__, adapters, checks_gov, checks_trace, selftest  # noqa: F401
from .checks_gov import DEFAULT_APPROVERS, decisions, gate_roles
from .checks_trace import build_manifest
from .core import (DECISIONS, GATES, KIT_DIR, PROFILE_GATES, PROFILES, REGISTRY, Context, KitError, Source,
                   approval_line, audit_append, evidence_hash, run_check)

DEFAULT_EVIDENCE = {
    "G1": ["spec.md"], "G2": ["spec.md"], "G3": ["plan.md", "impact.md", "data-change-plan.md"],
    "G4": ["tasks.md", "trace-manifest.json"], "G5": ["trace-manifest.json", "evidence/*"],
    "G6": ["verification/*"], "G7": ["release/*"],
}
for _gate in list(DEFAULT_EVIDENCE):  # every gate also binds its reviewer brief, when one has been generated (GOV-20)
    DEFAULT_EVIDENCE[_gate].append(f"briefs/{_gate}.md")
DOCTOR_CHECKS = ["CK-PROFILE", "CK-ROLES", "CK-UPSTREAM-PIN", "CK-ENFORCE-SETUP"]


def _context(args) -> Context:
    src = Source(args.root)
    trusted = src.at(args.base_ref) if getattr(args, "base_ref", None) else src
    options = {}
    if getattr(args, "today", None):
        options["today"] = args.today
    if getattr(args, "changed_files", None):
        options["changed_files"] = [x.strip() for x in Path(args.changed_files).read_text().splitlines() if x.strip()]
    return Context(src, trusted, options)


def _report(results, as_json: bool) -> int:
    failed = [r for r in results if r.findings]
    not_run = [r for r in results if r.not_run]
    if as_json:
        print(json.dumps({"ok": not failed and not not_run, "results": [r.as_dict() for r in results]}, indent=2))
    else:
        for r in results:
            status = "NOT RUN" if r.not_run else ("FAIL" if r.findings else "ok")
            print(f"{status:8} {r.check}")
            if r.not_run:
                print(f"         {r.not_run}")
            for f in r.findings:
                print(f"         {f.line()}")
            for n in r.notes:
                print(f"         note: {n}")
        print(f"\n{len(results) - len(failed) - len(not_run)} passed, {len(failed)} failed, {len(not_run)} not run")
    return 1 if failed else (2 if not_run else 0)


def cmd_check(args) -> int:
    ctx = _context(args)
    ids = args.ids or [c for c in sorted(REGISTRY) if c != "CK-SELFTEST"]
    unknown = [i for i in ids if i not in REGISTRY]
    if unknown:
        print(f"unknown check(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    results = [run_check(i, ctx) for i in ids]
    code = _report(results, args.json)
    # A check that cannot run is a warning in Lite and a failure otherwise (docs/design/checks.md).
    try:
        lite = ctx.profile == "lite"
    except KitError:
        lite = False
    return 0 if code == 2 and lite else code


def cmd_doctor(args) -> int:
    ctx = _context(args)
    results = [run_check(i, ctx) for i in DOCTOR_CHECKS]
    code = _report(results, args.json)
    if not args.json:
        try:
            adapter = (ctx.kit().get("enforcement") or {}).get("adapter")
        except KitError:
            adapter = None
        print("\nWhat this means:")
        if adapter == "file":
            print("  - The file adapter is configured. Approvals are NOT bound to any identity. Use it for tests only.")
        if any(r.findings for r in results if r.check == "CK-ENFORCE-SETUP"):
            print("  - Until the items above are fixed, approver rules (GOV-6, GOV-7, GOV-16) are convention, not enforcement.")
        print("  - Identity binding protects only while the agent cannot use an approver's credentials.")
    return code


CONSTITUTION_EVIDENCE = [".specify/memory/constitution.md", f"{KIT_DIR}/constitution.map.yml"]


def _evidence_files(ctx: Context, spec: str, gate: str, explicit: list[str] | None) -> list[str]:
    base = f"specs/{spec}"
    if explicit:
        return sorted(explicit)
    import fnmatch
    if gate == "G0":
        version = (ctx.src.yaml(CONSTITUTION_EVIDENCE[1]) or {}).get("version") if ctx.src.exists(CONSTITUTION_EVIDENCE[1]) else None
        report = f"{KIT_DIR}/constitution/amendment-v{version}.md"
        return sorted(f for f in CONSTITUTION_EVIDENCE + [report] if ctx.src.exists(f))
    from .checks_gov import FAST_MERGED, lane
    patterns = list(DEFAULT_EVIDENCE.get(gate, []))
    if gate == "G4" and lane(ctx, spec) == "fast":  # the fast lane's one review covers what G1 to G3 would have
        for merged in FAST_MERGED:
            patterns += [p for p in DEFAULT_EVIDENCE.get(merged, []) if p not in patterns]
    present = ctx.src.files(base)
    out = []
    for pat in patterns:
        out += [p for p in present if fnmatch.fnmatch(p, f"{base}/{pat}")]
    return sorted(set(out))


def cmd_gate(args) -> int:
    ctx = _context(args)
    if args.gate not in GATES:
        print(f"{args.gate} is not a gate", file=sys.stderr)
        return 2
    from .checks_gov import lane, required_gates
    spec_lane = lane(ctx, args.spec)
    if args.gate != "G0" and args.gate not in required_gates(ctx, args.spec):
        why = (f"{args.gate} is folded into G4 on the fast lane" if spec_lane == "fast"
               else f"{args.gate} is not required by the {ctx.profile} profile")
        if args.json:
            print(json.dumps({"spec": args.spec, "gate": args.gate, "required": False, "lane": spec_lane, "status": why}, indent=2))
        else:
            print(f"Gate {args.gate} for {args.spec}: {why}")
        return 0
    files = _evidence_files(ctx, args.spec, args.gate, args.file)
    if not files:
        print(f"no evidence files found for {args.gate} of {args.spec}", file=sys.stderr)
        return 2
    digest = evidence_hash(ctx.src, args.spec, args.gate, files)
    rel = f"{KIT_DIR}/decisions/{args.spec}/{args.gate}.yml"
    record = ctx.src.yaml(rel) if ctx.src.exists(rel) else None
    state = "no decision recorded"
    if record:
        same = (record.get("evidence") or {}).get("hash") == digest
        state = f"{record.get('decision')} recorded" + ("" if same else " for DIFFERENT evidence (the files changed since)")
    info = {"spec": args.spec, "gate": args.gate, "evidence": files, "hash": digest, "status": state,
            "approved": bool(record and record.get("decision") in ("approve", "approve-with-conditions")
                             and (record.get("evidence") or {}).get("hash") == digest),
            "required_roles": gate_roles(ctx, args.gate, args.spec), "required": True, "lane": spec_lane,
            "paste": approval_line(args.gate, "approve", digest)}
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print(f"Gate {args.gate} for {args.spec}: {state}")
        print("Evidence:")
        for f in files:
            print(f"  {f}")
        print(f"Roles that must approve: {', '.join(info['required_roles'])}")
        print("\nTo approve, a person holding the role submits an approving review containing this line:\n")
        print(f"  {info['paste']}\n")
        print("To reject, request changes with `reject` in place of `approve`.")
    return 0


def cmd_record(args) -> int:
    """Mirror a review that already exists into a decision record. Does not create approval."""
    ctx = _context(args)
    if args.decision not in DECISIONS:
        print(f"decision must be one of {', '.join(DECISIONS)}", file=sys.stderr)
        return 2
    files = _evidence_files(ctx, args.spec, args.gate, args.file)
    digest = evidence_hash(ctx.src, args.spec, args.gate, files)
    approvals = []
    for item in args.approval:
        try:
            reviewer, role, ref = item.split(":", 2)
        except ValueError:
            print("--approval must be reviewer:role:pull/<n>#review-<id>", file=sys.stderr)
            return 2
        approvals.append({"reviewer": reviewer, "role": role, "review_ref": ref})
    entry = audit_append(ctx.src.root, args.spec, {"type": "kit", "id": "record"}, "gate.decision",
                         spec=args.spec, gate=args.gate, decision=args.decision, commit=args.commit, evidence=digest)
    record = {"schema": "agentic-decision/1", "spec": args.spec, "gate": args.gate, "decision": args.decision,
              "commit": args.commit, "evidence": {"hash": digest, "files": files}, "approvals": approvals,
              "single_approver_exception": bool(args.exception), "audit_head": entry["hash"]}
    from .checks_gov import lane
    if lane(ctx, args.spec) == "fast":
        record["lane"] = "fast"
    if args.gate == "G0" and ctx.src.exists(CONSTITUTION_EVIDENCE[1]):
        record["constitution_version"] = (ctx.src.yaml(CONSTITUTION_EVIDENCE[1]) or {}).get("version")
    if args.condition:
        record["conditions"] = args.condition
    path = ctx.src.root / KIT_DIR / "decisions" / args.spec / f"{args.gate}.yml"
    if path.is_file():  # a gate decided again (an amendment re-opened it): keep what the earlier decision was
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        record["superseded"] = list(old.get("superseded") or []) + [{
            "decision": old.get("decision"), "commit": old.get("commit"), "hash": (old.get("evidence") or {}).get("hash"),
            "approvals": old.get("approvals") or []}]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ctx.src.root).as_posix()}")
    print("This is a mirror. CK-APPROVER and CK-GATE-MIRROR decide whether the review behind it is valid.")
    return 0


def cmd_brief(args) -> int:
    from . import lanes
    ctx = _context(args)
    try:
        text = lanes.build_brief(ctx, args.spec, args.gate)
    except KitError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.write:
        path = ctx.src.root / lanes.brief_path(args.spec, args.gate)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {lanes.brief_path(args.spec, args.gate)}")
    else:
        print(text)
    return 0


def cmd_amend(args) -> int:
    from . import lanes
    ctx = _context(args)
    try:
        if args.action == "report":
            rel, text = lanes.amendment_report(ctx)
            if args.write:
                path = ctx.src.root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
                print(f"wrote {rel}")
            else:
                print(text)
            return 0
        specs = [args.spec] if args.spec else ctx.specs()
        rows = {s: lanes.reopened(ctx, s)[0] for s in specs}
    except KitError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for spec, gates in rows.items():
            if not gates:
                print(f"{spec}: nothing approved has changed")
            for gate, why in sorted(gates.items()):
                print(f"{spec}: {gate} is re-opened ({'; '.join(why)})")
    return 1 if any(rows.values()) else 0


def cmd_lane(args) -> int:
    from .checks_gov import lane, required_gates
    ctx = _context(args)
    for spec in ([args.spec] if args.spec else ctx.specs()):
        print(f"{spec}: {lane(ctx, spec)} lane; gates {', '.join(required_gates(ctx, spec))}")
    return 0


def cmd_trace(args) -> int:
    ctx = _context(args)
    specs = [args.spec] if args.spec else ctx.specs()
    bad = False
    for spec in specs:
        manifest = build_manifest(ctx, spec)
        bad |= not manifest["gate"]["ok"]
        if args.write:
            path = ctx.src.root / "specs" / spec / "trace-manifest.json"
            path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
            print(f"wrote specs/{spec}/trace-manifest.json")
        if args.json:
            print(json.dumps(manifest, indent=2))
        else:
            print(f"\n{spec}")
            print("| Requirement | Criterion | Tasks | Tests | State |")
            print("|---|---|---|---|---|")
            for r in manifest["rows"]:
                print(f"| {r['requirement']} | {r['criterion']} | {', '.join(r['tasks']) or '-'} | {len(r['tests'])} | {r['state']} |")
            for f in manifest["gate"]["failures"]:
                print(f"  FAIL {f}")
    return 1 if bad else 0


def cmd_suppressions(args) -> int:
    ctx = _context(args)
    found = adapters.find_suppressions(ctx)
    counts: dict[str, int] = {}
    for s in found:
        counts[s["rule"]] = counts.get(s["rule"], 0) + 1
    if args.baseline:
        doc = {"schema": "agentic-baseline/1", "approved_by": {"reviewer": "", "review_ref": ""},
               "groups": [{"rule": r, "count": n, "owner": "", "reason": "Existing at adoption", "expires": ""}
                          for r, n in sorted(counts.items())]}
        print(yaml.safe_dump(doc, sort_keys=False))
        print("# Fill in owner and expiry for each group, get it approved at a gate, then save it as "
              f"{KIT_DIR}/waivers/baseline.yml", file=sys.stderr)
    elif args.json:
        print(json.dumps(found, indent=2))
    else:
        for s in found:
            print(f"{s['rule']:18} {s['path']}:{s['line']}  {s['text']}")
        print("\n" + ", ".join(f"{r}: {n}" for r, n in sorted(counts.items())) if counts else "no suppressions found")
    return 0


def cmd_init(args) -> int:
    root = Path(args.root).resolve()
    if args.profile not in PROFILES:
        print(f"profile must be one of {', '.join(PROFILES)}", file=sys.stderr)
        return 2
    templates = Path(__file__).resolve().parents[2] / "templates"
    kit_dir = root / KIT_DIR
    kit_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in ("kit.yml", "roles.yml", "constitution.map.yml"):
        dest = kit_dir / name
        if dest.exists() and not args.force:
            continue
        text = (templates / name).read_text(encoding="utf-8")
        if name == "kit.yml":
            text = text.replace("__PROFILE__", args.profile).replace("__REPOSITORY__", args.repository or "owner/name")
            packs = ", ".join(args.pack or [])
            text = text.replace("__PACKS__", packs)
            text = text.replace("__HASH__", "false" if args.profile == "lite" else "true")
        dest.write_text(text, encoding="utf-8", newline="\n")
        written.append(dest)
    for pack in args.pack or []:
        source = root / ".specify" / "extensions" / f"agentic-{pack}" / "pack.yml"
        if not source.exists():
            print(f"domain pack {pack} is not installed (expected {source.relative_to(root).as_posix()})", file=sys.stderr)
            return 2
        dest = kit_dir / "packs" / f"{pack}.yml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        written.append(dest)
    ci = root / ".github" / "workflows" / "agentic-checks.yml"
    source = Path(__file__).resolve().parents[2] / "ci" / "agentic-checks.yml"
    if source.exists() and (not ci.exists() or args.force):
        ci.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, ci)
        written.append(ci)
    if not (kit_dir / "audit" / "kit.jsonl").exists():
        audit_append(root, "kit", {"type": "kit", "id": "init"}, "kit.init", profile=args.profile)
        written.append(kit_dir / "audit" / "kit.jsonl")
    for p in written:
        print(f"wrote {p.relative_to(root).as_posix()}")
    print("Next: list real people in roles.yml, add CODEOWNERS, then run `doctor`.")
    return 0


def cmd_audit(args) -> int:
    entry = audit_append(Path(args.root).resolve(), args.log, {"type": args.actor_type, "id": args.actor_id},
                         args.action, **({"spec": args.spec} if args.spec else {}), **({"commit": args.commit} if args.commit else {}))
    print(entry["hash"])
    return 0


def cmd_selftest(args) -> int:
    good, rows = selftest.run_selftest()
    if args.json:
        print(json.dumps({"ok": good, "rows": rows}, indent=2))
    else:
        for r in rows:
            mark = "ok  " if r["expected"] == r["actual"] else "BAD "
            print(f"{mark} {r['check']:20} broken: {r['fixture']}\n       -> {r['actual']}: {r['detail'][:150]}")
        print(f"\n{'all self-tests behaved as expected' if good else 'SELF-TEST FAILURE'} ({len(rows)} fixtures)")
    return 0 if good else 1


def cmd_list(args) -> int:
    for cid in sorted(REGISTRY):
        c = REGISTRY[cid]
        print(f"{cid:20} {', '.join(c.requirements):32} {'/'.join(c.profiles):26} {c.summary}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic", description=f"agentic-spec-kit {__version__}")
    p.add_argument("--root", default=".", help="repository root (default: current directory)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, base=True):
        sp.add_argument("--json", action="store_true")
        if base:
            sp.add_argument("--base-ref", help="git ref to read roles.yml and kit.yml from (the base branch in CI)")

    sp = sub.add_parser("check", help="run checks for the active profile"); common(sp)
    sp.add_argument("ids", nargs="*"); sp.add_argument("--today"); sp.add_argument("--changed-files")
    sp.set_defaults(fn=cmd_check)
    sp = sub.add_parser("doctor", help="report enforcement setup and what is not enforced"); common(sp); sp.set_defaults(fn=cmd_doctor)
    sp = sub.add_parser("gate", help="show a gate's evidence, hash and the line to paste"); common(sp)
    sp.add_argument("--spec", required=True); sp.add_argument("--gate", required=True); sp.add_argument("--file", action="append")
    sp.set_defaults(fn=cmd_gate)
    sp = sub.add_parser("record", help="mirror an existing review into a decision record"); common(sp)
    sp.add_argument("--spec", required=True); sp.add_argument("--gate", required=True, choices=GATES)
    sp.add_argument("--decision", required=True); sp.add_argument("--commit", required=True)
    sp.add_argument("--approval", action="append", required=True, help="reviewer:role:pull/<n>#review-<id>")
    sp.add_argument("--condition", action="append"); sp.add_argument("--exception", action="store_true")
    sp.add_argument("--file", action="append"); sp.set_defaults(fn=cmd_record)
    sp = sub.add_parser("brief", help="the one-page brief for the person at a gate"); common(sp)
    sp.add_argument("--spec", required=True); sp.add_argument("--gate", required=True, choices=GATES)
    sp.add_argument("--write", action="store_true"); sp.set_defaults(fn=cmd_brief)
    sp = sub.add_parser("amend", help="which gates a change re-opens; the constitution amendment report"); common(sp)
    sp.add_argument("action", choices=["status", "report"]); sp.add_argument("--spec")
    sp.add_argument("--write", action="store_true"); sp.set_defaults(fn=cmd_amend)
    sp = sub.add_parser("lane", help="the lane impact analysis puts each spec on, and the gates that follow"); common(sp)
    sp.add_argument("--spec"); sp.set_defaults(fn=cmd_lane)
    sp = sub.add_parser("trace", help="build the trace manifest and matrix"); common(sp)
    sp.add_argument("--spec"); sp.add_argument("--write", action="store_true"); sp.set_defaults(fn=cmd_trace)
    sp = sub.add_parser("suppressions", help="list detected suppressions or propose a baseline"); common(sp)
    sp.add_argument("--baseline", action="store_true"); sp.set_defaults(fn=cmd_suppressions)
    sp = sub.add_parser("init", help="write kit.yml, roles.yml, the constitution map and the CI workflow")
    sp.add_argument("--profile", required=True); sp.add_argument("--repository"); sp.add_argument("--pack", action="append")
    sp.add_argument("--force", action="store_true"); sp.set_defaults(fn=cmd_init)
    sp = sub.add_parser("audit", help="append an entry to an audit log")
    sp.add_argument("--log", required=True); sp.add_argument("--actor-type", required=True, choices=["human", "agent", "kit"])
    sp.add_argument("--actor-id", required=True); sp.add_argument("--action", required=True)
    sp.add_argument("--spec"); sp.add_argument("--commit"); sp.set_defaults(fn=cmd_audit)
    sp = sub.add_parser("selftest", help="prove every check fails on its broken fixture"); sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_selftest)
    sp = sub.add_parser("list", help="list checks"); sp.set_defaults(fn=cmd_list)

    from .core import CLI_HOOKS
    for hook in CLI_HOOKS:
        hook(sub, common)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except KitError as exc:
        print(f"cannot run: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
