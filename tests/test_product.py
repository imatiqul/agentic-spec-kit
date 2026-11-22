"""Unit tests for the product extension (slice 0.5). Run: python -m pytest tests/test_product.py -q"""
import io
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

import agentic_kit_product as product  # noqa: E402
from agentic_kit_product import common, dedupe, intake, lineage, lint, living, text  # noqa: E402
from agentic_kit_product import sample as psample  # noqa: E402

SPEC = selftest.SPEC
BASE = f"specs/{SPEC}"
KIT = f"{core.KIT_DIR}/kit.yml"
PRODUCT = f"{core.KIT_DIR}/product"
ALICE = {"reviewer": "alice", "role": "product-owner"}


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


def write(root, rel, body):
    selftest._write(root, rel, body)


def kit(root, **changes):
    data = yaml.safe_load((root / KIT).read_text(encoding="utf-8"))
    data.update(changes)
    (root / KIT).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def cli(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--root", str(root), *args])
    return code, out.getvalue() + err.getvalue()


def draft(root, sid="002-export", title="Export invoices", requirement="System MUST export a user's invoices as a CSV file.",
          criterion="Given a user with invoices, When the user asks for an export, Then a CSV file with one row per invoice is returned.",
          front="", delta=True):
    write(root, f"specs/{sid}/spec.md", f"---\nspec: {sid}\ntier_declared: low\nowner_role: backend\n{front}---\n# Feature Specification: {title}\n\n"
          f"## Requirements\n- **FR-001**: {requirement}\n\n## Acceptance Criteria\n- **AC-001** (verifies FR-001): {criterion}\n")
    if delta:
        write(root, f"specs/{sid}/deltas/invoicing.md", "---\ncapability: invoicing\ntitle: Invoicing\nowner_role: product-owner\n"
              "purpose: Let users see and take away what they were billed.\n---\n## ADDED Requirements\n\n### Requirement: Export invoices\n"
              "Verifies: FR-001\nThe system SHALL export a user's invoices as a CSV file.\n\n#### Scenario: Export\n- GIVEN a user with invoices\n"
              "- WHEN the user asks for an export\n- THEN a CSV file is returned\n")
    return sid


def test_every_product_check_is_registered_with_a_fixture():
    assert set(product.PRODUCT_CHECKS) == set(psample.fixtures())
    assert set(product.PRODUCT_CHECKS) <= set(core.REGISTRY)


def test_the_sample_passes_every_product_check(sample):
    for cid in product.PRODUCT_CHECKS:
        r = run(sample, cid)
        assert r.ok, r.as_dict()


# ── comparing text ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a,b,alike", [
    ("System MUST greet the user by name.", "Greet each user by their name when they sign in", True),
    ("Members MUST be able to reset a forgotten password by email", "Send a password reset link by email when a member forgets the password", True),
    ("System MUST greet the user by name.", "Export invoices as CSV for the finance team", False),
    ("Lock an account after five failed sign-in attempts", "Show the account balance on the dashboard", False),
])
def test_requirements_that_share_vocabulary_score_high(a, b, alike):
    fa, fb = text.features(a), text.features(b)
    score, shared = text.cosine(fa, fb, text.idf([fa, fb]))
    assert (score >= dedupe.THRESHOLD) is alike, (score, shared)


def test_the_same_input_always_gives_the_same_score():
    fa, fb = text.features("Export invoices as CSV"), text.features("Download invoices in CSV format")
    assert text.cosine(fa, fb, text.idf([fa, fb])) == text.cosine(fa, fb, text.idf([fa, fb]))


def test_an_agreed_term_makes_two_wordings_one():
    plain = text.jaccard("delete a customer", "delete a member")
    assert text.jaccard("delete a customer", "delete a member", {"customer": "member"}) > plain


@pytest.mark.parametrize("word,stemmed", [("exports", "export"), ("exported", "export"), ("exporting", "export"), ("invoices", "invoice"),
                                           ("queries", "query"), ("status", "status"), ("classes", "class")])
def test_stemmer(word, stemmed):
    assert text.stem(word) == stemmed


# ── intake records ──────────────────────────────────────────────────────────────

