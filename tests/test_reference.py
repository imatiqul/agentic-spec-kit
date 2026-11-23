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
               "CK-CROSS-SPEC", "CK-PROGRAMME", "CK-IMPACT", "CK-MAP-SCHEMA", "CK-MAP-OWNER", "CK-BRIEF", "CK-LANE", "CK-AUDIT-CHAIN",
               # Phase 6: what a plan and a task list must have, which an agent can write
               "CK-TRACE-GENERATED", "CK-PRIVACY-IMPACT", "CK-TEST-STRATEGY", "CK-ROLLOUT", "CK-PROGRESSIVE", "CK-FLAG", "CK-DATA-PLAN", "CK-DATA-CLASS"]
#: Phase 6. Specs with a plan; all but 013 also have a task list. Drafted on the owner's instruction to carry on: G3 and G4 are not passed.
PLANNED = ["001-fail-closed-auth", "003-identity-from-token", "004-audit-identity", "005-triage-validation", "006-eval-production-path",
           "013-migrations-production-engine"]
TASKED = PLANNED[:-1]


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
    assert smap["schema"] == "agentic-map/1" and len(smap["nodes"]) == 100 and len(smap["edges"]) == 206, \
        "77 from Phase 1; the pipeline, the build configuration and the development host; and 20 event topics the kit's discovery found"
    added = {n["id"] for n in smap["nodes"] if "added in Phase 5" in str(n.get("note"))}
    assert added == {"ci-pipeline", "repo-config", "dev-apphost"}, "each node the findings needed and Phase 1 did not draw says so"
    found = [x for x in smap["nodes"] + smap["edges"] if "found by the kit's discovery in Phase 6" in str(x.get("note"))]
    assert len(found) == 49 and all(x["origin"] == "derived" and x.get("evidence") for x in found), "20 topics, 22 publishers, 7 build edges, each citing a file"
    # Found in Phase 7, while tracing the C4 change: the audit event stream had no writer on the map.
    writers = sorted(e["from"] for e in smap["edges"] if e["to"] == "event-hubs-audit" and e["rel"] == "writes")
    assert len(writers) == 9 and writers == sorted(e["from"] for e in smap["edges"] if e["to"] == "phi-audit-logs" and e["rel"] == "writes"), \
        "the nine services that write the audit table also write the audit event stream"
    edges = {(e["from"], e["rel"], e["to"]) for e in smap["edges"]}
    assert {("agent-service", "publishes", "topic-triage.completed"), ("agent-service", "publishes", "topic-escalation.required")} <= edges, \
        "the two publishers the Phase 1 draft missed, which a review of pull request 72 pointed out"
    events = {n["id"] for n in smap["nodes"] if n["type"] == "event"}
    unpublished = events - {to for _, rel, to in edges if rel == "publishes"}
    assert unpublished == {"topic-healthq-dlq", "topic-revenue.prior-auth.status-changed"}, "the dead-letter topic, and one topic nobody publishes"
    assert {n["classification"] for n in smap["nodes"]} == {"restricted", "internal", "none"}
    unknown = [n for n in smap["nodes"] if "Not classified in Phase 1" in str(n.get("note"))]
    assert len(unknown) == 20 and all(n["classification"] == "restricted" for n in unknown), "what nobody classified is treated as protected"
    unclassified = [n for n in smap["nodes"] if "Not classified" in str(n.get("note"))]
    assert len(unclassified) == 40 and all(n["classification"] == "restricted" for n in unclassified), "20 from Phase 1 and the 20 topics found since"


def test_a_change_to_the_agent_service_reaches_the_subscribers_of_its_events():
    impact = yaml.safe_load((PROJECT / "specs/005-triage-validation/impact.md").read_text(encoding="utf-8").split("---")[1])
    reached = {a["node"]: a["distance"] for a in impact["affected"]}
    assert reached["topic-triage.completed"] == 1 and reached["topic-escalation.required"] == 1
    assert {reached[n] for n in ("scheduling-service", "pophealth-service", "revenue-service", "notification-service")} == {2}
    assert "solutions-architect" in impact["required_approvers"]["G3"], "the owner of the events is asked about the plan"


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


