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
#: Batch 2. N5 has no spec of its own: 005 covers it, which the owner approved with batch 1.
HIGH = {"H1", "H2", "H3", "H4", "H5", "H6", "N3", "N4"}
#: Batches 3 and 4, drafted on the owner's instruction to carry on; no gate is passed for them. N10 has no spec of its own: 021 covers it.
MEDIUM = {"M1", "M2", "M3", "M4", "M5", "N6"}
LOW = {"N7", "N8", "N9"}
#: Pairs the kit's word comparison lists as similar, which the owner decided as Product Owner (`distinct`, in chat on 2026-11-22).
DECIDED = [{"002-endpoint-authorization", "003-identity-from-token"}, {"005-triage-validation", "006-eval-production-path"},
           {"002-endpoint-authorization", "010-bff-authorization"}, {"004-audit-identity", "016-audit-record-content"},
           {"007-audit-export-complete", "015-audit-write-durable"}, {"007-audit-export-complete", "016-audit-record-content"}]
#: Pairs nobody has decided. Only a Product Owner can; until then CK-DUPLICATE fails on them, and it should.
WAITING = [{"014-pipeline-gates", "019-skipped-tests"}, {"014-pipeline-gates", "021-advisories-and-review"},
           {"019-skipped-tests", "021-advisories-and-review"}]
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
    assert smap["schema"] == "agentic-map/1" and len(smap["nodes"]) == 80 and len(smap["edges"]) == 168, \
        "77 from Phase 1, then the pipeline, the repository's build configuration and the development host"
    added = {n["id"] for n in smap["nodes"] if "added in Phase 5" in str(n.get("note"))}
    assert added == {"ci-pipeline", "repo-config", "dev-apphost"}, "each node the findings needed and Phase 1 did not draw says so"
    assert {n["classification"] for n in smap["nodes"]} == {"restricted", "internal", "none"}
    unknown = [n for n in smap["nodes"] if "Not classified in Phase 1" in str(n.get("note"))]
    assert len(unknown) == 20 and all(n["classification"] == "restricted" for n in unknown), "what nobody classified is treated as protected"


def test_there_is_one_spec_for_each_finding_drafted_so_far():
    found = [front(s).get("finding") for s in specs()]
    assert sorted(found) == sorted(CRITICAL | HIGH | MEDIUM | LOW), "one spec per finding, none twice"
    assert len(found) == 25, "27 findings in Phase 1; N5 is covered by 005 and N10 by 021"
    assert all(front(s)["spec"] == s.name for s in specs())
    assert all(front(s)["tier_declared"] == "critical" for s in specs() if front(s)["finding"] in CRITICAL)


def test_a_draft_says_it_is_a_draft_and_an_approved_spec_says_who_approved_it_and_how():
    for s in specs():
        text = (s / "spec.md").read_text(encoding="utf-8")
        if front(s)["finding"] in CRITICAL | HIGH:
            assert "G1 and G2 approved by the owner on 2026-11-22, in chat" in text and "No kit decision record exists yet" in text, s.name
            assert "## Decided at G2" in text and "## Questions for G2" not in text, s.name
        else:
            assert "Draft, waiting at gates G1 and G2" in text and "approved by the owner" not in text, s.name
            assert "## Questions for G2" in text and "(assumed)" in text and "(accepted)" not in text, s.name
    assert not list((PROJECT / ".specify/agentic").glob("decisions/**/*.yml")), "no gate of the reference has a kit decision record: every approval so far was in chat"


@pytest.mark.parametrize("cid", SPEC_CHECKS)
def test_the_specs_pass_the_kits_checks(cid):
    r = run(cid)
    assert r.ok, [f.message for f in r.findings][:5]


def dispositions(spec: str) -> dict:
    path = PROJECT / "specs" / spec / "origin.yml"
    if not path.is_file():
        return {}
    return {d["target"]: d for d in yaml.safe_load(path.read_text(encoding="utf-8")).get("dispositions") or []}


def test_only_the_pairs_nobody_has_decided_wait_for_the_product_owner():
    waiting = set()
    for f in run("CK-DUPLICATE").findings:
        this = str(f.path).split("/")[1]
        other = f.message.split(" ", 1)[0]
        waiting.add(frozenset({this, other}))
    assert waiting == {frozenset(p) for p in WAITING}, "the check fails on exactly the pairs that wait, and on nothing the owner decided"


def test_a_similar_pair_is_decided_only_by_the_owner_and_never_by_the_agent():
    for pair in DECIDED:
        a, b = sorted(pair)
        d = dispositions(a).get(b) or dispositions(b).get(a)
        assert d and d["decision"] == "distinct" and d["decided_by"] == {"reviewer": "imatiqul", "role": "product-owner"}, pair
        assert "Decided in chat on 2026-11-22" in d["reason"], "the record says how the decision was made"
    for pair in WAITING:
        a, b = sorted(pair)
        assert b not in dispositions(a) and a not in dispositions(b), f"{pair}: the agent may recommend; it may not record a decision"


def test_every_spec_has_an_impact_report_and_a_brief_for_its_first_gate():
    for s in specs():
        impact = yaml.safe_load((s / "impact.md").read_text(encoding="utf-8").split("---")[1])
        assert impact["tier_computed"] == front(s)["tier_declared"] and impact["required_approvers"]["G3"], s.name
        brief = (s / "briefs" / "G1.md").read_text(encoding="utf-8")
        assert f"Brief for G1 of {s.name}" in brief and len(brief.splitlines()) <= 80


def test_the_specs_that_share_a_component_are_ordered_and_nothing_waits_on_the_analysis_only_spec():
    deps = {s.name: set(front(s)["depends_on"]["specs"]) for s in specs()}
    assert all("002-endpoint-authorization" not in d for d in deps.values()), "C2 is analysis only in the reference; nothing may wait for it"
    assert deps["004-audit-identity"] == {"001-fail-closed-auth", "003-identity-from-token"}, "the reference brief: C4 depends on C1 and C3"
    out = subprocess.run([sys.executable, str(REF / "phase-5" / "order_specs.py"), "--check"], capture_output=True, text=True)
    assert out.returncode == 0, "the order in the specs is the one order_specs.py derives: " + out.stdout


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
