"""Unit tests for slice 0.1. Run: python -m pytest tests -q   (needs pyyaml and git)."""
import errno
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "extensions" / "agentic" / "scripts"))

from agentic_kit import adapters, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402
from agentic_kit.core import KIT_DIR, REGISTRY, Context, Source, approval_line, evidence_hash, parse_approval_lines, run_check  # noqa: E402

KIT = f"{KIT_DIR}/kit.yml"


@pytest.fixture()
def sample(tmp_path):
    selftest.build_sample(tmp_path)
    return tmp_path


def run(root, cid, **options):
    return run_check(cid, selftest.context(root, **options))


def edit(root, rel, old, new):
    p = root / rel
    text = p.read_text(encoding="utf-8")
    assert old in text
    p.write_text(text.replace(old, new), encoding="utf-8")


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)


def test_every_check_has_fixtures_and_they_behave():
    good, rows = selftest.run_selftest()
    assert good, [r for r in rows if r["expected"] != r["actual"]]
    assert {r["check"] for r in rows} == set(REGISTRY)


def test_sample_project_passes_every_check(sample):
    for cid in REGISTRY:
        r = run(sample, cid, **selftest.FIXTURES.get(cid, ("", None, {}, {}))[2])
        assert r.ok, (cid, [f.line() for f in r.findings], r.not_run)


# ── approvals ───────────────────────────────────────────────────────────────────

def reviews(root, fn):
    p = root / f"{KIT_DIR}/_adapter/reviews.json"
    data = json.loads(p.read_text())
    fn(data)
    p.write_text(json.dumps(data))


def test_agent_identity_cannot_approve(sample):
    reviews(sample, lambda d: d.update(agent_identity="alice"))
    assert any("agent's or CI's own identity" in f.message for f in run(sample, "CK-APPROVER").findings)


def test_bot_account_cannot_approve(sample):
    reviews(sample, lambda d: d["changes"]["pull/1"]["reviews"][0].update(type="Bot"))
    assert any("not a human account" in f.message for f in run(sample, "CK-APPROVER").findings)


def test_person_outside_roles_cannot_approve(sample):
    reviews(sample, lambda d: d["changes"]["pull/1"]["reviews"][0].update(reviewer="mallory"))
    msgs = [f.message for f in run(sample, "CK-APPROVER").findings]
    assert any("not listed in roles.yml" in m for m in msgs)


def test_dismissed_review_does_not_count(sample):
    reviews(sample, lambda d: d["changes"]["pull/1"]["reviews"][0].update(state="DISMISSED"))
    assert any("review state is DISMISSED" in f.message for f in run(sample, "CK-APPROVER").findings)


def test_review_on_another_commit_does_not_count(sample):
    reviews(sample, lambda d: d["changes"]["pull/1"]["reviews"][0].update(commit="deadbee"))
    assert any("different commit" in f.message for f in run(sample, "CK-APPROVER").findings)


def test_missing_review_is_reported(sample):
    reviews(sample, lambda d: d["changes"]["pull/1"]["reviews"].pop(0))
    assert any("was not found" in f.message for f in run(sample, "CK-APPROVER").findings)


def test_single_approver_exception_must_be_recorded(sample):
    reviews(sample, lambda d: d["changes"]["pull/1"]["authors"].append("alice"))
    r = run(sample, "CK-APPROVER")
    assert any("single_approver_exception is not recorded" in f.message for f in r.findings)
    for gate in ("G1", "G2", "G3", "G4", "G5"):  # wherever alice approved; sibling extensions may add her at later gates
        edit(sample, f"{KIT_DIR}/decisions/001-demo/{gate}.yml", "single_approver_exception: false", "single_approver_exception: true")
    assert run(sample, "CK-APPROVER").ok


def test_review_with_gate_line_but_no_record_is_reported(sample):
    def add(d):
        d["changes"]["pull/1"]["reviews"].append({"id": "99", "reviewer": "bob", "type": "User", "state": "APPROVED",
                                                  "commit": "c0ffee1", "body": approval_line("G6", "approve", "sha256:" + "a" * 64)})
    reviews(sample, add)
    assert any("no decision record mirrors" in f.message for f in run(sample, "CK-GATE-MIRROR").findings)


