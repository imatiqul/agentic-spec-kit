"""Unit tests for the connect extension (slice 0.6). No test here opens a network connection:
adapters are given a scripted transport, and the mail server is a stand-in.
Run: python -m pytest tests/test_connect.py -q"""
import base64
import io
import json
import subprocess
import sys
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, selftest  # noqa: E402
from agentic_kit.__main__ import _evidence_files, main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

import agentic_kit_connect as connect  # noqa: E402
from agentic_kit_connect import checks, notify, pipeline, trackers, transport  # noqa: E402
from agentic_kit_connect import sample as csample  # noqa: E402
from agentic_kit_connect.transport import Recorded, Response  # noqa: E402
from agentic_kit_product import intake  # noqa: E402

SPEC = selftest.SPEC
ENV = {"JIRA_USER": "kit@example.com", "JIRA_TOKEN": "jira-token-value", "ADO_TOKEN": "ado-token-value", "CLICKUP_TOKEN": "pk_clickup_value",
       "TRACKER_GITHUB_TOKEN": "gh-token-value", "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T1/B1/slack-secret-path",
       "TEAMS_WEBHOOK_URL": "https://example.powerplatform.com/workflows/abc/triggers/manual/paths/invoke?sig=teams-secret",
       "SMTP_HOST": "smtp.example.com", "SMTP_USER": "mailer", "SMTP_PASSWORD": "smtp-password-value"}
JIRA = "https://example.atlassian.net"
ADO = "https://dev.azure.com/example/Demo"
SECRET_TEXT = "As a user I want to be greeted by name"   # words from the sample intake record's body
# Made-up values in the shape of real credentials, joined here so that no file in the repository holds one whole.
FAKE_SLACK_HOOK = "https://hooks.slack.com/" + "services/T0000000/B0000000/" + "abcdefghijklmnop"
FAKE_GITHUB_TOKEN = "ghp_" + "abcdefghijklmnopqrstuvwxyz0123456789"
FAKE_SLACK_TOKEN = "xoxb-" + "1234567890-abcdefghij"


@pytest.fixture()
def sample(tmp_path):
    selftest.build_sample(tmp_path)
    return tmp_path


@pytest.fixture()
def seams():
    yield
    connect.TRANSPORT = connect.SMTP = connect.ENV = None


def ctx(root, **options):
    return selftest.context(root, **options)


def run(root, cid, **options):
    return core.run_check(cid, ctx(root, **options))


def msgs(r):
    return " | ".join(f.message for f in r.findings)


def edit(root, rel, old, new):
    p = root / rel
    body = p.read_text(encoding="utf-8")
    assert old in body, f"{old!r} not in {rel}"
    p.write_text(body.replace(old, new), encoding="utf-8")


def cli(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--root", str(root), *args])
    return code, out.getvalue() + err.getvalue()


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
                   check=True, capture_output=True)


def source(root, sid):
    return next(s for s in yaml.safe_load((root / csample.CONNECT).read_text(encoding="utf-8"))["sources"] if s["id"] == sid)


class FakeSMTP:
    sent = []

    def __init__(self, host, port):
        self.host, self.port, self.log = host, port, []

    def starttls(self):
        self.log.append("starttls")

    def login(self, user, password):
        self.log.append(("login", user, password))

    def send_message(self, msg):
        FakeSMTP.sent.append((self, msg))

    def quit(self):
        self.log.append("quit")


# ── the transport ───────────────────────────────────────────────────────────────

def test_only_https_leaves_the_repository():
    with pytest.raises(core.KitError, match="only https"):
        transport.Http().request("GET", "http://example.com/x")
    with pytest.raises(core.KitError, match="only https"):
        Recorded().request("POST", "ftp://example.com/x")


def test_a_missing_secret_is_named_and_a_present_one_is_never_shown():
    with pytest.raises(core.KitError, match="JIRA_TOKEN is not set"):
        transport.secret("JIRA_TOKEN", {})
    assert transport.redact("failed for https://hooks.slack.com/services/T1/B1/slack-secret-path", [ENV["SLACK_WEBHOOK_URL"]]) == "failed for [secret]"


def test_a_busy_service_is_retried_a_bounded_number_of_times(monkeypatch):
    calls, waits = [], []

    class Ok:
        status, headers = 200, {}

        def read(self):
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout):
        calls.append(req.full_url)
        if len(calls) < 3:
            raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, io.BytesIO(b""))
        return Ok()
    monkeypatch.setattr(transport.urllib.request, "urlopen", urlopen)
    resp = transport.Http(sleep=waits.append).request("GET", "https://example.com/x")
    assert resp.status == 200 and len(calls) == 3 and waits == [1, 2]
    calls.clear()
    monkeypatch.setattr(transport.urllib.request, "urlopen", lambda req, timeout: (_ for _ in ()).throw(urllib.error.HTTPError(req.full_url, 404, "no", {}, io.BytesIO(b""))))
    assert transport.Http(sleep=waits.append).request("GET", "https://example.com/x").status == 404


# ── trackers ────────────────────────────────────────────────────────────────────

