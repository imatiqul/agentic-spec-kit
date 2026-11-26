"""The conversation behind a change (CNV-1 to CNV-14, docs/design/conversation.md).

Each test is named after the acceptance criterion it proves. No test here opens a network connection: the three
trackers are a scripted transport that answers from recorded responses, as in tests/test_connect.py, and a request
that is not in the script fails the test. AC-016 is the test of `fetch` in that file.
Run: python -m pytest tests/test_conversation.py -q"""
import hashlib
import html
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, lanes, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

import agentic_kit_connect as connect  # noqa: E402
from agentic_kit_connect import notify, trackers  # noqa: E402
from agentic_kit_connect import sample as csample  # noqa: E402
from agentic_kit_connect.transport import Recorded  # noqa: E402
from agentic_kit_product import conversation, intake  # noqa: E402
from agentic_kit_product import sample as psample  # noqa: E402

SPEC = selftest.SPEC
DRAFT = "002-export"
ORIGIN = f"specs/{SPEC}/origin.yml"
DRAFT_ORIGIN = f"specs/{DRAFT}/origin.yml"
ENV = {"JIRA_USER": "kit@example.com", "JIRA_TOKEN": "jira-token-value", "ADO_TOKEN": "ado-token-value", "CLICKUP_TOKEN": "pk_clickup_value",
       "TRACKER_GITHUB_TOKEN": "gh-token-value"}
JIRA = "https://example.atlassian.net"
ADO = "https://dev.azure.com/example/Demo"
GITHUB = "https://api.github.com"
CHAT = "https://chat.example.com/archives/C1/p1764150000000100"
HEADING = "## The conversation behind it"

# What was said on a work item: (id, account, text). All of it is made up, and none of it may reach a file.
PASSWORD = "hunter2" + "hunter2"   # in the shape of a credential, joined here so that no file of the repository holds it whole
SAID = [("101", "pat-example", "Take the name from the account, never from the mail address: \u00abHello, pat\u00bb is enough."),
        ("102", "sam-example", f"Agreed for the account name.\nThe login for the trial is password = {PASSWORD}")]
LATER = ("103", "pat-example", "Then greet such a person with the word friend.")
# The same two comments as the screen leaves them. The hash is over these.
SCREENED = [SAID[0], ("102", "sam-example", "Agreed for the account name.\nThe login for the trial is [removed: credential]")]
NOTE = ("900", "kit-pipeline", notify.render_note(notify.Event("gate-ready", "0123456789abcdef", SPEC, "G1", {"roles": ["product-owner"]}),
                                                 "Gate G1 of 001-demo is ready for review by product-owner", "https://github.com/example/demo/pull/7"))


def by_hand(comments):
    """The formula of docs/design/conversation.md, written out here a second time so that the code cannot move it unseen."""
    lines = sorted(json.dumps([cid, account, hashlib.sha256(text.encode("utf-8")).hexdigest()], separators=(",", ":"), ensure_ascii=True)
                   for cid, account, text in comments)
    return "sha256:" + hashlib.sha256("\n".join(["agentic-discussion/1", *lines]).encode("utf-8")).hexdigest()


def shown(account):
    return account.replace("-", " ").title()   # the name a tracker shows beside the account: Pat Example


def as_jira(cid, account, text):
    return {"id": cid, "author": {"accountId": account, "displayName": shown(account)}, "body": trackers.adf_doc(text), "created": "2026-11-20T10:00:00.000+0000"}


def as_ado(cid, account, text):   # the reference calls the id `id` and its samples call it `commentId`: one of each
    name = "commentId" if cid == "102" else "id"
    return {name: int(cid), "workItemId": 41, "version": 1, "text": "<div>" + html.escape(text).replace("\n", "<br>") + "</div>",
            "createdBy": {"id": account, "displayName": shown(account), "uniqueName": f"{account}@example.com"}, "isDeleted": False}


def as_github(cid, account, text):   # GitHub keeps the line ends a browser sends
    return {"id": int(cid), "user": {"login": account, "id": 5000 + int(cid)}, "body": text.replace("\n", "\r\n"), "created_at": "2026-11-20T10:00:00Z"}


def jira_pages(comments, size=100):
    url = f"{JIRA}/rest/api/3/issue/DEMO-9/comment"
    pages = [comments[i:i + size] for i in range(0, len(comments), size)] or [[]]
    return [("GET", f"{url}?startAt={n * size}&maxResults=100", {"startAt": n * size, "maxResults": size, "total": len(comments), "comments": [as_jira(*c) for c in page]})
            for n, page in enumerate(pages)]


def ado_pages(comments, size=100):
    url = f"{ADO}/_apis/wit/workItems/41/comments?$top=100&api-version=7.1-preview.4"
    pages = [comments[i:i + size] for i in range(0, len(comments), size)] or [[]]
    out = []
    for n, page in enumerate(pages):   # the token of the service is opaque: it is sent back as it came, made safe for an address
        answer = {"totalCount": len(comments), "count": len(page), "comments": [as_ado(*c) for c in page]}
        if n + 1 < len(pages):
            answer["continuationToken"] = f"page/{n + 2}+more"
        out.append(("GET", url + (f"&continuationToken=page%2F{n + 1}%2Bmore" if n else ""), answer))
    return out


