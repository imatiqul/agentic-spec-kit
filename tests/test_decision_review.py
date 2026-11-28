"""A decision of the log, bound to a review (DRV-1 to DRV-8, docs/design/decision-review.md).

Each test is named after the acceptance criterion it proves. The project is the demo's Lite project with a plan and a
task list, as tests/test_decision_log.py builds it. The reviews come from the file adapter, which proves nothing about
who approved: it stands where GitHub stands.
Run: python -m pytest tests/test_decision_review.py -q
"""
import json
import re

import yaml

import test_decision_log as tdl
from agentic_kit import core, decision_log, demo, selftest

SPEC, CHANGE, LOG, AUDIT = tdl.SPEC, tdl.CHANGE, tdl.LOG, tdl.AUDIT
CHECK = "CK-DECISION-REVIEW"
OUTCOME = "Yes, letter for letter."


def stand_in(root, reviews, **more):
    """The file that plays GitHub: the reviews on pull/1, and who the agent and the pipeline are."""
    demo._write(root, demo.ADAPTER, json.dumps({"agent_identity": demo.AGENT, "ci_identity": "demo-ci", **more,
                                                "changes": {CHANGE: {"authors": [demo.AGENT], "reviews": reviews}}}, indent=2) + "\n")


def review(number, line, reviewer=demo.PERSON, state="APPROVED", account="User"):
    return {**demo._review(number, reviewer, "", line), "state": state, "type": account}


def entry(root, eid="D-001"):
    return next(e for e in decision_log.entries(tdl.ctx(root), SPEC) if e["id"] == eid)


def line_of(root, eid="D-001"):
    code, text = tdl.kit(root, "decision", "line", "--spec", SPEC, "--id", eid)
    assert code == 0, text
    return next(row.strip() for row in text.splitlines() if row.strip().startswith(f"decision {SPEC} {eid} sha256:"))


def bound(tmp_path):
    """The project with D-001 decided by pat, and bound to review 9 on pull/1, which carries its line."""
    root = tdl.lite(tmp_path)
    tdl.write_log(root, tdl.decided())
    stand_in(root, [review(9, line_of(root))])
    code, text = tdl.kit(root, "decision", "bind", "--spec", SPEC, "--id", "D-001", "--change", CHANGE)
    assert code == 0, text
    return root


def edit_log(root, change):
    doc = yaml.safe_load((root / LOG).read_text(encoding="utf-8"))
    change(doc["entries"])
    tdl.write_log(root, *doc["entries"])


def edit_stand_in(root, change):
    path = root / demo.ADAPTER
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def run(root):
    return core.run_check(CHECK, tdl.ctx(root))


# ── the line and the binding ────────────────────────────────────────────────────

def test_AC_001_a_decided_entry_has_a_line_that_moves_with_its_outcome_and_not_with_spaces(tmp_path):
    root = tdl.lite(tmp_path)
    tdl.write_log(root, tdl.decided(), {"id": "D-002", "title": "Is a name of spaces greeted?", "state": "proposed", "proposed_by": "an-agent"})
    code, text = tdl.kit(root, "decision", "line", "--spec", SPEC, "--id", "D-001")
    assert code == 0, text
    found = entry(root)
    assert f"  {decision_log.decision_line(SPEC, found)}\n" in text and found["review"] is None
    assert re.fullmatch(rf"decision {SPEC} D-001 sha256:[0-9a-f]{{64}}", decision_log.decision_line(SPEC, found))
    assert f"{demo.PERSON} puts it, on a line of its own, into the text of a pull-request review that approves" in text
    assert f"decision bind --spec {SPEC} --id D-001 --change pull/<n>" in text
    spaced = {**found, "outcome": "  Yes,   letter for\nletter. ", "title": f" {found['title']}  "}
    assert decision_log.decision_hash(SPEC, spaced) == decision_log.decision_hash(SPEC, found), "spaces alone change nothing"
    assert decision_log.decision_hash(SPEC, {**found, "outcome": "No."}) != decision_log.decision_hash(SPEC, found)
    assert decision_log.decision_hash("002-other", found) != decision_log.decision_hash(SPEC, found)
    code, text = tdl.kit(root, "decision", "line", "--spec", SPEC, "--id", "D-002")
    assert code == 2 and "only a decided entry has a line" in text
    assert all("review" in e for e in decision_log.entries(tdl.ctx(root), SPEC))