def test_jira_search_pages_and_flattens_the_description(sample):
    adf = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Export invoices"}, {"type": "hardBreak"}, {"type": "text", "text": "as CSV."}]},
                                      {"type": "bulletList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "One row per invoice"}]}]}]}]}
    t = Recorded([("POST", f"{JIRA}/rest/api/3/search/jql", {"issues": [{"key": "DEMO-7", "fields": {"summary": "Export", "description": adf, "updated": "2026-11-20T10:00:00",
                                                                                                    "issuetype": {"name": "Story"}, "priority": {"name": "High"}, "labels": ["spec-ready"], "status": {"name": "To Do"}}}],
                                                                  "nextPageToken": "p2"}),
                  ("POST", f"{JIRA}/rest/api/3/search/jql", {"issues": [{"key": "DEMO-8", "fields": {"summary": "Second", "description": None}}]}),
                  ])
    items = trackers.Jira(source(sample, "backlog"), t, ENV).fetch()
    assert [i["key"] for i in items] == ["DEMO-7", "DEMO-8"]
    assert items[0]["body"] == "Export invoices\nas CSV.\nOne row per invoice" and items[0]["url"] == f"{JIRA}/browse/DEMO-7" and items[0]["type"] == "Story"
    first, second = t.calls
    assert first["headers"]["Authorization"] == "Basic " + base64.b64encode(b"kit@example.com:jira-token-value").decode()
    assert first["body"]["jql"] == "project = DEMO AND labels = spec-ready" and "nextPageToken" not in first["body"] and second["body"]["nextPageToken"] == "p2"


def test_jira_search_stops_on_an_empty_page_even_if_a_token_keeps_coming(sample):
    t = Recorded([("POST", f"{JIRA}/rest/api/3/search/jql", {"issues": [], "nextPageToken": "again"})])
    assert trackers.Jira(source(sample, "backlog"), t, ENV).fetch() == [] and len(t.calls) == 1


def test_a_jira_note_is_posted_once(sample):
    url = f"{JIRA}/rest/api/3/issue/DEMO-1/comment"
    t = Recorded([("GET", url, {"comments": []}), ("POST", url, (201, {"id": "1"}))])
    j = trackers.Jira(source(sample, "backlog"), t, ENV)
    assert j.note("DEMO-1", "agentic-spec-kit: Gate G6\n(ref agentic:abc)", "agentic:abc") == "posted"
    assert t.calls[1]["body"] == {"body": {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "agentic-spec-kit: Gate G6"}]},
        {"type": "paragraph", "content": [{"type": "text", "text": "(ref agentic:abc)"}]}]}}
    t.add("GET", url, {"comments": [{"body": trackers.adf_doc("earlier\n(ref agentic:abc)")}]})
    assert j.note("DEMO-1", "x", "agentic:abc") == "exists"


def test_azure_devops_query_then_batch_read(sample):
    t = Recorded([("POST", f"{ADO}/_apis/wit/wiql?api-version=7.1", {"workItems": [{"id": 41}, {"id": 42}]}),
                  ("GET", f"{ADO}/_apis/wit/workitems?ids=41,42&api-version=7.1", {"value": [
                      {"id": 41, "rev": 5, "fields": {"System.Title": "Export invoices", "System.Description": "<div>As finance<br>I want <b>CSV</b>.</div><script>x()</script>",
                                                       "Microsoft.VSTS.Common.AcceptanceCriteria": "<ul><li>One row per invoice</li></ul>", "System.WorkItemType": "User Story",
                                                       "System.Tags": "spec-ready; billing", "System.State": "New"}},
                      {"id": 42, "rev": 1, "fields": {"System.Title": "Second"}}]})])
    items = trackers.Ado(source(sample, "boards"), t, ENV).fetch()
    assert items[0]["body"] == "As finance\nI want CSV.\n\nAcceptance criteria:\nOne row per invoice" and "x()" not in items[0]["body"]
    assert items[0]["url"] == f"{ADO}/_workitems/edit/41" and items[0]["revision"] == "5" and items[0]["labels"] == ["spec-ready", "billing"]
    assert t.calls[0]["headers"]["Authorization"] == "Basic " + base64.b64encode(b":ado-token-value").decode()
    assert "CONTAINS 'spec-ready'" in t.calls[0]["body"]["query"]


def test_an_azure_devops_note(sample):
    url = f"{ADO}/_apis/wit/workItems/41/comments"
    t = Recorded([("GET", f"{url}?api-version=7.1-preview.4", {"comments": [{"text": "<div>unrelated</div>"}]}), ("POST", f"{url}?api-version=7.0-preview.3", {"id": 9})])
    assert trackers.Ado(source(sample, "boards"), t, ENV).note("41", "Gate <G6>\n(ref agentic:k)", "agentic:k") == "posted"
    assert t.calls[1]["body"] == {"text": "Gate &lt;G6&gt;<br>(ref agentic:k)"}


def test_clickup_reads_pages_until_the_last(sample):
    base = "https://api.clickup.com/api/v2/list/901/task"
    t = Recorded([("GET", f"{base}?page=0&include_closed=false", {"tasks": [{"id": "abc1", "name": "Export", "text_content": "Plain text", "url": "https://app.clickup.com/t/abc1",
                                                                              "date_updated": "1700000000000", "priority": {"priority": "high"}, "tags": [{"name": "spec-ready"}],
                                                                              "status": {"status": "to do"}}], "last_page": False}),
                  ("GET", f"{base}?page=1&include_closed=false", {"tasks": [{"id": "abc2", "name": "Second", "description": "From description"}], "last_page": True})])
    items = trackers.ClickUp(source(sample, "tasks"), t, ENV).fetch()
    assert [(i["key"], i["body"]) for i in items] == [("abc1", "Plain text"), ("abc2", "From description")] and items[0]["priority"] == "high"
    assert t.calls[0]["headers"]["Authorization"] == "pk_clickup_value", "a ClickUp personal token is sent as it is, with no Bearer prefix"
    url = "https://api.clickup.com/api/v2/task/abc1/comment"
    t.add("GET", url, {"comments": []}).add("POST", url, {"id": 1})
    assert trackers.ClickUp(source(sample, "tasks"), t, ENV).note("abc1", "note (ref agentic:k)", "agentic:k") == "posted"
    assert t.calls[-1]["body"] == {"comment_text": "note (ref agentic:k)", "notify_all": False}


