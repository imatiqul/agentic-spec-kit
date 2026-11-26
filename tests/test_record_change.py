"""`record --change` and the warning from `gate` (REC-1 to REC-7, docs/design/record-finds-review.md).
Each test is named after the acceptance criterion it proves. The reviews come from the file adapter.
Run: python -m pytest tests/test_record_change.py -q"""
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit import core, demo  # noqa: E402
from agentic_kit.__main__ import _captured  # noqa: E402

core.load_plugins(CORE)

SPEC, GATE, CHANGE = demo.SPEC, demo.GATE, demo.CHANGE
RECORD = f"{core.KIT_DIR}/decisions/{SPEC}/{GATE}.yml"
SHORT = ("record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)


def kit(root, *words):
    return _captured(["--root", str(root), *words])


def line_of(root):
    text = kit(root, "gate", "--spec", SPEC, "--gate", GATE)[1]
    return next(row.strip() for row in text.splitlines() if row.strip().startswith(f"gate {GATE} approve sha256:"))


@pytest.fixture()
def project(tmp_path):
    """The demo's Lite project as a git repository, its spec and brief committed: the root, the commit, and the line for G1."""
    demo.build_project(tmp_path)
    demo._git(tmp_path, "init", "-q")
    demo._git(tmp_path, "symbolic-ref", "HEAD", "refs/heads/main")
    assert kit(tmp_path, "brief", "--spec", SPEC, "--gate", GATE, "--write")[0] == 0
    commit = demo._commit(tmp_path, "the spec and the reviewer's page")
    return tmp_path, commit, line_of(tmp_path)


def mirrored(root):
    record = yaml.safe_load((root / RECORD).read_text(encoding="utf-8"))
    return {key: record[key] for key in ("spec", "gate", "decision", "commit", "evidence", "approvals", "single_approver_exception")}


def test_AC_001_the_short_form_writes_what_the_long_form_writes_and_the_checks_accept_it(project):
    root, commit, line = project
    demo._reviews(root, [demo._review(2, demo.PERSON, commit, line)])
    code, text = kit(root, *SHORT)
    assert code == 0, text
    assert f"found on {CHANGE}: review 2 by {demo.PERSON}, APPROVED, on {commit[:12]}" in text
    assert "This is a mirror." in text
    short = mirrored(root)
    assert kit(root, "check", "CK-APPROVER", "CK-GATE-MIRROR", "CK-GATE-RECORD")[0] == 0
    (root / RECORD).unlink()
    assert kit(root, "record", "--spec", SPEC, "--gate", GATE, "--decision", "approve", "--commit", commit,
               "--approval", f"{demo.PERSON}:{demo.ROLE}:{CHANGE}#review-2")[0] == 0
    assert mirrored(root) == short


@pytest.mark.parametrize("reviews", ["none", "other evidence", "a comment, not an approval"])
def test_AC_002_with_no_review_that_carries_the_line_nothing_is_written(project, reviews):
    root, commit, line = project
    stale = demo._review(2, demo.PERSON, commit, f"gate {GATE} approve sha256:{'0' * 64}")
    comment = {**demo._review(2, demo.PERSON, commit, line), "state": "COMMENTED"}
    demo._reviews(root, {"none": [], "other evidence": [stale], "a comment, not an approval": [comment]}[reviews])
    code, text = kit(root, *SHORT)
    assert code == 2
    assert line in text and "Nothing was recorded." in text
    assert not (root / RECORD).exists()


def test_AC_003_a_reviewer_who_holds_no_needed_role_is_named_with_the_role_and_nothing_is_written(project):
    root, commit, line = project
    demo._reviews(root, [demo._review(2, "sam", commit, line)])   # sam holds qa; G1 needs product-owner
    code, text = kit(root, *SHORT)
    assert code == 2
    assert "sam" in text and demo.ROLE in text and "Nothing was recorded." in text
    assert not (root / RECORD).exists()


def test_AC_004_a_review_that_sends_the_work_back_is_recorded_as_a_rejection(project):
    root, commit, line = project
    back = {"id": "3", "reviewer": demo.PERSON, "type": "User", "state": "CHANGES_REQUESTED", "commit": commit,
            "body": "Not yet.\n" + line.replace(" approve ", " reject ") + "\n"}
    demo._reviews(root, [back])
    code, text = kit(root, *SHORT)
    assert code == 0, text
    assert mirrored(root)["decision"] == "reject"


@pytest.mark.parametrize("extra", [("--commit", "0123456789ab"), ("--decision", "reject")])
def test_AC_005_a_commit_or_a_decision_that_differs_from_the_review_stops_the_record(project, extra):
    root, commit, line = project
    demo._reviews(root, [demo._review(2, demo.PERSON, commit, line)])
    code, text = kit(root, *SHORT, *extra)
    assert code == 2 and "Nothing was recorded." in text
    assert not (root / RECORD).exists()


def test_AC_006_the_long_form_still_writes_and_one_of_the_two_forms_has_to_be_given(project):
    root, commit, _ = project
    code, text = kit(root, "record", "--spec", SPEC, "--gate", GATE)
    assert code == 2 and "give --change pull/<n>, or all three of --decision, --commit and --approval" in text
    code, text = kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE, "--approval", "a:b:pull/1#review-1")
    assert code == 2 and "not both" in text
    assert not (root / RECORD).exists()
    assert kit(root, "record", "--spec", SPEC, "--gate", GATE, "--decision", "approve", "--commit", commit,
               "--approval", f"anyone:{demo.ROLE}:{CHANGE}#review-9")[0] == 0   # the long form writes whatever it is given
    assert mirrored(root)["approvals"] == [{"reviewer": "anyone", "role": demo.ROLE, "review_ref": f"{CHANGE}#review-9"}]


def test_AC_008_gate_lists_the_evidence_that_is_not_committed(project):
    root, _, _ = project
    code, text = kit(root, "gate", "--spec", SPEC, "--gate", GATE)
    assert code == 0 and "Not committed" not in text
    assert json.loads(kit(root, "gate", "--spec", SPEC, "--gate", GATE, "--json")[1])["uncommitted"] == []
    spec = root / demo.SPEC_FILE
    spec.write_text(spec.read_text(encoding="utf-8") + "\nOne more line.\n", encoding="utf-8", newline="\n")
    code, text = kit(root, "gate", "--spec", SPEC, "--gate", GATE)
    assert code == 0
    assert f"Not committed:\n  {demo.SPEC_FILE}\n" in text
    assert "A reviewer sees only what is committed and pushed." in text
    assert f"specs/{SPEC}/briefs/{GATE}.md" not in text.split("Not committed:")[1]
    assert json.loads(kit(root, "gate", "--spec", SPEC, "--gate", GATE, "--json")[1])["uncommitted"] == [demo.SPEC_FILE]
    demo._commit(root, "the spec, changed")
    assert "Not committed" not in kit(root, "gate", "--spec", SPEC, "--gate", GATE)[1]


def test_AC_009_in_a_folder_that_is_not_a_git_repository_gate_says_what_it_said_before(tmp_path):
    demo.build_project(tmp_path)
    code, text = kit(tmp_path, "gate", "--spec", SPEC, "--gate", GATE)
    assert code == 0 and "Not committed" not in text
    assert text.rstrip().endswith("To reject, request changes with `reject` in place of `approve`.")
    assert json.loads(kit(tmp_path, "gate", "--spec", SPEC, "--gate", GATE, "--json")[1])["uncommitted"] is None