def test_AC_002_bind_names_the_review_that_stands_and_otherwise_says_what_is_missing(tmp_path):
    root = tdl.lite(tmp_path)
    tdl.write_log(root, tdl.decided())
    line = line_of(root)
    other_outcome = decision_log.decision_line(SPEC, {**entry(root), "outcome": "No."})
    for reviews, said in (
            ([review(9, line, reviewer="sam")], f"{CHANGE} has no review by {demo.PERSON}, who owns D-001"),
            ([review(9, line, state="COMMENTED")], "the review state is COMMENTED, not APPROVED"),
            ([review(9, "gate G1 approve sha256:" + "0" * 64)], "its text does not carry the line of this decision"),
            ([review(9, other_outcome)], "for another outcome or question: the entry was changed after the review"),
            ([review(9, line, account="Bot")], f"{demo.PERSON} is not a human account")):
        stand_in(root, reviews)
        before = (root / LOG).read_bytes()
        code, text = tdl.kit(root, "decision", "bind", "--spec", SPEC, "--id", "D-001", "--change", CHANGE)
        assert code == 2 and said in text and "Nothing was written." in text, (said, text)
        assert f"  {line}\n" in text, "the refusal gives the line"
        assert (root / LOG).read_bytes() == before and not (root / AUDIT).exists()

    stand_in(root, [review(8, line, state="COMMENTED"), review(9, line)])
    code, text = tdl.kit(root, "decision", "bind", "--spec", SPEC, "--id", "D-001", "--change", CHANGE)
    assert code == 0 and f"D-001 is bound to {CHANGE}#review-9" in text, text
    assert tdl.held(root)[0]["review"] == f"{CHANGE}#review-9" and entry(root)["review"] == f"{CHANGE}#review-9"
    [bind] = [json.loads(row) for row in (root / AUDIT).read_text(encoding="utf-8").splitlines()]
    assert bind["action"] == "decision-log.bind" and bind["review"] == f"{CHANGE}#review-9" and bind["entry"] == "D-001"
    r = run(root)
    assert r.ok and r.not_run is None, tdl.msgs(r)
    assert tdl.run(root).ok, "the log is still well formed"

    before = ((root / LOG).read_bytes(), (root / AUDIT).read_bytes())
    code, text = tdl.kit(root, "decision", "bind", "--spec", SPEC, "--id", "D-001", "--change", CHANGE)
    assert code == 0 and "names pull/1#review-9 already. Nothing was written." in text
    assert ((root / LOG).read_bytes(), (root / AUDIT).read_bytes()) == before
    code, text = tdl.kit(root, "decision", "bind", "--spec", SPEC, "--id", "D-001", "--change", "pull/x")
    assert code == 2 and "bind needs --change pull/<n>" in text


# ── the check ───────────────────────────────────────────────────────────────────

def test_AC_003_the_check_asks_the_channel_who_approved_which_outcome(tmp_path):
    cases = [
        (lambda root: edit_log(root, lambda rows: rows[0].update(review=f"{CHANGE}#review-99")), "which is not in the enforcement channel"),
        (lambda root: edit_stand_in(root, lambda data: data["changes"][CHANGE]["reviews"][0].update(reviewer="sam")),
         f"the record says {demo.PERSON} but the review is by sam"),
        (lambda root: edit_stand_in(root, lambda data: data["changes"][CHANGE]["reviews"][0].update(state="CHANGES_REQUESTED")),
         "the review state is CHANGES_REQUESTED, not APPROVED"),
        (lambda root: edit_stand_in(root, lambda data: data["changes"][CHANGE]["reviews"][0].update(body="Read it. Approved.\n")),
         "its text does not carry the line of this decision"),
        (lambda root: edit_log(root, lambda rows: rows[0].update(outcome="No, the spaces go.")),
         "carries the line of this decision for another outcome or question: the entry was changed after the review"),
        (lambda root: edit_stand_in(root, lambda data: data.update(agent_identity=demo.PERSON)), f"{demo.PERSON} is the agent's or CI's own identity"),
        (lambda root: edit_log(root, lambda rows: rows[0].update(review="#9")), "names the review '#9', which is not of the form pull/<n>#review-<id>"),
        (lambda root: edit_log(root, lambda rows: rows.append({"id": "D-002", "title": "Is a name of spaces greeted?", "state": "proposed",
                                                                "proposed_by": "an-agent", "review": f"{CHANGE}#review-9"})),
         "D-002 is proposed and names a review: a review is bound to a decision"),
    ]
    for number, (spoil, said) in enumerate(cases):
        root = bound(tmp_path / f"case-{number}")
        assert run(root).ok
        spoil(root)
        r = run(root)
        assert not r.ok and r.not_run is None and any(said in m for m in tdl.msgs(r)), (said, tdl.msgs(r))
        assert all(f.path == LOG for f in r.findings)

    root = bound(tmp_path / "dismissed")
    line = line_of(root)
    edit_stand_in(root, lambda data: data["changes"][CHANGE]["reviews"][0].update(state="DISMISSED"))
    r = run(root)
    assert not r.ok and "the review state is DISMISSED, not APPROVED" in tdl.msgs(r)[0], "no later approval stands for it"
    edit_stand_in(root, lambda data: data["changes"][CHANGE]["reviews"].extend([review(10, line, reviewer="sam"), review(11, line)]))
    r = run(root)
    assert r.ok, tdl.msgs(r)
    assert [n for n in r.notes if "review 9 on pull/1 was dismissed; review 11, later and by the same person" in n], r.notes