def test_github_issues_and_a_project(sample):
    cfg = {**source(sample, "issues"), "project": {"owner": "example", "number": 5}}
    api = "https://api.github.com"
    t = Recorded([("GET", f"{api}/repos/example/demo/issues?state=open&per_page=100&page=1&labels=spec-ready", [
                       {"number": 12, "title": "Export", "body": "Body", "html_url": "https://github.com/example/demo/issues/12", "updated_at": "2026-11-20T00:00:00Z",
                        "labels": [{"name": "spec-ready"}], "state": "open"},
                       {"number": 13, "title": "A pull request", "pull_request": {}}]),
                  ("POST", f"{api}/graphql", {"data": {"owner": {"projectV2": {"items": {"pageInfo": {"hasNextPage": False}, "nodes": [
                      {"id": "PVTI_1", "content": {"__typename": "Issue", "number": 12, "title": "Export", "repository": {"nameWithOwner": "example/demo"}}},
                      {"id": "PVTI_2", "content": {"__typename": "Issue", "number": 3, "title": "Other repo", "body": "B", "url": "https://github.com/example/other/issues/3",
                                                   "repository": {"nameWithOwner": "example/other"}, "labels": {"nodes": [{"name": "x"}]}}},
                      {"id": "PVTI_3", "content": {"__typename": "DraftIssue", "title": "A draft", "body": "Draft body"}},
                      {"id": "PVTI_4", "content": None}]}}}}})])
    g = trackers.GitHub(cfg, t, ENV)
    items = g.fetch()
    assert [i["key"] for i in items] == ["example/demo#12", "example/other#3", "project-example-5-draft-PVTI_3"], "a pull request is not a requirement; an issue is listed once"
    assert t.calls[0]["headers"]["Authorization"] == "Bearer gh-token-value" and "organization(login: $login)" in t.calls[1]["body"]["query"]
    assert t.calls[1]["body"]["variables"] == {"login": "example", "number": 5, "after": None}
    assert g.note("project-example-5-draft-PVTI_3", "x", "m").startswith("skipped")
    url = f"{api}/repos/example/demo/issues/12/comments"
    t.add("GET", f"{url}?per_page=100&page=1", []).add("POST", url, (201, {"id": 1}))
    assert g.note("example/demo#12", "note", "agentic:k") == "posted" and t.calls[-1]["body"] == {"body": "note"}
    assert intake.record_id("github", "example/demo#12") == "github-example-demo-12"


def test_a_github_graphql_error_is_reported(sample):
    cfg = {"id": "p", "platform": "github", "project": {"owner": "me", "number": 1, "owner_type": "user"}, "auth": {"token_env": "TRACKER_GITHUB_TOKEN"}}
    t = Recorded([("POST", "https://api.github.com/graphql", {"errors": [{"message": "Could not resolve to a User"}]})])
    with pytest.raises(core.KitError, match="Could not resolve"):
        trackers.GitHub(cfg, t, ENV).fetch()
    assert "user(login: $login)" in t.calls[0]["body"]["query"]


def test_documents_in_five_formats(sample):
    inbox = sample / "requirements/inbox"
    inbox.mkdir(parents=True)
    (inbox / "a.md").write_text("---\nkey: REQ-1\ntype: feature\n---\n# Export invoices\n\nAs finance I want CSV.\n", encoding="utf-8")
    (inbox / "b.txt").write_text("Print receipts\nAs a cashier I want paper.\n", encoding="utf-8")
    (inbox / "c.html").write_text("<html><head><title>Artifact: Refunds</title><style>p{}</style></head><body><h1>Refunds</h1><p>Refund within 14 days.</p>"
                                  "<script>track()</script></body></html>", encoding="utf-8")
    (inbox / "d.csv").write_text("ID,Summary,Description,Priority,Tags\n7,Bulk import,Upload a CSV of users,High,admin;import\n,,,,\n", encoding="utf-8")
    (inbox / "e.json").write_text(json.dumps({"items": [{"key": "J-1", "title": "Audit log", "body": "Record every sign-in"}, {"note": "no title, not a requirement"}]}), encoding="utf-8")
    items = trackers.Documents(source(sample, "inbox"), None, {}, sample).fetch()
    got = {i["key"]: i for i in items}
    assert set(got) == {"REQ-1", "requirements/inbox/b.txt", "requirements/inbox/c.html", "requirements/inbox/d.csv#7", "requirements/inbox/e.json#J-1"}
    assert got["REQ-1"]["title"] == "Export invoices" and got["REQ-1"]["body"] == "As finance I want CSV." and got["REQ-1"]["type"] == "feature"
    assert got["requirements/inbox/b.txt"]["title"] == "Print receipts"
    html_item = got["requirements/inbox/c.html"]
    assert html_item["title"] == "Artifact: Refunds" and "Refund within 14 days." in html_item["body"] and "track()" not in html_item["body"] and "p{}" not in html_item["body"]
    assert got["requirements/inbox/d.csv#7"]["labels"] == ["admin", "import"] and got["requirements/inbox/d.csv#7"]["priority"] == "High"
    assert all(i["revision"] for i in items)
    assert trackers.Documents({}, None, {}, sample).note("k", "t", "m").startswith("skipped")


def test_a_document_source_stays_inside_the_repository(sample):
    for bad in ("../outside/*", "/etc/*"):
        with pytest.raises(core.KitError, match="must stay inside"):
            trackers.Documents({"id": "x", "paths": [bad]}, None, {}, sample).fetch()
    (sample / "requirements/inbox").mkdir(parents=True)
    (sample / "requirements/inbox/x.pdf").write_bytes(b"%PDF")
    with pytest.raises(core.KitError, match="documents are read from"):
        trackers.Documents(source(sample, "inbox"), None, {}, sample).fetch()


def test_fetch_writes_screened_records_once_and_notices_a_later_change(sample):
    def answer(desc, updated):
        return {"issues": [{"key": "DEMO-9", "fields": {"summary": "Fix billing for MRN 0045871", "description": desc, "updated": updated}}]}
    t = Recorded([("POST", f"{JIRA}/rest/api/3/search/jql", answer("Patient 123-45-6789 was charged twice.", "u1"))])
    rows = trackers.fetch_sources(ctx(sample), [source(sample, "backlog")], t, ENV)
    assert rows == [{"source": "backlog", "key": "DEMO-9", "id": "jira-demo-9", "action": "new", "path": f"{core.KIT_DIR}/intake/jira-demo-9.yml",
                     "screened": {"national-id": 1, "record-number": 1}}]
    rec = yaml.safe_load((sample / rows[0]["path"]).read_text(encoding="utf-8"))
    assert "0045871" not in rec["title"] and "123-45-6789" not in rec["body"] and rec["via"] == "backlog" and rec["status"] == "new"
    assert run(sample, "CK-INTAKE-RECORD").ok
    t.add("POST", f"{JIRA}/rest/api/3/search/jql", answer("Patient 123-45-6789 was charged twice.", "u1"))
    assert trackers.fetch_sources(ctx(sample), [source(sample, "backlog")], t, ENV)[0]["action"] == "unchanged"
    rec["status"] = "triaged"
    intake.write_record(sample, rec)
    t.add("POST", f"{JIRA}/rest/api/3/search/jql", answer("The charge was applied three times.", "u2"))
    assert trackers.fetch_sources(ctx(sample), [source(sample, "backlog")], t, ENV)[0]["action"] == "source-changed"
    assert run(sample, "CK-INTAKE-DRIFT").findings


