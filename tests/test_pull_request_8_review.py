"""What GitHub Copilot's review of pull request 8 found (PRV-1 to PRV-7, docs/design/pull-request-8-review.md).

Each test is named after the acceptance criterion it proves, and builds on the helpers of the four features' own tests.
No test reaches GitHub: the reviews come from the file adapter's stand-in.
Run: python -m pytest tests/test_pull_request_8_review.py -q
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import yaml

import test_both_ways_to_record as tbw
import test_changeset as tcs
import test_decision_log as tdl
import test_decision_review as tdr
import test_mcp as tm
import test_mcp_first_write as tmf
import test_programme_release as tpr
from agentic_kit import core, decision_log, demo, selftest
from agentic_kit.__main__ import main
from agentic_kit_mcp import tools

BROKEN_TAIL = '{"seq": 1, "hash": "sha256:' + "0" * 64 + '", "action": "decision-log.add"}\n{"seq": 2, "action": "cut short\n'


def split(root, *argv):
    """A command of the kit: its exit code, what it printed on standard output, and what on standard error."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(["--root", str(root), *argv])
        except SystemExit as stop:
            code = stop.code if isinstance(stop.code, int) else 2
    return code, out.getvalue(), err.getvalue()


# ── PRV-1: the release check reads the whole programme entry ────────────────────

def test_AC_001_a_release_is_not_passed_over_a_contract_or_a_rollout_order_of_the_wrong_shape(tmp_path):
    root = tmp_path
    selftest.build_sample(root)
    for name in (tpr.FIRST, tpr.SECOND):
        selftest._write(root, f"specs/{name}/spec.md", tpr.spec_md(name, parent=tpr.PARENT))
        tpr.passed(root, name)
    tpr.parent(root, {"spec": tpr.FIRST}, {"spec": tpr.SECOND})
    tpr.record(root, tpr.PARENT, "G7")
    assert tpr.run(root).ok, tpr.msgs(tpr.run(root))
    rows = [{"spec": tpr.FIRST}, {"spec": tpr.SECOND}]
    for prog, said in (({"children": rows, "contract": ["a", "list"], "rollout": [tpr.FIRST, tpr.SECOND]}, "its shared contract is not a name"),
                       ({"children": rows, "contract": "contract-demo-openapi", "rollout": 5}, "its rollout order is not a list")):
        tpr.parent(root, programme=prog)
        r = tpr.run(root)
        assert not r.ok and r.not_run is None and tpr.msgs(r) == [f"the release of {tpr.PARENT} (G7) is approved while {said}"], tpr.msgs(r)


# ── PRV-2: the audit log is asked before the decision log is written ────────────

def test_AC_002_nothing_is_written_to_a_decision_log_whose_audit_log_cannot_take_an_entry(tmp_path):
    root = tdl.lite(tmp_path / "cli")
    (root / tdl.AUDIT).parent.mkdir(parents=True, exist_ok=True)
    (root / tdl.AUDIT).write_text(BROKEN_TAIL, encoding="utf-8", newline="\n")
    code, text = tdl.kit(root, "decision", "add", "--spec", tdl.SPEC, "--title", tdl.QUESTION, "--by", demo.PERSON)
    assert code == 2 and "is not an entry of the audit log" in text and "Nothing was written." in text, text
    assert not (root / tdl.LOG).exists() and (root / tdl.AUDIT).read_text(encoding="utf-8") == BROKEN_TAIL

    shop = tmf.project(tmp_path / "mcp")
    selftest._write(shop, tmf.AUDIT, BROKEN_TAIL)
    before = tm.snapshot(shop)
    with tmf.writing(shop) as client:
        client.open()
        text, failed = client.call("decision_add", spec=tmf.NOTES, question=tmf.ASKED)
    assert failed and "is not an entry of the audit log" in text, text
    assert tm.snapshot(shop) == before

    other = tmf.project(tmp_path / "rollback")

    def fails_on_the_audit_log(ctx, spec, questions, by, affects=(), actor=None):
        doc = {"schema": decision_log.SCHEMA, "entries": [{"id": "D-001", "title": questions[0], "state": "proposed", "proposed_by": by}]}
        decision_log.write(ctx, spec, doc)  # the log is written, and then the audit log cannot be added to
        raise OSError("the audit log could not be opened")

    before = tm.snapshot(other)
    with pytest.raises(tools.Refused, match="nothing was written: the audit log could not be added to"):
        tools.decision_add(tools.Project(other), {"spec": tmf.NOTES, "question": tmf.ASKED}, fails_on_the_audit_log)
    assert tm.snapshot(other) == before, "the log made for the call is gone again"
    decision_log.write(selftest.context(other), tmf.NOTES, {"schema": decision_log.SCHEMA, "entries": []})
    held = (other / tmf.LOG).read_bytes()
    with pytest.raises(tools.Refused):
        tools.decision_add(tools.Project(other), {"spec": tmf.NOTES, "question": tmf.ASKED}, fails_on_the_audit_log)
    assert (other / tmf.LOG).read_bytes() == held, "a log that was there is put back as it was"