def test_pull_request_cannot_grant_itself_approvers(tmp_path):
    """roles.yml is read from the base branch: adding yourself in the PR changes nothing."""
    selftest.build_sample(tmp_path)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    git(tmp_path, "switch", "-qc", "feature")
    reviews(tmp_path, lambda d: d["changes"]["pull/1"]["reviews"][0].update(reviewer="mallory"))
    edit(tmp_path, f"{KIT_DIR}/decisions/001-demo/G1.yml", "reviewer: alice", "reviewer: mallory")
    edit(tmp_path, f"{KIT_DIR}/roles.yml", "- id: alice", "- id: mallory\n  roles:\n  - product-owner\n- id: alice")
    working = Source(tmp_path)
    naive = run_check("CK-APPROVER", Context(working, working, {"today": selftest.TODAY}))
    assert not any("mallory is not listed" in f.message for f in naive.findings)  # the PR's own copy would accept mallory
    trusted = run_check("CK-APPROVER", Context(working, working.at("main"), {"today": selftest.TODAY}))
    assert any("mallory is not listed in roles.yml on the base branch" in f.message for f in trusted.findings)


# ── evidence and records ────────────────────────────────────────────────────────

def test_evidence_hash_is_order_independent_and_content_sensitive(sample):
    src = Source(sample)
    a = evidence_hash(src, "001-demo", "G4", ["specs/001-demo/tasks.md", "specs/001-demo/trace-manifest.json"])
    b = evidence_hash(src, "001-demo", "G4", ["specs/001-demo/trace-manifest.json", "specs/001-demo/tasks.md"])
    assert a == b
    assert a != evidence_hash(src, "001-demo", "G5", ["specs/001-demo/tasks.md", "specs/001-demo/trace-manifest.json"])
    edit(sample, "specs/001-demo/tasks.md", "Implement greet", "Implement greeting")
    assert a != evidence_hash(Source(sample), "001-demo", "G4", ["specs/001-demo/tasks.md", "specs/001-demo/trace-manifest.json"])


def test_approval_line_round_trip():
    digest = "sha256:" + "0f" * 32
    assert parse_approval_lines("LGTM\n" + approval_line("G3", "approve-with-conditions", digest)) == [("G3", "approve-with-conditions", digest)]
    assert parse_approval_lines("gate G3 approve sha256:short") == []
    assert parse_approval_lines("please do not gate G3 approve " + digest) == []


def test_later_gate_cannot_pass_before_earlier_one(sample):
    (sample / f"{KIT_DIR}/decisions/001-demo/G2.yml").unlink()
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD").findings]
    assert any("earlier gate G2 is not" in m for m in msgs)
    assert any("plan.md exists but gate G2" in m for m in msgs)


def test_approve_with_conditions_needs_conditions(sample):
    edit(sample, f"{KIT_DIR}/decisions/001-demo/G3.yml", "decision: approve", "decision: approve-with-conditions")
    assert any("needs at least one condition" in f.message for f in run(sample, "CK-GATE-RECORD").findings)


def test_decision_is_checked_against_evidence_at_its_commit(tmp_path):
    selftest.build_sample(tmp_path)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    sha = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    for gate in ("G1", "G2", "G3", "G4", "G5"):
        edit(tmp_path, f"{KIT_DIR}/decisions/001-demo/{gate}.yml", "commit: c0ffee1", f"commit: {sha}")
    edit(tmp_path, "specs/001-demo/plan.md", "One function", "Later edit, after approval,")
    assert run(tmp_path, "CK-GATE-RECORD").ok  # the approved commit still holds the approved evidence
    edit(tmp_path, f"{KIT_DIR}/decisions/001-demo/G3.yml", f"commit: {sha}", "commit: deadbeef0")
    assert any("is not in this repository" in f.message for f in run(tmp_path, "CK-GATE-RECORD").findings)


def test_all_digit_commit_is_still_a_commit(sample):
    """YAML parses an unquoted all-digit SHA as a number; it must not be treated as missing."""
    edit(sample, f"{KIT_DIR}/decisions/001-demo/G1.yml", "commit: c0ffee1", "commit: 1234567")
    assert not any("not tied to a commit" in f.message for f in run(sample, "CK-GATE-RECORD").findings)


# ── work ahead of its gates ─────────────────────────────────────────────────────

DECISIONS = f"{KIT_DIR}/decisions/001-demo"
ON_DEFAULT = "the implementation is on the default branch (main) but gate {} has no approving decision record ("
STARTED = "implementation has started but gate {} has no approving decision record ("
UNTOLD = "could not tell whether this is the default branch ({}), so the gates before a merge were not asked for: {}; say which branch it is with --branch"
NO_REPOSITORY = "the project root is not the top of a git repository"


def ordinary(root):
    """The sample's spec is the retrospective of an open emergency, which lets its gates follow the change. Without the record it is an ordinary spec."""
    (root / f"{KIT_DIR}/emergencies/E-001.yml").unlink()


def repository(root, branch="main"):
    """Make the sample a git repository of its own, on `branch`, with each decision tied to a commit that exists. Returns that commit."""
    git(root, "init", "-q", "-b", branch)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "the sample")
    sha = head(root)
    for gate in ("G1", "G2", "G3", "G4", "G5"):
        edit(root, f"{DECISIONS}/{gate}.yml", "commit: c0ffee1", f"commit: {sha}")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "decisions tied to their commit")
    return sha