def test_a_failed_fetch_does_not_show_the_token(sample, seams):
    connect.TRANSPORT = Recorded([("POST", f"{JIRA}/rest/api/3/search/jql", (401, "bad token jira-token-value"))])
    connect.ENV = ENV
    code, out = cli(sample, "connect", "fetch", "--source", "backlog")
    assert code == 2 and "HTTP 401" in out and "jira-token-value" not in out


def test_fetch_command_reads_only_the_named_source(sample, seams):
    (sample / "requirements/inbox").mkdir(parents=True)
    (sample / "requirements/inbox/a.md").write_text("# Export invoices as CSV\n\nFor finance.\n", encoding="utf-8")
    connect.TRANSPORT, connect.ENV = Recorded(), {}
    code, out = cli(sample, "connect", "fetch", "--source", "inbox", "--dry-run")
    assert code == 0 and "1 item(s) from 1 source(s)" in out and not (sample / core.KIT_DIR / "intake/document-requirements-inbox-a-md.yml").exists()
    code, out = cli(sample, "connect", "fetch", "--source", "inbox")
    assert code == 0 and (sample / core.KIT_DIR / "intake/document-requirements-inbox-a-md.yml").exists()


# ── events ──────────────────────────────────────────────────────────────────────

def test_a_gate_is_ready_only_when_the_checks_are_green(sample):
    c = ctx(sample)
    green = pipeline.run_checks(c)
    events = notify.detect(c, green)
    ready = [e for e in events if e.type == "gate-ready"]
    assert [(e.spec, e.gate, e.facts["roles"]) for e in ready] == [(SPEC, "G6", ["qa"])]
    edit(sample, f"specs/{SPEC}/plan.md", "One function", "Two functions")
    c = ctx(sample)
    red = pipeline.run_checks(c)
    events = notify.detect(c, red)
    assert [e.type for e in events if e.type in ("gate-ready", "check-failed")] == ["check-failed"]
    assert "CK-GATE-RECORD" in events[0].facts["ids"]


def test_an_event_key_is_stable_and_changes_with_the_evidence(sample):
    def keys():
        return [e.key for e in notify.detect(ctx(sample), []) if e.type == "gate-ready"]
    first = keys()
    assert first and first == keys(), "the same state gives the same key, so a re-run sends nothing twice"
    (sample / f"specs/{SPEC}/verification/notes.md").write_text("more evidence\n", encoding="utf-8")
    assert keys() and keys() != first, "new evidence is a new thing to review"


def test_changes_since_the_base_branch_become_events(sample):
    git(sample, "init", "-q")
    git(sample, "add", "-A")
    git(sample, "commit", "-qm", "base")
    for gate in ("G6", "G7"):
        selftest._dump(sample, f"{core.KIT_DIR}/decisions/{SPEC}/{gate}.yml", {"schema": "agentic-decision/1", "spec": SPEC, "gate": gate,
                                                                              "decision": "approve" if gate == "G6" else "reject", "evidence": {"hash": "sha256:x"}})
    intake.write_record(sample, intake.make_record("jira", "DEMO-30", "Greet the user by name on the mobile app", "Use the name.", via="backlog"))
    rec = yaml.safe_load((sample / f"{core.KIT_DIR}/intake/jira-demo-1.yml").read_text(encoding="utf-8"))
    rec["latest"] = {"hash": "sha256:" + "cd" * 32, "revision": "9"}
    intake.write_record(sample, rec)
    src = core.Source(sample)
    events = notify.detect(core.Context(src, src.at("HEAD"), {"today": selftest.TODAY}), None)
    kinds = {e.type: e for e in events}
    assert {"gate-approved", "gate-rejected", "intake-new", "duplicate-candidate", "source-changed"} <= set(kinds)
    assert kinds["gate-approved"].gate == "G6" and kinds["intake-new"].facts["ids"] == ["jira-demo-30"]
    assert kinds["source-changed"].spec == SPEC and kinds["source-changed"].records == ["jira-demo-1"]
    assert "gate-approved" not in {e.type for e in notify.detect(ctx(sample), None)}, "with no base to compare with, only the current state is reported"


def test_release_is_an_event(sample):
    git(sample, "init", "-q")
    git(sample, "add", "-A")
    git(sample, "commit", "-qm", "base")
    from agentic_kit_product import sample as psample
    psample._release(sample)
    src = core.Source(sample)
    assert "released" in {e.type for e in notify.detect(core.Context(src, src.at("HEAD"), {"today": selftest.TODAY}), None)}


def test_dates_that_are_close_are_announced_once_each(sample):
    events = [e for e in notify.detect(ctx(sample), None) if e.type == "deadline"]
    assert [e.facts["ids"] for e in events] == [["emergency retrospective E-001"]] and events[0].facts["status"] == "2026-11-27"
    edit(sample, f"{core.KIT_DIR}/waivers/W-001.yml", "2099-01-01", "2026-11-30")
    ids = [e.facts["ids"][0] for e in notify.detect(ctx(sample), None) if e.type == "deadline"]
    assert "waiver W-001" in ids
    assert not [e for e in notify.detect(ctx(sample, today="2026-01-01"), None) if e.type == "deadline"]


# ── what a notification may say ─────────────────────────────────────────────────

def test_no_channel_ever_carries_requirement_text(sample):
    c = ctx(sample)
    cfg = connect.config(c)
    edit(sample, f"specs/{SPEC}/plan.md", "One function", "Two functions")
    c = ctx(sample)
    events = notify.detect(c, pipeline.run_checks(c)) + notify.detect(ctx(sample), None)
    events.append(notify.Event("duplicate-candidate", "k1", facts={"ids": ["jira-demo-1"]}, records=["jira-demo-1"]))
    assert events
    for e in events:
        text = notify.title(e, cfg["notify"].get("templates"))
        url = notify.link(e, cfg["notify"])
        blob = json.dumps([notify.render_slack(e, text, url), notify.render_teams(e, text, url), notify.render_note(e, text, url),
                           notify.render_email(e, text, url, "kit@example.com", ["t@example.com"]).as_string()])
        for forbidden in (SECRET_TEXT, "greet the user by name", "Greet people by name", "One function", "Two functions"):
            assert forbidden.lower() not in blob.lower(), (e.type, forbidden)


