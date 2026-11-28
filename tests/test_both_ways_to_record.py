"""Tests for docs/design/both-ways-to-record.md (BWR-1 to BWR-8): a gate recorded either way where approvals are
dismissed on a push.

No test reaches GitHub. The reviews come from the file adapter's stand-in, in the order its file has them, as GitHub
lists a pull request's reviews in the order they were submitted.
Run: python -m pytest tests/test_both_ways_to_record.py -q
"""
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentic_kit import core, demo, selftest  # noqa: E402
from agentic_kit.__main__ import _evidence_files  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

import test_changeset as tcs  # noqa: E402  (the demo's project as a git repository, and its helpers)
import test_connect as tc  # noqa: E402  (a review added to the self-test's sample)

SPEC, GATE, CHANGE = demo.SPEC, demo.GATE, demo.CHANGE
RECORD = f"{core.KIT_DIR}/decisions/{SPEC}/{GATE}.yml"
CONNECT_FLOW = ROOT / "extensions" / "agentic-connect" / "ci" / "github-actions.yml"


def project(root):
    """The demo's project as a git repository, with G1 approved in review 2 and recorded with `record --change`, the
    record committed as a push onto the pull request would commit it. The commit of the review, the line, and the commit
    of the record."""
    root.mkdir(parents=True, exist_ok=True)
    demo.build_project(root)
    demo._git(root, "init", "-q")
    demo._git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    assert tcs.kit(root, "brief", "--spec", SPEC, "--gate", GATE, "--write")[0] == 0
    reviewed = demo._commit(root, "the spec and the reviewer's page")
    line = tcs.line_of(root)
    demo._reviews(root, [demo._review(2, demo.PERSON, reviewed, line)])
    code, text = tcs.kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    assert code == 0, text
    recorded = demo._commit(root, "the record, pushed onto the pull request")
    return reviewed, line, recorded


def reviews(root, change):
    """Change the reviews the stand-in holds for the demo's pull request."""
    tcs.stand_in(root, lambda held: change(held["changes"][CHANGE]["reviews"]))


def dismiss(found, rid="2"):
    next(r for r in found if r["id"] == rid)["state"] = "DISMISSED"


def run(root, cid):
    return core.run_check(cid, tcs.ctx(root))


def msgs(result):
    return " | ".join(f.message for f in result.findings)


# ── BWR-1, BWR-2: a later approval stands for a dismissed one ─────────────────────

def test_AC_001_a_later_approval_with_the_same_line_stands_for_the_dismissed_review(tmp_path):
    root = tmp_path / "stands"
    reviewed, line, recorded = project(root)
    reviews(root, lambda found: (dismiss(found), found.append(demo._review(3, demo.PERSON, recorded, line))))
    approver, mirror = run(root, "CK-APPROVER"), run(root, "CK-GATE-MIRROR")
    assert approver.ok and mirror.ok, (msgs(approver), msgs(mirror))
    for result in (approver, mirror):
        assert any("review 2" in n and "review 3" in n and "stands for it" in n for n in result.notes), result.notes

    def fails(name, change):
        other = tmp_path / name
        _, line_, recorded_ = project(other)
        reviews(other, lambda found: change(found, line_, recorded_))
        said = msgs(run(other, "CK-APPROVER"))
        assert "the review state is DISMISSED, not APPROVED" in said, (name, said)

    fails("nobody", lambda found, l, c: dismiss(found))
    fails("another", lambda found, l, c: (dismiss(found), found.append(demo._review(3, "sam", c, l))))
    fails("other-hash", lambda found, l, c: (dismiss(found), found.append(demo._review(3, demo.PERSON, c, l[:-4] + "0000"))))
    fails("before", lambda found, l, c: (dismiss(found), found.insert(0, demo._review(3, demo.PERSON, c, l))))

    changed = tmp_path / "changed"
    _, line, _ = project(changed)
    spec = changed / demo.SPEC_FILE
    spec.write_text(spec.read_text(encoding="utf-8") + "\nA sentence added after the review.\n", encoding="utf-8", newline="\n")
    elsewhere = demo._commit(changed, "the evidence changed")
    reviews(changed, lambda found: (dismiss(found), found.append(demo._review(3, demo.PERSON, elsewhere, line))))
    assert "DISMISSED" in msgs(run(changed, "CK-APPROVER")), "where its commit holds other evidence, a later review does not stand in"


