"""Tests for the change packs (slice 0.2, part 2). Run: python -m pytest tests -q

Most of these work on a copy of fixtures/multi-app committed to a throwaway git repository, so the
checks compare the working tree with a real base commit, as they do in CI.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

from agentic_kit_system import checks_change as cc  # noqa: E402
from agentic_kit_system import contracts, engines  # noqa: E402

FIXTURE = ROOT / "fixtures" / "multi-app"
SPEC = "002-order-notes"
SPEC_MD = """---
spec: 002-order-notes
tier_declared: high
owner_role: backend
principles: [P-1]
touches: [{touches}]
depends_on: {{specs: [001-money-format]}}
{extra}---
# Order notes

- **FR-001**: An order MUST carry an optional note.
"""


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   check=True, capture_output=True)


@pytest.fixture()
def shop(tmp_path):
    root = tmp_path / "shop"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return root


def ctx(root, **options):
    """The working tree compared with the last commit, as CI compares a pull request with its base."""
    src = core.Source(root)
    return core.Context(src, src.at("HEAD"), {"today": selftest.TODAY, **options})


def run(root, cid, **options):
    return core.run_check(cid, ctx(root, **options))


def msgs(result):
    return [f.message for f in result.findings]


def edit(root, rel, old, new):
    p = root / rel
    text = p.read_text()
    assert old in text, (rel, old)
    p.write_text(text.replace(old, new))


def add_spec(root, touches, extra="", plan=True):
    d = root / "specs" / SPEC
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.md").write_text(SPEC_MD.format(touches=touches, extra=extra))
    if plan:
        (d / "plan.md").write_text("# Plan\n")
    return d


def commit(root):
    """Settings in kit.yml are read from the base, so a change cannot relax them for itself. Tests commit them."""
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "settings")


def cli(root, *args):
    return main(["--root", str(root), *args])


# ── the fixture as committed ────────────────────────────────────────────────────

def test_fixture_meets_every_change_rule(shop):
    for cid in sorted(cc.RULES.values()) + ["CK-DATA-PLAN", "CK-DATA-CLASS", "CK-SHARED-STORE", "CK-SYNTH-DATA", "CK-CONTRACT-BREAK",
                                              "CK-DEPRECATION", "CK-CONSUMER-MATRIX", "CK-SBOM", "CK-ROLLOUT"]:
        r = run(shop, cid)
        assert r.ok, (cid, msgs(r), r.not_run)


# ── data stores ─────────────────────────────────────────────────────────────────

def test_touching_a_store_needs_a_plan_and_the_skeleton_names_its_writers(shop, capsys):
    d = add_spec(shop, "shop-db, shop-orders")
    assert any("has no data-change plan" in m for m in msgs(run(shop, "CK-DATA-PLAN")))
    assert cli(shop, "change", "plan", "--spec", SPEC, "--write") == 0
    plan = (d / "data-change-plan.md").read_text()
    assert "shop-billing, shop-orders" in plan and "## Backfill" in plan
    out = msgs(run(shop, "CK-DATA-PLAN"))
    assert any("section 'Backfill' is empty" in m for m in out) and any("classification must be" in m for m in out)
    assert not any("does not name" in m for m in out)  # the skeleton listed both writers from the map
    rollout = (d / "rollout.yml").read_text()
    assert "deploy: [shop-db, shop-orders]" in rollout and "rollback: [shop-orders, shop-db]" in rollout


def fill_plan(d, classification="additive", migrations="db/migrations/002_notes.sql", extra_front="", extra_body=""):
    heads = engines.engine_for("postgresql").headings
    body = "".join(f"## {h}\n{'Used by shop-orders and shop-billing.' if h == 'Readers and writers' else 'Stated.'}\n\n" for h in heads)
    (d / "data-change-plan.md").write_text(
        f"---\nstores: [shop-db]\nclassification: {classification}\nmigrations: [{migrations}]\n{extra_front}---\n# Plan\n\n{body}{extra_body}")


def test_complete_plan_passes_and_a_planned_migration_need_not_exist_yet(shop):
    d = add_spec(shop, "shop-db")
    fill_plan(d)
    assert run(shop, "CK-DATA-PLAN").ok
    r = run(shop, "CK-DATA-CLASS")
    assert r.ok and any("planned but not written yet" in n for n in r.notes)
    assert run(shop, "CK-MIGRATION-ENGINE").ok  # nothing written, so nothing to apply


def test_plan_must_name_every_reader_and_writer_in_the_map(shop):
    d = add_spec(shop, "shop-db")
    fill_plan(d)
    edit(shop, f"specs/{SPEC}/data-change-plan.md", "Used by shop-orders and shop-billing.", "Used by shop-orders.")
    assert any("does not name shop-billing" in m for m in msgs(run(shop, "CK-DATA-PLAN")))


def test_destructive_migration_declared_additive_fails_then_needs_restore_proof(shop):
    d = add_spec(shop, "shop-db")
    fill_plan(d)
    (shop / "db/migrations/002_notes.sql").write_text("ALTER TABLE orders ADD COLUMN note TEXT;\nALTER TABLE invoices DROP COLUMN amount_cents;\n")
    out = msgs(run(shop, "CK-DATA-CLASS"))
    assert any("declares additive, but this is destructive" in m for m in out)
    assert any("declares additive, but this is backward-compatible" in m for m in out)
    fill_plan(d, classification="destructive")
    out = msgs(run(shop, "CK-DATA-CLASS"))
    assert any("Expand, migrate, contract" in m for m in out) and any("Restore test" in m for m in out) and any("restore_evidence" in m for m in out)
    (d / "evidence").mkdir()
    (d / "evidence/restore.txt").write_text("restore rehearsed on a synthetic copy\n")
    fill_plan(d, classification="destructive", extra_front=f"restore_evidence: specs/{SPEC}/evidence/restore.txt\n",
              extra_body="## Expand, migrate, contract\nStop reading, then drop one release later.\n\n## Restore test\nRehearsed.\n")
    assert run(shop, "CK-DATA-CLASS").ok


def test_destructive_change_approved_without_the_data_owner_fails(shop):
    d = add_spec(shop, "shop-db")
    (d / "evidence").mkdir()
    (d / "evidence/restore.txt").write_text("ok\n")
    fill_plan(d, classification="destructive", extra_front=f"restore_evidence: specs/{SPEC}/evidence/restore.txt\n",
              extra_body="## Expand, migrate, contract\nx\n\n## Restore test\nx\n")
    dec = shop / f".specify/agentic/decisions/{SPEC}"
    dec.mkdir(parents=True)
    (dec / "G3.yml").write_text(f"schema: agentic-decision/1\nspec: {SPEC}\ngate: G3\ndecision: approve\n"
                                "approvals:\n  - {reviewer: pat, role: solutions-architect}\n")
    assert any("without the Data Owner" in m for m in msgs(run(shop, "CK-DATA-CLASS")))


def test_a_changed_migration_the_plan_does_not_list_fails(shop):
    d = add_spec(shop, "shop-db")
    fill_plan(d)
    (shop / "db/migrations/003_extra.sql").write_text("CREATE TABLE extra (id int);\n")
    assert any("003_extra.sql is a migration for shop-db that the plan does not list" in m for m in msgs(run(shop, "CK-DATA-CLASS")))


def test_written_migration_needs_a_run_on_the_production_engine_and_is_bound_to_its_content(shop):
    d = add_spec(shop, "shop-db")
    fill_plan(d, classification="backward-compatible")
    (shop / "db/migrations/002_notes.sql").write_text("ALTER TABLE orders ADD COLUMN note TEXT;\n")
    assert any("no record of applying them" in m for m in msgs(run(shop, "CK-MIGRATION-ENGINE")))
    assert cli(shop, "run", "migration", "--spec", SPEC, "--engine-version", "15.8", "--result", "pass", "--model-drift", "none") == 0
    assert any("applied on version 15.8, but shop-db runs 16" in m for m in msgs(run(shop, "CK-MIGRATION-ENGINE")))
    assert cli(shop, "run", "migration", "--spec", SPEC, "--engine-version", "16.4", "--result", "pass", "--model-drift", "none") == 0
    assert run(shop, "CK-MIGRATION-ENGINE").ok and run(shop, "CK-MIGRATION-DRIFT").ok
    (shop / "db/migrations/002_notes.sql").write_text("ALTER TABLE orders ADD COLUMN note VARCHAR(200);\n")
    assert any("changed after the recorded run" in m for m in msgs(run(shop, "CK-MIGRATION-ENGINE")))


def test_model_drift_reported_by_the_run_fails(shop):
    d = add_spec(shop, "shop-db")
    fill_plan(d, classification="backward-compatible")
    (shop / "db/migrations/002_notes.sql").write_text("ALTER TABLE orders ADD COLUMN note TEXT;\n")
    cli(shop, "run", "migration", "--spec", SPEC, "--engine-version", "16.4", "--result", "pass", "--model-drift", "Order.Note has no migration")
    assert any("the model has changes with no migration" in m for m in msgs(run(shop, "CK-MIGRATION-DRIFT")))


def test_migration_written_for_another_engine_fails_and_a_baseline_can_carry_it(shop):
    (shop / "db/migrations/000_legacy.sql").write_text("CREATE TABLE legacy (id INTEGER PRIMARY KEY AUTOINCREMENT, name NVARCHAR(50));\n")
    out = msgs(run(shop, "CK-MIGRATION-ENGINE"))
    assert any("migration-foreign-engine" in m and "SQLite AUTOINCREMENT" in m for m in out)
    w = shop / ".specify/agentic/waivers"
    w.mkdir(parents=True)
    (w / "baseline.yml").write_text(
        "schema: agentic-baseline/1\napproved_by: {reviewer: lee, review_ref: pull/1#review-1}\ngroups:\n"
        "  - {rule: migration-foreign-engine, count: 1, owner: data-owner, reason: Existing at adoption, expires: 2099-01-01}\n")
    assert run(shop, "CK-MIGRATION-ENGINE").ok


def test_store_with_no_engine_version_is_reported(shop):
    edit(shop, "system-map/map.yml", 'engine_version: "16", ', "")
    assert any("store-engine-unknown" in m for m in msgs(run(shop, "CK-MIGRATION-ENGINE")))


def test_two_writers_need_the_shared_flag_and_both_names(shop):
    edit(shop, "system-map/map.yml", "writers: [shop-orders, shop-billing]", "writers: [shop-orders]")
    assert msgs(run(shop, "CK-SHARED-STORE")) == ["shop-db does not name writer shop-billing under `writers`"]


def test_vector_store_plan_asks_for_re_embedding_and_declared_changes_are_classified(shop):
    edit(shop, "system-map/map.yml", "edges:\n",
         "  - {id: shop-vectors, type: data-store, engine: qdrant, engine_version: \"1.12\", owner: data-owner, tier: high,\n"
         "     classification: internal, origin: assumed}\nedges:\n")
    d = add_spec(shop, "shop-vectors")
    heads = engines.engine_for("qdrant").headings
    assert "Re-embedding plan" in heads and "Backfill" not in heads
    body = "".join(f"## {h}\nStated.\n\n" for h in heads)
    (d / "data-change-plan.md").write_text(
        f"---\nstores: [shop-vectors]\nclassification: backward-compatible\nchanges: [{{kind: change-embedding-model}}]\n---\n{body}")
    assert run(shop, "CK-DATA-PLAN").ok
    assert any("declares backward-compatible, but this is breaking: declared change change-embedding-model" in m
               for m in msgs(run(shop, "CK-DATA-CLASS")))


def test_unknown_engine_gets_headings_and_a_note(shop):
    edit(shop, "system-map/map.yml", "engine: postgresql", "engine: cockroachdb")
    d = add_spec(shop, "shop-db")
    fill_plan(d)
    r = run(shop, "CK-DATA-PLAN")
    assert any("no engine adapter for cockroachdb" in n for n in r.notes)


# ── engine adapters ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("sql,expected", [
    ("CREATE TABLE a (id int); CREATE INDEX i ON a (id);", "additive"),
    ("ALTER TABLE a ADD COLUMN b text;", "backward-compatible"),
    ("ALTER TABLE a ADD COLUMN b text NOT NULL DEFAULT '';", "backward-compatible"),
    ("ALTER TABLE a ADD COLUMN b numeric(10,2) NOT NULL;", "breaking"),
    ("ALTER TABLE a ALTER COLUMN b TYPE bigint;", "breaking"),
    ("ALTER TABLE a RENAME COLUMN b TO c;", "breaking"),
    ("ALTER TABLE a ADD CONSTRAINT c CHECK (b > 0) NOT VALID;", "backward-compatible"),
    ("ALTER TABLE a ADD CONSTRAINT c UNIQUE (b);", "breaking"),
    ("CREATE UNIQUE INDEX u ON a (b);", "breaking"),
    ("ALTER TABLE a DROP COLUMN b;", "destructive"),
    ("DROP TABLE a;", "destructive"),
    ("-- DROP TABLE a;\nCREATE TABLE b (id int);", "additive"),
    ("DO $$ BEGIN IF true THEN TRUNCATE a; END IF; END $$;", "destructive"),
])
def test_postgresql_classification(sql, expected):
    assert engines.worst(engines.classify_sql("m.sql", sql))[0] == expected


def test_index_without_concurrently_is_called_out():
    assert "without CONCURRENTLY" in engines.classify_sql("m.sql", "CREATE INDEX i ON a (b);")[0][1]


EF = """
public partial class M : Migration {
    protected override void Up(MigrationBuilder migrationBuilder) {
        migrationBuilder.AddColumn<string>(name: "Note", table: "Orders", type: "text", nullable: true);
        migrationBuilder.AddColumn<int>(name: "Rank", table: "Orders", type: "integer", nullable: false);
        migrationBuilder.RenameColumn(name: "Old", table: "Orders", newName: "New");
        migrationBuilder.DropColumn(name: "Legacy", table: "Orders");
        migrationBuilder.Sql("DELETE FROM \\"Orders\\" WHERE 1 = 0");
    }
    protected override void Down(MigrationBuilder migrationBuilder) {
        migrationBuilder.DropTable(name: "Everything");
    }
}
"""


def test_efcore_migrations_are_classified_from_up_only():
    found = engines.classify_efcore("M.cs", EF)
    assert [c for c, _ in found] == ["backward-compatible", "breaking", "breaking", "destructive", "destructive"]
    assert not any("Everything" in r for _, r in found)  # Down() is the rollback, not the change


def test_efcore_migration_generated_for_sqlite_is_detected():
    text = 'Id = table.Column<int>(type: "INTEGER", nullable: false).Annotation("Sqlite:Autoincrement", true)'
    assert engines.foreign_efcore("M.cs", text) == ["SQLite annotation", "SQLite column type"]
    assert engines.foreign_efcore("M.cs", 'table.Column<string>(type: "text", nullable: false)') == []


# ── synthetic data ──────────────────────────────────────────────────────────────

def test_personal_data_patterns_and_reserved_values():
    made_up_id = "-".join(["512", "40", "7731"])  # an invented value in a national-identifier format, assembled here
    assert cc.personal_patterns(f"id,{made_up_id}") == ["US social security number format"]
    assert cc.personal_patterns("ada@example.com, bob@clinic.test, 555-0142, 000-12-3456") == []
    assert cc.personal_patterns("call 212-867-5309") == ["phone number outside the reserved 555-01xx range"]
    assert cc.personal_patterns("card 4242 4242 4242 4242") == []  # a published test number
    assert cc.personal_patterns("order 20261121000042") == []


def test_seed_data_finding_never_prints_the_value(shop):
    address = "sam.lee@" + "fabrikam" + ".com"  # invented, on a vendor's fictitious domain
    (shop / "db/seed").mkdir()
    (shop / "db/seed/customers.csv").write_text(f"name,email\nSam Lee,{address}\n")
    r = run(shop, "CK-SYNTH-DATA")
    assert [f.path for f in r.findings] == ["db/seed/customers.csv:2"]
    assert address not in json.dumps(r.as_dict())


def test_a_domain_pack_can_add_patterns(shop):
    edit(shop, ".specify/agentic/kit.yml", "domain_packs: []", "domain_packs: [clinic]")
    (shop / ".specify/agentic/packs").mkdir()
    (shop / ".specify/agentic/packs/clinic.yml").write_text(
        "schema: agentic-pack/1\nid: clinic\npersonal_data_patterns:\n  medical record number: 'MRN-\\d{7}'\n")
    commit(shop)
    (shop / "tests/fixtures").mkdir(parents=True)
    (shop / "tests/fixtures/patients.json").write_text('[{"mrn": "MRN-0012345"}]\n')
    assert any("medical record number" in m for m in msgs(run(shop, "CK-SYNTH-DATA")))


# ── contracts ───────────────────────────────────────────────────────────────────

CONTRACT = "contracts/payments-openapi.yaml"


def test_removed_response_field_is_breaking_until_a_spec_declares_it(shop):
    edit(shop, CONTRACT, "                  status: {type: string}\n", "")
    out = msgs(run(shop, "CK-CONTRACT-BREAK"))
    assert "POST /charges response 201: property status removed" in out
    add_spec(shop, "contract-payments-openapi", extra="breaking: [contract-payments-openapi]\n")
    r = run(shop, "CK-CONTRACT-BREAK")
    assert r.ok and any("declared by the spec" in n for n in r.notes)


def test_new_required_request_field_is_breaking_and_a_new_optional_one_is_not(shop):
    edit(shop, CONTRACT, "currency: {type: string}", "currency: {type: string}\n                memo: {type: string}")
    assert run(shop, "CK-CONTRACT-BREAK").ok
    edit(shop, CONTRACT, "required: [amount_cents, currency]", "required: [amount_cents, currency, memo]")
    assert any("property memo is now required" in m for m in msgs(run(shop, "CK-CONTRACT-BREAK")))


def test_changed_contract_needs_a_new_version_and_a_consumer_run_against_it(shop):
    edit(shop, CONTRACT, "currency: {type: string}", "currency: {type: string}\n                memo: {type: string}")
    assert any("changed but its version is still 2.1.0" in m for m in msgs(run(shop, "CK-CONTRACT-VERSION")))
    edit(shop, CONTRACT, "version: 2.1.0", "version: 2.2.0")
    assert run(shop, "CK-CONTRACT-VERSION").ok
    add_spec(shop, "contract-payments-openapi")
    assert any("contract test of consumer shop-orders did not run" in m for m in msgs(run(shop, "CK-CONTRACT-CONSUMER")))
    assert cli(shop, "run", "contract", "--spec", SPEC, "--provider", "contract-payments-openapi", "--consumer", "shop-orders", "--result", "pass") == 0
    assert run(shop, "CK-CONTRACT-CONSUMER").ok
    edit(shop, CONTRACT, "memo: {type: string}", "memo: {type: string, maxLength: 80}")
    assert any("ran against an earlier version" in m for m in msgs(run(shop, "CK-CONTRACT-CONSUMER")))
    cli(shop, "run", "contract", "--spec", SPEC, "--provider", "contract-payments-openapi", "--consumer", "shop-orders", "--result", "fail")
    assert any("shop-orders failed" in m for m in msgs(run(shop, "CK-CONTRACT-CONSUMER")))


def test_a_comment_only_edit_is_not_a_contract_change(shop):
    edit(shop, CONTRACT, "openapi: 3.0.3", "# reviewed\nopenapi: 3.0.3")
    assert run(shop, "CK-CONTRACT-VERSION").ok and run(shop, "CK-CONTRACT-CONSUMER").ok


def test_consumer_without_a_contract_test_is_reported(shop):
    edit(shop, "system-map/map.yml", ",\n     contract_test: services/orders/test/payments.contract.test.js}", "}")
    assert any("contract-untested" in m and "shop-orders has no contract test" in m for m in msgs(run(shop, "CK-CONTRACT-CONSUMER")))


def test_deprecation_needs_a_date_and_a_migration_path(shop):
    edit(shop, CONTRACT, "    post:\n", "    post:\n      deprecated: true\n")
    out = msgs(run(shop, "CK-DEPRECATION"))
    assert any("no removal date" in m for m in out) and any("no migration path" in m for m in out)
    edit(shop, CONTRACT, "      deprecated: true\n", "      deprecated: true\n      x-sunset: 2027-03-31\n      x-migration: Use POST /v2/charges\n")
    assert run(shop, "CK-DEPRECATION").ok


def test_contract_drift_compares_with_the_copy_generated_from_code(shop):
    edit(shop, "system-map/map.yml", "drift: {mode: design-first}", "drift: {generated: build/payments.generated.yaml}")
    r = run(shop, "CK-CONTRACT-DRIFT")
    assert r.not_run and "generate it before running the checks" in r.not_run
    (shop / "build").mkdir()
    text = (shop / CONTRACT).read_text()
    (shop / "build/payments.generated.yaml").write_text(text)
    assert run(shop, "CK-CONTRACT-DRIFT").ok
    (shop / "build/payments.generated.yaml").write_text(text.replace("  /charges:", "  /refunds:\n    post: {responses: {'201': {description: ok}}}\n  /charges:"))
    assert msgs(run(shop, "CK-CONTRACT-DRIFT")) == ["contract-payments-openapi: POST /refunds exists in the code but not in the contract"]


def test_contract_that_says_nothing_about_drift_is_reported(shop):
    edit(shop, "system-map/map.yml", ", drift: {mode: design-first}", "")
    assert any("contract-drift-undeclared" in m for m in msgs(run(shop, "CK-CONTRACT-DRIFT")))


def test_a_format_with_no_adapter_is_not_run_rather_than_passed(shop):
    (shop / "contracts/orders.proto").write_text('syntax = "proto3";\nmessage Order { string id = 1; }\n')
    edit(shop, "system-map/map.yml", "edges:\n",
         "  - {id: contract-orders, type: api-contract, owner: backend, tier: high, classification: internal, origin: derived,\n"
         "     evidence: contracts/orders.proto, version: \"1\", drift: {mode: design-first}, aliases: [contract-orders]}\nedges:\n")
    git(shop, "add", "-A")
    git(shop, "commit", "-q", "-m", "proto")
    edit(shop, "contracts/orders.proto", "string id = 1;", "string id = 1; string note = 2;")
    r = run(shop, "CK-CONTRACT-BREAK")
    assert r.not_run and "no contract adapter can compare contract-orders" in r.not_run


def test_graphql_breaking_changes():
    old = 'type Query {\n  order(id: ID!): Order\n}\ntype Order { id: ID! note: String }\nenum Status { OPEN CLOSED }\n'
    new = 'type Query {\n  order(id: ID!, tenant: ID!): Order\n}\ntype Order { id: ID! }\nenum Status { OPEN }\n'
    g = contracts.GraphQL()
    assert g.breaking(old, new) == ["Query.order: new required argument tenant", "field removed: Order.note", "value removed: Status.CLOSED"]
    assert g.breaking(old, old.replace("note: String", "note: String\n  tags: [String]")) == []


# ── shared components ───────────────────────────────────────────────────────────

LIB = "packages/shared-lib"


def test_shared_library_change_needs_a_version_change_that_fits(shop):
    (shop / LIB / "src/index.js").write_text((shop / LIB / "src/index.js").read_text() + "\n// changed\n")
    assert any("changed (1 file(s)) but its version is still 1.2.0" in m for m in msgs(run(shop, "CK-SHARED-SEMVER")))
    edit(shop, f"{LIB}/package.json", '"version": "1.2.0"', '"version": "1.2.1"')
    assert any("no spec says what kind of change" in m for m in msgs(run(shop, "CK-SHARED-SEMVER")))
    edit(shop, "specs/001-money-format/spec.md", "touches: [shop-shared-lib]\n", "touches: [shop-shared-lib]\nchanges: {shop-shared-lib: feature}\n")
    assert any("a feature change needs a minor version change; 1.2.0 -> 1.2.1 is patch" in m for m in msgs(run(shop, "CK-SHARED-SEMVER")))
    edit(shop, f"{LIB}/package.json", '"version": "1.2.1"', '"version": "1.3.0"')
    assert run(shop, "CK-SHARED-SEMVER").ok
    edit(shop, "specs/001-money-format/spec.md", "changes: {shop-shared-lib: feature}\n", "breaking: [shop-shared-lib]\n")
    assert any("a breaking change needs a major version change" in m for m in msgs(run(shop, "CK-SHARED-SEMVER")))


def test_every_consumer_must_be_built_against_the_changed_library(shop):
    (shop / LIB / "src/index.js").write_text((shop / LIB / "src/index.js").read_text() + "\n// changed\n")
    out = msgs(run(shop, "CK-CONSUMER-MATRIX"))
    assert len(out) == 2 and all("did not run" in m for m in out)
    for consumer in ("shop-orders", "shop-billing"):
        cli(shop, "run", "build", "--spec", "001-money-format", "--provider", "shop-shared-lib", "--consumer", consumer, "--result", "pass")
    assert run(shop, "CK-CONSUMER-MATRIX").ok
    (shop / LIB / "src/index.js").write_text((shop / LIB / "src/index.js").read_text() + "// again\n")
    assert all("ran against an earlier version" in m for m in msgs(run(shop, "CK-CONSUMER-MATRIX")))


def test_unversioned_shared_component_is_reported(shop):
    edit(shop, "system-map/map.yml", ", version_file: packages/shared-lib/package.json", "")
    assert any("unversioned-shared" in m for m in msgs(run(shop, "CK-SHARED-SEMVER")))


def test_versions_before_one_use_the_zero_rule():
    assert contracts.required_bump("breaking", "0.4.2") == "minor" and contracts.required_bump("breaking", "1.4.2") == "major"
    assert contracts.bump("1.2.3", "1.2.3") == "none" and contracts.bump("1.2.3", "1.1.0") == "down"


# ── external dependencies ───────────────────────────────────────────────────────

def test_external_dependency_must_be_complete(shop):
    edit(shop, "system-map/map.yml", "      timeout: 3 seconds\n", "")
    edit(shop, "system-map/map.yml", "      test_double: services/orders/test/payments.double.js\n", "")
    assert any("external-dep-incomplete: payments-provider: the dependency record lacks timeout, test_double" in m
               for m in msgs(run(shop, "CK-EXTERNAL-DEP")))


def test_protected_data_needs_an_agreement_status_and_never_the_document(shop):
    edit(shop, ".specify/agentic/kit.yml", "domain_packs: []", "domain_packs: [hipaa]")
    (shop / ".specify/agentic/packs").mkdir()
    shutil.copy(ROOT / "extensions/agentic-hipaa/pack.yml", shop / ".specify/agentic/packs/hipaa.yml")
    commit(shop)
    assert run(shop, "CK-EXTERNAL-DEP").ok  # classification is internal: no agreement asked for
    edit(shop, "system-map/map.yml", "    tier: high\n    classification: internal\n", "    tier: high\n    classification: restricted\n")
    assert any("must record the status of the business associate agreement" in m for m in msgs(run(shop, "CK-EXTERNAL-DEP")))
    edit(shop, "system-map/map.yml", "    origin: assumed\n    dependency:", "    origin: assumed\n    agreement: {status: in-place, file: legal/baa.pdf}\n    dependency:")
    assert any("record the agreement's status, not the agreement" in m for m in msgs(run(shop, "CK-EXTERNAL-DEP")))
    edit(shop, "system-map/map.yml", "{status: in-place, file: legal/baa.pdf}", "{status: in-place, reviewed: 2026-10-01}")
    assert run(shop, "CK-EXTERNAL-DEP").ok


def test_a_change_cannot_weaken_a_domain_pack_it_is_checked_against(shop):
    edit(shop, ".specify/agentic/kit.yml", "domain_packs: []", "domain_packs: [hipaa]")
    (shop / ".specify/agentic/packs").mkdir()
    shutil.copy(ROOT / "extensions/agentic-hipaa/pack.yml", shop / ".specify/agentic/packs/hipaa.yml")
    edit(shop, "system-map/map.yml", "    tier: high\n    classification: internal\n", "    tier: high\n    classification: restricted\n")
    commit(shop)
    assert any("business associate agreement" in m for m in msgs(run(shop, "CK-EXTERNAL-DEP")))
    pack = shop / ".specify/agentic/packs/hipaa.yml"
    pack.write_text(pack.read_text().replace("agreement:", "retired_agreement:"))
    assert any("business associate agreement" in m for m in msgs(run(shop, "CK-EXTERNAL-DEP")))  # the base copy still applies


# ── supply chain ────────────────────────────────────────────────────────────────

def test_floating_references_fail_and_pinned_ones_pass(shop):
    wf = shop / ".github/workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("jobs:\n  build:\n    steps:\n      - uses: actions/checkout@v4\n      - uses: ./.github/actions/local\n"
                               "      - uses: actions/setup-node@1a4442cacd436585916779262731d5b162bc6ec7\n")
    (shop / "Dockerfile").write_text("FROM node:22.11.0 AS build\nFROM build AS test\nFROM gcr.io/distroless/nodejs22\n")
    edit(shop, "services/billing/package.json", '"express": "4.19.2"', '"express": "*"')
    out = msgs(run(shop, "CK-PIN"))
    assert any("actions/checkout@v4 is not pinned to a commit" in m for m in out)
    assert any("gcr.io/distroless/nodejs22 floats: no tag" in m for m in out)
    assert any("express is requested as '*'" in m for m in out)
    assert not any("setup-node" in m or "local" in m or "node:22.11.0" in m or "pin-image: build" in m for m in out)


def test_digests_are_required_under_the_regulated_profile(shop):
    assert run(shop, "CK-PIN").ok
    edit(shop, ".specify/agentic/kit.yml", "profile: standard", "profile: regulated")
    assert run(shop, "CK-PIN").ok  # an uncommitted edit to kit.yml changes nothing: settings come from the base
    commit(shop)
    assert any("postgres:16.4 has a tag but no digest" in m for m in msgs(run(shop, "CK-PIN")))


def test_images_an_aspire_application_host_starts_are_read_from_its_code(shop):
    host = shop / "apphost"
    host.mkdir()
    (host / "Program.cs").write_text(
        'var builder = DistributedApplication.CreateBuilder(args);\n'
        'builder.AddContainer("sql", "mcr.example.test/mssql/server", "2022-latest")\n    .WithEndpoint(port: 1433, targetPort: 1433);\n'
        'builder.AddContainer("bus", "example.test/bus-emulator", "latest");\n'
        'builder.AddContainer("cache", "example.test/cache");\n'
        'builder.AddContainer("queue", "example.test/queue", "3.13.7")\n    .WithImageSHA256("' + "a" * 64 + '");\n'
        'builder.AddContainer("search", "example.test/search", "latest")\n    .WithImageTag("8.15.1");\n'
        'var image = "example.test/built-at-run-time"; builder.AddContainer("other", image, tag);\n')
    found = run(shop, "CK-PIN").findings
    out = msgs(run(shop, "CK-PIN"))
    assert any("mcr.example.test/mssql/server:2022-latest floats: tag 2022-latest" in f.message and f.path == "apphost/Program.cs:2"
               for f in found), "a tag that ends in -latest moves too, and the finding names the file and the line"
    assert any("example.test/bus-emulator:latest floats: tag latest" in m for m in out)
    assert any("example.test/cache floats: no tag" in m for m in out)
    assert not any("example.test/queue" in m or "example.test/search" in m or "built-at-run-time" in m for m in out), \
        "a digest is a pin; under the standard profile a version is one; what is built from variables is not read"
    edit(shop, ".specify/agentic/kit.yml", "profile: standard", "profile: regulated")
    commit(shop)
    out = msgs(run(shop, "CK-PIN"))
    assert any("example.test/search:8.15.1 has a tag but no digest" in m for m in out) and not any("example.test/queue" in m for m in out)


def test_manifest_with_dependencies_and_no_lockfile_fails(shop):
    (shop / "package-lock.json").rename(shop / "package-lock.json.bak")
    assert any("no lockfile" in m for m in msgs(run(shop, "CK-PIN")))


def test_adoption_baseline_carries_existing_pins_and_only_lets_the_count_fall(shop, capsys):
    wf = shop / ".github/workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("jobs:\n  b:\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n")
    assert cli(shop, "suppressions", "--baseline") == 0
    assert "pin-action" in capsys.readouterr().out  # the proposed baseline includes the new rules
    w = shop / ".specify/agentic/waivers"
    w.mkdir(parents=True)
    (w / "baseline.yml").write_text(
        "schema: agentic-baseline/1\napproved_by: {reviewer: lee, review_ref: pull/1#review-1}\ngroups:\n"
        "  - {rule: pin-action, count: 2, owner: devops-sre, reason: Existing at adoption, expires: 2099-01-01}\n")
    assert run(shop, "CK-PIN").ok and run(shop, "CK-WAIVER").ok
    (wf / "release.yml").write_text("jobs:\n  r:\n    steps:\n      - uses: actions/upload-artifact@v4\n")
    assert any("1 pin-action" in m and "the baseline allows 2" in m for m in msgs(run(shop, "CK-PIN")))


SBOM = {"bomFormat": "CycloneDX", "specVersion": "1.6", "components": [
    {"name": "express", "version": "4.19.2", "licenses": [{"license": {"id": "MIT"}}]},
    {"name": "left", "version": "1.0.0", "licenses": [{"expression": "(MIT OR GPL-3.0-only)"}]}]}


def test_release_needs_a_bill_of_materials_with_allowed_licences(shop):
    dec = shop / ".specify/agentic/decisions/001-money-format"
    dec.mkdir(parents=True)
    (dec / "G7.yml").write_text("schema: agentic-decision/1\nspec: 001-money-format\ngate: G7\ndecision: approve\n")
    assert any("released with no bill of materials" in m for m in msgs(run(shop, "CK-SBOM")))
    rel = shop / "specs/001-money-format/release"
    rel.mkdir()
    (rel / "sbom.cdx.json").write_text(json.dumps(SBOM))
    assert any("states no licence policy" in m for m in msgs(run(shop, "CK-SBOM")))
    k = shop / ".specify/agentic/kit.yml"
    k.write_text(k.read_text() + "supply_chain: {licences: {deny: [GPL-3.0-only]}}\n")
    commit(shop)
    assert msgs(run(shop, "CK-SBOM")) == ["left@1.0.0 is licensed GPL-3.0-only, which the licence policy does not allow"]
    doc = dict(SBOM, components=[SBOM["components"][0], {"name": "mystery", "version": "0.1.0"}])
    (rel / "sbom.cdx.json").write_text(json.dumps(doc))
    assert any("state no licence" in m for m in msgs(run(shop, "CK-SBOM")))


# ── release order ───────────────────────────────────────────────────────────────

def test_rollout_order_must_follow_the_map(shop):
    d = add_spec(shop, "shop-db, shop-orders, shop-billing")
    assert any("states no deploy and rollback order" in m for m in msgs(run(shop, "CK-ROLLOUT")))
    (d / "rollout.yml").write_text("schema: agentic-rollout/1\ndeploy: [shop-orders, shop-db]\nrollback: [shop-db, shop-orders]\n")
    out = msgs(run(shop, "CK-ROLLOUT"))
    assert "shop-orders is deployed before shop-db, which it depends on" in out
    assert "shop-db is rolled back before shop-orders, which depends on it" in out
    assert "the deploy order does not include shop-billing" in out
    assert any("compatibility window" in m for m in out) and any("flags" in m for m in out)
    (d / "rollout.yml").write_text(
        "schema: agentic-rollout/1\ndeploy: [{node: shop-db, phase: expand}, shop-orders, shop-billing, {node: shop-db, phase: contract}]\n"
        "rollback: [shop-billing, shop-orders, shop-db]\nflags: [order-notes]\ncompatibility_window: One release\n")
    assert run(shop, "CK-ROLLOUT").ok


def test_one_deployable_node_needs_no_rollout(shop):
    add_spec(shop, "shop-orders, shop-shared-lib")
    assert run(shop, "CK-ROLLOUT").ok


# ── wiring ──────────────────────────────────────────────────────────────────────

def test_real_diff_drives_touch_and_change_checks_together(shop):
    """An undeclared edit to the shared library is caught from the git diff alone."""
    add_spec(shop, "shop-orders", plan=False)
    (shop / LIB / "src/index.js").write_text((shop / LIB / "src/index.js").read_text() + "\n// sneaked in\n")
    r = run(shop, "CK-TOUCH")
    assert any("packages/shared-lib/src/index.js belongs to shop-shared-lib, which no spec in this change declares" in m for m in msgs(r))


def test_plan_evidence_is_bound_at_g3(shop):
    from agentic_kit.__main__ import DEFAULT_EVIDENCE
    assert {"data-change-plan.md", "rollout.yml"} <= set(DEFAULT_EVIDENCE["G3"])


def test_change_checks_do_not_run_in_lite(shop):
    edit(shop, ".specify/agentic/kit.yml", "profile: standard", "profile: lite")
    commit(shop)
    edit(shop, "docker-compose.yml", "postgres:16.4", "postgres:latest")
    for cid in ("CK-PIN", "CK-DATA-PLAN", "CK-ROLLOUT"):
        r = run(shop, cid)
        assert r.ok and any("not required by the lite profile" in n for n in r.notes)
    assert run(shop, "CK-WAIVER").ok  # and the new rules do not leak into the core waiver check


def test_contract_diff_command(shop, capsys):
    edit(shop, CONTRACT, "                  status: {type: string}\n", "")
    assert cli(shop, "contract", "diff", "--node", "contract-payments-openapi", "--base-ref", "HEAD") == 1
    assert "property status removed" in capsys.readouterr().out


def test_classify_command(shop, capsys):
    (shop / "db/migrations/002.sql").write_text("ALTER TABLE orders DROP COLUMN total_cents;\n")
    assert cli(shop, "change", "classify", "--engine", "postgresql", "--file", "db/migrations/002.sql") == 0
    assert "overall: destructive" in capsys.readouterr().out