def head(root):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def gate_check(root, base=None, **options):
    """CK-GATE-RECORD, compared with `base` when one is given, as a pipeline runs it with --base-ref."""
    src = Source(root)
    return run_check("CK-GATE-RECORD", Context(src, src.at(base) if base else src, {"today": selftest.TODAY, **options}))


def test_an_implementation_on_the_default_branch_without_its_implementation_and_verification_gates_is_reported(sample):
    """The gap: a change was merged with no review, and the gate check reported the same missing records as before the merge."""
    ordinary(sample)
    (sample / f"{DECISIONS}/G5.yml").unlink()
    found = run(sample, "CK-GATE-RECORD", branch="main").findings
    assert [f.path for f in found] == ["specs/001-demo"] * 2, "each finding names the spec"
    assert found[0].message.startswith(ON_DEFAULT.format("G5")) and found[1].message.startswith(ON_DEFAULT.format("G6")), "and the gate"
    assert all("tasks ticked off in tasks.md: T001" in f.message for f in found), "and says what was found on the branch"


def test_the_verification_gate_is_asked_for_on_the_default_branch_once_the_implementation_gate_is_approved(sample):
    ordinary(sample)
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD", branch="main").findings]
    assert len(msgs) == 1 and msgs[0].startswith(ON_DEFAULT.format("G6"))
    assert run(sample, "CK-GATE-RECORD", branch="refs/heads/main").findings, "a pipeline may pass the full ref it builds"
    assert not any("G7" in m for m in msgs), "a release is decided after the merge: G7 is not asked for"


def test_work_in_progress_on_a_feature_branch_is_not_asked_for_g5_and_g6_but_is_asked_for_the_gates_before_code(sample):
    ordinary(sample)
    (sample / f"{DECISIONS}/G5.yml").unlink()
    for branch in ("spec/001-demo", "refs/pull/7/merge", "refs/heads/spec/main"):
        r = run(sample, "CK-GATE-RECORD", branch=branch)
        assert r.ok and not r.notes, f"{branch}: nothing is said about G5 and G6 where work is still in progress"
    (sample / f"{DECISIONS}/G4.yml").unlink()
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD", branch="spec/001-demo").findings]
    assert len(msgs) == 1 and msgs[0].startswith(STARTED.format("G4")) and "tasks ticked off in tasks.md: T001" in msgs[0]


def test_a_gate_that_a_plan_or_a_task_list_already_asks_for_is_not_reported_a_second_time_for_the_code(sample):
    ordinary(sample)
    for gate in ("G2", "G3", "G4", "G5"):
        (sample / f"{DECISIONS}/{gate}.yml").unlink()
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD", branch="spec/001-demo").findings]
    assert sorted(m.split(" (")[0] for m in msgs) == ["implementation has started but gate G4 has no approving decision record",
                                                      "plan.md exists but gate G2 has no approving decision record",
                                                      "tasks.md exists but gate G3 has no approving decision record"]
    msgs = [f.message.split(" (")[0] for f in run(sample, "CK-GATE-RECORD", branch="main").findings]
    assert msgs[-3:] == ["implementation has started but gate G4 has no approving decision record",
                         "the implementation is on the default branch", "the implementation is on the default branch"], \
        "on the default branch each missing gate up to verification is one finding, in the order of the gates"


def test_a_spec_with_no_finished_task_is_asked_for_nothing_more_than_before(sample, monkeypatch):
    from agentic_kit import checks_gov
    monkeypatch.setattr(checks_gov, "IMPLEMENTATION_HOOKS", [])  # the core alone: what a sibling extension records is tested with that extension
    ordinary(sample)
    edit(sample, "specs/001-demo/tasks.md", "- [x] T001", "- [ ] T001")
    for gate in ("G4", "G5"):
        (sample / f"{DECISIONS}/{gate}.yml").unlink()
    r = run(sample, "CK-GATE-RECORD", branch="main")
    assert r.ok and not r.notes, "a task list with nothing ticked does not show code"
    edit(sample, "specs/001-demo/tasks.md", "- [ ] T001", "* [X] T001")
    assert len(run(sample, "CK-GATE-RECORD", branch="main").findings) == 3, "G4, G5 and G6, once a task is ticked"


