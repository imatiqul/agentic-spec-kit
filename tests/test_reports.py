"""Unit tests for views, metrics and the auditor evidence pack (TRC-11 to TRC-16).
Run: python -m pytest tests/test_reports.py -q"""
import hashlib
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, reports, selftest  # noqa: E402
from agentic_kit.__main__ import _evidence_files, main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

SPEC = selftest.SPEC
BASE = f"specs/{SPEC}"
KIT = f"{core.KIT_DIR}/kit.yml"
PACK = f"{BASE}/{reports.PACK_FILE}"
G7 = f"{core.KIT_DIR}/decisions/{SPEC}/G7.yml"


@pytest.fixture()
def sample(tmp_path):
    selftest.build_sample(tmp_path)
    return tmp_path


def ctx(root, **options):
    return selftest.context(root, **options)


def run(root, cid, **options):
    return core.run_check(cid, ctx(root, **options))


def msgs(r):
    return " | ".join(f.message for f in r.findings)


def edit(root, rel, old, new):
    p = root / rel
    body = p.read_text(encoding="utf-8")
    assert old in body, f"{old!r} not in {rel}"
    p.write_text(body.replace(old, new), encoding="utf-8")


def cli(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--root", str(root), *args])
    return code, out.getvalue() + err.getvalue()


def release(root):
    """Record a release decision that lists the evidence pack, as the gate command would bind it."""
    selftest._dump(root, G7, {"schema": "agentic-decision/1", "spec": SPEC, "gate": "G7", "decision": "approve",
                              "evidence": {"hash": "sha256:" + "0" * 64, "files": [PACK]}})


# ── views ───────────────────────────────────────────────────────────────────────

def test_views_come_from_the_core_and_from_each_extension(sample):
    code, out = cli(sample, "report", "list")
    assert code == 0 and out.split() == ["capabilities", "changesets", "debt", "gates", "map", "metrics", "spend", "trace", "waivers"]
    assert cli(sample, "report", "nonsense")[0] == 2


def test_the_gate_board_names_who_is_needed_next(sample):
    out = reports.view_gates(ctx(sample))
    assert "| 001-demo | approved | approved | approved | approved | approved | open | later | qa |" in out
    edit(sample, f"{BASE}/plan.md", "One function", "Two functions")
    assert "| 001-demo | approved | approved | open | approved | approved | later | later | solutions-architect" in reports.view_gates(ctx(sample)), \
        "a plan that changed after approval puts its own gate back to open; gates whose evidence did not change keep their decision"


def test_the_waiver_register_shows_what_has_run_out(sample):
    out = reports.view_waivers(ctx(sample))
    assert "| W-001 | test-skip | `tests/demo.spec.ts` | qa | 2099-01-01 | active |" in out and "| adoption baseline | ci-escape | 1 existing finding(s) |" in out
    assert "| qa | 2099-01-01 | expired |" in reports.view_waivers(ctx(sample, today="2100-01-01"))


def test_the_traceability_matrix_runs_from_principle_to_test(sample):
    out = reports.view_trace(ctx(sample))
    assert "| P-1 | FR-001 | AC-001 | T001 | 1 | proven |" in out
    edit(sample, f"{BASE}/spec.md", "## Data Classification", "- **AC-002** (verifies FR-001): Given no name, When greeted, Then it fails.\n\n## Data Classification")
    out = cli(sample, "report", "trace", "--spec", SPEC)[1]
    assert "AC-002" in out and "- Not traced:" in out


def test_the_map_view_is_a_diagram_and_a_table(sample):
    out = core.VIEW_HOOKS["map"](ctx(sample))
    assert "```mermaid" in out and 'n_demo_app["demo-app<br/>' in out and "-->|" in out and "| `demo-db` | data-store |" in out


def test_a_measure_with_no_data_is_not_shown(sample):
    names = [r["metric"] for r in reports.metrics(ctx(sample))]
    assert "Approvals recorded by people" in names and "Agent steps" in names and "Defects that escaped to production" in names
    assert not any(n.startswith("Time to decision") for n in names), "no decision has been recorded through the kit in the sample, so there is nothing to time"
    import shutil
    for folder in ("runs", "work", "incidents"):
        shutil.rmtree(sample / core.KIT_DIR / folder)
    names = [r["metric"] for r in reports.metrics(ctx(sample))]
    assert not any(n.startswith(("Agent", "Work items", "Defects")) for n in names)


def test_time_to_decision_is_counted_from_the_brief_to_the_recorded_decision(sample):
    assert cli(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")[0] == 0
    c = ctx(sample)
    digest = core.evidence_hash(c.src, SPEC, "G6", _evidence_files(c, SPEC, "G6", None))
    assert digest.startswith("sha256:")
    assert cli(sample, "record", "--spec", SPEC, "--gate", "G6", "--decision", "approve", "--commit", selftest.COMMIT,
               "--approval", "bob:qa:pull/1#review-50")[0] == 0
    times = reports.decision_times(ctx(sample))
    assert list(times) == ["G6"] and 0 <= times["G6"][0] < 0.1
    assert "| Time to decision at G6 (median hours, 1 spec(s)) | 0.0 | audit log |" in reports.view_metrics(ctx(sample))
    assert run(sample, "CK-AUDIT-CHAIN").ok, "the entry the brief adds keeps the chain intact"


def test_writing_a_brief_that_has_not_changed_adds_nothing_to_the_audit_log(sample):
    log = sample / core.KIT_DIR / "audit" / f"{SPEC}.jsonl"
    code, out = cli(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")
    assert code == 0 and out.startswith("wrote ")
    once = log.read_text(encoding="utf-8")
    assert once.count('"gate.ready"') == 1
    code, out = cli(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")
    assert code == 0 and out.startswith("unchanged ") and log.read_text(encoding="utf-8") == once, "the gate was already ready; nothing changed for the reviewer"
    inputs = sample / "specs" / SPEC / "verification" / "G6-inputs.yml"
    inputs.write_text(inputs.read_text(encoding="utf-8") + "# run again after a fix\n", encoding="utf-8")
    code, out = cli(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")
    assert code == 0 and out.startswith("wrote ") and log.read_text(encoding="utf-8").count('"gate.ready"') == 2, "new evidence, so the reviewer is asked again"


def test_all_views_can_be_written_as_files_and_as_one_page(sample, tmp_path_factory):
    out = tmp_path_factory.mktemp("report")
    code, text = cli(sample, "report", "all", "--out", str(out), "--html", "--today", "2026-11-22")
    assert code == 0 and "wrote 9 view(s)" in text
    assert sorted(p.name for p in out.iterdir()) == ["capabilities.md", "changesets.md", "debt.md", "gates.md", "index.html", "map.md", "metrics.md", "spend.md",
                                                     "trace.md", "waivers.md"]
    page = (out / "index.html").read_text(encoding="utf-8")
    assert page.startswith("<!DOCTYPE html>") and '<section id="gates">' in page and "<th>Spec</th>" in page and "Generated on 2026-11-22" in page
    assert "<script" not in page and "http" not in page.replace("http-equiv", ""), "the page stands alone: no script and nothing fetched"


def test_markdown_to_html_escapes_what_it_is_given():
    out = reports.to_html("# T <b>\n\nA `code` and **bold** <script>x</script>\n\n- one\n- two\n\n| a | b |\n|---|---|\n| 1 | <i> |\n\n```\n<raw>\n```\n")
    assert "<h1>T &lt;b&gt;</h1>" in out and "<code>code</code>" in out and "<strong>bold</strong>" in out and "&lt;script&gt;" in out
    assert "<ul><li>one</li><li>two</li></ul>" in out and "<td>&lt;i&gt;</td>" in out and "<pre>&lt;raw&gt;</pre>" in out and "<td>---</td>" not in out


# ── the evidence pack ───────────────────────────────────────────────────────────

def test_the_pack_holds_every_file_it_lists_with_its_hash(sample, tmp_path_factory):
    out = tmp_path_factory.mktemp("pack")
    code, text = cli(sample, "audit-pack", "--spec", SPEC, "--out", str(out), "--today", "2026-11-22")
    assert code == 0 and reports.STATEMENT in text
    manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == reports.PACK_SCHEMA and manifest["statement"] == reports.STATEMENT and manifest["generated_on"] == "2026-11-22"
    assert manifest["scope"] == {"specs": [SPEC]} and manifest["kit"]["profile"] == "regulated" and manifest["audit_log"] == "intact"
    on_disk = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file() and p.name != "MANIFEST.json")
    assert on_disk == sorted(manifest["files"])
    for name, digest in manifest["files"].items():
        assert digest == "sha256:" + hashlib.sha256((out / name).read_bytes()).hexdigest(), name
    assert {"decisions", "evidence", "audit", "trace", "waivers", "config"} <= {n.split("/")[0] for n in manifest["files"]}
    assert reports.STATEMENT in (out / "README.md").read_text(encoding="utf-8")
    gates = sorted(a["gate"] for a in manifest["approvals"])
    assert gates == ["G1", "G2", "G3", "G4", "G5"] and all(a["approvals"] and a["evidence_hash"].startswith("sha256:") for a in manifest["approvals"])
    assert {"kind": "emergency change", "id": "E-001"}.items() <= manifest["exceptions"][0].items()
    assert [w["id"] for w in manifest["waivers"]] == ["W-001", "adoption baseline"]
    assert manifest["checks"]["CK-TRACE"] == "pass" and "CK-SELFTEST" not in manifest["checks"]


def test_the_pack_maps_each_control_of_the_domain_pack_to_the_spec_section_that_answers_it(sample):
    rel = f"{core.KIT_DIR}/packs/demo.yml"
    pack = yaml.safe_load((sample / rel).read_text(encoding="utf-8"))
    pack["controls"] = [{"section": "Data Classification", "reference": "DEMO 1.2", "asks": "Which data the change touches"},
                        {"section": "Retention", "reference": "DEMO 4.1", "asks": "How long data is kept"}]
    (sample / rel).write_text(yaml.safe_dump(pack), encoding="utf-8")
    manifest, _ = reports.build_pack(ctx(sample), [SPEC])
    first, second = manifest["controls"]
    assert first["pack"] == "demo" and first["reference"] == "DEMO 1.2"
    assert first["specs"][SPEC]["present"] is True and first["specs"][SPEC]["sha256"] == "sha256:" + hashlib.sha256(b"Synthetic data only.").hexdigest()
    assert second["specs"][SPEC] == {"present": False, "sha256": None, "where": f"specs/{SPEC}/spec.md, section 'Retention'"}, \
        "a control the spec does not answer is shown as unanswered, not left out"


def test_a_single_approver_exception_is_listed(sample):
    edit(sample, f"{core.KIT_DIR}/decisions/{SPEC}/G3.yml", "single_approver_exception: false", "single_approver_exception: true")
    manifest, _ = reports.build_pack(ctx(sample), [SPEC])
    assert {"kind": "single approver", "spec": SPEC, "gate": "G3"}.items() <= manifest["exceptions"][0].items()


def test_a_pack_for_a_date_range_takes_the_specs_decided_in_it(sample):
    assert reports.specs_in_range(ctx(sample), None, None) == [], "the sample's decisions were not recorded through the kit, so the log has none"
    cli(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")
    cli(sample, "record", "--spec", SPEC, "--gate", "G6", "--decision", "approve", "--commit", selftest.COMMIT, "--approval", "bob:qa:pull/1#review-50")
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).date()
    assert reports.specs_in_range(ctx(sample), today, today) == [SPEC]
    assert reports.specs_in_range(ctx(sample), today + datetime.timedelta(days=1), None) == []
    code, out = cli(sample, "audit-pack", "--from", "2000-01-01", "--to", "2000-12-31")
    assert code == 0 and json.loads(out[: out.rindex("}") + 1])["scope"] == {"specs": [], "from": "2000-01-01", "to": "2000-12-31"}
    assert cli(sample, "audit-pack", "--from", "yesterday")[0] == 2 and cli(sample, "audit-pack", "--spec", "999-none")[0] == 2


def test_a_release_needs_its_pack_in_front_of_the_approver(sample):
    release(sample)
    assert "released with no evidence pack" in msgs(run(sample, "CK-AUDIT-PACK"))
    code, out = cli(sample, "audit-pack", "--spec", SPEC, "--write")
    assert code == 0 and f"wrote {PACK}" in out
    kept = json.loads((sample / PACK).read_text(encoding="utf-8"))
    assert "files" not in kept and kept["statement"] == reports.STATEMENT and f"{BASE}/spec.md" in kept["sources"]
    assert run(sample, "CK-AUDIT-PACK").ok
    selftest._dump(sample, G7, {"schema": "agentic-decision/1", "spec": SPEC, "gate": "G7", "decision": "approve", "evidence": {"hash": "x", "files": []}})
    assert "does not list the evidence pack among what was reviewed" in msgs(run(sample, "CK-AUDIT-PACK"))


def test_a_pack_goes_stale_when_what_it_recorded_changes(sample):
    cli(sample, "audit-pack", "--spec", SPEC, "--write")
    release(sample)
    assert run(sample, "CK-AUDIT-PACK").ok
    with (sample / core.KIT_DIR / "audit" / f"{SPEC}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write("")
    core.audit_append(sample, SPEC, {"type": "kit", "id": "test"}, "note", spec=SPEC)
    assert run(sample, "CK-AUDIT-PACK").ok, "the audit log grows after a release; that is not a change to the evidence"
    edit(sample, f"{core.KIT_DIR}/roles.yml", "id: bob", "id: robert")
    assert run(sample, "CK-AUDIT-PACK").ok, "people change roles after a release; the pack holds the roles as they were"
    edit(sample, f"{BASE}/plan.md", "One function", "Two functions")
    assert f"{BASE}/plan.md changed after the evidence pack was made" in msgs(run(sample, "CK-AUDIT-PACK"))


def test_a_pack_the_kit_did_not_make_is_not_a_pack(sample):
    cli(sample, "audit-pack", "--spec", SPEC, "--write")
    release(sample)
    edit(sample, PACK, "It does not certify compliance with any law, regulation or standard.", "It certifies compliance.")
    assert "lacks the statement that it does not certify compliance" in msgs(run(sample, "CK-AUDIT-PACK"))
    (sample / PACK).write_text("not json", encoding="utf-8")
    assert "not valid JSON" in msgs(run(sample, "CK-AUDIT-PACK"))


def test_the_pack_is_asked_of_regulated_projects_only(sample):
    release(sample)
    edit(sample, KIT, "profile: regulated", "profile: standard")
    r = run(sample, "CK-AUDIT-PACK")
    assert r.ok and any("skipped" in n for n in r.notes)


# ── the as-built requirement map ────────────────────────────────────────────────

def test_the_as_built_requirement_map_matches_the_code():
    """Every requirement has a check or a stated way it is met, and the committed map says what the code says."""
    import importlib.util
    path = ROOT / "docs" / "design" / "gen_as_built_map.py"
    spec = importlib.util.spec_from_file_location("gen_as_built_map", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    text, _ = module.build()
    committed = (ROOT / "docs" / "design" / "requirement-map-as-built.md").read_text(encoding="utf-8")
    assert committed == text, "run `python docs/design/gen_as_built_map.py` and commit the result"


# ── the reference constitution (Phase 4 draft) ──────────────────────────────────

def test_the_reference_constitution_maps_every_principle_and_answers_every_finding(sample):
    import shutil
    ref = ROOT / "examples" / "healthq" / "phase-4"
    shutil.copy(ref / "constitution.md", sample / ".specify/memory/constitution.md")
    shutil.copy(ref / "constitution.map.yml", sample / core.KIT_DIR / "constitution.map.yml")
    r = run(sample, "CK-CONSTITUTION")
    assert r.ok, [f.message for f in r.findings]
    cmap = yaml.safe_load((ref / "constitution.map.yml").read_text(encoding="utf-8"))
    answered = {f for p in cmap["principles"] for f in p.get("findings", [])}
    findings = [f"C{i}" for i in range(1, 7)] + [f"H{i}" for i in range(1, 7)] + [f"M{i}" for i in range(1, 6)] + [f"N{i}" for i in range(1, 11)]
    assert [f for f in findings if f not in answered] == [], "every Phase 1 finding traces to a principle"
    assert all(v.get("status") == "not built" for v in cmap["external_checks"].values()), "a check outside the kit is not claimed to exist"
    used = {c for p in cmap["principles"] for c in p.get("checks", []) if not c.startswith("ck:")}
    assert used == set(cmap["external_checks"]), "every declared external check is used, and every one used is declared"