def test_AC_004_kit_yml_may_ask_that_every_decision_be_bound(tmp_path):
    root = tdl.lite(tmp_path / "unbound")
    tdl.write_log(root, tdl.decided())
    kit_yml = root / core.KIT_DIR / "kit.yml"
    settings = yaml.safe_load(kit_yml.read_text(encoding="utf-8"))
    for rule, ok in ((None, True), ("optional", True), ("required", False), ("always", False)):
        if rule is None:
            settings.pop("decisions", None)
        else:
            settings["decisions"] = {"bind_to_review": rule}
        kit_yml.write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8", newline="\n")
        r = run(root)
        assert r.ok is ok and r.not_run is None, (rule, tdl.msgs(r))
    assert tdl.msgs(r) == ["decisions.bind_to_review is 'always'; it is optional or required"]
    settings["decisions"] = {"bind_to_review": "required"}
    kit_yml.write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8", newline="\n")
    assert tdl.msgs(run(root))[0].startswith("D-001 is decided and names no review, and kit.yml asks for one (decisions.bind_to_review: required)")

    root = bound(tmp_path / "bound")
    (root / core.KIT_DIR / "kit.yml").write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8", newline="\n")
    assert run(root).ok


def test_AC_005_a_superseded_entry_is_not_looked_at(tmp_path):
    root = bound(tmp_path)
    edit_log(root, lambda rows: rows[0].update(review=f"{CHANGE}#review-99"))
    assert not run(root).ok
    assert tdl.kit(root, "decision", "add", "--spec", SPEC, "--title", "Is a name greeted as it was typed? Asked again.", "--by", demo.PERSON)[0] == 0
    code, text = tdl.kit(root, "decision", "supersede", "--spec", SPEC, "--id", "D-001", "--by", "D-002")
    assert code == 0, text
    r = run(root)
    assert r.ok and r.findings == [], tdl.msgs(r)


# ── where it shows, the self-test and the documents ─────────────────────────────

def test_AC_006_the_page_and_the_brief_show_the_review_and_the_self_test_has_both_fixtures(tmp_path):
    root = bound(tmp_path / "project")
    shown = f"`D-001` decided by {demo.PERSON} on 2026-11-26, in review {CHANGE}#review-9: {tdl.QUESTION}"
    [(_, lines)] = decision_log.brief_hook(tdl.ctx(root), SPEC, "G5")
    assert any(row.startswith(f"- {shown} **Outcome:** {OUTCOME}") for row in lines), lines
    code, page = tdl.kit(root, "changeset", "--spec", SPEC)
    assert code == 0 and f"- {shown} **Outcome:** {OUTCOME}" in page, page

    what, mutate, passing, failing = selftest.all_fixtures()[CHECK]
    good, broken = tmp_path / "good", tmp_path / "broken"
    selftest.build_sample(good)
    assert core.run_check(CHECK, selftest.context(good, **passing)).ok
    selftest.build_sample(broken)
    mutate(broken)
    found = core.run_check(CHECK, selftest.context(broken, **failing))
    assert [f.message for f in found.findings] == ["D-002 names review pull/1#review-1, which does not stand for it: "
                                                   "its text does not carry the line of this decision"]
    assert "review" in what and passing == {} and failing == {}
    assert core.run_check("CK-SELFTEST", selftest.context(good)).ok


def test_AC_007_the_documents_say_what_a_binding_proves_and_what_it_does_not():
    root = tdl.ROOT
    design = (root / "docs" / "design" / "decision-log.md").read_text(encoding="utf-8")
    report = (root / "docs" / "phase-reports" / "phase-12-features.md").read_text(encoding="utf-8")
    limits = (root / "docs" / "limits.md").read_text(encoding="utf-8")
    assert "decision-review.md" in design and "decision bind" in design
    assert re.search(r"1\. \*\*A decision of the log can be bound to a review\.\*\*", report) and CHECK in report
    for words in (CHECK, "cannot tell who typed `decision decide`", "opens G5 again", "approves again with the same line"):
        assert words in limits, words
