"""Bindings to things outside the neutral rules: the enforcement channel and suppression patterns.

Enforcement adapter interface (GOV-6 to GOV-8, ADP-3):
    agent_identity() -> str | None     account the agent's own credential belongs to
    ci_identity() -> str | None        account CI runs as
    reviews(change) -> list[Review]    reviews on a change, e.g. change = "pull/12"
    authors(change) -> set[str]        accounts that authored the commits in the change
    setup_report() -> list[dict]       [{"item", "status": pass|fail|not-checkable, "detail"}]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass

from .core import KIT_DIR, Context, KitError, Source


@dataclass
class Review:
    id: str
    reviewer: str
    account_type: str  # "User" for a human account; anything else never counts
    state: str  # APPROVED | CHANGES_REQUESTED | COMMENTED | DISMISSED
    commit: str
    body: str

    @property
    def ref_suffix(self) -> str:
        return f"review-{self.id}"


class FileAdapter:
    """Reads reviews from a JSON file in the repo. For self-tests and offline demos only.

    It proves nothing about who approved: anyone who can write the repo can write the file.
    `doctor` reports that when this adapter is configured.
    """

    name = "file"
    PATH = f"{KIT_DIR}/_adapter/reviews.json"

    def __init__(self, src: Source):
        self.data = json.loads(src.read(self.PATH)) if src.exists(self.PATH) else {}

    def agent_identity(self):
        return self.data.get("agent_identity")

    def ci_identity(self):
        return self.data.get("ci_identity")

    def _change(self, change: str) -> dict:
        return (self.data.get("changes") or {}).get(change) or {}

    def reviews(self, change: str) -> list[Review]:
        return [Review(str(r["id"]), r["reviewer"], r.get("type", "User"), r.get("state", ""), r.get("commit", ""),
                       r.get("body", "")) for r in self._change(change).get("reviews", [])]

    def authors(self, change: str) -> set[str]:
        return {a.lower() for a in self._change(change).get("authors", [])}

    def setup_report(self) -> list[dict]:
        # A fixture may simulate a configured channel; `doctor` still says the file adapter proves nothing.
        return self.data.get("setup") or [{"item": "enforcement adapter", "status": "fail",
                                           "detail": "the file adapter is for tests only; no approval is bound to an identity"}]


class GitHubAdapter:
    """GitHub pull request reviews as the trust anchor, read through the `gh` CLI.

    Not exercised against a live repository in this slice's self-tests; its parsing is unit-tested
    with recorded responses.
    """

    name = "github"

    def __init__(self, repository: str | None, default_branch: str = "main", runner=None):
        self.repository = repository
        self.branch = default_branch
        self._run = runner or self._gh

    def _gh(self, path: str):
        if not shutil.which("gh"):
            raise KitError("the gh CLI is not installed, so the enforcement channel cannot be read")
        p = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True)
        if p.returncode:
            raise KitError(f"gh api {path} failed: {p.stderr.strip()[:200]}")
        return json.loads(p.stdout or "null")

    def _repo(self) -> str:
        if not self.repository:
            raise KitError("enforcement.repository is not set in kit.yml (owner/name)")
        return self.repository

    def agent_identity(self):
        try:
            return (self._run("user") or {}).get("login")
        except KitError:
            return None

    def ci_identity(self):
        return "github-actions[bot]"

    @staticmethod
    def _number(change: str) -> str:
        m = re.fullmatch(r"pull/([1-9][0-9]*)", change)
        if not m:
            raise KitError(f"change reference {change!r} is not of the form pull/<number>")
        return m.group(1)

    def reviews(self, change: str) -> list[Review]:
        rows = self._run(f"repos/{self._repo()}/pulls/{self._number(change)}/reviews") or []
        return [Review(str(r.get("id")), (r.get("user") or {}).get("login", ""), (r.get("user") or {}).get("type", ""),
                       r.get("state", ""), r.get("commit_id", ""), r.get("body") or "") for r in rows]

    def authors(self, change: str) -> set[str]:
        rows = self._run(f"repos/{self._repo()}/pulls/{self._number(change)}/commits") or []
        return {(r.get("author") or {}).get("login", "").lower() for r in rows if (r.get("author") or {}).get("login")}

    def setup_report(self) -> list[dict]:
        out = []
        try:
            prot = self._run(f"repos/{self._repo()}/branches/{self.branch}/protection") or {}
        except KitError as exc:
            return [{"item": "branch protection", "status": "not-checkable", "detail": str(exc)}]
        reviews = prot.get("required_pull_request_reviews") or {}
        out.append({"item": "pull request reviews required",
                    "status": "pass" if reviews.get("required_approving_review_count", 0) >= 1 else "fail",
                    "detail": f"required approvals: {reviews.get('required_approving_review_count', 0)}"})
        out.append({"item": "code owner review required",
                    "status": "pass" if reviews.get("require_code_owner_reviews") else "fail", "detail": ""})
        contexts = ((prot.get("required_status_checks") or {}).get("contexts")) or []
        out.append({"item": "agentic-checks is a required status check",
                    "status": "pass" if any("agentic" in c for c in contexts) else "fail", "detail": ", ".join(contexts)})
        out.append({"item": "administrators are not exempt",
                    "status": "pass" if (prot.get("enforce_admins") or {}).get("enabled") else "fail", "detail": ""})
        return out


def enforcement(ctx: Context):
    cfg = ctx.kit().get("enforcement") or {}
    name = cfg.get("adapter")
    if name == "file":
        return FileAdapter(ctx.src)
    if name == "github":
        return GitHubAdapter(cfg.get("repository"), cfg.get("default_branch", "main"))
    raise KitError(f"unknown enforcement adapter {name!r} in kit.yml")


# ── suppression detection (GOV-15) ──────────────────────────────────────────────

#: rule id -> (path globs, regex). Projects extend or replace these in kit.yml under `suppressions:`.
DEFAULT_SUPPRESSIONS = {
    "ci-escape": ([".github/workflows/*", ".gitlab-ci.yml", "azure-pipelines*.yml"],
                  r"continue-on-error:\s*true|\|\|\s*true\b"),
    "test-skip": (["*.ts", "*.tsx", "*.js", "*.jsx", "*.cs", "*.py", "*.java", "*.go"],
                  r"\b(?:test|it|describe)\.skip\(|\bx(?:it|describe)\(|\[(?:Fact|Theory)\([^\]]*Skip\s*=|@pytest\.mark\.skip|@Disabled\b|\bt\.Skip\("),
    "lint-disable": (["*.ts", "*.tsx", "*.js", "*.jsx", "*.cs", "*.py"],
                     r"eslint-disable|#pragma\s+warning\s+disable|#\s*noqa|#\s*type:\s*ignore"),
    "advisory-suppress": (["*.props", "*.csproj", ".npmrc", "*.yml", "*.yaml"],
                          r"NuGetAuditSuppress|audit-level\s*=\s*none|--ignore-vuln"),
}


#: Installed tooling and dependencies are not the project's own code. Override with `suppression_exclude:` in kit.yml.
DEFAULT_EXCLUDE = [".specify/*", ".claude/*", ".github/skills/*", ".github/agents/*", "node_modules/*", "vendor/*",
                   "specs/*", "*.min.js", "*.map"]


def find_suppressions(ctx: Context) -> list[dict]:
    """Every suppression in the tree, plus findings from sibling extensions. Computed once per context."""
    cached = getattr(ctx, "_suppressions", None)
    if cached is None:
        cached = _find_suppressions(ctx)
        ctx._suppressions = cached
    return cached


def _find_suppressions(ctx: Context) -> list[dict]:
    rules = dict(DEFAULT_SUPPRESSIONS)
    exclude = list(ctx.kit().get("suppression_exclude") or DEFAULT_EXCLUDE)
    for rid, spec in (ctx.kit().get("suppressions") or {}).items():
        if spec is None:
            rules.pop(rid, None)
        else:
            rules[rid] = (list(spec.get("paths", [])), spec.get("pattern", ""))
    compiled = {rid: (globs, re.compile(pat)) for rid, (globs, pat) in rules.items() if pat}
    import fnmatch
    found = []
    for rel in ctx.src.files():
        if any(fnmatch.fnmatch(rel, g) for g in exclude):
            continue
        name = rel.rsplit("/", 1)[-1]
        todo = [(rid, rx) for rid, (globs, rx) in compiled.items()
                if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g) for g in globs)]
        if not todo:
            continue
        try:
            text = ctx.src.read(rel)
        except (OSError, KitError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for rid, rx in todo:
                if rx.search(line):
                    found.append({"rule": rid, "path": rel, "line": n, "text": line.strip()[:160]})
    from .core import FINDER_HOOKS
    for hook in FINDER_HOOKS:
        found += [f for f in hook(ctx) if not any(fnmatch.fnmatch(f["path"], g) for g in exclude)]
    return found