def test_slack_and_teams_payloads(sample):
    e = notify.Event("gate-ready", "abc123", SPEC, "G6", {"roles": ["qa"]})
    slack = notify.render_slack(e, "Gate G6 of 001-demo needs qa", "https://github.com/example/demo/pull/7")
    assert slack["text"] == "Needs a person: Gate G6 of 001-demo needs qa" and slack["blocks"][0]["type"] == "section"
    assert "<https://github.com/example/demo/pull/7|Open>" in slack["blocks"][0]["text"]["text"]
    teams = notify.render_teams(e, "Gate G6 of 001-demo needs qa", "https://github.com/example/demo/pull/7")
    assert teams["type"] == "message" and teams["attachments"][0]["contentType"] == "application/vnd.microsoft.card.adaptive"
    card = teams["attachments"][0]["content"]
    assert card["type"] == "AdaptiveCard" and card["actions"] == [{"type": "Action.OpenUrl", "title": "Open", "url": "https://github.com/example/demo/pull/7"}]
    assert "actions" not in notify.render_teams(e, "x", "")["attachments"][0]["content"]


def test_delivery_to_every_channel_once(sample, tmp_path_factory):
    c = ctx(sample)
    cfg = connect.config(c)
    ledger = tmp_path_factory.mktemp("state") / "sent.txt"
    note_url = f"{JIRA}/rest/api/3/issue/DEMO-1/comment"
    t = Recorded([("POST", ENV["SLACK_WEBHOOK_URL"], "ok"), ("GET", note_url, {"comments": []}), ("POST", note_url, (201, {})),
                  ("POST", ENV["TEAMS_WEBHOOK_URL"], (202, ""))])
    FakeSMTP.sent = []
    events = [notify.Event("gate-ready", "k-ready", SPEC, "G6", {"roles": ["qa"]}), notify.Event("check-failed", "k-failed", facts={"ids": ["CK-TRACE"], "count": 1})]
    rows = notify.deliver(c, cfg, events, t, ENV, ledger, FakeSMTP, "https://github.com/example/demo/pull/7")
    assert [(r["channel"], r["status"]) for r in rows] == [("chat", "sent"), ("origin", "1 posted"), ("teams", "sent"), ("mail", "sent")]
    assert rows[0]["text"] == "Gate G6 of 001-demo needs qa", "the project's own headline is used"
    assert t.calls[0]["body"]["text"].startswith("Needs a person") and t.calls[3]["body"]["attachments"][0]["content"]["body"][0]["text"] == "Problem"
    assert "(ref agentic:k-ready)" in json.dumps(t.calls[2]["body"])
    server, msg = FakeSMTP.sent[0]
    assert (server.host, server.port) == ("smtp.example.com", 587) and server.log == ["starttls", ("login", "mailer", "smtp-password-value"), "quit"]
    assert msg["Subject"] == "[agentic-spec-kit] 1 check(s) failed: CK-TRACE" and msg["To"] == "team@example.com"
    assert "is not an approval" in msg.get_content()
    again = notify.deliver(c, cfg, events, Recorded(), ENV, ledger, FakeSMTP, "")
    assert {r["status"] for r in again} == {"already sent"} and len(FakeSMTP.sent) == 1


def test_a_note_is_not_repeated_even_without_a_ledger(sample):
    c = ctx(sample)
    cfg = connect.config(c)
    cfg["notify"]["routes"] = [{"events": ["gate-ready"], "channels": ["origin"]}]
    note_url = f"{JIRA}/rest/api/3/issue/DEMO-1/comment"
    t = Recorded([("GET", note_url, {"comments": [{"body": trackers.adf_doc("x (ref agentic:k-ready)")}]})])
    rows = notify.deliver(c, cfg, [notify.Event("gate-ready", "k-ready", SPEC, "G6", {"roles": ["qa"]})], t, ENV)
    assert rows[0]["status"] == "1 exists" and len(t.calls) == 1


def test_one_channel_failing_does_not_stop_the_others_or_leak_its_address(sample):
    c = ctx(sample)
    cfg = connect.config(c)
    cfg["notify"]["routes"] = [{"events": ["*"], "channels": ["chat", "teams", "mail"]}]
    t = Recorded([("POST", ENV["SLACK_WEBHOOK_URL"], (500, "down")), ("POST", ENV["TEAMS_WEBHOOK_URL"], (202, ""))])
    FakeSMTP.sent = []
    env = {k: v for k, v in ENV.items() if k != "SMTP_HOST"}
    rows = notify.deliver(c, cfg, [notify.Event("released", "k", SPEC)], t, env, None, FakeSMTP)
    status = {r["channel"]: r["status"] for r in rows}
    assert status["chat"] == "failed: the slack webhook failed: HTTP 500" and status["teams"] == "sent"
    assert status["mail"] == "failed: the secret SMTP_HOST is not set in this job"
    assert "slack-secret-path" not in json.dumps(rows)


def test_routes_decide_where_an_event_goes():
    cfg = {"channels": [{"id": "a", "type": "slack"}, {"id": "b", "type": "teams"}],
           "routes": [{"events": ["released"], "channels": ["a"]}, {"events": ["*"], "channels": ["b", "missing"]}]}
    assert [c["id"] for c in notify.channels_for(notify.Event("released", "k"), cfg)] == ["a", "b"]
    assert [c["id"] for c in notify.channels_for(notify.Event("deadline", "k"), cfg)] == ["b"]


# ── the pipeline ────────────────────────────────────────────────────────────────

def test_run_reports_and_exits_with_the_check_result(sample, tmp_path_factory, seams):
    connect.TRANSPORT, connect.ENV = Recorded(), {}
    out_file = tmp_path_factory.mktemp("out") / "summary.md"
    code, out = cli(sample, "connect", "run", "--summary", str(out_file))
    assert code == 0 and "0 failed, 0 not run" in out and "| 001-demo | approved | approved | approved | approved | approved | open | later |" in out
    assert "Gate G6 of 001-demo needs qa" in out and out_file.read_text(encoding="utf-8").startswith("# agentic-spec-kit")
    edit(sample, f"specs/{SPEC}/plan.md", "One function", "Two functions")
    code, out = cli(sample, "connect", "run", "--json")
    data = json.loads(out)
    assert code == 1 and data["ok"] is False and data["events"][0]["type"] == "check-failed"