def test_personal_data_and_credentials_are_removed_before_a_record_is_written():
    rec = intake.make_record("jira", "HQ-7", "Fix billing for patient 123-45-6789",
                             "MRN: 0045871 was charged twice.\npassword = hunter2hunter2\nCard 4111 1111 1111 1111 was used. Order 1234 5678 9012 3456 is fine.")
    assert "123-45-6789" not in rec["title"] and "hunter2" not in rec["body"] and "0045871" not in rec["body"]
    assert "4111 1111 1111 1111" not in rec["body"]
    assert "1234 5678 9012 3456" in rec["body"], "a number that fails the card checksum is not a card number"
    assert rec["screened"] == {"card-number": 1, "credential": 1, "national-id": 1, "record-number": 1}
    assert rec["hash"] == intake.content_hash(rec["title"], rec["body"])


def test_a_record_is_refreshed_until_someone_acts_on_it_and_never_after(tmp_path):
    first = intake.make_record("ado", "42", "Export invoices", "As finance I want CSV.", revision="1", fetched="2026-11-21")
    rel, action = intake.upsert(tmp_path, first)
    assert action == "new" and intake.upsert(tmp_path, first)[1] == "unchanged"
    second = intake.make_record("ado", "42", "Export invoices", "As finance I want CSV and PDF.", revision="2", fetched="2026-11-22")
    assert intake.upsert(tmp_path, second)[1] == "updated"
    saved = yaml.safe_load((tmp_path / rel).read_text(encoding="utf-8"))
    assert "PDF" in saved["body"]
    saved["status"] = "triaged"
    intake.write_record(tmp_path, saved)
    third = intake.make_record("ado", "42", "Export invoices", "As finance I want CSV, PDF and XLSX.", revision="3", fetched="2026-11-23")
    assert intake.upsert(tmp_path, third)[1] == "source-changed"
    after = yaml.safe_load((tmp_path / rel).read_text(encoding="utf-8"))
    assert "XLSX" not in after["body"] and after["latest"] == {"hash": third["hash"], "revision": "3", "fetched": "2026-11-23"}
    assert intake.upsert(tmp_path, third)[1] == "unchanged"


def test_a_record_with_unscreened_text_fails(sample):
    rec = yaml.safe_load((sample / psample.RECORD).read_text(encoding="utf-8"))
    rec["body"] += "\nContact 123-45-6789."
    rec["hash"] = intake.content_hash(rec["title"], rec["body"])
    intake.write_record(sample, rec)
    assert "national-id" in msgs(run(sample, "CK-INTAKE-RECORD"))


@pytest.mark.parametrize("change,expect", [
    ({"reason": ""}, "no reason"),
    ({"decided_by": {"reviewer": "bob", "role": "product-owner"}}, "does not hold the role"),
    ({"decided_by": {"reviewer": "bob", "role": "qa"}}, "it takes product-owner"),
    ({"target": "jira-none-9"}, "is not a spec"),
    ({"decision": "rejected"}, "needs disposition.decision: duplicate-of"),
])
def test_closing_a_requirement_takes_a_reason_a_target_and_a_product_owner(sample, change, expect):
    rel = f"{core.KIT_DIR}/intake/jira-demo-2.yml"
    rec = yaml.safe_load((sample / rel).read_text(encoding="utf-8"))
    rec["disposition"].update(change)
    intake.write_record(sample, rec)
    assert expect in msgs(run(sample, "CK-INTAKE-RECORD"))


def test_a_specified_record_must_be_listed_in_the_specs_origin(sample):
    edit(sample, f"{BASE}/origin.yml", "- jira-demo-1", "- jira-demo-9")
    assert "does not list this record" in msgs(run(sample, "CK-INTAKE-RECORD"))


def test_a_source_change_is_settled_by_a_product_owners_decision(sample):
    latest = "sha256:" + "ab" * 32
    rec = yaml.safe_load((sample / psample.RECORD).read_text(encoding="utf-8"))
    rec["latest"] = {"hash": latest, "revision": "7"}
    intake.write_record(sample, rec)
    assert run(sample, "CK-INTAKE-DRIFT").findings
    rec["acknowledged"] = {"hash": latest, "action": "ignore", "reason": "Only a typo was fixed", "decided_by": {"reviewer": "bob", "role": "qa"}}
    intake.write_record(sample, rec)
    assert "it takes product-owner" in msgs(run(sample, "CK-INTAKE-DRIFT"))
    rec["acknowledged"]["decided_by"] = ALICE
    intake.write_record(sample, rec)
    assert run(sample, "CK-INTAKE-DRIFT").ok