def github_pages(comments, size=100):
    url = f"{GITHUB}/repos/example/demo/issues/12/comments"
    pages = [comments[i:i + size] for i in range(0, len(comments), size)] or [[]]
    if len(pages[-1]) == size:
        pages.append([])   # a full page does not say that it is the last
    return [("GET", f"{url}?per_page=100&page={n}", [as_github(*c) for c in page]) for n, page in enumerate(pages, 1)]


def jira_item(text="For the finance team."):
    return [("POST", f"{JIRA}/rest/api/3/search/jql", {"issues": [{"key": "DEMO-9", "fields": {"summary": "Export invoices as CSV", "description": trackers.adf_doc(text),
                                                                                             "updated": "2026-11-20T10:00:00"}}]})]


def ado_item(text="For the finance team."):
    return [("POST", f"{ADO}/_apis/wit/wiql?api-version=7.1", {"workItems": [{"id": 41}]}),
            ("GET", f"{ADO}/_apis/wit/workitems?ids=41&api-version=7.1", {"value": [{"id": 41, "rev": 5, "fields": {"System.Title": "Export invoices as CSV",
                                                                                                                   "System.Description": f"<div>{text}</div>"}}]})]


def github_item(text="For the finance team."):
    return [("GET", f"{GITHUB}/repos/example/demo/issues?state=open&per_page=100&page=1&labels=spec-ready", [
        {"number": 12, "title": "Export invoices as CSV", "body": text, "html_url": "https://github.com/example/demo/issues/12", "updated_at": "2026-11-20T00:00:00Z",
         "labels": [{"name": "spec-ready"}], "state": "open", "comments": 2}])]


#: tracker -> (the source in the sample's connect.yml, the record it makes, the item's recorded answers, the comments' recorded answers)
TRACKERS = {"jira": ("backlog", "jira-demo-9", jira_item, jira_pages), "ado": ("boards", "ado-41", ado_item, ado_pages),
            "github": ("issues", "github-example-demo-12", github_item, github_pages)}
#: The first request for an item's comments, written out as the table of the spec has it.
FIRST_PAGE = {"jira": "https://example.atlassian.net/rest/api/3/issue/DEMO-9/comment?startAt=0&maxResults=100",
              "ado": "https://dev.azure.com/example/Demo/_apis/wit/workItems/41/comments?$top=100&api-version=7.1-preview.4",
              "github": "https://api.github.com/repos/example/demo/issues/12/comments?per_page=100&page=1"}
ALL = pytest.mark.parametrize("tracker", sorted(TRACKERS))


def script(tracker, comments, text="For the finance team."):
    """One fetch of one item, as the tracker would answer it: the item, then what was said on it."""
    _, _, item, pages = TRACKERS[tracker]
    return Recorded(item(text) + pages(comments))


def asked_for_comments(transport):
    return [c["url"] for c in transport.calls if c["method"] == "GET" and "omment" in c["url"].split("?")[0]]


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


def run(root, cid="CK-CONVERSATION", **options):
    return core.run_check(cid, ctx(root, **options))


def msgs(r):
    return " | ".join(f.message for f in r.findings)