def test_lite_is_asked_for_its_three_gates_and_no_others_when_code_is_on_the_default_branch(sample):
    lite(sample)
    ordinary(sample)
    for gate in ("G2", "G4"):
        (sample / f"{DECISIONS}/{gate}.yml").unlink()
    r = run(sample, "CK-GATE-RECORD", branch="main")
    assert r.ok and not r.notes, "G1, G3 and G5 are approved; Lite has no G4 and no G6 to ask for"
    (sample / f"{DECISIONS}/G5.yml").unlink()
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD", branch="main").findings]
    assert len(msgs) == 1 and msgs[0].startswith(ON_DEFAULT.format("G5"))
    assert run(sample, "CK-GATE-RECORD", branch="spec/001-demo").ok
    assert run(sample, "CK-GATE-RECORD").notes == [UNTOLD.format(NO_REPOSITORY, "001-demo (G5)")]
    (sample / f"{DECISIONS}/G3.yml").unlink()
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD", branch="spec/001-demo").findings]
    assert msgs == ["tasks.md exists but gate G3 has no approving decision record"], "the gate before code in Lite is G3, which the task list already asks for"
    (sample / "specs/001-demo/plan.md").unlink()
    (sample / f"{DECISIONS}/G1.yml").unlink()
    msgs = [f.message for f in run(sample, "CK-GATE-RECORD", branch="spec/001-demo").findings]
    assert len(msgs) == 2 and msgs[1].startswith(STARTED.format("G1")), "with no plan to ask for G1, the finished task does"


def test_when_the_kit_cannot_tell_which_branch_it_is_on_it_says_so_in_a_note_and_does_not_pass_in_silence(sample):
    ordinary(sample)
    r = run(sample, "CK-GATE-RECORD")
    assert r.ok and r.notes == [UNTOLD.format(NO_REPOSITORY, "001-demo (G6)")], "the sample is a folder of files: git has nothing to say about it"
    (sample / f"{DECISIONS}/G5.yml").unlink()
    assert run(sample, "CK-GATE-RECORD").notes == [UNTOLD.format(NO_REPOSITORY, "001-demo (G5, G6)")]
    (sample / f"{DECISIONS}/G4.yml").unlink()
    assert any(f.message.startswith(STARTED.format("G4")) for f in run(sample, "CK-GATE-RECORD").findings), "what holds on every branch is still asked"


def test_a_project_in_a_folder_of_another_repository_is_not_given_that_repositorys_branch(tmp_path):
    """The reference example is such a folder in this kit's repository. Asked there, git would name the kit's branch."""
    project = tmp_path / "examples" / "project"
    selftest.build_sample(project)
    ordinary(project)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "a kit project in a folder of another repository")
    assert run(project, "CK-GATE-RECORD").notes == [UNTOLD.format(NO_REPOSITORY, "001-demo (G6)")]
    (project / ".git").mkdir()  # an empty folder of that name does not make it a repository: git still answers for the one above
    r = run(project, "CK-GATE-RECORD")
    assert r.notes == [UNTOLD.format(NO_REPOSITORY, "001-demo (G6)")] and not any("default branch (main) but" in f.message for f in r.findings)
    assert any(f.message.startswith(ON_DEFAULT.format("G6")) for f in run(project, "CK-GATE-RECORD", branch="main").findings), \
        "the caller can still say which branch it is"


