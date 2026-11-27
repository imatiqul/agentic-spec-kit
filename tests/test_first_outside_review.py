"""Tests for docs/design/first-outside-review.md (REV-1 to REV-12): what the first review from outside found.

One test opens connections, to two servers that it starts on this machine itself. Nothing else leaves the machine:
the trackers and the chat services are a scripted transport, and the mail server is a stand-in.
Run: python -m pytest tests/test_first_outside_review.py -q
"""
import http.server
import io
import json
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentic_kit import core, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

import agentic_kit_connect as connect  # noqa: E402
from agentic_kit_connect import sample as csample  # noqa: E402
from agentic_kit_connect.transport import Http, Recorded  # noqa: E402
from agentic_kit_team import tools  # noqa: E402

import test_connect as tc  # noqa: E402  (its stand-ins: the secrets' names, the mail server, a review added to the sample)

SPEC = selftest.SPEC
CONNECT_CI = ROOT / "extensions" / "agentic-connect" / "ci"
TEAM = ROOT / "extensions" / "agentic-team"
ZEROS = "0" * 40
SAME_REPOSITORY = "github.event.workflow_run.head_repository.full_name == github.repository"
DEFAULT_BRANCH_ONLY = "github.ref_name == github.event.repository.default_branch"


def fresh(tmp_path, name="sample"):
    root = tmp_path / name
    root.mkdir()
    selftest.build_sample(root)
    return root


@pytest.fixture()
def sample(tmp_path):
    return fresh(tmp_path)


@pytest.fixture()
def seams():
    yield
    connect.TRANSPORT = connect.SMTP = connect.ENV = None


def committed(root, without=()):
    """Make the sample a repository whose one commit, the base branch, lacks the files named. They are put back after it."""
    kept = {rel: (root / rel).read_bytes() for rel in without}
    for rel in kept:
        (root / rel).unlink()
    tc.git(root, "init", "-q")
    tc.git(root, "add", "-A")
    tc.git(root, "commit", "-qm", "the base branch")
    for rel, body in kept.items():
        (root / rel).write_bytes(body)


def reviewed(root):
    """The change as a pipeline reads it: the files as they are, and the trusted ones from the base branch."""
    src = core.Source(root)
    return core.Context(src, src.at("HEAD"), {"today": selftest.TODAY})


def msgs(result):
    return " | ".join(finding.message for finding in result.findings)