# ── PRV-3: what `record` compares before it writes nothing ──────────────────────

def test_AC_003_record_writes_again_where_the_exception_or_the_people_differ(tmp_path):
    root = tmp_path / "exception"
    reviewed, line, _ = tbw.project(root)
    tcs.stand_in(root, lambda held: held["changes"][tbw.CHANGE].update(authors=[demo.PERSON]))  # the reviewer also wrote the change
    record = root / tbw.RECORD
    assert yaml.safe_load(record.read_text(encoding="utf-8"))["single_approver_exception"] is False
    code, text = tcs.kit(root, "record", "--spec", tbw.SPEC, "--gate", tbw.GATE, "--change", tbw.CHANGE)
    assert code == 0 and "recorded already" in text, "the same run again: nothing to write"
    code, text = tcs.kit(root, "record", "--spec", tbw.SPEC, "--gate", tbw.GATE, "--change", tbw.CHANGE, "--exception")
    assert code == 0 and "wrote" in text and "recorded already" not in text, text
    assert yaml.safe_load(record.read_text(encoding="utf-8"))["single_approver_exception"] is True
    before = record.read_bytes()
    code, text = tcs.kit(root, "record", "--spec", tbw.SPEC, "--gate", tbw.GATE, "--change", tbw.CHANGE, "--exception")
    assert code == 0 and "recorded already" in text and record.read_bytes() == before

    root = tmp_path / "people"
    reviewed, line, _ = tbw.project(root)
    roles = root / core.KIT_DIR / "roles.yml"
    held = yaml.safe_load(roles.read_text(encoding="utf-8"))
    for person in held["people"]:
        person["roles"] = [role for role in person["roles"] if role != demo.ROLE] + ([demo.ROLE] if person["id"] == "sam" else [])
    roles.write_text(yaml.safe_dump(held, sort_keys=False), encoding="utf-8", newline="\n")
    tbw.reviews(root, lambda found: found.append(demo._review(3, "sam", reviewed, line)))   # pat's approval still stands
    code, text = tcs.kit(root, "record", "--spec", tbw.SPEC, "--gate", tbw.GATE, "--change", tbw.CHANGE)
    assert code == 0 and "wrote" in text and "recorded already" not in text, text
    written = yaml.safe_load((root / tbw.RECORD).read_text(encoding="utf-8"))
    assert [(a["reviewer"], a["review_ref"]) for a in written["approvals"]] == [("sam", f"{tbw.CHANGE}#review-3")]


# ── PRV-4: equivalent reviews of the same person ────────────────────────────────

def test_AC_004_a_persons_equivalent_reviews_are_mirrored_with_the_one_that_stands(tmp_path):
    root = tmp_path
    reviewed, line, recorded = tbw.project(root)
    tbw.reviews(root, lambda found: (tbw.dismiss(found), found.append({**demo._review(3, demo.PERSON, recorded, line), "state": "DISMISSED"}),
                                     found.append(demo._review(4, demo.PERSON, recorded, line))))
    for cid in ("CK-APPROVER", "CK-GATE-MIRROR"):
        r = tbw.run(root, cid)
        assert r.ok and r.not_run is None, (cid, tbw.msgs(r))
    code, text = tcs.kit(root, "record", "--spec", tbw.SPEC, "--gate", tbw.GATE, "--change", tbw.CHANGE)
    assert code == 0 and "review 4 (for review 2, which was dismissed)" in text and "Nothing was written" in text, text

    other_evidence = "gate G1 approve sha256:" + "0" * 64
    tbw.reviews(root, lambda found: found.append(demo._review(5, demo.PERSON, recorded, other_evidence)))
    r = tbw.run(root, "CK-GATE-MIRROR")
    assert not r.ok and tbw.msgs(r) == f"{tbw.CHANGE}#review-5 states a decision for G1 that no decision record mirrors"
    tbw.reviews(root, lambda found: (found.pop(), found.append(demo._review(6, "sam", recorded, line))))
    r = tbw.run(root, "CK-GATE-MIRROR")
    assert not r.ok and tbw.msgs(r) == f"{tbw.CHANGE}#review-6 states a decision for G1 that no decision record mirrors"