def test_AC_002_a_review_that_stands_in_is_held_to_the_rules_of_the_one_it_stands_for(tmp_path):
    root = tmp_path / "author"
    _, line, recorded = project(root)
    reviews(root, lambda found: (dismiss(found), found.append(demo._review(3, demo.PERSON, recorded, line))))
    tcs.stand_in(root, lambda held: held["changes"][CHANGE]["authors"].append(demo.PERSON))
    result = run(root, "CK-APPROVER")
    assert any("review 3" in n and "stands for it" in n for n in result.notes), "the later review was taken in place of the dismissed one"
    assert f"{demo.PERSON} authored the change and exceptions are forbidden" in msgs(result), "and held to the same rule"
    assert "DISMISSED" not in msgs(result)


# ── BWR-3: record once ────────────────────────────────────────────────────────────

def test_AC_003_record_writes_nothing_where_the_gate_is_recorded_already_for_the_same_evidence(tmp_path):
    root = tmp_path / "once"
    _, line, recorded = project(root)
    record, audit = root / RECORD, root / core.KIT_DIR / f"audit/{SPEC}.jsonl"
    before = (record.read_bytes(), audit.read_bytes())
    code, text = tcs.kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    assert code == 0 and "is recorded already for this evidence" in text and "Nothing was written" in text, text
    assert (record.read_bytes(), audit.read_bytes()) == before

    reviews(root, lambda found: (dismiss(found), found.append(demo._review(3, demo.PERSON, recorded, line))))
    code, text = tcs.kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    assert code == 0 and "review 3 (for review 2, which was dismissed)" in text and "Nothing was written" in text, text
    assert (record.read_bytes(), audit.read_bytes()) == before

    spec = root / demo.SPEC_FILE
    spec.write_text(spec.read_text(encoding="utf-8") + "\nA sentence added before the next review.\n", encoding="utf-8", newline="\n")
    assert tcs.kit(root, "brief", "--spec", SPEC, "--gate", GATE, "--write")[0] == 0
    again = demo._commit(root, "the evidence changed")
    new_line = tcs.line_of(root)
    assert new_line != line
    reviews(root, lambda found: found.append(demo._review(4, demo.PERSON, again, new_line)))
    code, text = tcs.kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    assert code == 0 and "wrote" in text and "recorded already" not in text, text
    written = yaml.safe_load(record.read_text(encoding="utf-8"))
    assert written["approvals"][0]["review_ref"] == f"{CHANGE}#review-4" and written["superseded"][0]["approvals"][0]["review_ref"] == f"{CHANGE}#review-2"

    record.write_text("approvals: [a record, cut short\n", encoding="utf-8", newline="\n")   # a record that is not YAML
    before = (record.read_bytes(), audit.read_bytes())
    code, text = tcs.kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    assert code == 2 and "is not a record the kit can read" in text and "Nothing was recorded." in text, text
    assert (record.read_bytes(), audit.read_bytes()) == before, "neither the record nor the audit log is touched"


# ── BWR-4: the note names both ways ─────────────────────────────────────────────

def test_AC_004_the_note_names_both_ways(tmp_path):
    root = tmp_path / "note"
    root.mkdir()
    demo.build_project(root)
    demo._git(root, "init", "-q")
    demo._git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    assert tcs.kit(root, "brief", "--spec", SPEC, "--gate", GATE, "--write")[0] == 0
    reviewed = demo._commit(root, "the spec and the reviewer's page")
    demo._reviews(root, [demo._review(2, demo.PERSON, reviewed, tcs.line_of(root))])
    tcs.stand_in(root, lambda held: held.update(dismiss_stale_reviews_on_push=True))
    code, text = tcs.kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    flat = " ".join(text.split())
    assert code == 0 and "approve again with the same line" in flat and "after the merge, on a branch of its own" in flat, text


# ── BWR-5: mirror after the merge ────────────────────────────────────────────────

MERGED = "f" * 40


def sample(tmp_path, name, state="merged", merge_commit=MERGED):
    root = tmp_path / name
    root.mkdir()
    selftest.build_sample(root)
    tcs.stand_in(root, lambda held: held["changes"]["pull/1"].update(state=state, merge_commit=merge_commit))
    return root


def g6(root):
    return root / core.KIT_DIR / f"decisions/{selftest.SPEC}/G6.yml"


