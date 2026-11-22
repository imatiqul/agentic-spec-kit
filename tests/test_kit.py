"""Unit tests for slice 0.1. Run: python -m pytest tests -q   (needs pyyaml and git)."""
import json
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


def test_gate_command_prints_the_line_to_paste(sample, capsys):
    assert main(["--root", str(sample), "gate", "--spec", "001-demo", "--gate", "G3", "--json"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["approved"] and info["paste"].startswith("gate G3 approve sha256:") and "solutions-architect" in info["required_roles"]
    edit(sample, "specs/001-demo/plan.md", "One function", "Changed")
    main(["--root", str(sample), "gate", "--spec", "001-demo", "--gate", "G3", "--json"])
    assert not json.loads(capsys.readouterr().out)["approved"]


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