# ── PRV-5 to PRV-7: the decision log's review ───────────────────────────────────

def test_AC_005_a_decisions_line_with_windows_line_ends_is_found(tmp_path):
    root = tdl.lite(tmp_path)
    tdl.write_log(root, tdl.decided())
    line = tdr.line_of(root)
    tdr.stand_in(root, [{**tdr.review(9, line), "body": f"Read it. Approved.\r\n{line}\r\nThanks.\r\n"}])
    code, text = tdl.kit(root, "decision", "bind", "--spec", tdl.SPEC, "--id", "D-001", "--change", tdr.CHANGE)
    assert code == 0 and f"D-001 is bound to {tdr.CHANGE}#review-9" in text, text
    assert tdr.run(root).ok


def test_AC_006_a_decisions_setting_of_the_wrong_shape_is_a_finding(tmp_path):
    root = tdl.lite(tmp_path)
    tdl.write_log(root, tdl.decided())
    kit_yml = root / core.KIT_DIR / "kit.yml"
    settings = yaml.safe_load(kit_yml.read_text(encoding="utf-8"))
    for wrong in ("required", ["required"]):
        settings["decisions"] = wrong
        kit_yml.write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8", newline="\n")
        r = tdr.run(root)
        assert not r.ok and r.not_run is None and tdl.msgs(r) == [
            "decisions in kit.yml is not a mapping; it is written as decisions: {bind_to_review: optional} or {bind_to_review: required}"]
        code, text = tdl.kit(root, "check")
        assert "Traceback" not in text and "CK-DECISION-REVIEW" in text, text[-2000:]


def test_AC_007_a_second_bind_with_json_prints_the_entry_as_json(tmp_path):
    root = tdr.bound(tmp_path)
    code, out, err = split(root, "decision", "bind", "--spec", tdl.SPEC, "--id", "D-001", "--change", tdr.CHANGE, "--json")
    assert code == 0 and json.loads(out) == tdr.entry(root) and json.loads(out)["review"] == f"{tdr.CHANGE}#review-9"
    assert "names pull/1#review-9 already. Nothing was written." in err


# ── the second review: PRV-8 to PRV-13 ──────────────────────────────────────────

def test_AC_008_decision_add_puts_back_both_logs_and_names_a_file_it_could_not(tmp_path, monkeypatch):
    root = tmf.project(tmp_path / "both")
    log, audit = root / tmf.LOG, root / tmf.AUDIT
    selftest._write(root, tmf.AUDIT, '{"seq": 1, "hash": "sha256:' + "1" * 64 + '"}\n')

    def fails_part_of_the_way(ctx, spec, questions, by, affects=(), actor=None):
        decision_log.write(ctx, spec, {"schema": decision_log.SCHEMA, "entries": [{"id": "D-001", "title": questions[0], "state": "proposed"}]})
        with audit.open("a", encoding="utf-8") as fh:
            fh.write('{"seq": 2, "act')  # part of a line, and then the write fails
        raise OSError("no space left on the device")

    before = tm.snapshot(root)
    with pytest.raises(tools.Refused, match="nothing was written"):
        tools.decision_add(tools.Project(root), {"spec": tmf.NOTES, "question": tmf.ASKED}, fails_part_of_the_way)
    assert tm.snapshot(root) == before, "the decision log and the audit log are both what they were"

    decision_log.write(selftest.context(root), tmf.NOTES, {"schema": decision_log.SCHEMA, "entries": []})
    real = Path.write_bytes

    def refuses_the_log(self, data):
        if self == log:
            raise PermissionError("the file is held open by another program")
        return real(self, data)

    monkeypatch.setattr(Path, "write_bytes", refuses_the_log)
    with pytest.raises(tools.Refused) as said:
        tools.decision_add(tools.Project(root), {"spec": tmf.NOTES, "question": tmf.ASKED}, fails_part_of_the_way)
    assert f"{tmf.LOG} could not be put back" in str(said.value) and "nothing was written" not in str(said.value), str(said.value)
    assert audit.read_text(encoding="utf-8") == '{"seq": 1, "hash": "sha256:' + "1" * 64 + '"}\n', "the file that could be put back was"