def cli(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--root", str(root), *args])
    return code, out.getvalue() + err.getvalue()


def source(root, sid):
    return next(s for s in yaml.safe_load((root / csample.CONNECT).read_text(encoding="utf-8"))["sources"] if s["id"] == sid)


def fetch(root, tracker, comments, text="For the finance team.", today="2026-11-26", write=True):
    t = script(tracker, comments, text)
    rows = trackers.fetch_sources(ctx(root, today=today), [source(root, TRACKERS[tracker][0])], t, ENV, write=write)
    assert t.script == [], "every recorded answer was asked for"
    return rows, t


def record(root, rid):
    return yaml.safe_load((root / intake.path_of(rid)).read_text(encoding="utf-8"))


def acted_on(root, rid, status="specified"):
    """Someone has acted on the record: from here on its first digest stays."""
    rec = record(root, rid)
    rec["status"] = status
    intake.write_record(root, rec)


def origin(root, spec=SPEC):
    return yaml.safe_load((root / f"specs/{spec}/origin.yml").read_text(encoding="utf-8"))


def rewrite(root, rel, change):
    data = yaml.safe_load((root / rel).read_text(encoding="utf-8"))
    change(data)
    (root / rel).write_text(conversation.dump(data), encoding="utf-8", newline="\n")


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def draft(root, sid=DRAFT):
    """A second spec that waits at its first gate, with nothing decided about it."""
    selftest._write(root, f"specs/{sid}/spec.md", f"---\nspec: {sid}\ntier_declared: low\nowner_role: backend\n---\n# Feature Specification: Export invoices\n\n"
                    "## Requirements\n- **FR-001**: System MUST export a user's invoices as a CSV file.\n\n## Acceptance Criteria\n"
                    "- **AC-001** (verifies FR-001): Given a user with invoices, When the user asks for an export, Then a CSV file with one row per invoice is returned.\n")
    return sid


def asked(root, sid=DRAFT, thread=CHAT):
    """The draft with the request behind it: one intake record, added by hand with a thread link, and tied to the spec."""
    draft(root, sid)
    assert cli(root, "intake", "add", "--title", "Export invoices as CSV", "--key", "EXP-1", "--thread", thread)[0] == 0
    assert cli(root, "product", "specify", "--intake", "manual-exp-1", "--spec", sid, "--write")[0] == 0
    return sid


SUMMARY = "pat asked for an export of invoices as CSV. sam agreed to one row for each invoice.\nLeft open: whether a refund is a row of its own."
WRITE = ("product", "conversation", "--spec", DRAFT, "--summary", SUMMARY, "--link", "https://example.atlassian.net/browse/DEMO-7",
         "--person", "pat", "--person", "sam", "--captured-by", "spec-author", "--today", "2026-11-26")


# ── the summary in origin.yml ───────────────────────────────────────────────────

def test_AC_001_the_block_is_written_with_what_origin_held_before_and_read_back(sample):
    asked(sample)
    rewrite(sample, DRAFT_ORIGIN, lambda d: d.update(candidates=[{"target": SPEC, "suggested_by": "spec-author"}]))
    before = files(sample)
    code, out = cli(sample, *WRITE)
    assert code == 0 and f"would write {DRAFT_ORIGIN}" in out and "pat asked for an export" in out
    assert files(sample) == before, "without --write no file changes"

    code, out = cli(sample, *WRITE, "--write")
    assert code == 0 and f"wrote {DRAFT_ORIGIN}" in out
    held = origin(sample, DRAFT)
    assert held["conversation"] == {"summary": SUMMARY, "links": ["https://example.atlassian.net/browse/DEMO-7", CHAT], "people": ["pat", "sam"],
                                    "captured_on": "2026-11-26", "captured_by": "spec-author", "confirmed_by": ""}
    assert held["intake"] == ["manual-exp-1"] and held["candidates"] == [{"target": SPEC, "suggested_by": "spec-author"}] and held["schema"] == "agentic-origin/1"
    assert "  summary: |-\n    pat asked for an export" in (sample / DRAFT_ORIGIN).read_text(encoding="utf-8"), "the summary is lines a person can read in a review"
    assert {rel for rel, body in files(sample).items() if before.get(rel) != body} == {DRAFT_ORIGIN}, "and nothing else was touched"

    code, out = cli(sample, "product", "conversation", "--spec", DRAFT)
    assert code == 0 and "> pat asked for an export of invoices as CSV." in out and "> Left open: whether a refund is a row of its own." in out
    assert json.loads(cli(sample, "product", "conversation", "--spec", DRAFT, "--json")[1])["conversation"]["summary"] == SUMMARY

    assert cli(sample, "product", "conversation", "--spec", "009-nothing", "--summary", "x", "--captured-by", "pat", "--write")[0] == 2
    assert cli(sample, "product", "conversation", "--spec", DRAFT, "--summary", "x", "--write")[0] == 2, "it has to say who wrote the summary"
    assert cli(sample, "product", "conversation", "--spec", DRAFT, "--link", CHAT, "--write")[0] == 2, "the block is written whole"
    selftest._write(sample, f"specs/{DRAFT}/SEALED.yml", "schema: agentic-seal/1\n")
    sealed = files(sample)
    code, out = cli(sample, *WRITE, "--summary", "Another summary.", "--write")
    assert code == 2 and "is sealed" in out and files(sample) == sealed


def test_AC_002_what_the_screen_finds_in_the_summary_and_in_a_name_is_counted_and_never_written(sample):
    asked(sample)
    rewrite(sample, f"{core.KIT_DIR}/kit.yml", lambda d: d.update(intake={"screen": {"ticket": "TKT-[0-9]{6}"}}))
    said = f"pat asked on the phone. The number given was 123-45-6789, and the trial login is password = {PASSWORD}.\nSee TKT-123456."
    code, out = cli(sample, "product", "conversation", "--spec", DRAFT, "--summary", said, "--person", "pat", "--person", "sam (MRN 0045871)",
                    "--captured-by", "spec-author", "--write")
    assert code == 0, out
    assert "removed before writing: {'credential': 1, 'national-id': 1, 'record-number': 1, 'ticket': 1}" in out
    conv = origin(sample, DRAFT)["conversation"]
    assert conv["summary"] == ("pat asked on the phone. The number given was [removed: national-id], and the trial login is [removed: credential]\n"
                               "See [removed: ticket].")
    assert conv["people"] == ["pat", "sam ([removed: record-number])"]
    held = b"".join(files(sample).values())
    for value in ("123-45-6789", PASSWORD, "TKT-123456", "0045871"):
        assert value.encode() not in held and value not in out, value
    assert run(sample).ok, "what was written is what the check asks for"


def test_AC_003_a_link_that_is_no_address_or_carries_a_secret_is_refused_and_a_long_number_is_not_a_card(sample):
    asked(sample)
    before = files(sample)
    for link, why, secret in (("https://chat.example.com/t/1?token=abcdef123456", "link 2 holds what looks like a credential", "abcdef123456"),
                              (f"https://pat:{PASSWORD}@chat.example.com/t/1", "link 2 carries a user name or a password", PASSWORD),
                              ("chat.example.com/t/1", "link 2 is not an http or https address", "chat.example.com"),
                              ("ftp://chat.example.com/t/1", "link 2 is not an http or https address", "ftp:")):
        code, out = cli(sample, *WRITE, "--link", link, "--write")
        assert code == 2 and why in out and "Nothing was written." in out, link
        assert secret not in out, "the address may be the secret, so it is named by its place and not by its text"
        assert files(sample) == before, link

    link = "https://teams.example.com/l/message/19:a@thread.v2/1732632000003?createdTime=1732632000003"
    assert intake._luhn("1732632000003") and intake.screen(link)[1] == {"card-number": 2}, "the screen for text would take both numbers out"
    code, out = cli(sample, *WRITE, "--link", link, "--write")
    assert code == 0, out
    assert origin(sample, DRAFT)["conversation"]["links"] == ["https://example.atlassian.net/browse/DEMO-7", link, CHAT]
    assert run(sample).ok


def test_AC_004_only_a_listed_person_confirms_and_a_new_summary_is_not_confirmed(sample):
    asked(sample)
    confirm = ("product", "conversation", "--spec", DRAFT, "--confirmed-by")
    code, out = cli(sample, *confirm, "alice", "--write")
    assert code == 2 and "holds no summary to confirm" in out
    assert cli(sample, *WRITE, "--write")[0] == 0
    before = files(sample)

    code, out = cli(sample, *confirm, "spec-author", "--write")
    assert code == 2 and "spec-author is not listed in roles.yml" in out and "Nothing was written." in out
    assert files(sample) == before, "an agent's name confirms nothing"

    code, out = cli(sample, *confirm, "alice")
    assert code == 0 and "would write" in out and files(sample) == before
    code, out = cli(sample, *confirm, "alice", "--write")
    assert code == 0 and "The kit cannot tell who typed this command." in out and "evidence of the first gate" in out
    conv = origin(sample, DRAFT)["conversation"]
    assert conv["confirmed_by"] == "alice" and conv["summary"] == SUMMARY and conv["captured_by"] == "spec-author"

    code, out = cli(sample, *WRITE, "--summary", "pat asked for an export of invoices as PDF.", "--write")
    assert code == 0 and "No person has confirmed this summary." in out
    assert origin(sample, DRAFT)["conversation"]["confirmed_by"] == "", "the confirmation was of the earlier text"
    code, out = cli(sample, *WRITE, "--confirmed-by", "alice", "--write")
    assert code == 0 and origin(sample, DRAFT)["conversation"]["confirmed_by"] == "alice", "the one who writes it may confirm it in the same command"
    assert run(sample).ok


def test_AC_005_a_thread_link_is_put_on_a_record_by_hand_and_a_fetch_keeps_it(sample):
    second = "https://example.atlassian.net/browse/DEMO-1?focusedCommentId=10042"
    code, out = cli(sample, "intake", "add", "--title", "Export invoices as CSV", "--key", "EXP-1", "--thread", CHAT, "--thread", second)
    assert code == 0 and "new:" in out and "2 thread link(s) added" in out
    assert record(sample, "manual-exp-1")["threads"] == [CHAT, second]

    was = record(sample, "jira-demo-1")
    code, out = cli(sample, "intake", "add", "--platform", "jira", "--key", "DEMO-1", "--thread", CHAT)
    assert code == 0 and out.startswith("linked:")
    now = record(sample, "jira-demo-1")
    assert now.pop("threads") == [CHAT] and now == was, "a record that was fetched and specified keeps its text, its hash and its status"
    assert cli(sample, "intake", "add", "--platform", "jira", "--key", "DEMO-1", "--thread", CHAT)[1].startswith("unchanged:")
    assert run(sample, "CK-INTAKE-RECORD").ok and run(sample).ok

    before = files(sample)
    code, out = cli(sample, "intake", "add", "--platform", "jira", "--key", "NONE-1", "--thread", CHAT)
    assert code == 2 and "no intake record jira-none-1" in out
    code, out = cli(sample, "intake", "add", "--title", "Print receipts", "--thread", "https://chat.example.com/t/1?token=abcdef123456")
    assert code == 2 and "thread link 1 holds what looks like a credential" in out and "abcdef123456" not in out
    code, out = cli(sample, "intake", "add", "--thread", CHAT)
    assert code == 2 and "--title is required" in out
    assert files(sample) == before

    fetch(sample, "jira", SAID)   # a record nobody has acted on: new text replaces the old, and takes nothing else away
    assert cli(sample, "intake", "add", "--platform", "jira", "--key", "DEMO-9", "--thread", CHAT)[0] == 0
    rows, _ = fetch(sample, "jira", SAID, text="For the finance team, each month.")
    assert rows[0]["action"] == "updated"
    rec = record(sample, "jira-demo-9")
    assert rec["body"] == "For the finance team, each month." and rec["threads"] == [CHAT] and rec["discussion"]["comments"] == 2


# ── the digest of a discussion ──────────────────────────────────────────────────

@ALL
def test_AC_006_fetch_keeps_the_count_and_the_hash_of_what_people_said_and_leaves_out_the_kits_own_note(sample, tracker):
    rid = TRACKERS[tracker][1]
    rows, t = fetch(sample, tracker, SAID + [NOTE])
    assert [(r["id"], r["action"], r["discussion"]) for r in rows] == [(rid, "new", "new")]
    assert record(sample, rid)["discussion"] == {"comments": 2, "hash": by_hand(SCREENED), "fetched": "2026-11-26"}
    assert by_hand(SCREENED) != by_hand(SAID), "the hash is over the text as the screen leaves it"
    odd = ("1", "pat-ex\u00e4mple", "\u00abHello\u00bb is enough.")
    assert conversation.digest([dict(zip(("id", "author", "body"), odd))])["hash"] == by_hand([odd]), "outside ASCII: escaped in the line, UTF-8 in the text"
    assert asked_for_comments(t) == [FIRST_PAGE[tracker]], "one request, the one in the table of the spec"
    assert run(sample).ok

    quoting = [("201", "pat-example", "I read the note above (ref agentic:0123456789abcdef) and I do not agree."),
               ("202", "sam-example", NOTE[2] + "\nThis is wrong, see below.")]
    rows, _ = fetch(sample, tracker, SAID + [NOTE] + quoting, today="2026-11-27")
    assert record(sample, rid)["discussion"] == {"comments": 4, "hash": by_hand(SCREENED + quoting), "fetched": "2026-11-27"}, \
        "a person who quotes the kit's marker, or goes on after it, is counted: only the note's own form is left out"


def test_AC_007_a_project_issue_is_read_through_the_issue_and_a_draft_a_task_and_a_document_have_no_digest(sample):
    board = {"id": "board", "platform": "github", "project": {"owner": "example", "number": 5}, "auth": {"token_env": "TRACKER_GITHUB_TOKEN"}}
    t = Recorded([("POST", f"{GITHUB}/graphql", {"data": {"owner": {"projectV2": {"items": {"pageInfo": {"hasNextPage": False}, "nodes": [
                      {"id": "PVTI_2", "content": {"__typename": "Issue", "number": 3, "title": "Print receipts", "body": "On paper.", "url": "https://github.com/example/other/issues/3",
                                                   "repository": {"nameWithOwner": "example/other"}}},
                      {"id": "PVTI_3", "content": {"__typename": "DraftIssue", "title": "A draft", "body": "Not yet an issue."}}]}}}}}),
                  ("GET", f"{GITHUB}/repos/example/other/issues/3/comments?per_page=100&page=1", [as_github(*c) for c in SAID])])
    rows = trackers.fetch_sources(ctx(sample, today="2026-11-26"), [board], t, ENV)
    issue, a_draft = "github-example-other-3", intake.record_id("github", "project-example-5-draft-PVTI_3")
    assert {r["id"]: r["discussion"] for r in rows} == {issue: "new", a_draft: None}
    assert t.script == [] and len(t.calls) == 2, "the project, and the comments of the one issue"
    assert record(sample, issue)["discussion"] == {"comments": 2, "hash": by_hand(SCREENED), "fetched": "2026-11-26"}
    assert "discussion" not in record(sample, a_draft)

    selftest._write(sample, "requirements/inbox/a.md", "# Bulk import of users\n\nFrom a CSV file.\n")
    t = Recorded([("GET", "https://api.clickup.com/api/v2/list/901/task?page=0&include_closed=false",
                   {"tasks": [{"id": "abc1", "name": "Audit log", "text_content": "Record every sign-in."}], "last_page": True})])
    rows = trackers.fetch_sources(ctx(sample), [source(sample, "tasks"), source(sample, "inbox")], t, ENV)
    assert [(r["id"], r["discussion"]) for r in rows] == [("clickup-abc1", None), ("document-requirements-inbox-a-md", None)]
    assert len(t.calls) == 1, "no comment was asked for"
    assert not [r["id"] for r in rows if "discussion" in record(sample, r["id"])]


@ALL
def test_AC_008_a_long_discussion_is_read_page_by_page_up_to_a_limit_and_a_failed_read_leaves_the_record_alone(sample, seams, monkeypatch, tracker):
    sid, rid, _, pages = TRACKERS[tracker]
    many = [(str(1000 + n), "pat-example", f"Remark number {n} on the export.") for n in range(101)]
    rows, t = fetch(sample, tracker, many)
    assert rows[0]["discussion"] == "new" and record(sample, rid)["discussion"] == {"comments": 101, "hash": by_hand(many), "fetched": "2026-11-26"}
    assert asked_for_comments(t) == [url for _, url, _ in pages(many)] and len(asked_for_comments(t)) == 2, "the second page was asked for"
    assert asked_for_comments(t)[0] == FIRST_PAGE[tracker] and asked_for_comments(t)[1] == {
        "jira": "https://example.atlassian.net/rest/api/3/issue/DEMO-9/comment?startAt=100&maxResults=100",
        "ado": FIRST_PAGE["ado"] + "&continuationToken=page%2F2%2Bmore",
        "github": "https://api.github.com/repos/example/demo/issues/12/comments?per_page=100&page=2"}[tracker]

    whole = record(sample, rid)
    before = files(sample)
    connect.TRANSPORT, connect.ENV = Recorded(TRACKERS[tracker][2]("New words for the request.") + [("GET", FIRST_PAGE[tracker], (404, "no such item"))]), ENV
    code, out = cli(sample, "connect", "fetch", "--source", sid)
    assert code == 2 and "cannot fetch" in out and "HTTP 404" in out
    assert files(sample) == before and record(sample, rid) == whole, "the comments are read first, so the record is byte for byte what it was"

    monkeypatch.setattr(trackers, "COMMENT_PAGES", 1)   # the limit, made small: one page, and that page is full
    full = many[:100]
    t = Recorded(TRACKERS[tracker][2]() + pages(many)[:1])
    rows = trackers.fetch_sources(ctx(sample, today="2026-11-27"), [source(sample, sid)], t, ENV)
    assert t.script == [] and rows[0]["discussion"] == "updated"
    assert record(sample, rid)["discussion"] == {"comments": 100, "hash": by_hand(full), "fetched": "2026-11-27", "partial": True}
    r = run(sample)
    assert r.ok and [n for n in r.notes if rid in n and "longer than the kit reads" in n], r.as_dict()


def test_AC_009_a_later_fetch_leaves_a_digest_alone_replaces_it_or_notes_what_it_found_beside_it(sample, seams):
    rid = "jira-demo-9"
    fetch(sample, "jira", SAID)
    before = files(sample)
    rows, _ = fetch(sample, "jira", SAID, today="2026-11-27")
    assert (rows[0]["action"], rows[0]["discussion"]) == ("unchanged", "unchanged") and files(sample) == before

    three = SAID + [LATER]
    rows, _ = fetch(sample, "jira", three, today="2026-11-27")   # nobody has acted on the record yet
    assert rows[0]["discussion"] == "updated"
    assert record(sample, rid)["discussion"] == {"comments": 3, "hash": by_hand(SCREENED + [LATER]), "fetched": "2026-11-27"}

    acted_on(sample, rid)
    four = three + [("104", "sam-example", "A person with no name is greeted as a guest.")]
    before = files(sample)
    connect.ENV = ENV
    connect.TRANSPORT = script("jira", four)
    code, out = cli(sample, "connect", "fetch", "--source", "backlog", "--dry-run", "--json", "--today", "2026-11-28")
    assert code == 0 and json.loads(out)[0]["discussion"] == "moved" and files(sample) == before, "a dry run says what a fetch would do"

    connect.TRANSPORT = script("jira", four)
    code, out = cli(sample, "connect", "fetch", "--source", "backlog", "--today", "2026-11-28")
    assert code == 0 and "unchanged       jira-demo-9  (discussion moved)" in out
    assert "1 item(s) from 1 source(s); 0 new, 0 changed after work began, 1 with a discussion that moved after work began" in out
    held = record(sample, rid)["discussion"]
    assert (held["comments"], held["hash"], held["fetched"]) == (3, by_hand(SCREENED + [LATER]), "2026-11-27"), "what was there when work began stays"
    assert held["latest"] == {"comments": 4, "hash": by_hand(SCREENED + [LATER, four[-1]]), "fetched": "2026-11-28"}

    connect.TRANSPORT = script("jira", four)
    code, out = cli(sample, "connect", "fetch", "--source", "backlog", "--json", "--today", "2026-11-29")
    assert json.loads(out)[0]["discussion"] == "unchanged" and record(sample, rid)["discussion"] == held, "the same again is not news"
    listing = cli(sample, "intake", "list")[1]
    assert [line for line in listing.splitlines() if rid in line and line.endswith("(discussion moved)")]
    assert not [line for line in listing.splitlines() if "jira-demo-1 " in line and "discussion moved" in line]


# ── the check ───────────────────────────────────────────────────────────────────

def test_AC_010_a_discussion_that_moved_fails_the_check_until_a_product_owner_has_looked(sample):
    assert run(sample).ok
    psample._moved(sample)
    r = run(sample)
    assert [f.path for f in r.findings] == [psample.RECORD]
    assert "the discussion moved after this record was specified: 2 comment(s) when fetched on 2026-11-21, 3 on 2026-11-25" in msgs(r)
    latest = record(sample, "jira-demo-1")["discussion"]["latest"]["hash"]

    def acknowledge(**given):
        ack = {"hash": latest, "action": "ignore", "reason": "The new comment asks for nothing", "decided_by": {"reviewer": "alice", "role": "product-owner"}, **given}
        rewrite(sample, psample.RECORD, lambda d: d["discussion"].update(acknowledged=ack))
        return msgs(run(sample))

    assert "the discussion moved after this record was specified" in acknowledge(hash="sha256:" + "0" * 64), "an acknowledgement of something else"
    assert "discussion.acknowledged gives no reason" in acknowledge(reason=" ")
    assert "discussion.acknowledged.action must be amend or ignore" in acknowledge(action="later")
    assert "it takes product-owner" in acknowledge(decided_by={"reviewer": "bob", "role": "qa"})
    assert "does not hold the role" in acknowledge(decided_by={"reviewer": "bob", "role": "product-owner"})
    assert acknowledge() == "" and run(sample).ok
    assert run(sample, "CK-INTAKE-RECORD").ok and run(sample, "CK-INTAKE-DRIFT").ok, "the item's own text did not change"

    again = conversation.digest(psample.SAID + [{"id": "10003", "author": "pat", "body": "Use the first name only."},
                                                {"id": "10004", "author": "sam", "body": "And the family name on an invoice."}], fetched="2026-11-27")
    assert conversation.store_digest(sample, "jira-demo-1", again) == "moved"
    assert "3 on 2026-11-25" not in msgs(run(sample)) and "2 comment(s) when fetched on 2026-11-21, 4 on 2026-11-27" in msgs(run(sample)), "it moved again"

    acted_on(sample, "jira-demo-1", "rejected")
    assert run(sample).ok, "what was said later about a request that was turned down asks nothing of anyone"


@pytest.mark.parametrize("rel,change,expect", [
    (ORIGIN, lambda d: d["conversation"].update(summary=f"pat said the login is password = {PASSWORD}"), "holds 1 value(s) that look like a credential"),
    (ORIGIN, lambda d: d["conversation"].update(confirmed_by="spec-author"), "`confirmed_by` names spec-author, who is not listed in roles.yml"),
    (ORIGIN, lambda d: d["conversation"].update(links=["https://chat.example.com/t/1?token=abcdef123456"]), "link 1 holds what looks like a credential"),
    (ORIGIN, lambda d: d["conversation"].pop("captured_by"), "does not say who wrote the summary"),
    (ORIGIN, lambda d: d["conversation"].update(captured_on="last week"), "does not say on which day"),
    (ORIGIN, lambda d: d["conversation"].update(summary="  "), "the conversation has no summary"),
    (ORIGIN, lambda d: d["conversation"].update(people=["pat", "sam (MRN 0045871)"]), "holds 1 value(s) that look like a record-number"),
    (ORIGIN, lambda d: d.update(conversation="pat and sam talked"), "`conversation` must be a mapping"),
    (psample.RECORD, lambda d: d.update(threads=["https://chat.example.com/t/1?token=abcdef123456"]), "thread link 1 holds what looks like a credential"),
    (psample.RECORD, lambda d: d["discussion"].pop("hash"), "`discussion` must hold `comments`, a number, and `hash`"),
    (psample.RECORD, lambda d: d["discussion"].update(comments="two"), "`discussion` must hold `comments`, a number, and `hash`"),
])
def test_AC_011_what_is_kept_by_hand_and_is_not_what_the_kit_writes_fails_the_check(sample, rel, change, expect):
    rewrite(sample, rel, change)
    r = run(sample)
    assert expect in msgs(r) and [f.path for f in r.findings] == [rel] * len(r.findings)
    assert "abcdef123456" not in msgs(r) and PASSWORD not in msgs(r), "a finding does not repeat what it found"


# ── what a reviewer and a reader are shown ──────────────────────────────────────

def section_of(text):
    assert text.count(HEADING) == 1
    return text.split(HEADING + "\n", 1)[1].split("\n\n", 1)[0].splitlines()


def test_AC_012_the_brief_of_the_first_gate_shows_the_summary_and_that_no_person_has_confirmed_it(sample, monkeypatch):
    rewrite(sample, ORIGIN, lambda d: d["conversation"].update(confirmed_by=""))
    brief = lanes.build_brief(ctx(sample), SPEC, "G1")
    part = section_of(brief)
    assert part[0] == "- **No person has confirmed this summary.** Written by spec-author on 2026-11-21. Read the thread before you rely on it."
    assert part[1:3] == ["> pat asked for a greeting that uses the person's name. sam agreed to take the name from the account.",
                         "> Left open: what to say when the account has no name."]
    assert part[3:] == ["- **Links:** https://example.atlassian.net/browse/DEMO-1", "- **People:** pat, sam"]
    assert len(brief.splitlines()) <= lanes.BRIEF_LINES, "the brief is still one page"
    r = run(sample)
    assert r.ok, "a summary nobody has confirmed is not a failure"
    assert r.notes == [f"{SPEC}: the conversation names 1 link(s) and no person has confirmed its summary; the brief for G1 says so"]
    assert HEADING not in lanes.build_brief(ctx(sample), SPEC, "G3"), "the Product Owner reads it at the first gate"

    assert cli(sample, "product", "conversation", "--spec", SPEC, "--confirmed-by", "alice", "--write")[0] == 0
    assert section_of(lanes.build_brief(ctx(sample), SPEC, "G1"))[0].startswith("- **Confirmed by alice**, as origin.yml says; the kit cannot tell who wrote that line.")
    assert run(sample).notes == []

    long = "\n".join(f"Line {n} of what was said." for n in range(1, 8))
    rewrite(sample, ORIGIN, lambda d: d["conversation"].update(summary=long, links=[f"https://chat.example.com/t/{n}" for n in range(6)]))
    part = section_of(lanes.build_brief(ctx(sample), SPEC, "G1"))
    assert len(part) == 7 and part[4] == "> (and 4 more line(s), in origin.yml)" and part[5].endswith("https://chat.example.com/t/2 and 3 more")

    asked(sample)   # a draft with a thread link on its record, and no summary
    part = section_of(lanes.build_brief(ctx(sample), DRAFT, "G1"))
    assert part == ["- No summary of the conversation is recorded. `manual-exp-1` has comments or a thread link, and nobody has written down "
                    "for this change what was agreed there."]
    other = draft(sample, "003-print")
    assert HEADING not in lanes.build_brief(ctx(sample), other, "G1"), "where nothing is recorded the brief says nothing"
    selftest._write(sample, f"specs/{other}/origin.yml", "schema: agentic-origin/1\nintake: [jira-demo-1]\n")
    assert section_of(lanes.build_brief(ctx(sample), other, "G1"))[0].startswith("- No summary of the conversation is recorded. `jira-demo-1` has comments"), \
        "a record with comments and no thread link counts as well"

    monkeypatch.setattr(core, "LANE_HOOKS", [lambda c, spec: "fast" if spec == DRAFT else None])   # the fast lane folds G1 into G4
    assert HEADING in lanes.build_brief(ctx(sample), DRAFT, "G4") and conversation.brief_hook(ctx(sample), DRAFT, "G1") == []


def test_AC_013_the_section_for_a_changes_page_holds_the_summary_the_confirmation_and_the_state_of_the_discussion(sample):
    assert conversation.changeset_hook in core.CHANGESET_HOOKS
    assert cli(sample, "intake", "add", "--platform", "jira", "--key", "DEMO-1", "--thread", CHAT)[0] == 0
    psample._moved(sample)
    (heading, lines), = conversation.changeset_hook(ctx(sample), SPEC)
    assert heading == "The conversation behind it"
    assert lines == [
        "- **Confirmed by alice**, as origin.yml says; the kit cannot tell who wrote that line. Written by spec-author on 2026-11-21.",
        "> pat asked for a greeting that uses the person's name. sam agreed to take the name from the account.",
        "> Left open: what to say when the account has no name.",
        "- **Links:**", "  - https://example.atlassian.net/browse/DEMO-1",
        "- **People:** pat, sam",
        f"- `jira-demo-1` (jira DEMO-1): thread link {CHAT}",
        "- `jira-demo-1` (jira DEMO-1): 2 comment(s) when fetched on 2026-11-21; 3 on 2026-11-25: the discussion moved, "
        "and nobody has acknowledged it (CK-CONVERSATION)"]

    ack = {"hash": record(sample, "jira-demo-1")["discussion"]["latest"]["hash"], "action": "amend", "reason": "The first name only is a new rule",
           "decided_by": {"reviewer": "alice", "role": "product-owner"}}
    rewrite(sample, psample.RECORD, lambda d: d["discussion"].update(acknowledged=ack))
    assert conversation.changeset_hook(ctx(sample), SPEC)[0][1][-1].endswith(
        "the discussion moved, and alice (product-owner) acknowledged it as amend: The first name only is a new rule")

    other = draft(sample)
    assert conversation.changeset_hook(ctx(sample), other) == [("The conversation behind it", [
        "- No summary of the conversation is recorded for this change. That is not the same as no conversation."])]
    for hook in core.CHANGESET_HOOKS:   # whatever else is registered, a page can be built for both specs
        assert all(isinstance(title, str) and isinstance(body, list) for spec in (SPEC, other) for title, body in hook(ctx(sample), spec))


def test_AC_014_no_file_and_no_output_holds_what_anyone_said_or_who_said_it(sample, seams):
    connect.ENV = ENV
    printed = ""
    for tracker, (sid, rid, _, _) in sorted(TRACKERS.items()):
        connect.TRANSPORT = script(tracker, SAID + [NOTE])
        code, out = cli(sample, "connect", "fetch", "--source", sid, "--today", "2026-11-26")
        assert code == 0 and connect.TRANSPORT.script == [], out
        printed += out
        acted_on(sample, rid)
        connect.TRANSPORT = script(tracker, SAID + [NOTE, LATER])
        code, out = cli(sample, "connect", "fetch", "--source", sid, "--json", "--today", "2026-11-27")
        assert code == 0 and json.loads(out)[0]["discussion"] == "moved" and connect.TRANSPORT.script == [], out
        printed += out
        held = record(sample, rid)["discussion"]
        assert (held["comments"], held["latest"]["comments"]) == (2, 3) and held["latest"]["hash"] == by_hand(SCREENED + [LATER])
    printed += cli(sample, "check", "CK-CONVERSATION")[1] + cli(sample, "intake", "list")[1]
    printed += "\n".join(line for _, body in conversation.changeset_hook(ctx(sample), SPEC) for line in body)
    held = b"".join(files(sample).values())
    said = [line for _, _, text in SAID + [LATER] for line in text.splitlines()] + [c["body"] for c in psample.SAID] + [PASSWORD, "[removed: credential]"]
    names = [account for _, account, _ in SAID] + [shown(account) for _, account, _ in SAID] + [f"{account}@example.com" for _, account, _ in SAID]
    assert len(said) == 8 and len(names) == 6
    for text in said + names:
        assert text.encode("utf-8") not in held, f"a file holds {text!r}"
        assert text not in printed, f"the output holds {text!r}"


def test_AC_015_the_self_test_has_a_fixture_the_check_passes_and_one_it_fails(tmp_path):
    import agentic_kit_product as product
    assert "CK-CONVERSATION" in product.PRODUCT_CHECKS and "CK-CONVERSATION" in selftest.all_fixtures()
    what, broken, pass_options, fail_options = psample.fixtures()["CK-CONVERSATION"]
    good, bad = tmp_path / "good", tmp_path / "bad"
    selftest.build_sample(good)
    assert record(good, "jira-demo-1")["discussion"] == {"comments": 2, "hash": conversation.digest(psample.SAID)["hash"], "fetched": selftest.TODAY}
    assert origin(good)["conversation"]["confirmed_by"] == "alice" and origin(good)["conversation"]["summary"].startswith("pat asked for a greeting")
    r = run(good, **pass_options)
    assert r.ok and r.notes == [], r.as_dict()
    selftest.build_sample(bad)
    broken(bad)
    r = run(bad, **fail_options)
    assert r.findings and "the discussion moved after this record was specified" in msgs(r) and "moved" in what
