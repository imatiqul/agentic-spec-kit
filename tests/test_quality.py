"""Unit tests for the quality packs (slice 0.4). Run: python -m pytest tests/test_quality.py -q"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

import agentic_kit_quality as quality  # noqa: E402
from agentic_kit_quality import sample as qsample  # noqa: E402
from agentic_kit_system.mapmodel import MAP_PATH  # noqa: E402

SPEC = selftest.SPEC
BASE = f"specs/{SPEC}"
FIXTURES = qsample.fixtures()


@pytest.fixture()
def sample(tmp_path):
    selftest.build_sample(tmp_path)
    return tmp_path


def run(root, cid, **options):
    return core.run_check(cid, selftest.context(root, **options))


def edit(root, rel, old, new):
    p = root / rel
    text = p.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {rel}"
    p.write_text(text.replace(old, new), encoding="utf-8")


def cli(root, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(["--root", str(root), *args])
    return code, out.getvalue()


def test_every_quality_check_has_a_fixture():
    assert set(quality.QUALITY_CHECKS) == set(FIXTURES)
    assert set(quality.QUALITY_CHECKS) <= set(core.REGISTRY)


@pytest.mark.parametrize("cid", sorted(FIXTURES))
def test_check_passes_on_the_sample_and_fails_on_its_broken_variant(sample, cid):
    what, mutate, pass_opts, fail_opts = FIXTURES[cid]
    good = run(sample, cid, **pass_opts)
    assert good.ok, good.as_dict()
    mutate(sample)
    bad = run(sample, cid, **fail_opts)
    assert bad.findings and bad.not_run is None, f"{cid} did not fail when {what}"


def test_quality_packs_are_not_asked_of_a_lite_project(sample):
    edit(sample, f"{core.KIT_DIR}/kit.yml", "profile: regulated", "profile: lite")
    for cid in quality.QUALITY_CHECKS:
        r = run(sample, cid)
        assert r.ok and any("skipped" in n for n in r.notes), cid


def test_plan_writes_only_what_is_missing_and_never_overwrites(sample):
    code, out = cli(sample, "quality", "plan", "--spec", SPEC)
    assert code == 0 and "already exists" in out
    threat = sample / BASE / "threat-model.yml"
    before = (sample / BASE / "test-strategy.yml").read_text(encoding="utf-8")
    threat.unlink()
    code, out = cli(sample, "quality", "plan", "--spec", SPEC, "--write")
    assert code == 0 and "wrote" in out and threat.exists()
    assert yaml.safe_load(threat.read_text(encoding="utf-8"))["schema"] == "agentic-threats/1"
    assert (sample / BASE / "test-strategy.yml").read_text(encoding="utf-8") == before


def test_plan_asks_for_an_evaluation_when_the_spec_touches_a_prompt(sample):
    edit(sample, f"{BASE}/spec.md", "contract-demo-openapi]", "contract-demo-openapi, demo-prompt]")
    names = [rel for rel, _ in quality.skeletons(selftest.context(sample), SPEC)]
    assert f"{BASE}/ai-eval.yml" in names


def test_a_threat_tested_by_a_criterion_that_does_not_exist_fails(sample):
    edit(sample, f"{BASE}/threat-model.yml", "test: AC-900", "test: AC-404")
    assert run(sample, "CK-THREAT-MODEL").findings


def test_a_failed_scan_is_not_evidence(sample):
    edit(sample, f"{BASE}/evidence/security.yml", "tool: gitleaks, result: pass", "tool: gitleaks, result: fail")
    assert run(sample, "CK-SECURITY-EVIDENCE").findings


def test_environment_drift_is_named(sample):
    edit(sample, f"{core.KIT_DIR}/environments.yml", 'staging: "16.4", production: "16.4"', 'staging: "15.6", production: "16.4"')
    r = run(sample, "CK-ENV-PARITY")
    assert r.findings and any("15.6" in f.message or "staging" in f.message for f in r.findings)


def test_check_command_reports_all_packs(sample):
    code, out = cli(sample, "quality", "check")
    assert code == 0 and "CK-AI-PROD-PATH" in out and "0 failed" in out


def test_debt_register_lists_waivers_and_the_baseline(sample):
    code, out = cli(sample, "quality", "debt")
    assert code == 0 and "W-001" in out


def test_flag_past_its_removal_date_fails_on_that_date_only(sample):
    assert run(sample, "CK-FLAG").ok
    edit(sample, MAP_PATH, "remove_by: 2099-01-01", "remove_by: 2026-11-30")
    assert run(sample, "CK-FLAG", today="2026-11-29").ok
    assert run(sample, "CK-FLAG", today="2026-12-01").findings