# ── requirement quality ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("requirement,criterion,expect", [
    ("System should export invoices.", None, "does not say MUST or SHALL"),
    ("System MUST export invoices and MUST email them.", None, "2 obligations"),
    ("System MUST export invoices quickly.", None, "'quickly' with no number"),
    ("System MUST export invoices [NEEDS CLARIFICATION: which format?].", None, "NEEDS CLARIFICATION"),
    (None, "The export works.", "needs a When and a Then"),
    (None, "Given invoices, When exported, Then the file opens easily.", "'easily' with no number"),
])
def test_wording_an_agent_could_misread_fails(sample, requirement, criterion, expect):
    kwargs = {k: v for k, v in (("requirement", requirement), ("criterion", criterion)) if v}
    draft(sample, **kwargs)
    assert expect in msgs(run(sample, "CK-REQ-QUALITY"))


def test_a_clean_draft_passes_and_a_weak_word_with_a_number_is_fine(sample):
    draft(sample, requirement="System MUST return the export quickly: within 2 seconds for 1000 invoices.")
    assert run(sample, "CK-REQ-QUALITY").ok, msgs(run(sample, "CK-REQ-QUALITY"))


def test_a_requirement_with_no_criterion_fails(sample):
    sid = draft(sample)
    edit(sample, f"specs/{sid}/spec.md", "(verifies FR-001)", "(verifies FR-002)")
    out = msgs(run(sample, "CK-REQ-QUALITY"))
    assert "FR-001 has no acceptance criterion" in out and "verifies FR-002, which the spec does not have" in out


def test_ears_style_is_checked_when_the_project_chooses_it(sample):
    kit(sample, requirements={"style": "ears"})
    draft(sample, requirement="When a user asks for an export, the system shall return a CSV file.")
    assert run(sample, "CK-REQ-QUALITY").ok
    draft(sample, sid="003-other", title="Printing", requirement="Printing of receipts MUST be possible.", delta=False)
    assert "EARS" in msgs(run(sample, "CK-REQ-QUALITY"))


def test_a_project_can_allow_a_word_and_add_its_own(sample):
    draft(sample, requirement="System MUST show a simple summary.")
    assert "'simple'" in msgs(run(sample, "CK-REQ-QUALITY"))
    kit(sample, requirements={"allow_words": ["simple"], "weak_words": ["summary"]})
    out = msgs(run(sample, "CK-REQ-QUALITY"))
    assert "'simple'" not in out and "'summary'" in out


def test_approved_wording_is_left_alone_until_it_changes(sample):
    assert run(sample, "CK-REQ-QUALITY").ok
    edit(sample, f"{BASE}/spec.md", "System MUST greet the user by name.", "System should greet the user nicely and quickly.")
    assert run(sample, "CK-REQ-QUALITY").findings, "changing an approved spec re-opens its wording"


def test_size_limits_come_from_kit_yml(sample):
    draft(sample)
    assert run(sample, "CK-SPEC-SIZE").ok
    kit(sample, requirements={"limits": {"lines": 5}})
    assert "limit is 5" in msgs(run(sample, "CK-SPEC-SIZE"))


def test_glossary_rules(sample):
    draft(sample, requirement="System MUST export an end user's invoices as a CSV file. The `customer` table is unchanged.")
    out = msgs(run(sample, "CK-GLOSSARY"))
    assert "'end user'" in out and "'customer'" not in out, "a word in code quotes is a name, not prose"
    write(sample, f"{PRODUCT}/glossary.yml", "terms:\n  - {term: user, definition: A person, avoid: [member]}\n  - {term: member, definition: Also a person}\n"
          "  - {term: user, definition: Again}\n")
    out = msgs(run(sample, "CK-GLOSSARY"))
    assert "defined twice" in out and "also a term of its own" in out


# ── living specs ────────────────────────────────────────────────────────────────

def test_a_living_spec_survives_a_round_trip(sample):
    rel = living.cap_path("sign-in")
    body = (sample / rel).read_text(encoding="utf-8")
    assert living.MARK in body and "Sources: _adoption" in body
    assert living.render_capability(living.parse_capability("sign-in", body)) == body