def failures(cid, root=PROJECT) -> set[tuple[str, str]]:
    """(spec, message) of each finding of a check."""
    out = set()
    for f in run(cid, root).findings:
        parts = str(f.path).split("/")
        out.add((parts[1] if len(parts) > 1 and parts[0] == "specs" else str(f.path), f.message))
    return out


def test_the_plans_are_drafts_that_wait_at_g3_and_the_task_lists_at_g4():
    for name in PLANNED:
        folder = PROJECT / "specs" / name
        assert "Draft, waiting at gate G3" in (folder / "plan.md").read_text(encoding="utf-8"), name
        assert front(folder)["changes_existing_code"] is True, "an adopted codebase: each planned spec says it changes existing code"
        for gate in ("G3",) + (("G4",) if name in TASKED else ()):
            assert f"Brief for {gate} of {name}" in (folder / "briefs" / f"{gate}.md").read_text(encoding="utf-8")
        assert (folder / "tasks.md").is_file() == (name in TASKED), "013 is spec and plan only"
        if name in TASKED:
            assert "Draft, waiting at gate G4" in (folder / "tasks.md").read_text(encoding="utf-8"), name
    planned = sorted(s.name for s in specs() if (s / "plan.md").is_file())
    assert planned == PLANNED, "plans for C1, C3 to C6 and H5; C2 has a breakdown and no plan"
    breakdown = (PROJECT / "specs/002-endpoint-authorization/programme.md").read_text(encoding="utf-8")
    assert "A proposal, waiting for the owner" in breakdown and "programme" not in front(PROJECT / "specs/002-endpoint-authorization"), \
        "making 002 a programme is an amendment to an approved spec: it is proposed, not applied"


def test_what_only_a_person_can_do_still_fails_and_nothing_else_does():
    # No pull-request review has approved a gate, so a plan or a task list is ahead of its gates. The kit says so.
    expect = {(n, f"plan.md exists but gate {g} has no approving decision record") for n in PLANNED for g in ("G1", "G2")} | \
             {(n, "tasks.md exists but gate G3 has no approving decision record") for n in TASKED}
    assert failures("CK-GATE-RECORD") == expect
    # Nobody has run the tests that pin today's behaviour: the agent cannot restore the solution's packages, and no pipeline runs.
    got = failures("CK-CHARACTERIZATION")
    assert {n for n, _ in got} == set(PLANNED)
    assert ("004-audit-identity", "the characterization tests did not pass (result: not-run)") in got, "they exist for 004; they have not been run"
    # No clinician has signed a golden set or accepted a safety case, and nobody in roles.yml is one.
    assert {n for n, _ in failures("CK-AI-EVAL")} == {n for n, _ in failures("CK-AI-SAFETY-CASE")} == {"005-triage-validation", "006-eval-production-path"}
    assert all("accepted through the enforcement channel" in m for _, m in failures("CK-AI-SAFETY-CASE"))
    # Two threats of 004 are tested by criteria the approved spec did not write as abuse cases. Marking them is the owner's amendment.
    assert failures("CK-THREAT-MODEL") == {("004-audit-identity", f"{ac} tests threat {th} but is not written as an abuse case in the spec")
                                           for ac, th in (("AC-004", "TH-2"), ("AC-005", "TH-3"))}


C4 = "004-audit-identity"