def test_run_takes_the_branch_from_the_caller_and_on_the_default_branch_asks_for_the_gates_before_a_merge(sample, seams):
    connect.TRANSPORT, connect.ENV = Recorded(), {}
    (sample / f"{core.KIT_DIR}/emergencies/E-001.yml").unlink()  # without its open emergency 001-demo is an ordinary spec: finished, with G6 undecided
    code, out = cli(sample, "connect", "run", "--branch", "refs/pull/7/merge")
    assert code == 0 and "0 failed, 0 not run" in out, "a pull request: work in progress"
    code, out = cli(sample, "connect", "run", "--branch", "refs/heads/main")
    assert code == 1 and "**CK-GATE-RECORD** failed" in out
    assert "the implementation is on the default branch (main) but gate G6 has no approving decision record" in out
    code, out = cli(sample, "connect", "run", "--branch", "", "--json")
    notes = [n for r in json.loads(out)["results"] if r["check"] == "CK-GATE-RECORD" for n in r["notes"]]
    assert code == 0 and len(notes) == 1 and notes[0].startswith("could not tell whether this is the default branch"), \
        "a pipeline variable that is empty says nothing; the sample is a folder of files, so git has nothing to say either"


def test_run_with_notify_uses_the_configured_channels(sample, tmp_path_factory, seams):
    note_url = f"{JIRA}/rest/api/3/issue/DEMO-1/comment"
    connect.TRANSPORT = Recorded([("POST", ENV["SLACK_WEBHOOK_URL"], "ok"), ("GET", note_url, {"comments": []}), ("POST", note_url, (201, {})),
                                  ("POST", ENV["TEAMS_WEBHOOK_URL"], (202, ""))])
    connect.ENV, connect.SMTP = ENV, FakeSMTP
    FakeSMTP.sent = []
    ledger = tmp_path_factory.mktemp("state") / "sent.txt"
    code, out = cli(sample, "connect", "run", "--notify", "--ledger", str(ledger), "--pr-url", "https://github.com/example/demo/pull/7")
    assert code == 0 and "gate-ready to chat: sent" in out and "gate-ready to origin: 1 posted" in out and "deadline to mail: sent" in out
    assert connect.TRANSPORT.script == [] and len(ledger.read_text(encoding="utf-8").splitlines()) == 4


def test_the_pipeline_uses_the_base_branchs_connections(sample):
    git(sample, "init", "-q")
    git(sample, "add", "-A")
    git(sample, "commit", "-qm", "base")
    edit(sample, csample.CONNECT, "https://example.atlassian.net", "https://attacker.example.net")
    src = core.Source(sample)
    reviewed = core.Context(src, src.at("HEAD"), {})
    assert connect.config(reviewed)["sources"][0]["base_url"] == "https://example.atlassian.net", "a change cannot point the pipeline's token at a new address"
    assert connect.config(core.Context(src, src, {}))["sources"][0]["base_url"] == "https://attacker.example.net"


def _open_g6(sample):
    assert cli(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")[0] == 0
    c = ctx(sample)
    return core.evidence_hash(c.src, SPEC, "G6", _evidence_files(c, SPEC, "G6", None))


def _review(sample, **review):
    path = sample / core.KIT_DIR / "_adapter/reviews.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["changes"]["pull/1"]["reviews"].append({"type": "User", "commit": selftest.COMMIT, **review})
    path.write_text(json.dumps(data), encoding="utf-8")


def test_a_review_with_the_approval_line_is_mirrored_into_a_decision_record(sample):
    digest = _open_g6(sample)
    assert cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT)[1].startswith("no review on this change")
    _review(sample, id="90", reviewer="bob", state="APPROVED", body="Verified.\n" + core.approval_line("G6", "approve", digest))
    code, out = cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT)
    assert code == 0 and "001-demo G6: approve - ready to record" in out and not (sample / core.KIT_DIR / f"decisions/{SPEC}/G6.yml").exists()
    code, out = cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")
    assert code == 0 and "recorded" in out
    rec = yaml.safe_load((sample / core.KIT_DIR / f"decisions/{SPEC}/G6.yml").read_text(encoding="utf-8"))
    assert rec["decision"] == "approve" and rec["approvals"] == [{"reviewer": "bob", "role": "qa", "review_ref": "pull/1#review-90"}]
    for cid in ("CK-GATE-RECORD", "CK-APPROVER", "CK-GATE-MIRROR", "CK-BRIEF", "CK-AUDIT-CHAIN"):
        r = run(sample, cid)
        assert r.ok, r.as_dict()
    assert "no review on this change" in cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT)[1], "a mirrored gate is not mirrored twice"


@pytest.mark.parametrize("review,expect", [
    ({"reviewer": "alice", "state": "APPROVED"}, "waiting for qa"),                 # alice does not hold the role G6 needs
    ({"reviewer": "bob", "state": "COMMENTED"}, "no review on this change"),         # a comment is not an approval
    ({"reviewer": "bob", "state": "APPROVED", "type": "Bot"}, "no review on this change"),
])
def test_mirroring_creates_no_approval(sample, review, expect):
    digest = _open_g6(sample)
    _review(sample, id="91", body=core.approval_line("G6", "approve", digest), **review)
    code, out = cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")
    assert expect in out and not (sample / core.KIT_DIR / f"decisions/{SPEC}/G6.yml").exists()


def test_an_approval_of_other_evidence_is_not_mirrored_and_a_rejection_is(sample):
    digest = _open_g6(sample)
    _review(sample, id="92", reviewer="bob", state="APPROVED", body=core.approval_line("G6", "approve", "sha256:" + "0" * 64))
    assert "no review on this change" in cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")[1]
    _review(sample, id="93", reviewer="bob", state="CHANGES_REQUESTED", body="Not yet.\n" + core.approval_line("G6", "reject", digest))
    code, out = cli(sample, "connect", "mirror", "--change", "pull/1", "--commit", selftest.COMMIT, "--write")
    assert "001-demo G6: reject - recorded" in out
    assert yaml.safe_load((sample / core.KIT_DIR / f"decisions/{SPEC}/G6.yml").read_text(encoding="utf-8"))["decision"] == "reject"