def test_git_says_which_branch_it_is_where_the_project_is_a_repository_of_its_own(tmp_path):
    selftest.build_sample(tmp_path)
    ordinary(tmp_path)
    repository(tmp_path)

    def asked_for_g6(base=None, **options):
        r = gate_check(tmp_path, base, **options)
        assert not r.notes and len(r.findings) <= 1, (r.notes, [f.message for f in r.findings])
        return bool(r.findings) and r.findings[0].message.startswith(ON_DEFAULT.format("G6"))

    assert asked_for_g6(), "the default branch is checked out"
    git(tmp_path, "checkout", "-q", "--detach")
    assert asked_for_g6(), "a pipeline's commit with no branch, which the default branch contains"
    git(tmp_path, "switch", "-qc", "spec/001-demo")
    assert gate_check(tmp_path).notes == [UNTOLD.format("branch spec/001-demo is checked out at a commit that main already holds", "001-demo (G6)")], \
        "a branch with nothing of its own yet: just started, or the default branch under another name"
    (tmp_path / "src/demo/more.py").write_text("x = 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "work in progress")
    assert not asked_for_g6(), "a feature branch"
    assert not asked_for_g6("main"), "and the same compared with the default branch, as a pipeline compares a pull request"
    git(tmp_path, "checkout", "-q", "--detach")
    assert not asked_for_g6("main"), "a pull request's commit with no branch, which the default branch does not contain"
    assert asked_for_g6(branch="main"), "what the caller says wins over what git says"
    git(tmp_path, "switch", "-q", "main")
    assert not asked_for_g6(branch="spec/001-demo")


def test_the_default_branch_under_another_name_checked_against_the_commit_before_a_merge_is_a_case_the_kit_cannot_tell(tmp_path):
    """How the gap was found: merged work, checked against the commit before the merge, in a clone whose main was older and whose branch had another name."""
    selftest.build_sample(tmp_path)
    ordinary(tmp_path)
    before = repository(tmp_path)
    git(tmp_path, "switch", "-qc", "gh-main")
    for name in ("one", "two"):
        (tmp_path / f"src/demo/{name}.py").write_text("x = 1\n")
        git(tmp_path, "add", "-A")
        git(tmp_path, "commit", "-qm", f"merged work, {name}")
    earlier = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD~1"], capture_output=True, text=True).stdout.strip()
    why = "branch gh-main is checked out and compared with {}, a commit that is not on main as this repository has it"
    r = gate_check(tmp_path, earlier)
    assert r.ok and r.notes == [UNTOLD.format(why.format(earlier[:10]), "001-demo (G6)")], \
        "a push to the default branch is checked against the commit before it; so is a feature branch against its own past"
    assert gate_check(tmp_path, "HEAD~1").notes == [UNTOLD.format(why.format("HEAD~1"), "001-demo (G6)")]
    git(tmp_path, "checkout", "-q", "--detach")
    assert "a commit with no branch is checked out and compared with HEAD~1, a commit that is not on main" in gate_check(tmp_path, "HEAD~1").notes[0]
    msgs = [f.message for f in gate_check(tmp_path, earlier, branch="main").findings]
    assert len(msgs) == 1 and msgs[0].startswith(ON_DEFAULT.format("G6")), "the caller can say which branch it is"
    # What reads as a change proposed to a branch stays work in progress. That it is main under another name, only the caller knows.
    git(tmp_path, "branch", "spec/base", "HEAD~1")
    for base in (before, "main", "spec/base", None):
        r = gate_check(tmp_path, base)
        assert r.ok and not r.notes, f"compared with {base}"


def test_a_repository_with_no_branch_of_the_name_kit_yml_gives_is_a_case_the_kit_cannot_tell(tmp_path):
    """kit.yml says the default branch is main. A repository whose branch is called something else may be a clone of one branch, or kit.yml may be wrong."""
    selftest.build_sample(tmp_path)
    ordinary(tmp_path)
    repository(tmp_path, branch="trunk")
    why = "the repository has no branch main; enforcement.default_branch in kit.yml names the default branch"
    r = run(tmp_path, "CK-GATE-RECORD")
    assert r.ok and r.notes == [UNTOLD.format(why, "001-demo (G6)")]
    git(tmp_path, "checkout", "-q", "--detach")
    assert run(tmp_path, "CK-GATE-RECORD").notes == [UNTOLD.format(why, "001-demo (G6)")]
    edit(tmp_path, KIT, "default_branch: main", "default_branch: trunk")
    msgs = [f.message for f in run(tmp_path, "CK-GATE-RECORD").findings]
    assert len(msgs) == 1 and "is on the default branch (trunk) but gate G6" in msgs[0]


def test_an_open_emergency_lets_the_gates_of_its_retrospective_spec_follow_the_change_onto_the_default_branch(sample):
    """GOV-18: the fix goes in on one approval, and CK-EMERGENCY-DEADLINE holds the retrospective spec to its date."""
    for options in ({"branch": "main"}, {}):
        r = run(sample, "CK-GATE-RECORD", **options)
        assert r.ok and not r.notes, "emergency E-001 is open and names 001-demo as its retrospective"
    edit(sample, f"{KIT_DIR}/emergencies/E-001.yml", "status: open", "status: closed")
    assert run(sample, "CK-GATE-RECORD", branch="main").findings[0].message.startswith(ON_DEFAULT.format("G6"))


def test_the_check_command_takes_the_branch_from_the_caller(sample, capsys):
    ordinary(sample)
    assert main(["--root", str(sample), "check", "CK-GATE-RECORD", "--branch", "spec/001-demo"]) == 0
    assert "note:" not in capsys.readouterr().out
    assert main(["--root", str(sample), "check", "CK-GATE-RECORD"]) == 0
    assert "note: could not tell whether this is the default branch" in capsys.readouterr().out
    assert main(["--root", str(sample), "check", "CK-GATE-RECORD", "--branch", "main"]) == 1
    assert "but gate G6 has no approving decision record" in capsys.readouterr().out
    assert main(["--root", str(sample), "check", "CK-GATE-RECORD", "--branch", ""]) == 0, "a pipeline variable that is empty says nothing"
    assert "note: could not tell whether this is the default branch" in capsys.readouterr().out


# ── waivers and baseline ────────────────────────────────────────────────────────

def test_expired_waiver_fails(sample):
    edit(sample, f"{KIT_DIR}/waivers/W-001.yml", "2099-01-01", "2026-01-01")
    msgs = [f.message for f in run(sample, "CK-WAIVER").findings]
    assert any("expired" in m for m in msgs) and any("test-skip suppression" in m for m in msgs)


def test_baseline_count_can_only_go_down(sample):
    wf = sample / ".github/workflows/ci.yml"
    wf.write_text(wf.read_text() + "      - run: make test || true\n")
    assert any("ci-escape suppression(s) have no waiver (the baseline allows 1)" in f.message for f in run(sample, "CK-WAIVER").findings)
    wf.write_text("jobs: {}\n")
    r = run(sample, "CK-WAIVER")
    assert r.ok and any("can be lowered from 1 to 0" in n for n in r.notes)


def test_critical_waiver_needs_approval(sample):
    edit(sample, f"{KIT_DIR}/waivers/W-001.yml", "owner: qa", "owner: qa\ncritical: true")
    assert any("critical waiver needs approved_by" in f.message for f in run(sample, "CK-WAIVER").findings)


def test_suppression_patterns(sample):
    (sample / "src/a.cs").write_text('[Fact(Skip = "flaky")]\n#pragma warning disable CS0168\n')
    (sample / "Directory.Build.props").write_text('<NuGetAuditSuppress Include="x" />\n')
    rules = {s["rule"] for s in adapters.find_suppressions(selftest.context(sample))}
    assert rules == {"ci-escape", "test-skip", "lint-disable", "advisory-suppress"}


def test_installed_tooling_is_not_scanned_for_suppressions(sample):
    """The kit's own code under .specify/ contains suppression patterns as data; it is not the project's code."""
    tool = sample / ".specify/extensions/agentic/scripts/x.py"
    tool.parent.mkdir(parents=True)
    tool.write_text("import os  # noqa: F401\npattern = 'test.skip('\n")
    assert run(sample, "CK-WAIVER").ok


# ── traceability ────────────────────────────────────────────────────────────────

def test_failing_test_is_a_gap(sample):
    edit(sample, "specs/001-demo/evidence/junit.xml", "/></testsuite>", "><failure/></testcase></testsuite>")
    assert any("did not pass" in f.message for f in run(sample, "CK-TRACE").findings)


def test_open_task_is_tracked_debt_not_a_gap(sample):
    (sample / "specs/001-demo/evidence/junit.xml").unlink()
    edit(sample, "specs/001-demo/tasks.md", "- [x] T001", "- [ ] T001")
    assert run(sample, "CK-TRACE").ok
    edit(sample, "specs/001-demo/tasks.md", "- [ ] T001", "- [x] T001")
    assert any("gap" in f.message for f in run(sample, "CK-TRACE").findings)


def test_orphans_are_reported(sample):
    edit(sample, "specs/001-demo/tasks.md", "Carries: AC-001", "Carries: AC-001, AC-777")
    edit(sample, "specs/001-demo/spec.md", "principles: [P-1]", "principles: [P-9]")
    msgs = [f.message for f in run(sample, "CK-TRACE").findings]
    assert any("AC-777" in m for m in msgs) and any("P-9" in m for m in msgs)


def test_spec_without_tasks_is_not_failed_for_missing_tests(sample):
    for name in ("tasks.md", "evidence/junit.xml", "trace-manifest.json"):
        (sample / "specs/001-demo" / name).unlink()
    assert run(sample, "CK-TRACE").ok


# ── profiles ────────────────────────────────────────────────────────────────────

def lite(root):
    edit(root, KIT, "profile: regulated", "profile: lite")
    edit(root, KIT, "- demo", "")


def test_lite_skips_checks_it_does_not_require(sample):
    lite(sample)
    for cid in ("CK-CONSTITUTION", "CK-TRACE-GENERATED", "CK-DOMAIN-SECTIONS", "CK-DRIFT-SPEC"):
        r = run(sample, cid)
        assert r.ok and any("not required by the lite profile" in n for n in r.notes)


def test_lite_needs_only_one_approver_role_and_three_gates(sample):
    lite(sample)
    for gate in ("G2", "G4"):
        (sample / f"{KIT_DIR}/decisions/001-demo/{gate}.yml").unlink()
    assert run(sample, "CK-GATE-RECORD").ok
    assert run(sample, "CK-APPROVER").ok


def test_lite_reports_setup_gaps_without_failing(sample):
    lite(sample)
    (sample / ".github/CODEOWNERS").unlink()
    r = run(sample, "CK-ENFORCE-SETUP")
    assert r.ok and any("not enforced" in n for n in r.notes)


def test_a_reviewing_agents_findings_are_part_of_the_evidence_of_the_gate_they_were_written_for(sample):
    """A decision at a gate is bound to what the reviewers found for it, and to nothing they wrote for another gate."""
    from agentic_kit.__main__ import _evidence_files
    ctx = selftest.context(sample)
    before = _evidence_files(ctx, "001-demo", "G5", None)
    reviews = sample / "specs" / "001-demo" / "reviews"
    reviews.mkdir()
    (reviews / "G5-security.md").write_text("# Security review\n\nS-1: must fix.\n")
    (reviews / "G3-security.md").write_text("# Security review of the plan\n")
    ctx = selftest.context(sample)
    assert _evidence_files(ctx, "001-demo", "G5", None) == sorted(before + ["specs/001-demo/reviews/G5-security.md"])
    assert "specs/001-demo/reviews/G3-security.md" in _evidence_files(ctx, "001-demo", "G3", None)
    assert not [f for f in _evidence_files(ctx, "001-demo", "G4", None) if "/reviews/" in f]


def test_evidence_hash_may_be_optional_only_in_lite(sample):
    edit(sample, KIT, "require_evidence_hash: true", "require_evidence_hash: false")
    assert any("only in the lite profile" in f.message for f in run(sample, "CK-PROFILE").findings)


# ── audit ───────────────────────────────────────────────────────────────────────

def test_deleted_audit_entry_is_detected(sample):
    log = sample / f"{KIT_DIR}/audit/001-demo.jsonl"
    lines = log.read_text().splitlines()
    log.write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    assert not run(sample, "CK-AUDIT-CHAIN").ok


def test_decision_must_point_into_the_log(sample):
    edit(sample, f"{KIT_DIR}/decisions/001-demo/G1.yml", "audit_head: sha256:", "audit_head: sha256:00")
    assert any("not an entry" in f.message for f in run(sample, "CK-AUDIT-CHAIN").findings)


# ── adapter and CLI ─────────────────────────────────────────────────────────────

def test_github_adapter_parses_recorded_responses():
    canned = {
        "user": {"login": "kit-agent"},
        "repos/o/r/pulls/5/reviews": [{"id": 11, "user": {"login": "Alice", "type": "User"}, "state": "APPROVED",
                                       "commit_id": "abc123", "body": "gate G1 approve sha256:" + "1" * 64}],
        "repos/o/r/pulls/5/commits": [{"author": {"login": "Carol"}}, {"author": None}],
        "repos/o/r/branches/main/protection": {
            "required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": False},
            "required_status_checks": {"contexts": ["agentic-checks"]}, "enforce_admins": {"enabled": True}},
    }
    gh = adapters.GitHubAdapter("o/r", "main", runner=lambda path: canned[path])
    assert gh.agent_identity() == "kit-agent"
    (review,) = gh.reviews("pull/5")
    assert (review.id, review.reviewer, review.account_type, review.state, review.commit) == ("11", "Alice", "User", "APPROVED", "abc123")
    assert gh.authors("pull/5") == {"carol"}
    report = {r["item"]: r["status"] for r in gh.setup_report()}
    assert report["pull request reviews required"] == "pass" and report["code owner review required"] == "fail"
    with pytest.raises(Exception):
        gh.reviews("issue/5")