def test_the_c4_change_was_worked_task_by_task_and_reviewed_by_agents_that_did_not_write_it():
    """Phase 7. The run log: which agent did what, each hand-off, each rework round."""
    items = {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted((PROJECT / ".specify/agentic/work" / C4).glob("T*.yml"))}
    assert {k: v["state"] for k, v in items.items()} == {"T001": "done", "T002": "done", "T003": "done", "T004": "done", "T005": "ready", "T006": "ready"}, \
        "the four tasks an agent could do are done; the test run and the verification that follows it are not"
    for tid in ("T001", "T002", "T003", "T004"):
        item = items[tid]
        assert item["reviewer_agent"] in ("security-reviewer", "independent-verifier") and item["reviewer_agent"] != item["owner_agent"]
        assert (PROJECT / item["context"]["path"]).is_file() and (PROJECT / item["handoff"]["evidence"][0]).is_file()
    assert {tid: v["rework_rounds"] for tid, v in items.items() if v.get("rework_rounds")} == {"T001": 1, "T003": 1, "T004": 1}, \
        "three items came back once with a reviewer's finding; none came back twice"
    assert all(f["by"] in ("security-reviewer", "independent-verifier") for v in items.values() for f in v.get("findings") or [])
    for cid in ("CK-WORKITEM", "CK-REWORK-LIMIT", "CK-PATH-DIFF", "CK-CONTEXT", "CK-VERIFY-INPUTS", "CK-AUTHOR-NEQ-VERIFIER", "CK-ROUTING", "CK-AUDIT-CHAIN"):
        assert run(cid).ok, (cid, [f.message for f in run(cid).findings][:3])
    record = yaml.safe_load((PROJECT / ".specify/agentic/runs" / C4 / "r1.yml").read_text(encoding="utf-8"))
    assert record["state"] == "stopped" and record["steps"] == 11 and "T005 needs a machine" in record["stop_reason"]
    # What the run record lacks is what only a runtime can report, and nobody made it up: what each step cost.
    lacking = {m.split(" does not record ")[-1] for _, m in failures("CK-RUN-RECORD") if " does not record " in m}
    assert lacking == {"the cost"}


def test_the_c4_change_stops_where_a_person_or_a_build_is_needed():
    """Phase 7. Evidence is prepared for G5 to G7; no gate is passed, and the kit says what stands in the way."""
    from agentic_kit.__main__ import _evidence_files
    src = core.Source(PROJECT)
    ctx = core.Context(src, src, {"today": "2026-11-22"})
    spec = PROJECT / "specs" / C4
    g5 = _evidence_files(ctx, C4, "G5", None)
    assert f"specs/{C4}/reviews/G5-security.md" in g5 and f"specs/{C4}/evidence/trace-lines.md" in g5, "a decision at G5 is bound to the review and the trace"
    for gate in ("G5", "G6", "G7"):
        assert (spec / "briefs" / f"{gate}.md").is_file()
    for report, rounds in (("reviews/G5-security.md", "## Round 2"), ("verification/G6-report.md", "## Round 2")):
        assert rounds in (spec / report).read_text(encoding="utf-8")
    assert not (PROJECT / ".specify/agentic/decisions").exists(), "no gate decision is recorded: none was made in a pull request"
    # The approved spec is as the owner approved it. What the reviews found wrong in it is proposed, not applied.
    text = (spec / "spec.md").read_text(encoding="utf-8")
    assert "- **AC-004** (verifies FR-003): " in text and "event-hubs-audit" not in str(front(spec)["touches"])
    proposed = (spec / "amendment-proposed.md").read_text(encoding="utf-8")
    assert "`spec.md` has not been edited" in proposed and proposed.count("\n## ") == 7
    # Still failing for this spec, each for a reason an agent cannot remove: a build, an environment, or a person.
    assert ("specs/004-audit-identity/release/sbom.cdx.json", "the spec is being released with no bill of materials") in failures("CK-SBOM") \
        or (C4, "the spec is being released with no bill of materials") in failures("CK-SBOM")
    assert run("CK-OPS-READINESS").ok


def test_the_showcase_proposals_are_proposals():
    """Phase 9. A baseline nobody approved waives nothing; the matrix for C2 has no row that was run."""
    assert not (PROJECT / ".specify/agentic/waivers").exists(), "the kit reads a baseline only from the waivers folder, and none is there"
    text = (PROJECT / ".specify/agentic/proposals/adoption-baseline.md").read_text(encoding="utf-8")
    block = yaml.safe_load(text.split("```yaml")[1].split("```")[0])
    assert block["approved_by"] == {"reviewer": "", "review_ref": ""} and len(block["groups"]) == 14
    assert sum(g["count"] for g in block["groups"]) == 635 and all(g["owner"] and g["expires"] for g in block["groups"])
    roles = yaml.safe_load((PROJECT / ".specify/agentic/roles.yml").read_text(encoding="utf-8"))["roles"]
    assert {g["owner"] for g in block["groups"]} <= set(roles)
    c2 = PROJECT / "specs" / "002-endpoint-authorization"
    matrix = yaml.safe_load((c2 / "authorization-matrix.yml").read_text(encoding="utf-8"))["rows"]
    assert len(matrix) == 20 and {r["result"] for r in matrix} == {"not-run"} and all(r["role"] and r["tenant"] and r["resource"] and r["expect"] for r in matrix)
    threats = yaml.safe_load((c2 / "threat-model.yml").read_text(encoding="utf-8"))
    acs = (c2 / "spec.md").read_text(encoding="utf-8")
    assert all(f"**{t['test']}** (verifies {t['mitigation']}) (abuse case)" in acs for t in threats["threats"]), "each listed threat is tested by an abuse case of the approved spec"
    assert len(threats["gaps"]) == 6