FAKE_GH = """#!/bin/sh
# A stand-in for gh: the pull requests it has opened are the names of their branches, one a line, in $PRS.
head=""; prev=""
for word in "$@"; do [ "$prev" = "--head" ] && head="$word"; prev="$word"; done
case "$1 $2" in
  "pr list") grep -qx "$head" "$PRS" 2>/dev/null && echo 1; exit 0 ;;
  "pr create") [ -n "$FAIL_CREATE" ] && { echo "gh: could not open the pull request" >&2; exit 1; }; echo "$head" >> "$PRS"; echo "https://example.invalid/pull/1" ;;
  *) echo "the stand-in for gh was asked: $*" >&2; exit 3 ;;
esac
"""
FAKE_PYTHON = """#!/bin/sh
# A stand-in for the kit's mirror: records whose text differs on every run, as a real record's audit head does.
mkdir -p .specify/agentic/decisions/001-demo .specify/agentic/audit
echo "written: $(date +%s%N) $$" > .specify/agentic/decisions/001-demo/G1.yml
echo "{}" >> .specify/agentic/audit/001-demo.jsonl
"""


@pytest.mark.skipif(sys.platform == "win32" or shutil.which("bash") is None,
                    reason="the job runs on Ubuntu; its script is run here with bash, a stand-in for gh and a local repository")
def test_AC_009_a_second_run_of_the_after_merge_job_keeps_the_branch_and_opens_its_pull_request_once(tmp_path):
    flow = yaml.safe_load(tbw.CONNECT_FLOW.read_text(encoding="utf-8"))
    step = next(s for s in flow["jobs"]["mirror-after-merge"]["steps"] if str(s.get("name", "")).startswith("Mirror the reviews"))
    script = tmp_path / "step.sh"
    script.write_text(step["run"], encoding="utf-8", newline="\n")
    tools_dir = tmp_path / "bin"
    tools_dir.mkdir()
    for name, text in (("gh", FAKE_GH), ("python", FAKE_PYTHON)):
        (tools_dir / name).write_text(text, encoding="utf-8", newline="\n")
        (tools_dir / name).chmod(0o755)

    def git(cwd, *words):
        done = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *words],
                              capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        return done.stdout.strip()

    def repository(name):
        origin, seed = tmp_path / f"{name}.git", tmp_path / f"{name}-seed"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        seed.mkdir()
        git(seed, "init", "-q")
        (seed / "README.md").write_text("the merged change\n", encoding="utf-8")
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "the merge")
        git(seed, "push", "-q", str(origin), "HEAD:refs/heads/main")
        return origin, git(seed, "rev-parse", "HEAD")

    def run(origin, merged, clone, prs, fail_create=False):
        git(tmp_path, "clone", "-q", str(origin), str(clone))   # each run of a job begins with a checkout of its own
        git(clone, "checkout", "-q", "--detach", merged)
        env = {**os.environ, "PATH": f"{tools_dir}{os.pathsep}{os.environ.get('PATH', '')}", "BASE": "main", "MERGED": merged,
               "GH_TOKEN": "a stand-in", "PRS": str(prs), "FAIL_CREATE": "1" if fail_create else ""}
        return subprocess.run(["bash", "-e", str(script)], cwd=clone, env=env, capture_output=True, text=True)

    origin, merged = repository("first")
    branch, prs = f"refs/heads/agentic/records-{merged[:12]}", tmp_path / "first-prs.txt"
    done = run(origin, merged, tmp_path / "run-1", prs)
    assert done.returncode == 0, done.stdout + done.stderr
    pushed = git(origin, "rev-parse", branch)
    assert prs.read_text(encoding="utf-8").splitlines() == [f"agentic/records-{merged[:12]}"]
    done = run(origin, merged, tmp_path / "run-2", prs)
    assert done.returncode == 0, done.stdout + done.stderr
    assert git(origin, "rev-parse", branch) == pushed, "the records a person may have read are kept as they are"
    assert len(prs.read_text(encoding="utf-8").splitlines()) == 1, "one pull request for the branch"

    origin, merged = repository("second")
    prs = tmp_path / "second-prs.txt"
    done = run(origin, merged, tmp_path / "run-3", prs, fail_create=True)
    assert done.returncode != 0 and not prs.exists(), "the branch was pushed and the pull request could not be opened"
    pushed = git(origin, "rev-parse", f"refs/heads/agentic/records-{merged[:12]}")
    done = run(origin, merged, tmp_path / "run-4", prs)
    assert done.returncode == 0, done.stdout + done.stderr
    assert prs.read_text(encoding="utf-8").splitlines() == [f"agentic/records-{merged[:12]}"]
    assert git(origin, "rev-parse", f"refs/heads/agentic/records-{merged[:12]}") == pushed