def test_applying_a_delta():
    cap, errs = living.apply(None, living.parse_delta("d.md", psample.GREETING_DELTA), "001")
    assert not errs and list(cap.requirements) == ["greet by name"] and cap.front["nodes"] == ["demo-app"]
    change = ("---\ncapability: greeting\n---\n## MODIFIED Requirements\n### Requirement: Greet by name\nThe system SHALL greet the user by first name.\n"
              "#### Scenario: s\n- WHEN greeted\n- THEN the first name is used\n\n## ADDED Requirements\n### Requirement: Greet in the user's language\n"
              "The system SHALL greet in the user's language.\n#### Scenario: s\n- WHEN greeted\n- THEN the language matches\n\n"
              "## RENAMED Requirements\n- `Greet by name` -> `Greet by first name`\n")
    cap2, errs = living.apply(cap, living.parse_delta("d2.md", change), "002")
    assert errs and "modifies 'Greet by name'" in errs[0], "a rename is applied first, so the old name is gone"
    cap2, errs = living.apply(cap, living.parse_delta("d2.md", change.replace("### Requirement: Greet by name", "### Requirement: Greet by first name")), "002")
    assert not errs and list(cap2.requirements) == ["greet by first name", "greet in the user's language"]
    assert cap2.requirements["greet by first name"].sources == ["001", "002"] and "first name" in cap2.requirements["greet by first name"].body
    assert list(cap.requirements) == ["greet by name"], "applying a delta does not alter the capability it was applied to"
    gone, errs = living.apply(cap2, living.parse_delta("d3.md", "---\ncapability: greeting\n---\n## REMOVED Requirements\n"
                                                                "### Requirement: Greet by first name\nReason: Replaced by a title\n"), "003")
    assert not errs and list(gone.requirements) == ["greet in the user's language"]


@pytest.mark.parametrize("delta,expect", [
    ("---\ncapability: greeting\n---\n## ADDED Requirements\n### Requirement: X\nThe system SHALL x.\n#### Scenario: s\n- WHEN a\n- THEN b\n", "must give title, owner_role, purpose"),
    ("---\ncapability: sign-in\n---\n## MODIFIED Requirements\n### Requirement: Nope\nThe system SHALL x.\n#### Scenario: s\n- WHEN a\n- THEN b\n", "which sign-in does not have"),
    ("---\ncapability: sign-in\n---\n## ADDED Requirements\n### Requirement: Sign in with a password\nThe system SHALL x.\n#### Scenario: s\n- WHEN a\n- THEN b\n", "already has"),
    ("---\ncapability: sign-in\n---\n## ADDED Requirements\n### Requirement: Stay signed in\nThe system keeps the session.\n#### Scenario: s\n- WHEN a\n- THEN b\n", "does not say SHALL or MUST"),
    ("---\ncapability: sign-in\n---\n## ADDED Requirements\n### Requirement: Stay signed in\nThe system SHALL keep the session.\n", "has no scenario"),
    ("---\ncapability: sign-in\n---\n## REMOVED Requirements\n### Requirement: Sign in with a password\n", "removed with no `Reason:`"),
    ("---\ncapability: sign-in\n---\n## Notes\nhello\n", "is not one of ADDED Requirements"),
    ("---\ncapability: Sign In\n---\n## ADDED Requirements\n### Requirement: X\nThe system SHALL x.\n#### Scenario: s\n- WHEN a\n- THEN b\n", "lower-case words joined by hyphens"),
])
def test_a_delta_that_does_not_apply_or_cannot_be_tested_fails(sample, delta, expect):
    sid = draft(sample, delta=False)
    write(sample, f"specs/{sid}/deltas/x.md", delta)
    assert expect in msgs(run(sample, "CK-DELTA-VALID"))


def test_every_requirement_of_the_spec_must_reach_the_living_spec(sample):
    sid = draft(sample)
    edit(sample, f"specs/{sid}/spec.md", "## Acceptance Criteria", "- **FR-002**: System MUST email the export.\n\n## Acceptance Criteria")
    assert "FR-002 is in the spec but no delta requirement says" in msgs(run(sample, "CK-DELTA-VALID"))


def test_a_change_must_say_how_behaviour_changes_or_that_it_does_not(sample):
    sid = draft(sample, delta=False)
    assert "carries no delta" in msgs(run(sample, "CK-CAPABILITY-COVERAGE"))
    edit(sample, f"specs/{sid}/spec.md", "owner_role: backend\n", "owner_role: backend\nbehaviour: none\n")
    assert "needs `behaviour_reason:`" in msgs(run(sample, "CK-CAPABILITY-COVERAGE"))
    edit(sample, f"specs/{sid}/spec.md", "behaviour: none\n", "behaviour: none\nbehaviour_reason: Renames a module\n")
    assert run(sample, "CK-CAPABILITY-COVERAGE").ok
    draft(sample, front="behaviour: none\nbehaviour_reason: x\n")
    assert "remove one or the other" in msgs(run(sample, "CK-CAPABILITY-COVERAGE"))