def cli(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--root", str(root), *args])
    return code, out.getvalue() + err.getvalue()


def rewrite(path, change):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix in (".yml", ".yaml") else json.loads(path.read_text(encoding="utf-8"))
    change(data)
    text = yaml.safe_dump(data, sort_keys=False) if path.suffix in (".yml", ".yaml") else json.dumps(data)
    path.write_text(text, encoding="utf-8", newline="\n")


# ── REV-1: a redirect takes no header to another address ────────────────────────

class _Service(http.server.BaseHTTPRequestHandler):
    """Answers /moved with a redirect to wherever the test says, and any other path with that path. Keeps what it was asked."""
    seen: list = []
    target = ""

    def do_GET(self):  # noqa: N802 - the name http.server calls
        self.seen.append((self.path, self.headers.get("Authorization")))
        body = b"" if self.path == "/moved" else json.dumps({"path": self.path}).encode("utf-8")
        self.send_response(302 if self.path == "/moved" else 200)
        if self.path == "/moved":
            self.send_header("Location", self.target)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture()
def two_services():
    servers = []
    for _ in range(2):
        server = http.server.HTTPServer(("127.0.0.1", 0), type("Service", (_Service,), {"seen": [], "target": ""}))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
    yield servers
    for server in servers:
        server.shutdown()
        server.server_close()


def test_AC_001_a_redirect_to_another_address_is_not_followed_and_takes_no_header_there(two_services):
    first, second = two_services
    asked, there = first.RequestHandlerClass, second.RequestHandlerClass
    header = {"Authorization": "Bearer not-a-real-token"}
    for host in ("localhost", "127.0.0.1"):  # another host name; and the same host on another port, which is another origin too
        asked.target = f"http://{host}:{second.server_port}/elsewhere"
        answer = Http(timeout=5, attempts=1).request("GET", f"http://127.0.0.1:{first.server_port}/moved", headers=header)
        assert there.seen == [], f"the address the service pointed to was asked, and was sent {there.seen[0][1]!r}"
        assert answer.status == 302 and host in answer.text and "not followed" in answer.text
    asked.target = "/here"  # the same origin: followed, and the header goes along, as before
    answer = Http(timeout=5, attempts=1).request("GET", f"http://127.0.0.1:{first.server_port}/moved", headers=header)
    assert answer.status == 200 and answer.json() == {"path": "/here"}
    assert asked.seen[-1] == ("/here", "Bearer not-a-real-token") and there.seen == []


# ── REV-2: what sends reads connect.yml from the base branch alone ──────────────

def test_AC_002_where_the_base_branch_has_no_connect_yml_nothing_is_sent_with_the_one_a_change_brings(tmp_path, seams):
    sample = fresh(tmp_path, "new")
    committed(sample, without=[csample.CONNECT])
    connect.TRANSPORT, connect.ENV, connect.SMTP = Recorded(), tc.ENV, tc.FakeSMTP  # every secret is set; a request of any kind fails the test
    tc.FakeSMTP.sent = []
    summary = tmp_path / "summary.md"
    code, out = cli(sample, "connect", "notify", "--base-ref", "HEAD", "--summary", str(summary))
    said = f"{csample.CONNECT} is not on HEAD"
    assert code == 0 and said in out and said in summary.read_text(encoding="utf-8"), out
    assert " to teams: " not in out and " to mail: " not in out and connect.TRANSPORT.calls == [] and tc.FakeSMTP.sent == []
    code, out = cli(sample, "connect", "run", "--notify", "--base-ref", "HEAD", "--json")
    assert said in json.loads(out)["not_sent"] and connect.TRANSPORT.calls == [] and tc.FakeSMTP.sent == []
    code, out = cli(sample, "connect", "fetch", "--base-ref", "HEAD")
    assert code == 2 and said in out and connect.TRANSPORT.calls == [], out
    assert core.run_check("CK-CONNECT-CONFIG", reviewed(sample)).ok, "the checks still read the file the change brings"

    there = fresh(tmp_path, "merged")  # the same file, already on the base branch: sent as before
    committed(there)
    teams = tc.ENV["TEAMS_WEBHOOK_URL"]
    connect.TRANSPORT = Recorded([("POST", teams, (202, "")), ("POST", teams, (202, ""))])
    code, out = cli(there, "connect", "notify", "--base-ref", "HEAD")
    assert code == 0 and "deadline to teams: sent" in out and "deadline to mail: sent" in out and "is not on HEAD" not in out, out
    assert connect.TRANSPORT.script == [] and len(tc.FakeSMTP.sent) == 2


# ── REV-3, REV-4: the template for GitHub Actions ───────────────────────────────

def test_AC_003_the_intake_job_runs_on_the_default_branch_only_and_the_file_says_what_holds_on_github():
    text = (CONNECT_CI / "github-actions.yml").read_text(encoding="utf-8")
    intake = yaml.safe_load(text)["jobs"]["intake"]["if"]
    assert DEFAULT_BRANCH_ONLY in intake and "'schedule'" in intake and "'workflow_dispatch'" in intake
    head = text.split("\nname:")[0]
    assert "`schedule` and `workflow_dispatch` run on the default branch" not in head
    assert "environment" in head and "the person who starts it chooses" in head
    assert "environment" in (ROOT / "docs" / "adapters" / "pipeline.md").read_text(encoding="utf-8")


def test_AC_004_notify_and_mirror_run_only_for_a_run_that_came_from_this_repository():
    text = (CONNECT_CI / "github-actions.yml").read_text(encoding="utf-8")
    jobs = yaml.safe_load(text)["jobs"]
    for job in ("notify", "mirror"):
        assert SAME_REPOSITORY in jobs[job]["if"] and "'workflow_run'" in jobs[job]["if"], job
    assert "allow-unsafe-pr-checkout" in text and "gh.io/securely-using-pull_request_target" in text
    assert not any("allow-unsafe-pr-checkout" in (step.get("with") or {}) for job in jobs.values() for step in job["steps"]), "the template does not set it"


# ── REV-5, REV-6: the tool allowlist ────────────────────────────────────────────

def test_AC_005_a_server_and_the_allowlist_that_approves_it_cannot_arrive_in_one_change(tmp_path):
    both = fresh(tmp_path, "both")
    committed(both, without=[".mcp.json", tools.TOOLS])
    said = msgs(core.run_check("CK-TOOL-ALLOWLIST", reviewed(both)))
    assert "MCP server 'docs'" in said and "arrive in the same change" in said and "merge the allowlist first" in said

    listed = fresh(tmp_path, "listed")  # the server is on the base branch already; the change brings only the allowlist
    committed(listed, without=[tools.TOOLS])
    result = core.run_check("CK-TOOL-ALLOWLIST", reviewed(listed))
    assert result.ok, msgs(result)

    def other_release(data):
        for body in (data.get("mcpServers") or {}).values():
            body["args"] = ["-y", "@example/docs-mcp@1.4.3"]
        for entry in data.get("mcp_servers") or []:
            entry["args"] = ["-y", "@example/docs-mcp@1.4.3"]
    rewrite(listed / ".mcp.json", other_release)   # the launch changes together with the entry that approves the new one
    rewrite(listed / tools.TOOLS, other_release)
    assert "arrive in the same change" in msgs(core.run_check("CK-TOOL-ALLOWLIST", reviewed(listed)))

    assert core.run_check("CK-TOOL-ALLOWLIST", selftest.context(fresh(tmp_path, "local"))).ok, "with no base branch nothing changes"

    install = fresh(tmp_path, "install")  # the change that installs the kit: the base branch has the server and no kit.yml
    committed(install, without=[tools.TOOLS, f"{core.KIT_DIR}/kit.yml"])
    result = core.run_check("CK-TOOL-ALLOWLIST", reviewed(install))
    assert result.ok, msgs(result)


@pytest.mark.parametrize("runner", ["npx", "bunx", "pnpx", "/usr/local/bin/npx"])
def test_AC_006_for_npm_an_exact_version_has_three_numbers(runner):
    for loose in ("docs-mcp@1", "docs-mcp@1.2", "docs-mcp@1.x", "@example/docs-mcp@2", "docs-mcp@1.2.x"):
        assert tools.unpinned(runner, ["-y", loose]) == f"{loose} names no exact version", loose
    for exact in ("docs-mcp@1.4.2", "@example/docs-mcp@2.0.0-rc.1", "docs-mcp@2025.4.8", "docs-mcp@1.0.0+build.5"):
        assert tools.unpinned(runner, ["-y", exact]) is None, exact


def test_AC_006_for_uvx_and_pipx_the_rule_is_as_it_was():
    for runner in ("uvx", "pipx"):
        assert tools.unpinned(runner, ["docs-mcp@0.9"]) is None and tools.unpinned(runner, ["docs-mcp==0.9"]) is None
        assert tools.unpinned(runner, ["docs-mcp"]) == "docs-mcp names no exact version"


# ── REV-7: a production check is dated after the release and not after today ────

def test_AC_007_a_production_check_dated_after_today_or_before_the_release_fails(sample):
    checks = sample / f"specs/{SPEC}/release/production-checks.yml"
    audit = sample / core.KIT_DIR / f"audit/{SPEC}.jsonl"

    def dated(day):
        checks.write_text(f"checks:\n  - {{criterion: AC-001, result: pass, checked_by: bob, date: {day}}}\n", encoding="utf-8", newline="\n")
        return core.run_check("CK-POST-RELEASE", selftest.context(sample))

    assert selftest.TODAY == "2026-11-21"
    assert dated("2026-11-19").ok, "no release is on record yet, so there is nothing to compare the day with"
    assert "is dated 2026-11-22, which is after today (2026-11-21)" in msgs(dated("2026-11-22"))
    with audit.open("a", encoding="utf-8", newline="\n") as log:
        log.write(json.dumps({"action": "gate.decision", "gate": "G7", "decision": "approve", "at": "2026-11-20T09:00:00Z"}) + "\n")
    said = msgs(dated("2026-11-19"))
    assert "is dated 2026-11-19, before the release on 2026-11-20" in said
    assert dated("2026-11-20").ok and dated("2026-11-21").ok
    assert "after today" in msgs(dated("2026-11-22"))


# ── REV-8, REV-9: what the pipeline mirrors ─────────────────────────────────────

def _record(sample):
    return sample / core.KIT_DIR / f"decisions/{SPEC}/G6.yml"


def test_AC_008_a_review_that_approves_with_conditions_is_not_mirrored(sample):
    digest = tc._open_g6(sample)
    tc._review(sample, id="94", reviewer="bob", state="APPROVED", body="With one condition.\n" + core.approval_line("G6", "approve-with-conditions", digest))
    code, out = cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")
    assert code == 0 and not _record(sample).exists(), out
    assert f"{SPEC} G6: approve-with-conditions - not recorded" in out and "--condition" in out and "record --spec" in out
    code, out = cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--json")
    (row,) = json.loads(out[out.index("["):])
    assert row["written"] is False and "--condition" in row["note"]


def test_AC_009_a_reviewer_who_also_wrote_the_change_is_mirrored_with_the_exception_where_the_project_allows_it(tmp_path):
    def also_wrote(data):
        data["changes"]["pull/1"]["authors"].append("Bob")

    allowed = fresh(tmp_path, "allowed")
    digest = tc._open_g6(allowed)
    rewrite(allowed / core.KIT_DIR / "_adapter/reviews.json", also_wrote)
    tc._review(allowed, id="95", reviewer="bob", state="APPROVED", body=core.approval_line("G6", "approve", digest))
    code, out = cli(allowed, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")
    assert code == 0 and "recorded" in out and "single-approver exception" in out, out
    assert yaml.safe_load(_record(allowed).read_text(encoding="utf-8"))["single_approver_exception"] is True
    for cid in ("CK-APPROVER", "CK-GATE-RECORD", "CK-GATE-MIRROR"):  # the sample's older records by bob now lack the exception; G6 is the one mirrored here
        about_g6 = [f.message for f in core.run_check(cid, selftest.context(allowed)).findings if str(f.path).endswith("G6.yml")]
        assert about_g6 == [], cid

    forbidden = fresh(tmp_path, "forbidden")
    rewrite(forbidden / core.KIT_DIR / "kit.yml", lambda data: data["gates"].update(single_approver_exception="forbidden"))
    digest = tc._open_g6(forbidden)
    rewrite(forbidden / core.KIT_DIR / "_adapter/reviews.json", also_wrote)
    tc._review(forbidden, id="96", reviewer="bob", state="APPROVED", body=core.approval_line("G6", "approve", digest))
    code, out = cli(forbidden, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")
    assert code == 0 and not _record(forbidden).exists(), out
    assert "not recorded" in out and "bob wrote this change" in out and "forbids" in out

    other = fresh(tmp_path, "other")  # a reviewer who did not write the change: recorded without the exception, as before
    digest = tc._open_g6(other)
    tc._review(other, id="97", reviewer="bob", state="APPROVED", body=core.approval_line("G6", "approve", digest))
    assert "recorded" in cli(other, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")[1]
    assert yaml.safe_load(_record(other).read_text(encoding="utf-8"))["single_approver_exception"] is False


# ── REV-10, REV-11: what the agents are told ────────────────────────────────────

def test_AC_010_the_independent_verifier_reads_the_input_list_of_the_gate_it_reviews(sample):
    code, out = cli(sample, "team", "brief", "--agent", "independent-verifier", "--spec", SPEC)
    assert code == 0 and "verification/<gate>-inputs.yml" in out and "G6-inputs.yml" not in out, out
    definition = yaml.safe_load((TEAM / "agents" / "independent-verifier.yml").read_text(encoding="utf-8"))
    assert not any("G6" in str(line) for line in definition["inputs"])


def test_AC_011_in_lite_the_spec_author_writes_the_plan_and_the_tasks():
    rows = {line.split("|")[1].strip(): line for line in (TEAM / "commands" / "orchestrate.md").read_text(encoding="utf-8").splitlines()
            if line.lstrip().startswith("|") and line.count("|") >= 5}
    for stage in ("plan", "tasks"):
        authors = rows[stage].split("|")[2]
        assert "architect" in authors and "spec-author" in authors and "Lite" in authors, rows[stage]
    role = next(line for line in (TEAM / "commands" / "role.md").read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("| spec-author"))
    assert "Lite" in role and "/speckit.plan" in role and "/speckit.tasks" in role
    lite = yaml.safe_load((TEAM / "agents" / "spec-author.yml").read_text(encoding="utf-8"))["overrides"]["lite"]["write_paths"]
    assert {"specs/*/plan.md", "specs/*/tasks.md"} <= set(lite), "the two commands now say what the definition already allowed"


# ── REV-12: a build of the default branch is compared with the commit before it ─

def test_AC_012_the_gitlab_and_azure_files_compare_the_default_branch_with_the_commit_before():
    text = (CONNECT_CI / "gitlab-ci.yml").read_text(encoding="utf-8")
    flow = yaml.safe_load(text)
    checks = "\n".join(flow["agentic-checks"]["script"])
    assert "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME" in checks and "$CI_COMMIT_BEFORE_SHA" in checks and ZEROS in checks
    assert '--base-ref "origin/$CI_DEFAULT_BRANCH"' not in text
    assert ZEROS in "\n".join(flow["agentic-notify"]["script"]), "the notify job is given no base either where GitLab names none"

    azure = (CONNECT_CI / "azure-pipelines.yml").read_text(encoding="utf-8")
    steps = yaml.safe_load(azure)["stages"][0]["jobs"][0]["steps"]
    run = next(step["script"] for step in steps if "connect run" in str(step.get("script")))
    assert "HEAD~1" in run and "Build.SourceBranch" in run and "origin/main" in run