# ── checks ──────────────────────────────────────────────────────────────────────

def test_the_sample_passes_and_every_check_has_a_fixture(sample):
    assert set(connect.CONNECT_CHECKS) == set(csample.fixtures())
    for cid in connect.CONNECT_CHECKS:
        r = run(sample, cid)
        assert r.ok, r.as_dict()
    assert run(sample, "CK-ENFORCE-SETUP").ok, "connect.yml is covered by CODEOWNERS in the sample"


def test_an_unconnected_repository_is_left_alone(sample):
    (sample / csample.CONNECT).unlink()
    for cid in connect.CONNECT_CHECKS:
        r = run(sample, cid)
        assert r.ok and r.notes
    assert cli(sample, "connect", "run")[0] == 2


@pytest.mark.parametrize("old,new,expect", [
    ('base_url: "https://example.atlassian.net"', 'base_url: "http://example.atlassian.net"', "base_url must start with https://"),
    ("token_env: JIRA_TOKEN", "token_env: jira token", "must be the NAME of an environment variable"),
    ("token_env: ADO_TOKEN", "token_env: " + FAKE_GITHUB_TOKEN, "contains a GitHub token"),
    ("organization: example, ", "", "(ado) is missing organization"),
    ('list: "901", ', "", "(clickup) is missing list"),
    ("repo: example/demo, ", "", "needs repo, project or both"),
    ("platform: clickup", "platform: trello", "platform must be one of"),
    ("id: boards", "id: backlog", "used twice"),
    ("channels: [chat, origin]", "channels: [chat, pager]", "channel pager, which is not defined"),
    ("events: [gate-ready,", "events: [gate-opened,", "names event gate-opened"),
    ("type: slack", "type: irc", "type must be one of"),
    ("host_env: SMTP_HOST, ", "", "email needs smtp.host_env"),
])
def test_connection_settings_are_checked(sample, old, new, expect):
    edit(sample, csample.CONNECT, old, new)
    assert expect in msgs(run(sample, "CK-CONNECT-CONFIG"))


def test_a_notification_cannot_be_configured_to_carry_text(sample):
    edit(sample, csample.CONNECT, "  links:", "  include_text: true\n  links:")
    assert "notify.include_text is not supported" in msgs(run(sample, "CK-NOTIFY-CONTENT"))
    edit(sample, csample.CONNECT, "gate-ready: ", "gate-opened: ")
    assert "which is not an event" in msgs(run(sample, "CK-NOTIFY-CONTENT"))


@pytest.mark.parametrize("old,new,expect", [
    ("SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}", "SLACK_WEBHOOK_URL: " + FAKE_SLACK_HOOK, "a Slack webhook"),
    ("JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}", "JIRA_TOKEN: hunter2", "JIRA_TOKEN is given a literal value"),
    ("  workflow_run:\n    workflows: [agentic-checks]\n    types: [completed]\n", "  pull_request:\n", "runs on pull_request and uses JIRA_TOKEN"),
    ("  workflow_run:\n    workflows: [agentic-checks]\n    types: [completed]\n", "  pull_request_target:\n", "pull_request_target"),
    ("      - run: python trusted", "      - run: claude -p 'fix it'\n      - run: python trusted", "job notify runs an agent (claude)"),
])
def test_pipeline_rules(sample, old, new, expect):
    edit(sample, csample.NOTIFY_FLOW, old, new)
    assert expect in msgs(run(sample, "CK-PIPELINE-SECRETS"))


def test_an_agent_step_is_judged_by_everything_it_can_read(sample):
    edit(sample, csample.AGENT_FLOW, "name: agent\n", "name: agent\nenv:\n  CLICKUP_TOKEN: ${{ secrets.CLICKUP_TOKEN }}\n")
    assert "can read CLICKUP_TOKEN" in msgs(run(sample, "CK-PIPELINE-SECRETS"))
    edit(sample, csample.AGENT_FLOW, "env:\n  CLICKUP_TOKEN: ${{ secrets.CLICKUP_TOKEN }}\n", "")
    edit(sample, csample.AGENT_FLOW, '      - run: claude -p "Implement the next ready task"',
         '      - uses: anthropics/claude-code-action@0123456789abcdef0123456789abcdef01234567\n        env:\n          ADO_TOKEN: ${{ secrets.ADO_TOKEN }}')
    assert "anthropics/claude-code-action" in msgs(run(sample, "CK-PIPELINE-SECRETS"))
    edit(sample, csample.AGENT_FLOW, "          ADO_TOKEN: ${{ secrets.ADO_TOKEN }}", "          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}")
    assert run(sample, "CK-PIPELINE-SECRETS").ok, "the agent's own model key is not a tracker or notification credential"


def test_other_ci_systems_are_scanned_for_stored_secrets(sample):
    selftest._write(sample, "azure-pipelines.yml", "variables:\n  SLACK_WEBHOOK_URL: $(SLACK_WEBHOOK_URL)\nsteps:\n  - script: echo ok\n")
    selftest._write(sample, ".gitlab-ci.yml", "kit:\n  script:\n    - python agentic.py connect run --notify\n")
    assert run(sample, "CK-PIPELINE-SECRETS").ok
    edit(sample, "azure-pipelines.yml", "$(SLACK_WEBHOOK_URL)", f"'{FAKE_SLACK_TOKEN}'")
    out = msgs(run(sample, "CK-PIPELINE-SECRETS"))
    assert "a Slack token" in out and "SLACK_WEBHOOK_URL is given a literal value" in out


# ── commands ────────────────────────────────────────────────────────────────────

def test_init_writes_a_skeleton_that_is_valid_and_holds_no_secret(tmp_path):
    selftest.build_sample(tmp_path)
    (tmp_path / csample.CONNECT).unlink()
    code, out = cli(tmp_path, "connect", "init", "--write")
    assert code == 0 and "wrote" in out
    assert run(tmp_path, "CK-CONNECT-CONFIG").ok and run(tmp_path, "CK-NOTIFY-CONTENT").ok
    assert "already exists" in cli(tmp_path, "connect", "init", "--write")[1]