def test_coverage_of_the_existing_system_grows_with_each_change(sample):
    edit(sample, f"{BASE}/spec.md", "contract-demo-openapi]", "contract-demo-openapi, demo-client]")
    assert "touches demo-client, which no capability describes" in msgs(run(sample, "CK-CAPABILITY-COVERAGE"))
    edit(sample, psample.DELTA, "nodes: [demo-app]", "nodes: [demo-app, demo-client]")
    assert run(sample, "CK-CAPABILITY-COVERAGE").ok


def test_merge_is_refused_before_release_and_writes_the_living_spec_after(sample):
    code, out = cli(sample, "product", "merge", "--spec", SPEC, "--write")
    assert code == 2 and "merged when the change is released" in out
    psample._release(sample)
    code, out = cli(sample, "product", "merge", "--spec", SPEC)
    assert code == 0 and "would write" in out and not (sample / living.cap_path("greeting")).exists()
    code, out = cli(sample, "product", "merge", "--spec", SPEC, "--write")
    assert code == 0 and "greeting: +1 added" in out
    body = (sample / living.cap_path("greeting")).read_text(encoding="utf-8")
    assert "### Requirement: Greet by name" in body and "Sources: 001-demo" in body and "Verifies:" not in body
    assert run(sample, "CK-LIVING-SPEC").ok and run(sample, "CK-DELTA-MERGED").ok
    assert cli(sample, "product", "merge", "--spec", SPEC, "--write")[0] == 2


def test_history_cannot_be_rewritten(sample):
    psample._merge(sample)
    edit(sample, psample.DELTA, "greet the user by name", "greet the user by title")
    assert "changed after it was merged" in msgs(run(sample, "CK-LIVING-SPEC"))


def test_a_spec_cannot_be_merged_by_editing_the_index(sample):
    idx = yaml.safe_load((sample / common.INDEX).read_text(encoding="utf-8"))
    idx["order"].append(SPEC)
    (sample / common.INDEX).write_text(yaml.safe_dump(idx), encoding="utf-8")
    assert "has no record" in msgs(run(sample, "CK-LIVING-SPEC"))
    write(sample, f"{living.MERGES}/{SPEC}.yml", yaml.safe_dump({"schema": living.MERGE_SCHEMA, "spec": SPEC, "merged_on": "2026-11-21",
                                                                     "deltas": {psample.DELTA: common.sha((sample / psample.DELTA).read_text(encoding="utf-8"))}}))
    out = msgs(run(sample, "CK-LIVING-SPEC"))
    assert "before it passed every gate" in out and "living spec is missing" in out


def test_an_adoption_merge_needs_a_named_product_owner(sample):
    rel = f"{living.MERGES}/{living.ADOPTION_ID}.yml"
    edit(sample, rel, "reviewer: alice", "reviewer: bob")
    assert "does not hold the role" in msgs(run(sample, "CK-LIVING-SPEC"))
    code, out = cli(sample, "product", "merge", "--adoption", "--write")
    assert code == 2 and "--approved-by" in out


def test_a_released_change_has_a_few_days_to_be_merged(sample):
    psample._release(sample)
    done = living.completed_on(ctx(sample), SPEC)
    assert done is not None
    assert run(sample, "CK-DELTA-MERGED", today=done.isoformat()).ok
    assert run(sample, "CK-DELTA-MERGED", today="2027-06-01").findings
    kit(sample, product={"merge_days": 400})
    assert run(sample, "CK-DELTA-MERGED", today="2027-06-01").ok


def test_two_changes_to_one_requirement_are_ordered(sample):
    psample.fixtures()["CK-SPEC-COLLISION"][1](sample)
    assert run(sample, "CK-SPEC-COLLISION").findings
    edit(sample, "specs/002-other/spec.md", "owner_role: backend\n", "owner_role: backend\nafter: [001-demo]\n")
    assert run(sample, "CK-SPEC-COLLISION").ok


