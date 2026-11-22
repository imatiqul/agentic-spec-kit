"""Shared plumbing: file access, configuration, findings, the check registry, evidence hashing and the audit log.

Nothing here talks to the network. Checks are pure functions of files, plus one adapter call for approval checks.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

KIT_DIR = ".specify/agentic"
PROFILES = ("lite", "standard", "regulated")
GATES = ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7")
#: Gates each profile requires for a spec (G0 belongs to the constitution, not to a spec).
PROFILE_GATES = {
    "lite": ("G1", "G3", "G5"),
    "standard": ("G1", "G2", "G3", "G4", "G5", "G6", "G7"),
    "regulated": ("G1", "G2", "G3", "G4", "G5", "G6", "G7"),
}
TIERS = ("low", "medium", "high", "critical")
DECISIONS = ("approve", "reject", "approve-with-conditions")


class KitError(Exception):
    """A problem with inputs that stops a check from running at all."""


class Source:
    """Reads repository files either from the working tree or from a git ref.

    Trust-sensitive files (roles, kit config) are read from the base branch in CI so that a
    pull request cannot relax them by editing its own copy.
    """

    def __init__(self, root: str | Path, ref: str | None = None):
        self.root = Path(root).resolve()
        self.ref = ref

    def at(self, ref: str | None) -> "Source":
        return Source(self.root, ref)

    def _git(self, *args: str) -> str:
        p = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True)
        if p.returncode:
            raise KitError(f"git {' '.join(args)} failed: {p.stderr.decode(errors='replace').strip()}")
        return p.stdout.decode("utf-8", errors="replace")

    def exists(self, rel: str) -> bool:
        if self.ref is None:
            return (self.root / rel).is_file()
        p = subprocess.run(["git", "-C", str(self.root), "cat-file", "-e", f"{self.ref}:{rel}"], capture_output=True)
        return p.returncode == 0

    def read_bytes(self, rel: str) -> bytes:
        if self.ref is None:
            return (self.root / rel).read_bytes()
        p = subprocess.run(["git", "-C", str(self.root), "show", f"{self.ref}:{rel}"], capture_output=True)
        if p.returncode:
            raise KitError(f"{rel} not found at {self.ref}")
        return p.stdout

    def read(self, rel: str) -> str:
        return self.read_bytes(rel).decode("utf-8-sig", errors="replace")

    def files(self, under: str = "") -> list[str]:
        """Repository-relative paths of regular files, '/'-separated, sorted."""
        if self.ref is None:
            base = self.root / under if under else self.root
            if not base.exists():
                return []
            out = []
            for p in base.rglob("*"):
                rel = p.relative_to(self.root).as_posix()
                if p.is_file() and not rel.startswith(".git/") and "/node_modules/" not in f"/{rel}":
                    out.append(rel)
            return sorted(out)
        listing = self._git("ls-tree", "-r", "--name-only", self.ref, "--", under or ".")
        return sorted(x for x in listing.splitlines() if x)

    def yaml(self, rel: str) -> Any:
        try:
            return yaml.safe_load(self.read(rel))
        except yaml.YAMLError as exc:
            raise KitError(f"{rel} is not valid YAML: {exc}") from exc


@dataclass
class Finding:
    check: str
    message: str
    path: str = ""

    def line(self) -> str:
        return f"{self.check}: {self.message}" + (f" [{self.path}]" if self.path else "")


@dataclass
class Result:
    check: str
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    not_run: str | None = None  # reason, when the check could not run

    @property
    def ok(self) -> bool:
        return not self.findings and self.not_run is None

    def fail(self, message: str, path: str = "") -> None:
        self.findings.append(Finding(self.check, message, path))

    def as_dict(self) -> dict:
        return {"check": self.check, "ok": self.ok, "not_run": self.not_run,
                "findings": [f.line() for f in self.findings], "notes": self.notes}


@dataclass
class Context:
    src: Source  # the change under review (working tree, or the PR head in CI)
    trusted: Source  # where trust-sensitive files are read from (the base branch in CI)
    options: dict[str, Any] = field(default_factory=dict)
    _kit: dict | None = None

    def kit(self) -> dict:
        if self._kit is None:
            path = f"{KIT_DIR}/kit.yml"
            holder = self.trusted if self.trusted.exists(path) else self.src
            if not holder.exists(path):
                raise KitError(f"{path} is missing; run the init command")
            data = holder.yaml(path)
            if not isinstance(data, dict):
                raise KitError(f"{path} must be a mapping")
            self._kit = data
        return self._kit

    @property
    def profile(self) -> str:
        return str(self.kit().get("profile", ""))

    def roles(self) -> dict:
        path = f"{KIT_DIR}/roles.yml"
        holder = self.trusted if self.trusted.exists(path) else self.src
        if not holder.exists(path):
            raise KitError(f"{path} is missing")
        data = holder.yaml(path)
        if not isinstance(data, dict):
            raise KitError(f"{path} must be a mapping")
        return data

    def specs(self) -> list[str]:
        """Spec ids: directories under specs/ that contain spec.md."""
        return sorted({p.split("/")[1] for p in self.src.files("specs") if p.count("/") >= 2 and p.endswith("/spec.md")})


@dataclass
class Check:
    id: str
    requirements: tuple[str, ...]
    profiles: tuple[str, ...]
    summary: str
    run: Callable[[Context, Result], None]


REGISTRY: dict[str, Check] = {}

# Extension points for sibling extensions (agentic-system, agentic-team). Each is a list of callables.
ROLE_HOOKS: list = []      # (ctx, spec, gate) -> extra roles that must approve
MANIFEST_HOOKS: list = []  # (ctx, spec, manifest) -> None; may add fields to the trace manifest
CLI_HOOKS: list = []       # (subparsers) -> None; adds commands
SAMPLE_HOOKS: list = []    # (root) -> None; extends the self-test sample project before decisions are written
FIXTURE_HOOKS: list = []   # () -> dict of extra self-test fixtures
FINDER_HOOKS: list = []    # (ctx) -> list of {rule, path, line, text}: findings that waivers and the baseline can cover
RULE_OWNERS: dict[str, str] = {}  # suppression rule id -> check id that reports it (default CK-WAIVER)


def load_plugins(launcher_dir: Path) -> list[str]:
    """Import agentic_kit_* packages from sibling extensions so their checks and commands register.

    Layout, both in this repository and when installed: <extensions>/<id>/scripts/<package>/.
    """
    import importlib
    import sys
    loaded = []
    extensions = launcher_dir.parent.parent
    for scripts in sorted(extensions.glob("agentic-*/scripts")):
        for pkg in sorted(scripts.glob("agentic_kit_*/__init__.py")):
            if str(scripts) not in sys.path:
                sys.path.insert(0, str(scripts))
            importlib.import_module(pkg.parent.name)
            loaded.append(pkg.parent.name)
    return loaded


def check(id: str, requirements: tuple[str, ...], summary: str, profiles: tuple[str, ...] = PROFILES):
    def wrap(fn: Callable[[Context, Result], None]):
        REGISTRY[id] = Check(id, requirements, profiles, summary, fn)
        return fn
    return wrap


def run_check(id: str, ctx: Context) -> Result:
    chk = REGISTRY[id]
    res = Result(id)
    try:
        if id != "CK-PROFILE" and ctx.profile in PROFILES and ctx.profile not in chk.profiles:
            res.notes.append(f"skipped: not required by the {ctx.profile} profile")
            return res
        chk.run(ctx, res)
    except KitError as exc:
        res.not_run = str(exc)
    return res


# ── front matter ────────────────────────────────────────────────────────────────

_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)


def front_matter(text: str) -> dict:
    m = _FM.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        raise KitError(f"front matter is not valid YAML: {exc}") from exc
    return data if isinstance(data, dict) else {}


# ── evidence hash (TRC-18) ──────────────────────────────────────────────────────

def evidence_hash(src: Source, spec: str, gate: str, files: list[str]) -> str:
    """sha256 over the spec id, the gate id and each evidence file's path and content hash.

    Paths are sorted, so the order in a decision record does not matter. A missing file raises:
    an approval must never be bound to something that is not there.
    """
    h = hashlib.sha256()
    h.update(b"agentic-evidence/1\n" + spec.encode() + b"\n" + gate.encode() + b"\n")
    for rel in sorted(set(files)):
        if not src.exists(rel):
            raise KitError(f"evidence file {rel} does not exist")
        h.update(rel.encode() + b"\0" + hashlib.sha256(src.read_bytes(rel)).hexdigest().encode() + b"\n")
    return "sha256:" + h.hexdigest()


def approval_line(gate: str, decision: str, digest: str) -> str:
    """The line a reviewer pastes into their review."""
    return f"gate {gate} {decision} {digest}"


_LINE = re.compile(r"^\s*gate\s+(G[0-7])\s+(approve|reject|approve-with-conditions)\s+(sha256:[0-9a-f]{64})\s*$", re.M)


def parse_approval_lines(body: str) -> list[tuple[str, str, str]]:
    return _LINE.findall(body or "")


# ── audit log (TRC-5 to TRC-7) ──────────────────────────────────────────────────

GENESIS = "sha256:" + "0" * 64


def entry_hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def audit_append(root: Path, log: str, actor: dict, action: str, **fields: Any) -> dict:
    """Append one entry to .specify/agentic/audit/<log>.jsonl and return it."""
    import datetime
    path = Path(root) / KIT_DIR / "audit" / f"{log}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    prev, seq = GENESIS, 0
    if path.exists():
        lines = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        if lines:
            last = json.loads(lines[-1])
            prev, seq = last["hash"], int(last["seq"])
    entry = {"seq": seq + 1, "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "actor": actor, "action": action, **fields, "prev": prev}
    entry["hash"] = entry_hash(entry)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
    return entry


def match_any(path: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path, g.rstrip("/") + "/*") for g in globs)