def test_the_rollout_orders_follow_who_reads_whose_events():
    for name in ("004-audit-identity", "013-migrations-production-engine"):
        deploy = yaml.safe_load((PROJECT / "specs" / name / "rollout.yml").read_text(encoding="utf-8"))["deploy"]
        services = [d for d in deploy if d.endswith("-service")]
        assert services.index("agent-service") < services.index("scheduling-service") < services.index("fhir-service"), \
            "scheduling reads the agent service's events, and FHIR reads scheduling's"
        assert services.index("voice-service") < services.index("agent-service") and services[-1] == "notification-service"


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
    r = run("CK-MAP-DRIFT", work)
    assert r.ok, "the map matches what the kit's discovery finds in the code: " + str([f.message for f in r.findings][:5])
    # Finding C6, found by the kit: the evaluation harness never calls the classifier.
    assert failures("CK-AI-PROD-PATH", work) == {
        (n, "the harness never refers to ClassifyUrgency in src/HealthQCopilot.Agents/Plugins/TriagePlugin.cs: it does not exercise the production code path")
        for n in ("tests/HealthQCopilot.Tests.Eval/ClinicalAccuracyHarnessTests.cs",)}
    # Finding H4, found by the kit: figures written into endpoints, with no evaluation or telemetry behind them.
    unsourced = failures("CK-METRIC-PROVENANCE", work)
    assert ("src/HealthQCopilot.Agents/Endpoints/DemoDataEndpoints.cs:43",
            "the figure aiAccuracyRate = 94.2 has no recorded source; register it in .specify/agentic/metric-claims.yml or remove it") in unsourced
    assert {n.split(":")[0] for n, _ in unsourced} == {"src/HealthQCopilot.Agents/Endpoints/DemoDataEndpoints.cs", "src/HealthQCopilot.Agents/Endpoints/DemoEndpoints.cs"}
    # With the source present, the tests that pin 004's code exist. What is missing is a run of them.
    assert {m for n, m in failures("CK-CHARACTERIZATION", work) if n == "004-audit-identity"} == {"the characterization tests did not pass (result: not-run)"}
    assert subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout == before, "the repository is only read"


@pytest.mark.skipif(not os.environ.get("HEALTHQ_C4_REPO"), reason="set HEALTHQ_C4_REPO to a clone of the healthcare repository with the branch sdd/004-audit-identity checked out")
def test_a_line_of_the_c4_change_traces_back_to_the_principle_and_forward_to_what_it_reaches():
    """Acceptance, reference example: any line of the C4 change, to a principle and to what it affects. The clone is only read."""
    from agentic_kit_product import lineage
    src = core.Source(Path(os.environ["HEALTHQ_C4_REPO"]))
    out = lineage.why(core.Context(src, src, {"today": "2026-11-22"}), "src/HealthQCopilot.Fhir/Program.cs:86")
    assert "**Work item:** 004-audit-identity/T002" in out and "agent backend-implementer" in out and "**Task T002 carries:** AC-001" in out
    assert "**FR-001:** Each service MUST run the PHI audit middleware after authentication" in out
    assert "**Principle P-9:** Every access to PHI is attributed" in out
    assert "**Component:** `fhir-service` (service, owner backend, tier critical)" in out
    assert "**The spec depends on:** `phi-audit-logs` (schema-object), `event-hubs-audit` (event-stream), `entra-id` (external-service)" in out
    assert "Reaches data stores (9)" in out and "**Approvals:** none recorded yet" in out