def test_a_sealed_change_never_changes(sample):
    psample._merge(sample)
    assert run(sample, "CK-ARCHIVE").ok, "a merged change has time before it must be sealed"
    code, out = cli(sample, "product", "archive", "--spec", SPEC, "--write")
    assert code == 0 and "sealed" in out
    assert run(sample, "CK-ARCHIVE", today="2027-06-01").ok
    write(sample, f"{BASE}/release/production-checks.yml", "checks: []\n")
    assert run(sample, "CK-ARCHIVE").ok, "post-release records may still be written"
    write(sample, f"{BASE}/notes.md", "later thoughts\n")
    assert "added after the spec was sealed" in msgs(run(sample, "CK-ARCHIVE"))
    (sample / BASE / "notes.md").unlink()
    edit(sample, f"{BASE}/plan.md", "One function", "Two functions")
    assert "plan.md changed after the spec was sealed" in msgs(run(sample, "CK-ARCHIVE"))


def test_sealing_needs_a_merge_first(sample):
    code, out = cli(sample, "product", "archive", "--spec", SPEC, "--write")
    assert code == 2 and "not merged" in out


def test_a_change_cannot_exempt_itself(sample):
    def git(*args):
        subprocess.run(["git", "-C", str(sample), "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
                       check=True, capture_output=True)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-qm", "base")
    sid = draft(sample, delta=False)
    edit(sample, common.INDEX, "exempt: []", f"exempt: [{sid}]")
    src = core.Source(sample)
    own = core.Context(src, src, {"today": selftest.TODAY})
    assert core.run_check("CK-CAPABILITY-COVERAGE", own).ok, "with no base to compare against, the working tree is all there is"
    reviewed = core.Context(src, src.at("HEAD"), {"today": selftest.TODAY})
    assert "carries no delta" in msgs(core.run_check("CK-CAPABILITY-COVERAGE", reviewed))


def test_living_specs_are_optional(tmp_path):
    selftest.build_sample(tmp_path)
    import shutil
    shutil.rmtree(tmp_path / PRODUCT)
    for cid in ("CK-LIVING-SPEC", "CK-DELTA-VALID", "CK-CAPABILITY-COVERAGE", "CK-DELTA-MERGED", "CK-SPEC-COLLISION", "CK-ARCHIVE", "CK-OUTCOME"):
        r = run(tmp_path, cid)
        assert r.ok and any("not in use" in n for n in r.notes), cid


# ── duplicates ──────────────────────────────────────────────────────────────────

def test_a_likely_duplicate_blocks_the_first_gate_until_a_product_owner_decides(sample):
    sid = draft(sample, sid="002-hello", title="Hello", requirement="System MUST greet each user by their name.", delta=False)
    found = dedupe.spec_candidates(ctx(sample), sid)
    assert [c["target"] for c in found] == [SPEC] and found[0]["kind"] == "in-flight"
    assert "nobody has decided" in msgs(run(sample, "CK-DUPLICATE"))
    origin = {"schema": "agentic-origin/1", "dispositions": [{"target": SPEC, "decision": "distinct", "reason": "This one is for the mobile app",
                                                               "decided_by": {"reviewer": "bob", "role": "qa"}}]}
    write(sample, f"specs/{sid}/origin.yml", yaml.safe_dump(origin))
    assert "it takes product-owner" in msgs(run(sample, "CK-DUPLICATE"))
    origin["dispositions"][0]["decided_by"] = ALICE
    write(sample, f"specs/{sid}/origin.yml", yaml.safe_dump(origin))
    assert run(sample, "CK-DUPLICATE").ok
    origin["dispositions"][0]["decision"] = "duplicate-of"
    write(sample, f"specs/{sid}/origin.yml", yaml.safe_dump(origin))
    assert "should not go to its gate" in msgs(run(sample, "CK-DUPLICATE"))


def test_what_the_system_already_does_is_a_candidate(sample):
    sid = draft(sample, sid="002-login", title="Password sign-in", requirement="System MUST let a user sign in with an email address and a password.", delta=False)
    found = dedupe.spec_candidates(ctx(sample), sid)
    assert found and found[0]["target"] == "capability:sign-in#Sign in with a password" and found[0]["kind"] == "delivered"


def test_a_requirement_the_change_itself_modifies_is_not_a_candidate(sample):
    sid = draft(sample, sid="002-login", title="Password sign-in", requirement="System MUST let a user sign in with an email address and a password.", delta=False)
    write(sample, f"specs/{sid}/deltas/sign-in.md", "---\ncapability: sign-in\n---\n## MODIFIED Requirements\n### Requirement: Sign in with a password\n"
          "Verifies: FR-001\nThe system SHALL let a user sign in with an email address and a password of twelve characters.\n"
          "#### Scenario: s\n- WHEN the password is right\n- THEN the user is signed in\n")
    assert dedupe.spec_candidates(ctx(sample), sid) == []


def test_a_candidate_listed_by_an_agent_needs_a_decision_too(sample):
    sid = draft(sample)
    write(sample, f"specs/{sid}/origin.yml", yaml.safe_dump({"candidates": [{"target": "capability:sign-in#Sign in with a password",
                                                                              "suggested_by": "spec-author"}]}))
    r = run(sample, "CK-DUPLICATE")
    assert "listed by hand" in msgs(r) and len(r.findings) == 1


def test_the_threshold_is_the_projects_choice(sample):
    sid = draft(sample, sid="002-hello", title="Hello", requirement="System MUST greet each user by their name.", delta=False)
    kit(sample, intake={"dedupe": {"threshold": 0.95}})
    assert dedupe.spec_candidates(ctx(sample), sid) == [] and run(sample, "CK-DUPLICATE").ok


# ── outcomes ────────────────────────────────────────────────────────────────────

def test_outcomes_are_asked_of_medium_tier_and_up(sample):
    sid = draft(sample)
    assert run(sample, "CK-OUTCOME").ok, "a low-tier change need not state an outcome"
    edit(sample, f"specs/{sid}/spec.md", "tier_declared: low", "tier_declared: medium")
    assert "must say what result it expects" in msgs(run(sample, "CK-OUTCOME"))
    write(sample, f"specs/{sid}/outcomes.yml", "schema: agentic-outcomes/1\nnone_because: Removes dead code\n")
    assert run(sample, "CK-OUTCOME").ok
    write(sample, f"specs/{sid}/outcomes.yml", "schema: agentic-outcomes/1\noutcomes:\n  - {id: O-1, hypothesis: h, metric: m, baseline: 1, target: 2}\n")
    out = msgs(run(sample, "CK-OUTCOME"))
    assert "O-1 has no source" in out and "O-1 has no review_by" in out


def test_someone_looks_after_release(sample):
    edit(sample, f"{BASE}/outcomes.yml", "review_by: 2099-01-01", "review_by: 2027-01-01")
    assert run(sample, "CK-OUTCOME", today="2027-02-01").ok, "nothing is due until the change is released and merged"
    psample._merge(sample)
    assert "nobody has recorded what happened" in msgs(run(sample, "CK-OUTCOME", today="2027-02-01"))
    review = {"reviews": [{"outcome": "O-1", "result": "not-met", "measured": "41%", "evidence": "analytics report 2027-01", "reviewed_by": ALICE}]}
    write(sample, f"{BASE}/outcomes-review.yml", yaml.safe_dump(review))
    assert "`follow_up` must be the intake record" in msgs(run(sample, "CK-OUTCOME", today="2027-02-01"))
    review["reviews"][0]["follow_up"] = "accept: the effect was within noise; no further work"
    write(sample, f"{BASE}/outcomes-review.yml", yaml.safe_dump(review))
    assert run(sample, "CK-OUTCOME", today="2027-02-01").ok
    review["reviews"][0].update({"follow_up": "jira-demo-1", "result": "met"})
    write(sample, f"{BASE}/outcomes-review.yml", yaml.safe_dump(review))
    assert run(sample, "CK-OUTCOME", today="2027-02-01").ok


# ── commands and the brief ──────────────────────────────────────────────────────

def test_init_exempts_what_was_there_before(sample):
    import shutil
    shutil.rmtree(sample / PRODUCT)
    code, out = cli(sample, "product", "init")
    assert code == 0 and "would write" in out and not (sample / common.INDEX).exists()
    code, out = cli(sample, "product", "init", "--write")
    idx = yaml.safe_load((sample / common.INDEX).read_text(encoding="utf-8"))
    assert idx == {"schema": common.INDEX_SCHEMA, "exempt": [SPEC], "order": []}
    assert run(sample, "CK-CAPABILITY-COVERAGE").ok and "already exist" in cli(sample, "product", "init", "--write")[1]


def test_a_drafted_delta_is_valid_and_is_never_overwritten(sample):
    sid = draft(sample, delta=False)
    code, out = cli(sample, "product", "delta", "--spec", sid, "--capability", "invoicing", "--write")
    assert code == 0
    edit(sample, f"specs/{sid}/deltas/invoicing.md", "TBD: one sentence on what this capability is for.", "Let users take their invoices away.")
    r = run(sample, "CK-DELTA-VALID")
    assert r.ok, msgs(r)
    assert cli(sample, "product", "delta", "--spec", sid, "--capability", "invoicing", "--write")[0] == 2


def test_intake_by_hand_screens_and_shows_what_it_looks_like(sample):
    code, out = cli(sample, "intake", "add", "--title", "Greet users by their name", "--body", "token: abcdef123456 please", "--today", "2026-11-22")
    assert code == 0 and "new:" in out and "credential" in out and "looks like: 001-demo" in out
    code, out = cli(sample, "intake", "list")
    assert "Greet users by their name" in out and "manual-" in out and "specified" in out
    assert "greet" not in next(p.name for p in (sample / core.KIT_DIR / "intake").iterdir() if p.name.startswith("manual-")), "the id carries no words of the title"
    assert run(sample, "CK-INTAKE-RECORD").ok


def test_specify_links_a_record_to_a_spec(sample):
    cli(sample, "intake", "add", "--title", "Export invoices as CSV", "--key", "EXP-1")
    sid = draft(sample)
    code, out = cli(sample, "product", "specify", "--intake", "manual-exp-1", "--spec", sid, "--write")
    assert code == 0 and "linked" in out
    assert yaml.safe_load((sample / f"specs/{sid}/origin.yml").read_text(encoding="utf-8"))["intake"] == ["manual-exp-1"]
    assert run(sample, "CK-INTAKE-RECORD").ok
    assert cli(sample, "product", "specify", "--intake", "jira-demo-2", "--spec", sid, "--write")[0] == 2, "a closed record cannot be specified"


def test_duplicates_command(sample):
    code, out = cli(sample, "product", "duplicates", "--title", "Greet the user by name")
    assert code == 0 and SPEC in out and "matches shared words, not meaning" in out
    code, out = cli(sample, "product", "duplicates", "--title", "Greet the user by name", "--json")
    assert code == 0 and '"target"' in out
    code, out = cli(sample, "product", "duplicates", "--intake", "jira-demo-2")
    assert code == 0 and "0 candidate(s)" in out, "'say hello' and 'greet' share no words: the comparison cannot see they mean the same"


def test_catalog_and_report_view(sample):
    code, out = cli(sample, "product", "catalog")
    assert code == 0 and "`sign-in` Sign-in" in out and "_adoption" in out
    assert "sign-in" in core.VIEW_HOOKS["capabilities"](ctx(sample))


def test_the_brief_leads_with_the_behaviour_change_and_similar_work(sample):
    body = (sample / f"{BASE}/briefs/G1.md").read_text(encoding="utf-8")
    assert "## Behaviour change" in body and "`greeting` (new capability) adds: Greet by name" in body
    assert "## Similar work" in body
    assert len(body.splitlines()) <= 80


def test_why_follows_a_file_back_to_the_request_and_the_approvals(sample):
    out = lineage.why(ctx(sample), "src/demo/greet.py")
    assert f"## Spec {SPEC}" in out and "FR-001" in out and "capability `greeting`" in out
    assert "jira DEMO-1" in out and "G1 approved by:" in out and "alice as product-owner" in out
    assert "No spec claims this path" in lineage.why(ctx(sample), "README.md")
    code, out = cli(sample, "why", "src/demo/greet.py:1")
    assert code == 0 and "Why `src/demo/greet.py:1`" in out


def test_why_reads_the_work_item_from_the_commit(sample):
    def git(*args):
        subprocess.run(["git", "-C", str(sample), "-c", "user.name=Dev", "-c", "user.email=d@example.com", "-c", "commit.gpgsign=false", *args],
                       check=True, capture_output=True)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-qm", "Implement greet\n\nWork-Item: 001-demo/T001\nAgent: backend-implementer")
    out = lineage.why(ctx(sample), "src/demo/greet.py:2")
    assert "**Work item:** 001-demo/T001" in out and "agent backend-implementer" in out and "Task T001 carries:" in out
