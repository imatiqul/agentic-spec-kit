"""Tests for lanes, amendments and the reviewer brief (slice 0.4, group 1). Run: python -m pytest tests -q

Gate approvals here come from the test stand-in for a person (`golden.approve`), through the file adapter.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, lanes, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402
from agentic_kit.checks_gov import gate_roles, lane, required_gates  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

from agentic_kit_team import golden  # noqa: E402

FIXTURE = ROOT / "fixtures" / "multi-app"
KIT = ".specify/agentic"
SPEC = "040-docs"
SPEC_MD = """---
spec: {spec}
tier_declared: {tier}
owner_role: {owner}
principles: [P-1]
touches: [{touches}]
{extra}---
# Feature Specification: {spec}

## Requirements
- **FR-001**: The page MUST show the opening hours.

## Clarifications
- None yet.

## Acceptance Criteria
- **AC-001** (verifies FR-001): Given the page, When opened, Then the hours are shown.
"""


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def commit(root, message="change"):
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture()
def proj(tmp_path):
    """The fixture with a Low-tier docs site added to the map, a constitution, and one spec."""
    root = tmp_path / "shop"
    golden.prepare(FIXTURE, root)
    m = root / "system-map/map.yml"
    m.write_text(m.read_text().replace("edges:\n", "  - {id: docs-site, type: frontend, owner: backend, tier: low, classification: none, origin: assumed}\nedges:\n")
                 .replace("index:\n", "index:\n  - {paths: [\"docs-site/*\"], node: docs-site}\n"))
    (root / ".specify/memory").mkdir(parents=True)
    (root / ".specify/memory/constitution.md").write_text("# Constitution\n\n### P-1 Every requirement is traced to a test\nNo exceptions.\n\n### P-2 A person reviews every plan\n")
    (root / KIT / "constitution.map.yml").write_text(yaml.safe_dump({
        "schema": "agentic-constitution-map/1", "version": 1,
        "principles": [{"id": "P-1", "title": "Traced", "enforcement": "machine", "checks": ["ck:CK-TRACE"]},
                       {"id": "P-2", "title": "Plan review", "enforcement": "human", "judged_at": "G3"}]}, sort_keys=False))
    k = root / KIT / "kit.yml"
    k.write_text(k.read_text() + "lanes: {emergency: {days: 5}}\n")
    spec(root)
    commit(root, "docs site, constitution, spec")
    return root


def spec(root, name=SPEC, tier="low", touches="docs-site", owner="backend", extra=""):
    d = root / "specs" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.md").write_text(SPEC_MD.format(spec=name, tier=tier, touches=touches, owner=owner, extra=extra))
    return d


def ctx(root, base=None, **options):
    src = core.Source(root)
    return core.Context(src, src.at(base) if base else src, {"today": selftest.TODAY, **options})


def run(root, cid, base=None, **options):
    return core.run_check(cid, ctx(root, base, **options))


def msgs(r):
    return [f.message for f in r.findings]


def cli(root, *args):
    return main(["--root", str(root), *args])


def approve(root, gate, name=SPEC):
    golden.approve(root, name, gate, [])


def plan_and_tasks(root, name=SPEC):
    d = root / "specs" / name
    (d / "plan.md").write_text("# Plan\n\nOne static page.\n")
    cli(root, "impact", "--spec", name, "--write")
    (d / "tasks.md").write_text("# Tasks\n\n- [ ] T001 Write `docs-site/hours.html`. Carries: AC-001\n")
    cli(root, "trace", "--spec", name, "--write")


# ── the fast lane ───────────────────────────────────────────────────────────────

def test_a_low_tier_change_takes_the_fast_lane_with_one_review_for_g1_to_g4(proj, capsys):
    c = ctx(proj)
    assert lane(c, SPEC) == "fast" and required_gates(c, SPEC) == ("G4", "G5", "G6", "G7")
    assert cli(proj, "gate", "--spec", SPEC, "--gate", "G1", "--json") == 0
    assert json.loads(capsys.readouterr().out)["required"] is False
    plan_and_tasks(proj)
    # the one review carries the approvers and the evidence of all four gates
    assert set(gate_roles(ctx(proj), "G4", SPEC)) == {"engineering-manager", "qa", "product-owner", "solutions-architect", "backend"}
    approve(proj, "G4")
    rec = yaml.safe_load((proj / KIT / f"decisions/{SPEC}/G4.yml").read_text())
    assert rec["lane"] == "fast"
    names = {f.rsplit("/", 1)[-1] for f in rec["evidence"]["files"]}
    assert {"spec.md", "plan.md", "impact.md", "tasks.md", "trace-manifest.json", "G4.md"} <= names
    for cid in ("CK-GATE-RECORD", "CK-APPROVER", "CK-LANE", "CK-BRIEF", "CK-AMENDMENT"):
        r = run(proj, cid)
        assert r.ok, (cid, msgs(r), r.not_run)


def test_an_author_cannot_put_a_spec_on_the_fast_lane(proj):
    spec(proj, "041-orders", tier="high", touches="shop-orders", extra="lane: fast\n")
    assert lane(ctx(proj), "041-orders") == "standard"
    assert any("says lane fast, but impact analysis computes standard" in m for m in msgs(run(proj, "CK-LANE")))


def test_declaring_a_low_tier_does_not_buy_the_fast_lane(proj):
    spec(proj, "042-db", tier="low", touches="shop-db")  # a high-tier store that triggers the data pack
    assert lane(ctx(proj), "042-db") == "standard"
    spec(proj, "043-both", tier="low", touches="docs-site, shop-orders")
    assert lane(ctx(proj), "043-both") == "standard"


def test_a_spec_that_stops_qualifying_loses_its_fast_lane_approval(proj):
    plan_and_tasks(proj)
    approve(proj, "G4")
    spec(proj, tier="high", touches="docs-site, shop-orders")
    assert any("was approved on the fast lane, but the spec no longer qualifies" in m for m in msgs(run(proj, "CK-LANE")))
    assert any("G4 is approved but the earlier gate G1 is not" in m for m in msgs(run(proj, "CK-GATE-RECORD")))


def test_the_fast_lane_can_be_switched_off_and_does_not_exist_in_lite(proj):
    k = proj / KIT / "kit.yml"
    k.write_text(k.read_text().replace("lanes: {emergency: {days: 5}}", "lanes: {emergency: {days: 5}, fast: {enabled: false}}"))
    assert lane(ctx(proj), SPEC) == "standard"
    k.write_text(k.read_text().replace("fast: {enabled: false}", "fast: {enabled: true}").replace("profile: standard", "profile: lite"))
    assert lane(ctx(proj), SPEC) == "standard" and required_gates(ctx(proj), SPEC) == ("G1", "G3", "G5")


# ── the emergency lane ──────────────────────────────────────────────────────────

def emergency(root, **change):
    p = root / KIT / "_adapter/reviews.json"
    data = json.loads(p.read_text())
    data["changes"]["pull/1"]["reviews"].append({"id": "900", "reviewer": "lee", "type": "User", "state": "APPROVED", "commit": "abc1234",
                                                  "body": "Emergency: approve the hotfix now."})
    p.write_text(json.dumps(data))
    doc = {"schema": "agentic-emergency/1", "id": "E-7", "summary": "Payments time out", "declared": "2026-11-19",
           "declared_by": {"reviewer": "lee", "role": "devops-sre", "review_ref": "pull/1#review-900"}, "commit": "abc1234",
           "paths": ["services/billing/*"], "retrospective": {"spec": "050-retro", "due": "2026-11-24"}, "status": "open", **change}
    (root / KIT / "emergencies").mkdir(exist_ok=True)
    (root / KIT / "emergencies/E-7.yml").write_text(yaml.safe_dump(doc, sort_keys=False))


def test_an_emergency_passes_until_its_deadline_and_fails_the_branch_after(proj):
    emergency(proj)
    r = run(proj, "CK-EMERGENCY-DEADLINE")
    assert r.ok and any("retrospective due 2026-11-24 (3 day(s) left)" in n for n in r.notes)
    late = run(proj, "CK-EMERGENCY-DEADLINE", today="2026-11-25")
    assert msgs(late) == ["emergency E-7 was due on 2026-11-24: retrospective spec 050-retro has not passed every gate"]


def test_an_emergency_needs_a_valid_human_approval_from_an_allowed_role(proj):
    emergency(proj, declared_by={"reviewer": "pat", "role": "product-owner", "review_ref": "pull/1#review-900"})
    out = msgs(run(proj, "CK-EMERGENCY-DEADLINE"))
    assert any("the record says pat but the review is by lee" in m for m in out)
    assert any("role product-owner may not declare an emergency" in m for m in out)
    emergency(proj, declared_by={"reviewer": "lee", "role": "devops-sre", "review_ref": "pull/1#review-404"})
    assert any("was not found in the enforcement channel" in m for m in msgs(run(proj, "CK-EMERGENCY-DEADLINE")))


def test_an_emergency_cannot_give_itself_more_time_or_close_itself(proj):
    emergency(proj, retrospective={"spec": "050-retro", "due": "2026-12-31"})
    assert any("gives itself until 2026-12-31, later than the 5 days kit.yml allows (2026-11-24)" in m for m in msgs(run(proj, "CK-EMERGENCY-DEADLINE")))
    emergency(proj, status="closed")
    assert any("is closed, but its retrospective spec 050-retro has not passed every gate" in m for m in msgs(run(proj, "CK-EMERGENCY-DEADLINE")))


def test_emergency_records_need_a_configured_deadline(proj):
    emergency(proj)
    k = proj / KIT / "kit.yml"
    k.write_text(k.read_text().replace("lanes: {emergency: {days: 5}}\n", ""))
    assert any("sets no deadline" in m for m in msgs(run(proj, "CK-EMERGENCY-DEADLINE")))


def test_an_open_emergency_explains_a_change_that_has_no_spec_yet(proj):
    spec(proj, "044-billing", tier="high", touches="shop-billing", extra='paths: ["services/billing/*"]\n')
    dec = proj / KIT / "decisions/044-billing"
    dec.mkdir(parents=True)
    (dec / "G5.yml").write_text("schema: agentic-decision/1\nspec: 044-billing\ngate: G5\ndecision: approve\n")
    changed = ["services/billing/src/index.js"]
    assert any("changed with no spec" in m for m in msgs(run(proj, "CK-DRIFT-SPEC", changed_files=changed)))
    emergency(proj)
    assert run(proj, "CK-DRIFT-SPEC", changed_files=changed).ok


# ── amendments to an approved spec ──────────────────────────────────────────────

@pytest.fixture()
def approved(proj):
    """A standard-lane spec approved through G4."""
    spec(proj, tier="high", touches="shop-orders")
    for g in ("G1", "G2"):
        approve(proj, g)
    plan_and_tasks(proj)
    approve(proj, "G3")
    approve(proj, "G4")
    return proj


def edit(root, rel, old, new):
    p = root / rel
    assert old in p.read_text(), (rel, old)
    p.write_text(p.read_text().replace(old, new))


def test_nothing_is_reopened_while_nothing_approved_changes(approved, capsys):
    edit(approved, f"specs/{SPEC}/tasks.md", "- [ ] T001", "- [x] T001")  # ticking a task off is progress, not an amendment
    cli(approved, "trace", "--spec", SPEC, "--write")
    assert run(approved, "CK-AMENDMENT").ok and cli(approved, "amend", "status", "--spec", SPEC) == 0


def test_a_changed_requirement_reopens_g1_and_g2_only(approved, capsys):
    edit(approved, f"specs/{SPEC}/spec.md", "MUST show the opening hours", "MUST show the opening hours and the address")
    assert lanes.reopened(ctx(approved), SPEC)[0] == {"G1": ["spec.md: section 'Requirements'"], "G2": ["spec.md: section 'Requirements'"]}
    out = msgs(run(approved, "CK-AMENDMENT"))
    assert len(out) == 2 and all("it is re-opened and needs a new decision" in m for m in out)
    assert cli(approved, "amend", "status", "--spec", SPEC) == 1
    approve(approved, "G1")
    approve(approved, "G2")
    assert run(approved, "CK-AMENDMENT").ok and run(approved, "CK-GATE-RECORD").ok


def test_a_clarification_reopens_only_g2_and_a_plan_change_only_g3(approved):
    edit(approved, f"specs/{SPEC}/spec.md", "- None yet.", "- Hours are shown in local time.")
    assert sorted(lanes.reopened(ctx(approved), SPEC)[0]) == ["G2"]
    git(approved, "checkout", "--", f"specs/{SPEC}/spec.md")
    edit(approved, f"specs/{SPEC}/plan.md", "One static page.", "Two static pages.")
    assert sorted(lanes.reopened(ctx(approved), SPEC)[0]) == ["G3"]


def test_changing_what_a_spec_touches_reopens_the_spec_gates(approved):
    edit(approved, f"specs/{SPEC}/spec.md", "touches: [shop-orders]", "touches: [shop-orders, shop-billing]")
    assert lanes.reopened(ctx(approved), SPEC)[0]["G1"] == ["spec.md: front matter"]
    assert not run(approved, "CK-IMPACT").ok  # and the impact report must be regenerated, which re-opens G3 in turn


def test_a_new_task_reopens_g4(approved):
    edit(approved, f"specs/{SPEC}/tasks.md", "Carries: AC-001\n", "Carries: AC-001\n- [ ] T002 Add `docs-site/address.html`\n")
    assert sorted(lanes.reopened(ctx(approved), SPEC)[0]) == ["G4"]


# ── amendments to the constitution ──────────────────────────────────────────────

def test_a_constitution_amendment_needs_a_new_version_a_report_and_g0_again(approved, capsys):
    approve(approved, "G0", "_constitution")
    assert run(approved, "CK-AMENDMENT").ok
    edit(approved, ".specify/memory/constitution.md", "No exceptions.", "Generated code is exempt.")
    assert any("constitution.md changed since G0 approved it" in m for m in msgs(run(approved, "CK-AMENDMENT")))
    edit(approved, f"{KIT}/constitution.map.yml", "version: 1", "version: 2")
    out = msgs(run(approved, "CK-AMENDMENT"))
    assert any("is at version 2, but G0 approved version 1" in m for m in out) and any("has no amendment report" in m for m in out)
    assert cli(approved, "amend", "report", "--write") == 0
    report = (approved / KIT / "constitution/amendment-v2.md").read_text()
    front = yaml.safe_load(report.split("---")[1])
    assert front["changed"] == ["P-1"] and front["from_version"] == 1
    assert front["invalidated_specs"] == [{"spec": SPEC, "principles": ["P-1"], "approved_gates": ["G1", "G2", "G3", "G4"]}]
    approve(approved, "G0", "_constitution")
    rec = yaml.safe_load((approved / KIT / "decisions/_constitution/G0.yml").read_text())
    assert rec["constitution_version"] == 2 and f"{KIT}/constitution/amendment-v2.md" in rec["evidence"]["files"]
    assert run(approved, "CK-AMENDMENT").ok


# ── the reviewer brief ──────────────────────────────────────────────────────────

def test_brief_is_one_page_with_what_a_reviewer_needs(approved, capsys):
    edit(approved, f"specs/{SPEC}/plan.md", "One static page.", "One static page, cached for an hour.")
    assert cli(approved, "brief", "--spec", SPEC, "--gate", "G3") == 0
    text = capsys.readouterr().out
    for heading in ("## What changed since the last review", "## Impact", "## Risks", "## Open waivers", "## Disputed by a verifier", "## To decide"):
        assert heading in text
    assert "Since G3 was approved at" in text and f"`specs/{SPEC}/plan.md` changed: section 'Plan'" in text
    assert "Touches: shop-orders" in text and "solutions-architect" in text
    assert len(text.splitlines()) <= lanes.BRIEF_LINES


def test_brief_reports_what_a_verifier_disputed(approved, capsys):
    from agentic_kit_team import work
    c = work.context(approved)
    work.create_from_tasks(c, SPEC)
    item = work.read_item(c, SPEC, "T001")
    item["findings"] = [{"round": 1, "by": "independent-verifier", "text": "The hours ignore public holidays"}]
    work.write_item(c, item)
    cli(approved, "brief", "--spec", SPEC, "--gate", "G5")
    assert "T001, round 1: independent-verifier returned it: The hours ignore public holidays" in capsys.readouterr().out


def test_a_decision_made_on_a_stale_brief_fails(approved):
    assert run(approved, "CK-BRIEF").ok
    d = approved / "specs" / SPEC
    (d / "evidence").mkdir()
    (d / "evidence/junit.xml").write_text("<testsuite/>\n")
    cli(approved, "brief", "--spec", SPEC, "--gate", "G5", "--write")
    (d / "evidence/junit.xml").write_text('<testsuite><testcase name="later"/></testsuite>\n')  # the evidence moved on; the brief did not
    sha = commit(approved, "evidence after the brief")
    assert cli(approved, "record", "--spec", SPEC, "--gate", "G5", "--decision", "approve", "--commit", sha, "--approval", "sam:qa:pull/1#review-1") == 0
    assert any("describes different evidence from what was approved" in m for m in msgs(run(approved, "CK-BRIEF")))


def test_a_decision_without_a_brief_fails_in_standard_and_is_not_asked_for_in_lite(approved):
    rel = approved / KIT / f"decisions/{SPEC}/G3.yml"
    rec = yaml.safe_load(rel.read_text())
    rec["evidence"]["files"] = [f for f in rec["evidence"]["files"] if "/briefs/" not in f]
    rel.write_text(yaml.safe_dump(rec, sort_keys=False))
    assert any("does not include the reviewer brief" in m for m in msgs(run(approved, "CK-BRIEF")))
    k = approved / KIT / "kit.yml"
    k.write_text(k.read_text().replace("profile: standard", "profile: lite"))
    r = run(approved, "CK-BRIEF")
    assert r.ok and any("not required by the lite profile" in n for n in r.notes)  # Lite's effort is unchanged


def test_lane_command(proj, capsys):
    assert cli(proj, "lane") == 0
    assert f"{SPEC}: fast lane; gates G4, G5, G6, G7" in capsys.readouterr().out