def test_AC_005_mirror_after_the_merge_finds_the_pull_request_and_takes_the_commit_from_the_reviews(tmp_path):
    root = sample(tmp_path, "merged")
    digest = tc._open_g6(root)
    tc._review(root, id="95", reviewer="bob", state="APPROVED", body=core.approval_line("G6", "approve", digest))
    code, out = tc.cli(root, "connect", "mirror", "--merged", MERGED, "--write")
    assert code == 0 and "merged pull/1" in out and f"{selftest.SPEC} G6: approve - recorded" in out, out
    assert yaml.safe_load(g6(root).read_text(encoding="utf-8"))["commit"] == selftest.COMMIT, "the commit the review is on"

    nothing = sample(tmp_path, "nothing", state="open", merge_commit="")
    code, out = tc.cli(nothing, "connect", "mirror", "--merged", MERGED, "--write")
    assert code == 0 and f"no pull request was merged as {MERGED}" in out and not g6(nothing).exists(), out

    assert tc.cli(root, "connect", "mirror", "--merged", MERGED, "--change", "pull/1")[0] == 2

    # G5 asks for two people; their reviews on two commits do not make one record
    split = sample(tmp_path, "split")
    assert tc.cli(split, "brief", "--spec", selftest.SPEC, "--gate", "G5", "--write")[0] == 0
    c = tc.ctx(split)
    digest = core.evidence_hash(c.src, selftest.SPEC, "G5", _evidence_files(c, selftest.SPEC, "G5", None))
    line = core.approval_line("G5", "approve", digest)
    path = split / core.KIT_DIR / "_adapter/reviews.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["changes"]["pull/1"]["reviews"] += [{"id": "96", "reviewer": "alice", "type": "User", "state": "APPROVED", "commit": "a" * 40, "body": line},
                                             {"id": "97", "reviewer": "bob", "type": "User", "state": "APPROVED", "commit": "b" * 40, "body": line}]
    path.write_text(json.dumps(data), encoding="utf-8")
    g5 = split / core.KIT_DIR / f"decisions/{selftest.SPEC}/G5.yml"
    before = g5.read_bytes() if g5.exists() else None
    code, out = tc.cli(split, "connect", "mirror", "--merged", MERGED, "--write")
    assert code == 0 and "G5: approve - not recorded: the reviews that carry the line are not on one commit" in out, out
    assert (g5.read_bytes() if g5.exists() else None) == before


# ── BWR-6, BWR-7: the job that mirrors after the merge ────────────────────────────

def test_AC_006_the_connect_workflow_has_a_job_that_mirrors_after_the_merge(tmp_path):
    text = CONNECT_FLOW.read_text(encoding="utf-8")
    flow = yaml.safe_load(text)
    job = flow["jobs"]["mirror-after-merge"]
    condition = " ".join(job["if"].split())
    for words in ("vars.AGENTIC_MIRROR == 'after-merge'", "github.event.workflow_run.event == 'push'",
                  "github.event.workflow_run.head_branch == github.event.repository.default_branch",
                  "github.event.workflow_run.head_repository.full_name == github.repository"):
        assert words in condition, words
    assert job["permissions"] == {"contents": "write", "pull-requests": "write"}
    script = "\n".join(step.get("run", "") for step in job["steps"])
    assert "connect mirror --merged" in script and "gh pr create" in script and 'refs/heads/$RECORDS' in script and "agentic/records-" in script
    assert "secrets." not in json.dumps(job), "no secret"
    assert "vars.AGENTIC_MIRROR == 'true'" in flow["jobs"]["mirror"]["if"]
    head = text.split("\nname: agentic-connect", 1)[0]
    assert re.search(r"#\s+true\s", head) and re.search(r"#\s+after-merge\s", head)
    # and the check that guards pipelines finds nothing in it
    root = tmp_path / "flow"
    root.mkdir()
    selftest.build_sample(root)
    (root / ".github/workflows/agentic-connect.yml").write_text(CONNECT_FLOW.read_text(encoding="utf-8"), encoding="utf-8")
    result = core.run_check("CK-PIPELINE-SECRETS", selftest.context(root))
    assert not [f for f in result.findings if "agentic-connect.yml" in str(f.path)], msgs(result)


# ── BWR-8: the documents ─────────────────────────────────────────────────────────

def test_AC_007_the_documents_name_both_ways():
    for rel in ("docs/install.md", "extensions/agentic/commands/gate.md", "extensions/agentic-connect/README.md", "docs/limits.md"):
        text = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        assert re.search(r"approves? again with the same line", text), rel
        assert "after the merge" in text and "both-ways-to-record.md" in text or rel.endswith("gate.md"), rel