def test_AC_010_a_programme_entry_that_is_an_empty_list_false_or_zero_is_judged(tmp_path):
    root = tmp_path
    selftest.build_sample(root)
    tpr.record(root, tpr.PARENT, "G7")
    for value in ([], False, 0):
        selftest._write(root, f"specs/{tpr.PARENT}/spec.md", tpr.spec_md(tpr.PARENT, programme=value))
        shape = tpr.run(root, "CK-PROGRAMME")
        assert tpr.msgs(shape) == ["the programme entry is not a mapping, so it names no children, shared contract or rollout order"], (value, tpr.msgs(shape))
        release = tpr.run(root)
        assert not release.ok and "its programme entry names no children that can be read" in tpr.msgs(release)[0], (value, tpr.msgs(release))
    selftest._write(root, f"specs/{tpr.PARENT}/spec.md", tpr.spec_md(tpr.PARENT, programme=None))
    assert tpr.run(root, "CK-PROGRAMME").ok and tpr.run(root).ok, "`programme:` with no value is no programme"


def test_AC_011_record_writes_again_where_the_cited_review_lost_its_line(tmp_path):
    root = tmp_path
    reviewed, line, recorded = tbw.project(root)
    tbw.reviews(root, lambda found: (found[0].update(body="Read it. Approved.\n"), found.append(demo._review(3, demo.PERSON, recorded, line))))
    assert not tbw.run(root, "CK-GATE-MIRROR").ok, "the record names a review that no longer carries the line"
    code, text = tcs.kit(root, "record", "--spec", tbw.SPEC, "--gate", tbw.GATE, "--change", tbw.CHANGE)
    assert code == 0 and "wrote" in text and "recorded already" not in text, text
    written = yaml.safe_load((root / tbw.RECORD).read_text(encoding="utf-8"))
    assert [a["review_ref"] for a in written["approvals"]] == [f"{tbw.CHANGE}#review-3"]
    r = tbw.run(root, "CK-GATE-MIRROR")
    assert r.ok, tbw.msgs(r)


def test_AC_012_propose_asks_the_audit_log_before_it_adds_to_what_a_question_affects(tmp_path):
    root = tdl.lite(tmp_path)
    tdl.write_log(root, {"id": "D-001", "title": tdl.QUESTION, "state": "open", "affects": ["T001"]})
    (root / tdl.AUDIT).parent.mkdir(parents=True, exist_ok=True)
    (root / tdl.AUDIT).write_text(BROKEN_TAIL, encoding="utf-8", newline="\n")
    before = (root / tdl.LOG).read_bytes()
    with pytest.raises(core.KitError, match="is not an entry of the audit log"):
        decision_log.propose(tdl.ctx(root), tdl.SPEC, [tdl.QUESTION], "an-agent", affects=["T002"])
    assert (root / tdl.LOG).read_bytes() == before


def test_AC_013_each_of_the_four_documents_says_after_the_merge():
    for rel in ("docs/install.md", "extensions/agentic/commands/gate.md", "extensions/agentic-connect/README.md", "docs/limits.md"):
        text = " ".join((tbw.ROOT / rel).read_text(encoding="utf-8").split())
        assert "after the merge" in text, rel
        assert "both-ways-to-record.md" in text or rel.endswith("gate.md"), rel
    source = (tbw.ROOT / "tests" / "test_both_ways_to_record.py").read_text(encoding="utf-8")
    assert 'assert "after the merge" in text and ("both-ways-to-record.md" in text or rel.endswith("gate.md")), rel' in source