def test_cli_exit_codes(sample, capsys):
    assert main(["--root", str(sample), "check", "--today", selftest.TODAY]) == 0
    edit(sample, "specs/001-demo/spec.md", "tier_declared: high\n", "")
    assert main(["--root", str(sample), "check", "CK-TIER"]) == 1
    (sample / KIT).unlink()
    assert main(["--root", str(sample), "check", "CK-TIER"]) == 2
    assert main(["--root", str(sample), "check", "CK-NOPE"]) == 2
    capsys.readouterr()


LAUNCHER = Path(__file__).resolve().parents[1] / "extensions" / "agentic" / "scripts" / "agentic.py"


def to_a_reader_that_has_gone(*args):
    """Run the launcher as a program whose output nobody reads any more: what `... | head` does to it."""
    read_end, write_end = os.pipe()
    os.close(read_end)
    try:
        return subprocess.run([sys.executable, str(LAUNCHER), *args], stdout=write_end, stderr=subprocess.PIPE, text=True)
    finally:
        os.close(write_end)


def test_a_program_whose_reader_has_gone_ends_with_no_traceback_and_not_with_a_pass(sample):
    from agentic_kit.__main__ import PIPE_CLOSED
    passing = ["--root", str(sample), "check", "CK-TIER"]
    assert subprocess.run([sys.executable, str(LAUNCHER), *passing], capture_output=True, text=True).returncode == 0
    for args in (["list"], passing, ["--root", str(sample), "doctor"]):
        ended = to_a_reader_that_has_gone(*args)
        assert ended.stderr == "", (args, ended.stderr)
        assert ended.returncode == PIPE_CLOSED, (args, ended.returncode)
    helped = to_a_reader_that_has_gone("--help")  # argparse drops a help text it cannot write, so 0 is possible here
    assert helped.stderr == "" and helped.returncode in (0, PIPE_CLOSED)


