"""Tests for the system extension (slice 0.2, part 1). Run: python -m pytest tests -q"""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, selftest  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

from agentic_kit_system import checks_map, discover  # noqa: E402
from agentic_kit_system.mapmodel import load_map  # noqa: E402

FIXTURE = ROOT / "fixtures" / "multi-app"


@pytest.fixture()
def shop(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "shop")
    return tmp_path / "shop"


def ctx(root, **options):
    return selftest.context(root, **options)


def run(root, cid, **options):
    return core.run_check(cid, ctx(root, **options))


def test_all_fixtures_behave_with_the_system_extension_loaded():
    good, rows = selftest.run_selftest()
    assert good, [r for r in rows if r["expected"] != r["actual"]]
    assert len(rows) == len(core.REGISTRY) >= 46


def test_discovery_finds_the_fixture_and_cites_files():
    found = discover.discover(ctx(FIXTURE))
    ids = {n["id"]: n for n in found["nodes"]}
    assert set(ids) == {"shop-orders", "shop-billing", "shop-shared-lib", "shop-db", "contract-payments-openapi"}
    assert ids["shop-db"]["type"] == "data-store" and ids["shop-db"]["engine"] == "postgresql"
    assert ids["shop-orders"]["type"] == "service"
    assert all((FIXTURE / n["evidence"]).is_file() for n in found["nodes"])
    assert {(e["from"], e["to"]) for e in found["edges"]} == {("shop-orders", "shop-shared-lib"), ("shop-billing", "shop-shared-lib")}


def test_fixture_map_is_valid_and_matches_the_code():
    for cid in ("CK-MAP-SCHEMA", "CK-MAP-OWNER", "CK-MAP-EVIDENCE", "CK-MAP-DRIFT", "CK-MAP-FEDERATION"):
        r = run(FIXTURE, cid)
        assert r.ok, (cid, [f.line() for f in r.findings], r.not_run)


def test_shared_library_change_reaches_both_services_and_their_owners():
    c = ctx(FIXTURE)
    impact = checks_map.compute_impact(c, load_map(c), "001-money-format")
    assert [a["node"] for a in impact["affected"]] == ["shop-billing", "shop-orders"]
    assert impact["required_approvers"] == {"G3": ["backend", "platform"], "G5": ["platform"]}
    assert impact["packs_triggered"] == ["shared-component"]
    assert impact["tier_computed"] == "medium"


def test_database_change_reaches_both_writers_and_needs_the_data_owner(shop):
    spec = shop / "specs/001-money-format/spec.md"
    spec.write_text(spec.read_text().replace("touches: [shop-shared-lib]", "touches: [shop-db]"))
    c = ctx(shop)
    impact = checks_map.compute_impact(c, load_map(c), "001-money-format")
    assert {a["node"] for a in impact["affected"]} == {"shop-orders", "shop-billing"}
    assert "data-owner" in impact["required_approvers"]["G5"] and impact["packs_triggered"] == ["data-store"]


def test_transitive_reach_is_reported_with_distance(shop):
    m = shop / "system-map/map.yml"
    m.write_text(m.read_text().replace("edges:\n", "edges:\n  - {from: shop-billing, rel: calls, to: shop-orders, origin: assumed}\n"))
    spec = shop / "specs/001-money-format/spec.md"
    spec.write_text(spec.read_text().replace("touches: [shop-shared-lib]", "touches: [contract-payments-openapi]"))
    c = ctx(shop)
    reach = {a["node"]: a["distance"] for a in checks_map.compute_impact(c, load_map(c), "001-money-format")["affected"]}
    assert reach == {"shop-orders": 1, "shop-billing": 2}


def test_owner_of_a_touched_node_becomes_a_required_approver():
    from agentic_kit.checks_gov import gate_roles
    c = ctx(FIXTURE)
    assert gate_roles(c, "G3", "001-money-format") == ["solutions-architect", "backend", "platform"]
    assert gate_roles(c, "G5", "001-money-format") == ["qa", "platform"]
    assert gate_roles(c, "G1", "001-money-format") == ["product-owner"]