def test_events_command_lists_what_would_be_announced(sample):
    code, out = cli(sample, "connect", "events")
    assert code == 0 and "deadline" in out and "E-001" in out


def test_the_shipped_pipelines_follow_the_kits_own_rules(sample):
    ci = ROOT / "extensions" / "agentic-connect" / "ci"
    names = sorted(p.name for p in ci.iterdir())
    assert names == ["azure-pipelines.yml", "github-actions.yml", "gitlab-ci.yml"]
    selftest._write(sample, ".github/workflows/agentic.yml", (ci / "github-actions.yml").read_text(encoding="utf-8"))
    selftest._write(sample, "azure-pipelines.yml", (ci / "azure-pipelines.yml").read_text(encoding="utf-8"))
    selftest._write(sample, ".gitlab-ci.yml", (ci / "gitlab-ci.yml").read_text(encoding="utf-8"))
    r = run(sample, "CK-PIPELINE-SECRETS")
    assert r.ok, msgs(r)
    r = run(sample, "CK-PIN")
    assert r.ok, msgs(r)
    flow = yaml.safe_load((ci / "github-actions.yml").read_text(encoding="utf-8"))
    assert set(flow["jobs"]) == {"notify", "mirror", "intake"}
    triggers = flow.get("on", flow.get(True))
    assert set(triggers) == {"workflow_run", "schedule", "workflow_dispatch"}, "nothing that holds a secret runs on a pull request"
    core_flow = (ROOT / "extensions" / "agentic" / "ci" / "agentic-checks.yml").read_text(encoding="utf-8")
    assert "secrets." not in core_flow, "the workflow that runs on a pull request holds no secret"


def test_in_a_pipelines_full_clone_git_says_which_branch_was_built_so_the_shipped_pipelines_pass_no_flag(tmp_path):
    """On the default branch the gate check asks for more. The shipped files clone everything and check out one commit; that is enough for git to say."""
    from agentic_kit.checks_gov import on_default_branch
    ci = ROOT / "extensions" / "agentic-connect" / "ci"
    shipped = {"agentic-checks.yml": (ROOT / "extensions" / "agentic" / "ci" / "agentic-checks.yml").read_text(encoding="utf-8"),
               **{p.name: p.read_text(encoding="utf-8") for p in ci.iterdir()}}
    assert not [name for name, body in shipped.items() if "--branch" in body], "nothing a copy of these files could forget"
    assert "fetch-depth: 0" in shipped["agentic-checks.yml"] and "fetch-depth: 0" in shipped["github-actions.yml"]
    assert "fetchDepth: 0" in shipped["azure-pipelines.yml"] and 'GIT_DEPTH: "0"' in shipped["gitlab-ci.yml"], "each makes a full clone"

    origin, clone = tmp_path / "origin", tmp_path / "clone"
    selftest.build_sample(origin)
    git(origin, "init", "-q", "-b", "main")
    git(origin, "add", "-A")
    git(origin, "commit", "-qm", "the default branch")
    git(origin, "switch", "-qc", "spec/001-demo")
    (origin / "src/demo/more.py").write_text("x = 1\n")
    git(origin, "add", "-A")
    git(origin, "commit", "-qm", "a proposed change")
    git(origin, "switch", "-qc", "spec/002-next")
    (origin / "src/demo/next.py").write_text("x = 2\n")
    git(origin, "add", "-A")
    git(origin, "commit", "-qm", "a change proposed on top of the first")
    git(origin, "switch", "-q", "main")
    subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True, capture_output=True)

    def says(base, **options):
        src = core.Source(clone)
        return on_default_branch(core.Context(src, src.at(base) if base else src, options))

    assert says("HEAD~0") == (True, ""), "a push to the default branch on GitHub: the branch is checked out, compared with a commit"
    git(clone, "checkout", "-q", "--detach", "origin/main")
    git(clone, "branch", "-q", "-D", "main")
    assert says("origin/main") == (True, ""), "GitLab and Azure on the default branch: one commit, remote branches only, compared with the branch itself"
    git(clone, "checkout", "-q", "--detach", "origin/spec/001-demo")
    assert says("origin/main") == (False, ""), "a pull request: its commit is not on the default branch"
    git(clone, "checkout", "-q", "--detach", "origin/spec/002-next")
    assert says("origin/spec/001-demo") == (False, ""), "a pull request into another branch"
    kit = clone / core.KIT_DIR / "kit.yml"
    kit.write_text(kit.read_text(encoding="utf-8").replace("default_branch: main", "default_branch: trunk"), encoding="utf-8")
    assert says(None) == (None, "the repository has no branch trunk; enforcement.default_branch in kit.yml names the default branch"), \
        "a wrong name in kit.yml is said, not passed over"


def test_a_pipeline_whose_checkout_cannot_say_may_pass_the_ref_it_built(sample):
    """What CI systems call what they built, and how --branch reads it. The sample's default branch is main."""
    from agentic_kit.checks_gov import on_default_branch
    for ref, expected in (("refs/heads/main", True), ("main", True), ("refs/pull/7/merge", False), ("refs/merge-requests/7/head", False),
                          ("refs/heads/spec/001-demo", False), ("refs/tags/main", False), ("spec/001-demo", False)):
        assert on_default_branch(ctx(sample, branch=ref)) == (expected, ""), ref


def test_the_kits_own_pipeline_follows_the_kits_own_rules(sample):
    text = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    selftest._write(sample, ".github/workflows/tests.yml", text)
    for cid in ("CK-PIPELINE-SECRETS", "CK-PIN"):
        r = run(sample, cid)
        assert r.ok, msgs(r)
    flow = yaml.safe_load(text)
    assert set(flow.get("on", flow.get(True))) == {"pull_request", "push"}
    assert flow["permissions"] == {"contents": "read"}, "the job can read the repository and nothing else"
    assert "secrets." not in text and "pull_request_target" not in text
    commands = [step["run"] for step in flow["jobs"]["tests"]["steps"] if "run" in step]
    assert not [c for c in commands if "${{" in c], "nothing from the event is pasted into a command"
    assert any("pytest tests" in c for c in commands) and any("selftest" in c for c in commands) and any("golden run" in c for c in commands)