def test_a_reader_that_reads_to_the_end_gets_everything_and_the_usual_exit_code():
    whole = subprocess.run([sys.executable, str(LAUNCHER), "list"], capture_output=True, text=True)
    assert whole.returncode == 0 and whole.stderr == ""
    listed = [line.split()[0] for line in whole.stdout.splitlines()]
    assert listed == sorted(set(listed)) and set(REGISTRY) <= set(listed)  # the program also lists the checks of the other extensions


def test_only_a_closed_pipe_ends_a_run_quietly(monkeypatch):
    import agentic_kit.__main__ as program

    class Gone:  # standard output after its reader has gone: it can no longer be flushed
        def flush(self):
            raise OSError(errno.EINVAL, "Invalid argument")

    class Intact:
        def write(self, text):  # since 2026-11-26 the check also tries a line (tests/test_windows_first_run.py, AC-006)
            pass

        def flush(self):
            pass

    invalid = OSError(errno.EINVAL, "Invalid argument")
    assert program.reader_went_away(BrokenPipeError(errno.EPIPE, "Broken pipe"), stream=Intact(), windows=False)
    assert program.reader_went_away(invalid, stream=Gone(), windows=True), "Windows reports a closed pipe as an invalid argument"
    assert not program.reader_went_away(invalid, stream=Intact(), windows=True), "standard output is intact, so this is another error"
    assert not program.reader_went_away(invalid, stream=Gone(), windows=False)
    assert not program.reader_went_away(PermissionError(errno.EACCES, "no"), stream=Gone(), windows=True)

    def refused(argv=None):
        raise PermissionError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(program, "main", refused)
    with pytest.raises(PermissionError):
        program.cli([])