def test_undeclared_touch_fails_and_declared_touch_passes(shop):
    spec = "specs/001-money-format/spec.md"
    assert run(shop, "CK-TOUCH", changed_files=["packages/shared-lib/src/index.js", spec]).ok
    r = run(shop, "CK-TOUCH", changed_files=["packages/shared-lib/src/index.js", "db/migrations/002.sql", spec])
    assert any("belongs to shop-db" in f.message for f in r.findings)


def test_spec_touching_unknown_node_fails(shop):
    p = shop / "specs/001-money-format/spec.md"
    p.write_text(p.read_text().replace("touches: [shop-shared-lib]", "touches: [shop-shared-lib, ghost]"))
    assert any("ghost" in f.message for f in run(shop, "CK-TOUCH").findings)


def test_tier_must_rise_to_the_highest_touched(shop):
    p = shop / "specs/001-money-format/spec.md"
    p.write_text(p.read_text().replace("tier_declared: high", "tier_declared: low"))
    assert any("declared low but touches shop-shared-lib, which is medium" in f.message for f in run(shop, "CK-TIER-RAISE").findings)


def test_a_change_to_a_publisher_reaches_the_subscribers_of_what_it_publishes(shop):
    m = shop / "system-map/map.yml"
    m.write_text(m.read_text()
                 .replace("nodes:\n", "nodes:\n  - {id: topic-order.paid, type: event, owner: solutions-architect, tier: high, classification: internal, origin: assumed}\n")
                 .replace("edges:\n", "edges:\n  - {from: shop-orders, rel: publishes, to: topic-order.paid, origin: assumed}\n"
                                       "  - {from: shop-billing, rel: subscribes, to: topic-order.paid, origin: assumed}\n"))
    spec = shop / "specs/001-money-format/spec.md"
    spec.write_text(spec.read_text().replace("touches: [shop-shared-lib]", "touches: [shop-orders]"))
    c = ctx(shop)
    impact = checks_map.compute_impact(c, load_map(c), "001-money-format")
    reach = {a["node"]: (a["distance"], a["via"]) for a in impact["affected"]}
    assert reach["topic-order.paid"] == (1, "is published by shop-orders"), "what a touched component publishes is in play"
    assert reach["shop-billing"] == (2, "subscribes topic-order.paid"), "and so is everyone who subscribes to it"
    assert "solutions-architect" in impact["required_approvers"]["G3"], "the owner of the event is asked about the plan"
    spec.write_text(spec.read_text().replace("touches: [shop-orders]", "touches: [shop-billing]"))
    reach = {a["node"] for a in checks_map.compute_impact(ctx(shop), load_map(ctx(shop)), "001-money-format")["affected"]}
    assert "topic-order.paid" not in reach and "shop-orders" not in reach, "a change to a subscriber does not reach the publisher"


DAPR = {
    "src/Clinic.Triage/Clinic.Triage.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"></Project>\n',
    "src/Clinic.Billing/Clinic.Billing.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"></Project>\n',
    "tests/Clinic.Tests/Clinic.Tests.csproj": '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>\n',
    "src/Clinic.Triage/Handlers.cs": (
        'class Handlers {\n'
        '  async Task One() { await dapr.PublishEventAsync("pubsub", "triage.completed", new { Id = 1 }); }\n'
        '  async Task Two() {\n'
        '    await dapr.PublishEventAsync(\n'
        '        pubsubName: "pubsub",\n'
        '        topicName: "escalation.required",\n'
        '        data: new { Reason = "needs a person, urgently" },\n'
        '        cancellationToken: ct);\n'
        '  }\n'
        '  async Task Three(Workflow w) {\n'
        '    var topicName = w.Status == "Approved" ? "review.approved" : "review.denied";\n'
        '    await dapr.PublishEventAsync("pubsub", topicName, w);\n'
        '  }\n'
        '  async Task Four(string computed) { await dapr.PublishEventAsync("pubsub", computed + ".done", 1); await dapr.PublishEventAsync("pubsub", Name(), 1); }\n'
        '}\n'),
    "src/Clinic.Billing/Subscriber.cs": (
        'class Subscriber {\n'
        '  [Topic("pubsub", "triage.completed")]\n'
        '  [HttpPost("/dapr/sub/triage-completed")]\n'
        '  public Task Handle(Payload p) => Task.CompletedTask;\n'
        '}\n'),
    "tests/Clinic.Tests/HandlerTests.cs": 'class T { void M() { dapr.PublishEventAsync("pubsub", "only.in.a.test", 1); } }\n',
}


