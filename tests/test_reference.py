"""The HealthQ reference project (examples/healthq/project) checked with the kit itself.

Run: python -m pytest tests/test_reference.py -q
Set HEALTHQ_REPO to a clone of the healthcare repository to also run the checks that read its source.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

REF = ROOT / "examples" / "healthq"
PROJECT = REF / "project"
CRITICAL = {"C1", "C2", "C3", "C4", "C5", "C6", "N1", "N2"}
#: Pairs the kit's word comparison lists as similar. A Product Owner decides each; until then CK-DUPLICATE fails on them.
SIMILAR = [{"002-endpoint-authorization", "003-identity-from-token"}, {"005-triage-validation", "006-eval-production-path"}]
SPEC_CHECKS = ["CK-CONSTITUTION", "CK-ROLES", "CK-REQ-QUALITY", "CK-SPEC-SIZE", "CK-DOMAIN-SECTIONS", "CK-TIER", "CK-TIER-RAISE", "CK-TOUCH", "CK-TRACE",
               "CK-CROSS-SPEC", "CK-PROGRAMME", "CK-IMPACT", "CK-MAP-SCHEMA", "CK-MAP-OWNER", "CK-GATE-RECORD", "CK-BRIEF", "CK-LANE", "CK-AUDIT-CHAIN"]


def run(cid, root=PROJECT):
    src = core.Source(root)
    return core.run_check(cid, core.Context(src, src, {"today": "2026-11-22"}))


def front(spec_dir: Path) -> dict:
    return yaml.safe_load((spec_dir / "spec.md").read_text(encoding="utf-8").split("---")[1])


def specs() -> list[Path]:
    return sorted(p for p in (PROJECT / "specs").iterdir() if (p / "spec.md").is_file())


def test_the_project_carries_the_constitution_the_owner_approved():
    for name, where in (("constitution.md", ".specify/memory/constitution.md"), ("constitution.map.yml", ".specify/agentic/constitution.map.yml")):
        assert (PROJECT / where).read_text(encoding="utf-8") == (REF / "phase-4" / name).read_text(encoding="utf-8"), name


def test_one_person_holds_every_role_as_the_charter_says():
    roles = yaml.safe_load((PROJECT / ".specify/agentic/roles.yml").read_text(encoding="utf-8"))
    assert [p["id"] for p in roles["people"]] == ["imatiqul"] and set(roles["people"][0]["roles"]) == set(roles["roles"])
    kit = yaml.safe_load((PROJECT / ".specify/agentic/kit.yml").read_text(encoding="utf-8"))
    assert kit["profile"] == "regulated" and kit["domain_packs"] == ["hipaa"] and kit["gates"]["single_approver_exception"] == "allowed"


def test_the_map_is_in_the_kits_format_and_classifies_every_node():
    smap = yaml.safe_load((PROJECT / "system-map/map.yml").read_text(encoding="utf-8"))
    assert smap["schema"] == "agentic-map/1" and len(smap["nodes"]) == 77 and len(smap["edges"]) == 168
    assert {n["classification"] for n in smap["nodes"]} == {"restricted", "internal", "none"}
    unknown = [n for n in smap["nodes"] if "Not classified in Phase 1" in str(n.get("note"))]
    assert len(unknown) == 20 and all(n["classification"] == "restricted" for n in unknown), "what nobody classified is treated as protected"


def test_there_is_one_spec_for_each_critical_finding():
    found = [front(s).get("finding") for s in specs()]
    assert sorted(found) == sorted(CRITICAL) and all(front(s)["spec"] == s.name and front(s)["tier_declared"] == "critical" for s in specs())


@pytest.mark.parametrize("cid", SPEC_CHECKS)
def test_the_specs_pass_the_kits_checks(cid):
    r = run(cid)
    assert r.ok, [f.message for f in r.findings][:5]


def test_only_the_known_similar_pairs_wait_for_the_product_owner():
    waiting = set()
    for f in run("CK-DUPLICATE").findings:
        this = str(f.path).split("/")[1]
        other = f.message.split(" ", 1)[0]
        assert {this, other} in SIMILAR, f.message
        waiting.add(frozenset({this, other}))
    assert len(waiting) <= len(SIMILAR)


def test_every_spec_has_an_impact_report_and_a_brief_for_its_first_gate():
    for s in specs():
        impact = yaml.safe_load((s / "impact.md").read_text(encoding="utf-8").split("---")[1])
        assert impact["tier_computed"] == "critical" and impact["required_approvers"]["G3"], s.name
        brief = (s / "briefs" / "G1.md").read_text(encoding="utf-8")
        assert f"Brief for G1 of {s.name}" in brief and len(brief.splitlines()) <= 80


def test_the_specs_that_share_a_component_are_ordered_and_nothing_waits_on_the_analysis_only_spec():
    deps = {s.name: set(front(s)["depends_on"]["specs"]) for s in specs()}
    assert all("002-endpoint-authorization" not in d for d in deps.values()), "C2 is analysis only in the reference; nothing may wait for it"
    assert deps["004-audit-identity"] == {"001-fail-closed-auth", "003-identity-from-token"}, "the reference brief: C4 depends on C1 and C3"


@pytest.mark.skipif(not os.environ.get("HEALTHQ_REPO"), reason="set HEALTHQ_REPO to a clone of the healthcare repository")
def test_every_derived_fact_in_the_map_cites_a_file_in_the_healthcare_repository(tmp_path):
    repo = Path(os.environ["HEALTHQ_REPO"])
    before = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout
    sys.path.insert(0, str(REF))
    import overlay
    work = tmp_path / "work"
    overlay.build(repo, work)
    r = run("CK-MAP-EVIDENCE", work)
    assert r.ok, [f.message for f in r.findings][:5]
    assert subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout == before, "the repository is only read"