def test_gate_command_prints_the_line_to_paste(sample, capsys):
    assert main(["--root", str(sample), "gate", "--spec", "001-demo", "--gate", "G3", "--json"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["approved"] and info["paste"].startswith("gate G3 approve sha256:") and "solutions-architect" in info["required_roles"]
    edit(sample, "specs/001-demo/plan.md", "One function", "Changed")
    main(["--root", str(sample), "gate", "--spec", "001-demo", "--gate", "G3", "--json"])
    assert not json.loads(capsys.readouterr().out)["approved"]


def test_a_file_is_parsed_once_and_each_caller_gets_a_copy_of_its_own(tmp_path, monkeypatch):
    from agentic_kit import core
    (tmp_path / "a.yml").write_text("only-in-this-test: [1, 2]\n", encoding="utf-8")
    src, parsed, real = Source(tmp_path), [], core.yaml.safe_load
    monkeypatch.setattr(core.yaml, "safe_load", lambda text: parsed.append(text) or real(text))
    core._PARSED.clear()
    first = src.yaml("a.yml")
    first["only-in-this-test"].append(3)
    assert src.yaml("a.yml") == {"only-in-this-test": [1, 2]}, "changing what one caller was given does not change what the next one gets"
    assert Source(tmp_path).yaml("a.yml") == {"only-in-this-test": [1, 2]} and len(parsed) == 1, "the same text is parsed once"
    (tmp_path / "a.yml").write_text("only-in-this-test: [9]\n", encoding="utf-8")
    assert src.yaml("a.yml") == {"only-in-this-test": [9]} and len(parsed) == 2, "text that changed is parsed again"
    (tmp_path / "a.yml").write_text("only-in-this-test: [9\n", encoding="utf-8")
    for _ in range(2):
        with pytest.raises(core.KitError, match="a.yml is not valid YAML"):
            src.yaml("a.yml")


def test_init_writes_a_valid_lite_setup(tmp_path, capsys):
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify/init-options.json").write_text('{"speckit_version": "1.4.3"}')
    assert main(["--root", str(tmp_path), "init", "--profile", "lite", "--repository", "o/r"]) == 0
    kit = yaml.safe_load((tmp_path / KIT).read_text())
    assert kit["profile"] == "lite" and kit["gates"]["require_evidence_hash"] is False and kit["domain_packs"] == []
    assert (tmp_path / ".github/workflows/agentic-checks.yml").exists()
    src = Source(tmp_path)
    assert run_check("CK-PROFILE", Context(src, src)).ok
    assert run_check("CK-METRIC-SOURCE", Context(src, src)).ok  # init starts the audit log the default metrics read
    assert run_check("CK-AUDIT-CHAIN", Context(src, src)).ok
    capsys.readouterr()