def test_dapr_topics_are_discovered_with_who_publishes_and_who_subscribes(tmp_path):
    for rel, text in DAPR.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)
    found = discover.discover(ctx(tmp_path))
    events = {n["id"]: n for n in found["nodes"] if n["type"] == "event"}
    assert set(events) == {"topic-triage.completed", "topic-escalation.required", "topic-review.approved", "topic-review.denied"}, \
        "a call that names its arguments across lines is read; a condition's own strings and a test project's topics are not topics"
    assert events["topic-escalation.required"]["evidence"] == "src/Clinic.Triage/Handlers.cs"
    edges = {(e["from"], e["rel"], e["to"]) for e in found["edges"]}
    assert {("clinic-triage", "publishes", "topic-triage.completed"), ("clinic-triage", "publishes", "topic-escalation.required"),
            ("clinic-triage", "publishes", "topic-review.approved"), ("clinic-triage", "publishes", "topic-review.denied"),
            ("clinic-billing", "subscribes", "topic-triage.completed")} <= edges
    assert not any("computed" in e["to"] or "Name" in e["to"] for e in found["edges"]), "a name built at run time is not seen, and is not guessed"


def test_new_dependency_in_code_is_drift(shop):
    pkg = shop / "services/billing/package.json"
    pkg.write_text(pkg.read_text().replace('"@shop/shared-lib": "1.2.0"', '"@shop/shared-lib": "1.2.0", "@shop/orders": "0.1.0"'))
    assert any("shop-billing builds-with shop-orders exists in the code but not in the map" in f.message
               for f in run(shop, "CK-MAP-DRIFT").findings)


def test_removed_component_is_drift(shop):
    shutil.rmtree(shop / "services/billing")
    msgs = [f.message for f in run(shop, "CK-MAP-DRIFT").findings]
    assert any("shop-billing" in m and "no longer finds it" in m for m in msgs)


def test_dependency_must_pass_a_gate_first(shop):
    (shop / "specs/002-next").mkdir()
    (shop / "specs/002-next/spec.md").write_text(
        "---\nspec: 002-next\ntier_declared: high\nowner_role: platform\ntouches: [shop-shared-lib]\n"
        "depends_on: {specs: [001-money-format]}\n---\n# Next\n- **FR-001**: more\n")
    assert run(shop, "CK-CROSS-SPEC").ok  # ordered by the dependency
    d = shop / ".specify/agentic/decisions/002-next"
    d.mkdir(parents=True)
    (d / "G1.yml").write_text("schema: agentic-decision/1\nspec: 002-next\ngate: G1\ndecision: approve\n")
    assert any("001-money-format, which this spec depends on, has not passed G1" in f.message
               for f in run(shop, "CK-CROSS-SPEC").findings)


def test_trace_manifest_links_requirements_to_nodes():
    from agentic_kit.checks_trace import build_manifest
    manifest = build_manifest(ctx(FIXTURE), "001-money-format")
    assert manifest["rows"][0]["nodes"] == ["shop-shared-lib"]


def test_checks_do_not_run_in_lite(shop):
    k = shop / ".specify/agentic/kit.yml"
    k.write_text(k.read_text().replace("profile: standard", "profile: lite"))
    r = run(shop, "CK-MAP-OWNER")
    assert r.ok and any("not required by the lite profile" in n for n in r.notes)
