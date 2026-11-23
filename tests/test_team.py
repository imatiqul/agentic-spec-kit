"""Tests for the agent team (slice 0.3). Run: python -m pytest tests -q

They work on a copy of fixtures/multi-app with the team installed, in a throwaway git repository.
No model is involved anywhere in this file: where an agent would act, the test calls the kit as the agent would.
"""
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import adapters, core, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

from agentic_kit_team import agents as ag  # noqa: E402
from agentic_kit_team import golden, work  # noqa: E402

FIXTURE = ROOT / "fixtures" / "multi-app"
SPEC = "030-team"
IMPL, VERIFIER = "backend-implementer", "independent-verifier"
TASKS = """# Tasks
- [ ] T001 Extend the library in `packages/shared-lib/src/index.js` @backend-implementer
- [ ] T002 [P] Use it in `services/orders/src/index.js` @backend-implementer
- [ ] T003 [P] Use it in `services/billing/src/index.js` @backend-implementer
- [x] T004 Already finished before the team started in `README.md`
- [ ] T005 Write the migration `db/migrations/002_a.sql` @data-agent
"""


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture()
def proj(tmp_path):
    """The fixture with the team installed and one spec with a task list, committed."""
    root = tmp_path / "shop"
    golden.prepare(FIXTURE, root)
    d = root / "specs" / SPEC
    d.mkdir(parents=True)
    (d / "spec.md").write_text(f"---\nspec: {SPEC}\ntier_declared: high\nowner_role: backend\nprinciples: [P-1]\n"
                               "touches: [shop-shared-lib, shop-orders, shop-billing, shop-db]\n---\n# Team\n- **FR-001**: it works\n")
    (d / "tasks.md").write_text(TASKS)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "spec and tasks")
    return root


def ctx(root, **options):
    return work.context(root, today=selftest.TODAY, **options)


def run(root, cid, base=None, **options):
    src = core.Source(root)
    return core.run_check(cid, core.Context(src, src.at(base) if base else src, {"today": selftest.TODAY, **options}))


def msgs(r):
    return [f.message for f in r.findings]


def cli(root, *args):
    return main(["--root", str(root), *args])


def evidence(root, name="e.txt"):
    p = root / "specs" / SPEC / "evidence" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ran\n")
    return f"specs/{SPEC}/evidence/{name}"


def do(root, item, text="\n// changed\n", agent=IMPL):
    """Claim an item in the primary checkout, change its first path, and hand it off."""
    c = ctx(root)
    it = work.claim(c, SPEC, item, agent)
    path = root / it["paths"][0]
    path.write_text((path.read_text() if path.exists() else "") + text)
    return work.handoff(ctx(root), SPEC, item, agent, "changed it", [evidence(root, f"{item}.txt")])


# ── work items from the task list ───────────────────────────────────────────────

def test_task_list_becomes_work_items_with_paths_owners_and_dependencies(proj):
    made = {i["id"]: i for i in work.create_from_tasks(ctx(proj), SPEC)}
    assert sorted(made) == ["T001", "T002", "T003", "T005"]  # the finished task is not turned into work
    assert made["T001"]["paths"] == ["packages/shared-lib/src/index.js"] and made["T001"]["depends_on"] == []
    assert made["T002"]["depends_on"] == ["T001"] and made["T003"]["depends_on"] == ["T001"]  # [P]: beside each other, after T001
    assert made["T005"]["owner_agent"] == "data-agent" and made["T005"]["depends_on"] == ["T001", "T002", "T003"]  # through the finished T004
    assert work.create_from_tasks(ctx(proj), SPEC) == []  # running it again creates nothing
    assert run(proj, "CK-WORKITEM").ok


def test_only_independent_items_are_offered_together(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    assert [[i["id"] for i in g] for g in work.ready(ctx(proj), SPEC)] == [["T001"]]
    do(proj, "T001")
    assert work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=True) == "done"
    assert [[i["id"] for i in g] for g in work.ready(ctx(proj), SPEC)] == [["T002", "T003"]]


def test_an_item_cannot_start_before_what_it_depends_on(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    with pytest.raises(core.KitError, match="depends on T001"):
        work.claim(ctx(proj), SPEC, "T002", IMPL)


def test_an_item_belongs_to_its_owner_and_needs_paths(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    with pytest.raises(core.KitError, match="assigned to backend-implementer"):
        work.claim(ctx(proj), SPEC, "T001", "frontend-implementer")
    item = work.read_item(ctx(proj), SPEC, "T001")
    item["paths"] = []
    work.write_item(ctx(proj), item)
    with pytest.raises(core.KitError, match="declares no paths"):
        work.claim(ctx(proj), SPEC, "T001", IMPL)


# ── path locks ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a,b,expected", [
    ("src/a.py", "src/a.py", True), ("src/a.py", "src/b.py", False), ("src/*", "src/a.py", True), ("src/*", "lib/*", False),
    ("src/api/*", "src/*", True), ("src/*.py", "src/*.js", False), ("db/migrations/*", "db/migrations/002.sql", True),
])
def test_path_patterns_that_could_name_the_same_file(a, b, expected):
    assert work.globs_overlap(a, b, []) is expected


def _item(root, tid, paths, state="ready", owner=IMPL):
    work.write_item(ctx(root), {"schema": "agentic-work/1", "id": tid, "spec": SPEC, "title": tid, "state": state, "owner_agent": owner,
                                "paths": paths, "depends_on": [], "rework_rounds": 0,
                                "history": [{"state": "ready", "by": "orchestrator", "at": "2026-11-21T00:00:00Z"}]})


def test_two_agents_cannot_hold_the_same_file(proj):
    _item(proj, "T010", ["services/orders/src/index.js"])
    _item(proj, "T011", ["services/orders/src/*"])
    work.claim(ctx(proj), SPEC, "T010", IMPL)
    with pytest.raises(core.KitError, match="cannot start while 030-team/T010 is in-progress"):
        work.claim(ctx(proj), SPEC, "T011", IMPL)
    assert run(proj, "CK-PATH-LOCK").ok


def test_a_migration_folder_and_a_shared_component_allow_one_writer_at_a_time(proj):
    _item(proj, "T020", ["db/migrations/002_a.sql"], owner="data-agent")
    _item(proj, "T021", ["db/migrations/003_b.sql"], owner="data-agent")
    _item(proj, "T022", ["packages/shared-lib/src/index.js"])
    _item(proj, "T023", ["packages/shared-lib/package.json"])
    work.claim(ctx(proj), SPEC, "T020", "data-agent")
    with pytest.raises(core.KitError, match="both write shop-db, which allows one writer at a time"):
        work.claim(ctx(proj), SPEC, "T021", "data-agent")
    work.claim(ctx(proj), SPEC, "T022", IMPL)
    with pytest.raises(core.KitError, match="both write shop-shared-lib"):
        work.claim(ctx(proj), SPEC, "T023", IMPL)
    assert [[i["id"] for i in g] for g in work.ready(ctx(proj), SPEC)] == []  # the two waiting items are not offered while the lock is held


def test_two_services_may_be_edited_at_the_same_time(proj):
    _item(proj, "T030", ["services/orders/src/index.js"])
    _item(proj, "T031", ["services/billing/src/index.js"])
    work.claim(ctx(proj), SPEC, "T030", IMPL)
    work.claim(ctx(proj), SPEC, "T031", IMPL)
    assert run(proj, "CK-PATH-LOCK").ok


def test_a_lock_written_around_the_kit_is_caught_by_the_check(proj):
    _item(proj, "T040", ["services/orders/src/index.js"], state="in-progress")
    _item(proj, "T041", ["services/orders/src/index.js"], state="in-progress")
    assert any("both claim services/orders/src/index.js" in m for m in msgs(run(proj, "CK-PATH-LOCK")))


# ── handoff and the paths an agent may change ───────────────────────────────────

def test_handoff_is_refused_when_files_outside_the_item_changed(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    (proj / "packages/shared-lib/src/index.js").write_text("// lib\n")
    (proj / f"specs/{SPEC}/spec.md").write_text((proj / f"specs/{SPEC}/spec.md").read_text() + "\n- **FR-002**: sneaked in\n")
    with pytest.raises(core.KitError, match=f"changed files outside its declared paths: specs/{SPEC}/spec.md"):
        work.handoff(ctx(proj), SPEC, "T001", IMPL, "done", [evidence(proj)])
    git(proj, "checkout", "--", f"specs/{SPEC}/spec.md")
    item = work.handoff(ctx(proj), SPEC, "T001", IMPL, "done", [evidence(proj)])
    assert item["state"] == "in-review" and "packages/shared-lib/src/index.js" in item["handoff"]["files"]


def test_handoff_needs_a_statement_and_evidence_that_exists(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    with pytest.raises(core.KitError, match="names evidence files that exist"):
        work.handoff(ctx(proj), SPEC, "T001", IMPL, "done", [f"specs/{SPEC}/evidence/nothing.txt"])
    with pytest.raises(core.KitError, match="says what was done"):
        work.handoff(ctx(proj), SPEC, "T001", IMPL, " ", [evidence(proj)])


def test_changes_that_were_already_there_at_claim_are_not_blamed_on_the_item(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    (proj / "README.md").write_text("edited by a person before the agent started\n")
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    (proj / "packages/shared-lib/src/index.js").write_text("// lib\n")
    assert work.handoff(ctx(proj), SPEC, "T001", IMPL, "done", [evidence(proj)])["handoff"]["files"] == [
        "packages/shared-lib/src/index.js", f"specs/{SPEC}/evidence/e.txt"]


def test_rework_in_a_shared_working_copy_is_not_blamed_for_what_others_did_meanwhile(proj):
    """AGT-10: when an item comes back for rework, what other items and the reviewers wrote since its first claim is not its work."""
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=False, finding="handle the empty case")
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "T001, first round")
    # meanwhile: a reviewer writes a report, and someone edits a file that belongs to nobody's item
    report = proj / "specs" / SPEC / "reviews" / "round-1.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("findings\n")
    (proj / "docs.md").write_text("notes\n")

    item = work.claim(ctx(proj), SPEC, "T001", IMPL)  # taking the rework up: what is there now is the starting point
    assert item["state"] == "rework" and "docs.md" in item["dirty_at_claim"]
    path = proj / item["paths"][0]
    path.write_text(path.read_text() + "\n// the empty case\n")
    handed = work.handoff(ctx(proj), SPEC, "T001", IMPL, "handled the empty case", [evidence(proj, "T001-rework.txt")])
    assert sorted(handed["handoff"]["files"]) == sorted([item["paths"][0], f"specs/{SPEC}/evidence/T001-rework.txt"])

    # a change outside the item made after the rework was taken up is still refused
    work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=False, finding="once more")
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    (proj / "services" / "billing" / "src" / "index.js").write_text("// not mine\n")
    with pytest.raises(core.KitError, match="outside its declared paths"):
        work.handoff(ctx(proj), SPEC, "T001", IMPL, "again", [evidence(proj, "T001-rework.txt")])


def test_isolated_working_copy_commit_with_trailers_and_integration(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    base = git(proj, "rev-parse", "HEAD")
    assert cli(proj, "work", "claim", "--spec", SPEC, "--item", "T001", "--agent", IMPL, "--worktree") == 0
    item = work.read_item(ctx(proj), SPEC, "T001")
    wt = work.workdir(ctx(proj), item)
    assert wt != proj and (wt / "packages/shared-lib/src/index.js").is_file() and item["branch"] == f"work/{SPEC}/T001"
    (wt / "packages/shared-lib/src/index.js").write_text("// changed in the working copy\n")
    (wt / f"specs/{SPEC}/evidence").mkdir(parents=True)
    (wt / f"specs/{SPEC}/evidence/T001.txt").write_text("ran\n")
    assert "changed in the working copy" not in (proj / "packages/shared-lib/src/index.js").read_text()  # isolated until integrated
    work.handoff(ctx(proj), SPEC, "T001", IMPL, "extended the library", [f"specs/{SPEC}/evidence/T001.txt"])
    assert f"Work-Item: {SPEC}/T001" in git(wt, "log", "-1", "--format=%B") and "Agent: backend-implementer" in git(wt, "log", "-1", "--format=%B")
    assert work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=True) == "done"
    assert "merged" in work.integrate(ctx(proj), SPEC, "T001")
    assert "changed in the working copy" in (proj / "packages/shared-lib/src/index.js").read_text()
    for cid in ("CK-WORKITEM", "CK-PATH-DIFF", "CK-AUTHOR-NEQ-VERIFIER"):
        r = run(proj, cid, base)
        assert r.ok, (cid, msgs(r), r.not_run)


def test_work_is_never_integrated_into_the_default_branch(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    item = work.claim(ctx(proj), SPEC, "T001", IMPL, worktree=True)
    wt = work.workdir(ctx(proj), item)
    (wt / "packages/shared-lib/src/index.js").write_text("// x\n")
    (wt / f"specs/{SPEC}/evidence").mkdir(parents=True)
    (wt / f"specs/{SPEC}/evidence/T001.txt").write_text("ran\n")
    work.handoff(ctx(proj), SPEC, "T001", IMPL, "done", [f"specs/{SPEC}/evidence/T001.txt"])
    work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=True)
    git(proj, "stash", "-u", "-q")
    git(proj, "checkout", "-q", "-B", "main")
    git(proj, "stash", "pop", "-q")
    with pytest.raises(core.KitError, match="never into the default branch"):
        work.integrate(ctx(proj), SPEC, "T001")


def test_a_commit_that_names_a_work_item_but_changes_other_files_is_caught(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "work items")
    base = git(proj, "rev-parse", "HEAD")
    (proj / "services/billing/src/index.js").write_text("// not this item's file\n")
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", f"T001: quick fix\n\nWork-Item: {SPEC}/T001\nAgent: backend-implementer")
    out = msgs(run(proj, "CK-PATH-DIFF", base))
    assert any(f"for {SPEC}/T001 changed services/billing/src/index.js, outside the item's paths" in m for m in out)


def test_a_change_outside_every_work_item_is_caught(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    ok = run(proj, "CK-PATH-DIFF", changed_files=["services/orders/src/index.js", f"specs/{SPEC}/plan.md"])
    assert ok.ok
    r = run(proj, "CK-PATH-DIFF", changed_files=["services/orders/src/index.js", "docker-compose.yml"])
    assert msgs(r) == ["docker-compose.yml changed, and no work item of a spec in flight declares it"]


def test_a_change_cannot_widen_its_own_agents_limits(proj):
    """Agent specs are read from the base, as kit.yml and roles.yml are."""
    work.create_from_tasks(ctx(proj), SPEC)
    item = work.read_item(ctx(proj), SPEC, "T001")
    item.update(state="in-review", handoff={"done": "x", "evidence": [f"specs/{SPEC}/spec.md"], "files": [f"specs/{SPEC}/spec.md"]})
    item["history"] += [{"state": "in-progress", "by": IMPL, "at": "t"}, {"state": "in-review", "by": IMPL, "at": "t"}]
    work.write_item(ctx(proj), item)
    spec_file = proj / ag.AGENTS_DIR / "backend-implementer.yml"
    spec_file.write_text(spec_file.read_text().replace("- specs/*/evidence/*", "- specs/*"))
    assert any("changed specs/030-team/spec.md, outside its paths" in m for m in msgs(run(proj, "CK-PATH-DIFF", "HEAD")))


# ── work ahead of its gates ─────────────────────────────────────────────────────

def shown(root, base=None, gate="G4", **options):
    """What CK-GATE-RECORD found of the spec's work in this tree: the words in brackets of its finding for `gate`."""
    found = [m for m in msgs(run(root, "CK-GATE-RECORD", base, **options)) if f"but gate {gate} has no approving decision record" in m]
    assert len(found) <= 1, found
    return found[0].split("decision record (", 1)[1].rsplit(")", 1)[0] if found else ""


def unticked(root):
    """The fixture's task list has one task ticked. Without it only what the team records shows work."""
    (root / "specs" / SPEC / "tasks.md").write_text(TASKS.replace("- [x] T004", "- [ ] T004"))


def test_a_work_item_that_was_handed_off_or_is_done_shows_that_implementation_has_started(proj):
    assert shown(proj) == "tasks ticked off in tasks.md: T004", "the core reads the task list"
    unticked(proj)
    work.create_from_tasks(ctx(proj), SPEC)
    assert shown(proj) == "", "items that wait show nothing"
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    assert shown(proj) == "", "an item an agent has only taken shows nothing yet"
    work.handoff(ctx(proj), SPEC, "T001", IMPL, "changed it", [evidence(proj, "T001.txt")])
    assert shown(proj) == "work items handed off: T001"
    assert work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=True) == "done"
    do(proj, "T002")
    assert shown(proj) == "work items done: T001; work items handed off: T002"
    assert work.review(ctx(proj), SPEC, "T002", VERIFIER, accept=False, finding="not yet") == "rework"
    assert shown(proj) == "work items done: T001; work items handed off: T002", "an item sent back was still handed off once"


def test_work_on_the_default_branch_is_asked_for_its_implementation_and_verification_gates_and_on_a_feature_branch_is_not(proj):
    unticked(proj)
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=True)
    for gate in ("G5", "G6"):
        assert shown(proj, gate=gate, branch="main") == "work items done: T001", "the finding says what was found on the branch"
        assert shown(proj, gate=gate, branch="spec/030-team") == "", "work in progress"
    on_main = [m for m in msgs(run(proj, "CK-GATE-RECORD", branch="main")) if m.startswith("the implementation is on the default branch (main) but gate ")]
    assert len(on_main) == 2


def test_an_item_in_its_own_working_copy_shows_nothing_here_until_it_is_integrated(proj):
    unticked(proj)
    work.create_from_tasks(ctx(proj), SPEC)
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "work items")
    base = git(proj, "rev-parse", "HEAD")
    item = work.claim(ctx(proj), SPEC, "T001", IMPL, worktree=True)
    wt = work.workdir(ctx(proj), item)
    (wt / "packages/shared-lib/src/index.js").write_text("// changed in the working copy\n")
    (wt / f"specs/{SPEC}/evidence").mkdir(parents=True)
    (wt / f"specs/{SPEC}/evidence/T001.txt").write_text("ran\n")
    work.handoff(ctx(proj), SPEC, "T001", IMPL, "extended the library", [f"specs/{SPEC}/evidence/T001.txt"])
    work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=True)
    assert shown(proj, base) == "", "the item is done, but its files are in another working copy"
    work.integrate(ctx(proj), SPEC, "T001")
    assert shown(proj, base) == f"work items done: T001; 1 commit(s) since {base[:10]} name its work items"


def test_a_commit_that_names_a_work_item_shows_work_even_where_no_work_record_says_so(proj):
    unticked(proj)
    work.create_from_tasks(ctx(proj), SPEC)
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "work items")
    base = git(proj, "rev-parse", "HEAD")
    for n in (1, 2):
        (proj / "packages/shared-lib/src/index.js").write_text(f"// round {n}\n")
        git(proj, "add", "-A")
        git(proj, "commit", "-q", "-m", f"T001: round {n}\n\nWork-Item: {SPEC}/T001\nAgent: backend-implementer")
    (proj / "README.md").write_text("# shop\n")
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "a commit that names no work item")
    assert shown(proj, base) == f"2 commit(s) since {base[:10]} name its work items", "the items still say ready"
    assert shown(proj, "HEAD~1") == "" and shown(proj) == "", "nothing in the range that is checked, and no range"
    assert shown(proj, commits=[{"commit": "abc1234", "item": f"{SPEC}/T002", "files": []}]) == "1 commit(s) in the range checked name its work items"


def test_commits_are_not_read_from_a_repository_the_project_is_only_a_folder_of(tmp_path):
    """Asked in such a folder, git lists the commits of the repository around it."""
    project = tmp_path / "examples" / "project"
    selftest.build_sample(project)
    (project / f"{core.KIT_DIR}/work/{selftest.SPEC}/T001.yml").unlink()
    tasks = project / f"specs/{selftest.SPEC}/tasks.md"
    tasks.write_text(tasks.read_text().replace("- [x] T001", "- [ ] T001"))
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "a kit project in a folder of another repository")
    (tmp_path / "notes.md").write_text("x\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", f"the other repository's commit\n\nWork-Item: {selftest.SPEC}/T001")
    from agentic_kit_team import checks_team
    src = core.Source(project)
    nested = core.Context(src, src.at("HEAD~1"), {"today": selftest.TODAY})
    assert checks_team._named(nested) == [] and checks_team.implementation(nested) == {}
    top = core.Source(tmp_path)
    assert checks_team._named(core.Context(top, top.at("HEAD~1"), {})) == [f"{selftest.SPEC}/T001"], "the same commit, read where the root is the repository"


# ── review, rework and escalation ───────────────────────────────────────────────

def test_installing_the_team_keeps_the_rest_of_the_settings_file_as_it_was(tmp_path):
    root = tmp_path / "p"
    (root / core.KIT_DIR).mkdir(parents=True)
    settings = root / core.KIT_DIR / "kit.yml"
    before = ("schema: agentic-kit/1\nprofile: standard      # lite | standard | regulated\n"
              "gates:\n  require_evidence_hash: true   # a comment someone wrote\n")
    settings.write_text(before)
    (root / core.KIT_DIR / "roles.yml").write_text("schema: agentic-roles/1\nroles: []\n")

    assert cli(root, "team", "init", "--runtimes", "sequential") == 0
    after = settings.read_text()
    assert after.startswith(before), "nothing above the new block changed, comments included"
    assert yaml.safe_load(after)["team"] == {"runtimes": ["sequential"], "mode": "sequential", "budget": {"steps": 200, "minutes": 240}}

    settings.write_text(after + "\nmetrics: []   # after the team block\n")
    assert cli(root, "team", "init", "--runtimes", "sequential", "--mode", "parallel") == 0
    again = settings.read_text()
    assert yaml.safe_load(again)["team"]["mode"] == "parallel"
    assert again.startswith(before) and again.endswith("\nmetrics: []   # after the team block\n"), "only the team block was replaced"
    assert again.count("team:") == 1

    unchanged = settings.read_text()
    assert cli(root, "team", "init") == 0 and settings.read_text() == unchanged, "with nothing to change, the file is not written"


def test_a_verifier_may_be_given_what_its_spec_changes_and_nothing_of_the_authors(proj):
    """QLT-1: the artifact is the files the spec's tasks name and the files of the components it says it touches."""
    folder = proj / "specs" / SPEC / "verification"
    folder.mkdir()
    with (proj / "specs" / SPEC / "tasks.md").open("a") as tasks:
        tasks.write("- [x] T006 Written before the team started: `docs/guide/setup.md`\n")

    def given(*inputs):
        (folder / "G6-inputs.yml").write_text(yaml.safe_dump({"verifier": VERIFIER, "author": IMPL, "inputs": list(inputs)}))
        return msgs(run(proj, "CK-VERIFY-INPUTS"))

    assert given(f"specs/{SPEC}/spec.md", "system-map/map.yml",
                 "services/orders/src/index.js",      # named by a task
                 "db/migrations/002_a.sql",           # named by a task, not written yet
                 "docs/guide/setup.md",               # named by a task that was already finished
                 "services/orders/package.json",      # not named by a task; part of a component the spec touches
                 ) == []
    assert given("contracts/payments-openapi.yaml") == ["contracts/payments-openapi.yaml is not an allowed verifier input"], \
        "a component the spec does not say it touches"
    assert given("docs/guide/other.md") == ["docs/guide/other.md is not an allowed verifier input"], "no task names it and no component owns it"
    assert given(f"specs/{SPEC}/notes/author.md") == [f"specs/{SPEC}/notes/author.md is not an allowed verifier input"]
    assert given(f".specify/agentic/work/{SPEC}/T001.yml") == [f".specify/agentic/work/{SPEC}/T001.yml is not an allowed verifier input"]

    spec = proj / "specs" / SPEC / "spec.md"
    spec.write_text(spec.read_text().replace("touches:", "depends_on: {nodes: [contract-payments-openapi]}\ntouches:", 1))
    assert given("contracts/payments-openapi.yaml") == [], "a verifier may read what the spec says it depends on"


def test_the_author_cannot_review_and_only_a_reviewing_agent_can(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    with pytest.raises(core.KitError, match="authored 030-team/T001 and cannot review it"):
        work.review(ctx(proj), SPEC, "T001", IMPL, accept=True)
    with pytest.raises(core.KitError, match="frontend-implementer is not a reviewing agent"):
        work.review(ctx(proj), SPEC, "T001", "frontend-implementer", accept=True)
    with pytest.raises(core.KitError, match="needs a finding"):
        work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=False)


def test_a_review_that_names_nobody_or_somebody_unknown_is_refused_and_nothing_is_recorded(proj):
    """Found on the reference project: given no --by, the kit wrote "a person with no name" as the one who accepted a work item."""
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    log = proj / ".specify/agentic/audit" / f"{SPEC}.jsonl"
    before = log.read_text(encoding="utf-8")
    assert cli(proj, "work", "review", "--spec", SPEC, "--item", "T001", "--accept") != 0, "no --by"
    assert cli(proj, "work", "review", "--spec", SPEC, "--item", "T001", "--return", "no tenant filter") != 0, "no --by"
    with pytest.raises(core.KitError, match="a review must name who made it"):
        work.review(ctx(proj), SPEC, "T001", "  ", accept=True)
    with pytest.raises(core.KitError, match="independant-verifier is neither an agent of the team nor a person in the roles file"):
        work.review(ctx(proj), SPEC, "T001", "independant-verifier", accept=True)
    item = work.read_item(ctx(proj), SPEC, "T001")
    assert item["state"] == "in-review" and not item.get("reviewer_agent") and not item.get("findings")
    assert log.read_text(encoding="utf-8") == before, "a refused review leaves no line in the audit log"
    # A person the roles file names may review a work item, and is recorded as that person.
    assert work.review(ctx(proj), SPEC, "T001", "sam", accept=True) == "done"
    last = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert last["action"] == "work.done" and last["actor"] == {"type": "human", "id": "sam"}
    with pytest.raises(core.KitError, match="the record must name who moved it"):
        work.transition(ctx(proj), work.read_item(ctx(proj), SPEC, "T002"), "in-progress", "")
    # A record written before the kit refused: the check cannot show that the author did not review it, and says so.
    assert run(proj, "CK-AUTHOR-NEQ-VERIFIER").ok
    path = proj / ".specify/agentic/work" / SPEC / "T001.yml"
    old = yaml.safe_load(path.read_text(encoding="utf-8"))
    old["reviewer_agent"] = ""
    old["history"][-1]["by"] = ""
    path.write_text(yaml.safe_dump(old, sort_keys=False), encoding="utf-8")
    assert msgs(run(proj, "CK-AUTHOR-NEQ-VERIFIER")) == [f"{SPEC}/T001 was moved to done by a reviewer the record does not name"]


def test_a_third_rework_round_does_not_happen_the_disagreement_is_escalated(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    for n in (1, 2):
        assert work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=False, finding=f"still wrong, round {n}") == "rework"
        work.handoff(ctx(proj), SPEC, "T001", IMPL, f"fixed it, attempt {n}", [evidence(proj, "T001.txt")])
    assert cli(proj, "work", "review", "--spec", SPEC, "--item", "T001", "--by", VERIFIER, "--return", "it still does not meet AC-001") == 4
    item = work.read_item(ctx(proj), SPEC, "T001")
    assert item["state"] == "blocked" and item["rework_rounds"] == 2
    esc = yaml.safe_load((proj / work.escalation_path(SPEC, "T001")).read_text())
    assert esc["accountable_role"] == "backend" and esc["author"]["position"] == "fixed it, attempt 2"
    assert esc["reviewer"]["position"] == "it still does not meet AC-001" and len(esc["rounds"]) == 3
    assert run(proj, "CK-REWORK-LIMIT").ok and run(proj, "CK-WORKITEM").ok
    # work cannot resume until a person decides
    with pytest.raises(core.KitError, match="a person in roles.yml must record a decision"):
        work.claim(ctx(proj), SPEC, "T001", IMPL)
    esc.update(status="resolved", resolution={"decided_by": "kit-agent", "decision": "accept"})
    (proj / work.escalation_path(SPEC, "T001")).write_text(yaml.safe_dump(esc))
    assert any("who is not a person in roles.yml" in m for m in msgs(run(proj, "CK-REWORK-LIMIT")))
    esc["resolution"] = {"decided_by": "sam", "decision": "the reviewer is right; fix the rounding", "review_ref": "pull/1#review-9"}
    (proj / work.escalation_path(SPEC, "T001")).write_text(yaml.safe_dump(esc))
    assert work.claim(ctx(proj), SPEC, "T001", IMPL)["state"] == "in-progress"
    assert run(proj, "CK-REWORK-LIMIT").ok


def test_moving_on_from_an_escalation_without_a_person_fails(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    for n in (1, 2):
        work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=False, finding="no")
        work.handoff(ctx(proj), SPEC, "T001", IMPL, "again", [evidence(proj, "T001.txt")])
    work.review(ctx(proj), SPEC, "T001", VERIFIER, accept=False, finding="no")
    item = work.read_item(ctx(proj), SPEC, "T001")
    item["state"] = "done"
    item["history"].append({"state": "done", "by": VERIFIER, "at": "t"})
    work.write_item(ctx(proj), item)
    assert any("moved on from its escalation without a decision by a person" in m for m in msgs(run(proj, "CK-REWORK-LIMIT")))


def test_illegal_transitions_are_refused_by_the_kit_and_caught_by_the_check(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    item = work.read_item(ctx(proj), SPEC, "T001")
    with pytest.raises(core.KitError, match="cannot go from ready to done"):
        work.transition(ctx(proj), item, "done", VERIFIER)
    item = work.read_item(ctx(proj), SPEC, "T001")
    item["state"] = "done"
    item["history"].append({"state": "done", "by": VERIFIER, "at": "t"})
    work.write_item(ctx(proj), item)
    out = msgs(run(proj, "CK-WORKITEM"))
    assert any("went from ready straight to done" in m for m in out) and any("handed off with no evidence" in m for m in out)


# ── budgets and the run log ─────────────────────────────────────────────────────

def test_a_run_stops_with_a_report_when_its_step_budget_is_spent(proj, capsys):
    work.create_from_tasks(ctx(proj), SPEC)
    assert cli(proj, "orchestrate", "start", "--spec", SPEC, "--steps", "2", "--minutes", "30") == 0
    assert cli(proj, "orchestrate", "step", "--spec", SPEC, "--run", "r1", "--agent", "orchestrator", "--do", "dispatch") == 0
    assert cli(proj, "orchestrate", "step", "--spec", SPEC, "--run", "r1", "--agent", IMPL, "--do", "implement") == 0
    assert cli(proj, "orchestrate", "step", "--spec", SPEC, "--run", "r1", "--agent", IMPL, "--do", "implement") == 3
    run_doc = work.read_run(ctx(proj), SPEC, "r1")
    assert run_doc["state"] == "stopped" and run_doc["stop_reason"] == "budget-steps"
    report = (proj / run_doc["report"]).read_text()
    assert "T001 (ready, backend-implementer)" in report and "Steps: 3 of 2" in report
    assert cli(proj, "orchestrate", "step", "--spec", SPEC, "--run", "r1", "--do", "more") == 1  # a stopped run takes no more steps
    assert run(proj, "CK-BUDGET").ok


def test_a_run_stops_when_its_time_budget_is_spent(proj):
    r = work.run_start(ctx(proj, now="2026-11-21T10:00:00Z"), SPEC, "sequential", {"steps": 100, "minutes": 30})
    assert work.run_step(ctx(proj, now="2026-11-21T10:20:00Z"), SPEC, r["id"], IMPL, "implement")[1] == ""
    assert work.run_step(ctx(proj, now="2026-11-21T10:45:00Z"), SPEC, r["id"], IMPL, "implement")[1] == "budget-minutes"


def test_a_run_needs_a_budget(proj):
    with pytest.raises(core.KitError, match="needs a budget"):
        work.run_start(ctx(proj), SPEC, "sequential", {"steps": 0, "minutes": 0})


def test_agent_steps_are_logged_with_who_on_whose_behalf_inputs_and_outputs(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    r = work.run_start(ctx(proj), SPEC, "sequential")
    work.run_step(ctx(proj), SPEC, r["id"], IMPL, "implement", inputs=[f"specs/{SPEC}/tasks.md"], outputs=["packages/shared-lib/src/index.js"])
    do(proj, "T001")
    rows = [json.loads(x) for x in (proj / f".specify/agentic/audit/{SPEC}.jsonl").read_text().splitlines()]
    step = next(x for x in rows if x["action"] == "agent.implement")
    assert step["actor"] == {"type": "agent", "id": IMPL, "on_behalf_of": "backend"}
    assert step["inputs"] == [f"specs/{SPEC}/tasks.md"] and step["outputs"] == ["packages/shared-lib/src/index.js"]
    assert [x["action"] for x in rows if x["action"].startswith("work.")][-2:] == ["work.in-progress", "work.in-review"]
    assert run(proj, "CK-AUDIT-CHAIN").ok


# ── the path guard ──────────────────────────────────────────────────────────────

def guard(root, tool, path, **extra):
    return work.guard(root, {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": str(root), **extra})


def test_guard_blocks_writes_outside_the_work_in_progress(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    assert guard(proj, "Write", f"specs/{SPEC}/spec.md") == (True, "")  # nothing is in progress: the guard stays out of the way
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    assert guard(proj, "Edit", "packages/shared-lib/src/index.js")[0]
    assert guard(proj, "Write", f"specs/{SPEC}/evidence/out.txt")[0]
    allowed, why = guard(proj, "Edit", f"specs/{SPEC}/spec.md")
    assert not allowed and "outside the declared paths of the work in progress" in why
    assert not guard(proj, "Write", str(proj.parent / "elsewhere.txt"))[0]
    assert guard(proj, "Read", f"specs/{SPEC}/spec.md")[0] and guard(proj, "Bash", "x")[0]  # reads and shell commands are not judged


def test_guard_protects_what_only_the_kit_or_a_person_writes(proj):
    for path in (".specify/agentic/roles.yml", ".specify/agentic/kit.yml", f".specify/agentic/decisions/{SPEC}/G1.yml",
                 f".specify/agentic/audit/{SPEC}.jsonl", ".specify/agentic/agents/orchestrator.yml", f".specify/agentic/work/{SPEC}/T001.yml",
                 ".github/CODEOWNERS"):
        allowed, why = guard(proj, "Write", path)
        assert not allowed and "never by an agent's file tools" in why, path


def test_guard_holds_a_named_agent_to_its_own_write_paths(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    assert guard(proj, "Edit", "packages/shared-lib/src/index.js", agent_type=IMPL)[0]
    assert not guard(proj, "Edit", "packages/shared-lib/src/index.js", agent_type=VERIFIER)[0]  # a verifier never edits what it verifies
    assert guard(proj, "Write", f"specs/{SPEC}/verification/report.md", agent_type=VERIFIER)[0]
    assert not guard(proj, "Write", f"specs/{SPEC}/plan.md", agent_type="spec-author")[0]
    assert not guard(proj, "Write", "services/orders/src/index.js", agent_type=IMPL)[0]  # an implementer, but not its item


def test_guard_in_an_isolated_working_copy_follows_that_copys_item(proj):
    work.create_from_tasks(ctx(proj), SPEC)
    item = work.claim(ctx(proj), SPEC, "T001", IMPL, worktree=True)
    wt = work.workdir(ctx(proj), item)
    assert guard(wt, "Edit", "packages/shared-lib/src/index.js")[0]
    assert not guard(wt, "Edit", "services/orders/src/index.js")[0]
    assert not guard(wt, "Write", ".specify/agentic/roles.yml")[0]


def test_guard_command_reads_the_event_from_stdin_and_exits_2_to_block(proj, monkeypatch, capsys):
    work.create_from_tasks(ctx(proj), SPEC)
    work.claim(ctx(proj), SPEC, "T001", IMPL)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_name": "Write", "tool_input": {"file_path": "README.md"}, "cwd": str(proj)})))
    assert cli(proj, "guard") == 2
    assert "agentic path guard: README.md is outside the declared paths" in capsys.readouterr().err
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert cli(proj, "guard") == 0


# ── agent specs and the runtime files ───────────────────────────────────────────

def test_every_shipped_agent_spec_is_valid_and_the_roster_is_complete():
    roles = set(selftest.ROLE_IDS)
    ids = []
    for f in sorted(ag.SHIPPED.glob("*.yml")):
        spec = yaml.safe_load(f.read_text())
        assert ag.validate(spec, f"x/{f.name}", roles) == [], f.name
        ids.append(spec["id"])
    assert len(ids) == 16 and ag.minimum_team_missing(ids) == []
    lite = [yaml.safe_load(f.read_text())["id"] for f in ag.SHIPPED.glob("*.yml") if "lite" in yaml.safe_load(f.read_text())["profiles"]]
    assert sorted(lite) == ["ai-implementer", "backend-implementer", "frontend-implementer", "independent-verifier", "orchestrator", "spec-author"]


def test_runtime_files_are_rendered_from_the_spec(proj):
    c = ctx(proj)
    specs = ag.load(c)
    claude = ag.render(specs, "claude", {})
    text = claude[".claude/agents/independent-verifier.md"]
    front = yaml.safe_load(text.split("---")[1])
    assert front == {"name": "independent-verifier", "description": specs["independent-verifier"]["charter"] + " Supports the qa role.",
                     "tools": "Read, Grep, Glob, Bash", "model": "opus"}  # no Edit or Write: it cannot change what it verifies
    assert "Edit the artifact it verifies" in text and "Approve, merge, publish or deploy" in text and "Do not edit this file" in text
    assert yaml.safe_load(claude[".claude/agents/backend-implementer.md"].split("---")[1])["tools"] == "Read, Grep, Glob, Edit, Write, Bash"
    assert "Agent" in yaml.safe_load(claude[".claude/agents/orchestrator.md"].split("---")[1])["tools"]
    copilot = yaml.safe_load(ag.render(specs, "copilot", {})[".github/agents/backend-implementer.agent.md"].split("---")[1])
    assert copilot["tools"] == ["read", "search", "edit", "execute"] and "model" not in copilot
    assert ag.render(specs, "copilot", {"models": {"copilot": {"standard": "some-model"}}})[".github/agents/backend-implementer.agent.md"].count("model: some-model") == 1
    seq = ag.render(specs, "sequential", {})[f"{ag.AGENTS_DIR}/rendered/sequential.md"]
    assert seq.count("<!-- role: ") == 16 and "Start a new session for the Independent Verifier" in seq
    assert ag.render(specs, "claude", {}) == claude  # rendering is deterministic


def test_lite_profile_lets_the_spec_author_draft_the_plan(tmp_path):
    root = tmp_path / "lite"
    golden.prepare(FIXTURE, root, "lite")
    specs = ag.load(ctx(root))
    assert len(specs) == 6 and "specs/*/plan.md" in specs["spec-author"]["write_paths"]
    assert run(root, "CK-AGENT-SPEC").ok


def edit_spec(root, agent, old, new):
    p = root / ag.AGENTS_DIR / f"{agent}.yml"
    text = p.read_text()
    assert old in text, (agent, old)
    p.write_text(text.replace(old, new))


def test_agent_spec_rules(proj):
    assert run(proj, "CK-AGENT-SPEC").ok
    edit_spec(proj, "independent-verifier", "- search\n", "- search\n- edit\n")
    assert any("a reviewing agent must not hold the edit tool" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))
    git(proj, "checkout", "--", ".")
    edit_spec(proj, "orchestrator", "write_paths: []", "write_paths:\n- specs/*")
    assert any("the Orchestrator must not be able to edit artifacts" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))
    git(proj, "checkout", "--", ".")
    p = proj / ag.AGENTS_DIR / "scribe.yml"
    doc = yaml.safe_load(p.read_text())
    doc["never"] = []
    p.write_text(yaml.safe_dump(doc))
    assert any("the `never` list is empty" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))
    git(proj, "checkout", "--", ".")
    (proj / ag.AGENTS_DIR / "independent-verifier.yml").rename(proj / "verifier.bak")
    assert any("the minimum team is incomplete: independent-verifier is missing" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))


def test_changing_a_spec_without_rendering_and_stray_generated_files_fail(proj):
    edit_spec(proj, "scribe", "Summarise a disagreement away", "Paper over a disagreement")
    assert any("differs from a fresh render" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))
    assert cli(proj, "team", "render") == 0 and run(proj, "CK-AGENT-SPEC").ok
    k = proj / ".specify/agentic/kit.yml"
    k.write_text(k.read_text().replace("- sequential", "- sequential\n  - claude"))
    assert any("has not been rendered" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))
    assert cli(proj, "team", "render") == 0 and run(proj, "CK-AGENT-SPEC").ok
    (proj / ".claude/agents/extra.md").write_text((proj / ".claude/agents/scribe.md").read_text().replace("name: scribe", "name: extra"))
    assert any("a generated agent file has no agent spec behind it" in m for m in msgs(run(proj, "CK-AGENT-SPEC")))


def test_team_brief_tells_each_agent_what_is_waiting(proj, capsys):
    work.create_from_tasks(ctx(proj), SPEC)
    do(proj, "T001")
    assert cli(proj, "team", "brief", "--agent", VERIFIER, "--spec", SPEC) == 0
    out = capsys.readouterr().out
    assert "## Waiting for your review" in out and f"{SPEC}/T001 (in-review)" in out and "handed off by backend-implementer: changed it" in out
    assert cli(proj, "team", "brief", "--agent", "orchestrator", "--spec", SPEC) == 0
    assert "## Ready to dispatch" in capsys.readouterr().out
    assert cli(proj, "team", "brief", "--agent", "nobody", "--spec", SPEC) == 1


# ── credentials ─────────────────────────────────────────────────────────────────

def cred(root, **change):
    p = root / ".specify/agentic/_adapter/reviews.json"
    data = json.loads(p.read_text())
    for k, v in change.items():
        if k == "setup":
            data["setup"] = v
        else:
            data["agent_credential"][k] = v
    p.write_text(json.dumps(data))


def test_agent_credential_rules(proj):
    assert run(proj, "CK-CRED").ok
    cred(proj, permissions={"admin": False, "maintain": True, "push": True})
    assert any("has maintain permission" in m for m in msgs(run(proj, "CK-CRED")))
    cred(proj, permissions={"push": True}, setup=[{"item": "pull request reviews required", "status": "fail"}])
    assert any("can change the default branch alone" in m for m in msgs(run(proj, "CK-CRED")))
    cred(proj, setup=[{"item": "pull request reviews required", "status": "pass"}], scopes=["repo", "workflow", "write:packages"])
    out = msgs(run(proj, "CK-CRED"))
    assert any("holds the workflow scope" in m for m in out) and any("holds the write:packages scope" in m for m in out)
    cred(proj, scopes=[], identity="sam")
    assert any("sam is listed in roles.yml as a person" in m for m in msgs(run(proj, "CK-CRED")))


def test_credential_check_is_not_run_when_nothing_describes_the_credential(proj):
    p = proj / ".specify/agentic/_adapter/reviews.json"
    data = json.loads(p.read_text())
    del data["agent_credential"]
    p.write_text(json.dumps(data))
    assert run(proj, "CK-CRED").not_run


def test_github_adapter_reads_the_tokens_permissions_from_recorded_responses():
    recorded = {"user": {"login": "kit-agent", "type": "User"}, "repos/acme/shop": {"permissions": {"admin": True, "push": True, "pull": True}},
                "__token_scopes__": ["repo", "workflow"]}
    gh = adapters.GitHubAdapter("acme/shop", runner=lambda path: recorded[path])
    assert gh.agent_credential() == {"identity": "kit-agent", "account_type": "User", "permissions": {"admin": True, "push": True, "pull": True},
                                     "scopes": ["repo", "workflow"]}


# ── golden tasks ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def results():
    return golden.run(FIXTURE, ["parallel", "sequential"])


def test_golden_tasks_complete_in_both_modes_stopping_at_every_gate(results):
    assert golden.failures(results) == []
    for r in results["runs"]:
        by_id = {t["id"]: t for t in r["tasks"]}
        assert by_id["shared-lib-field"]["stopped_at"] == ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
        assert by_id["minimum-team"]["stopped_at"] == ["G1", "G3", "G5"] and "only the minimum team was installed" in by_id["minimum-team"]["observed"]
        assert sorted(by_id["shared-db-column"]["observed"]) == sorted(golden.TASKS["shared-db-column"]["expect"])
        assert all(t["completed"] and not t["failing_checks"] for t in r["tasks"])


def test_every_seeded_defect_is_returned_by_the_reviewing_side(results):
    for r in results["runs"]:
        caught = {d["id"]: d for d in r["defects"]}
        assert caught["undeclared-table-touch"]["via"] == "CK-TOUCH" and "belongs to shop-db" in caught["undeclared-table-touch"]["finding"]
        assert caught["breaking-described-additive"]["via"] == "CK-CONTRACT-BREAK"
        assert "scripted review rule" in caught["missing-tenant-filter"]["via"]  # a stand-in: a model has to make this judgement for real
        assert all(d["caught"] and d["caught_by"] == VERIFIER and d["caught_by"] != d["author"] for d in r["defects"])


def test_parallel_mode_really_uses_isolated_working_copies(tmp_path):
    t = golden.run_task(FIXTURE, "shared-lib-field", "parallel", golden.Scripted(), tmp_path)
    assert t["completed"] and t["work_items"] == 3
    root = tmp_path / "shared-lib-field-parallel"
    log = git(root, "log", "--format=%s")
    assert log.count("Integrate 010-shared-lib-field/") == 3  # one merge per work item's branch
    assert "Work-Item: 010-shared-lib-field/T002" in git(root, "log", "--format=%B")
    assert git(root, "worktree", "list").count("\n") == 0  # every working copy was removed after integration


def test_sequential_mode_uses_one_checkout_and_no_merges(tmp_path):
    t = golden.run_task(FIXTURE, "contract-change", "sequential", golden.Scripted(), tmp_path)
    root = tmp_path / "contract-change-sequential"
    assert t["completed"] and git(root, "log", "--merges", "--format=%s") == ""
    assert "Work-Item: 012-contract-change/T001" in git(root, "log", "--format=%B")


def test_an_external_agent_command_can_do_the_work_and_the_review(tmp_path):
    """The seam a real coding agent plugs into, exercised with a small script in place of a model."""
    agent = tmp_path / "agent.py"
    launcher = ROOT / "extensions" / "agentic" / "scripts" / "agentic.py"
    agent.write_text(f"""import os, subprocess, sys
from pathlib import Path
kit = [sys.executable, {str(launcher)!r}, "--root", os.environ["AGENTIC_ROOT"], "work"]
spec, item, where = os.environ["AGENTIC_SPEC"], os.environ["AGENTIC_ITEM"], Path(os.environ["AGENTIC_WORKDIR"])
if os.environ["AGENTIC_STEP"] == "implement":
    (where / "services/orders/src/index.js").open("a").write("\\n// done by the stand-in agent\\n")
    ev = where / "specs" / spec / "evidence" / "agent.txt"
    ev.parent.mkdir(parents=True, exist_ok=True); ev.write_text("ran\\n")
    sys.exit(subprocess.run(kit + ["handoff", "--spec", spec, "--item", item, "--agent", os.environ["AGENTIC_AGENT"], "--done", "implemented",
                                   "--evidence", f"specs/{{spec}}/evidence/agent.txt"]).returncode)
sys.exit(subprocess.run(kit + ["review", "--spec", spec, "--item", item, "--by", "independent-verifier", "--return", "no tenant filter"]).returncode)
""")
    d = golden.run_defect(FIXTURE, "missing-tenant-filter", "sequential", golden.Command(f"{sys.executable} {agent}"), tmp_path)
    assert d["caught"] and d["caught_by"] == VERIFIER and d["via"] == "the reviewing agent" and d["finding"] == "no tenant filter"


def test_golden_results_must_match_the_agent_specs_and_cover_both_modes(proj, results):
    assert run(proj, "CK-GOLDEN").ok  # no results here, and none required
    k = proj / ".specify/agentic/kit.yml"
    k.write_text(k.read_text().replace("team:\n", "team:\n  golden: {required: true}\n"))
    assert any("requires golden-task results and there are none" in m for m in msgs(run(proj, "CK-GOLDEN")))
    out = proj / golden.RESULTS
    out.parent.mkdir(parents=True)
    doc = dict(results, agents_hash=ag.specs_hash(ctx(proj)))
    out.write_text(yaml.safe_dump(doc))
    r = run(proj, "CK-GOLDEN")
    assert r.ok and any("scripted stand-in, not from a model" in n for n in r.notes)
    out.write_text(yaml.safe_dump(dict(doc, runs=doc["runs"][:1])))
    assert msgs(run(proj, "CK-GOLDEN")) == ["there are no results for sequential mode"]
    out.write_text(yaml.safe_dump(dict(doc, agents_hash="sha256:0")))
    assert any("different agent specs" in m for m in msgs(run(proj, "CK-GOLDEN")))


def test_golden_command_exits_non_zero_when_a_defect_slips_through(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(golden.Scripted, "review", lambda self, *a, **k: ("", ""))  # a reviewer that accepts everything
    monkeypatch.setattr(golden, "TASKS", {})
    assert cli(tmp_path, "golden", "run", "--fixture", str(FIXTURE), "--mode", "sequential") == 1
    assert "seeded defect undeclared-table-touch was not caught" in capsys.readouterr().out


# ── wiring ──────────────────────────────────────────────────────────────────────

def test_doctor_reports_the_agent_credential():
    from agentic_kit.__main__ import DOCTOR_CHECKS
    assert "CK-CRED" in DOCTOR_CHECKS


def test_workflows_name_every_gate_and_only_installed_commands():
    for name in ("agentic-sdd-team", "agentic-sdd-sequential"):
        doc = yaml.safe_load((ROOT / "workflows" / name / "workflow.yml").read_text())
        gates = [s["gate"] for s in doc["steps"] if s.get("type") == "agentic-gate"]
        assert gates == ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
        ids = [s["id"] for s in doc["steps"]]
        assert len(ids) == len(set(ids))
        commands = {s["command"] for s in doc["steps"] if "command" in s}
        assert commands <= {"speckit.agentic-team.orchestrate", "speckit.agentic-team.role", "speckit.agentic.check"}
    seq = yaml.safe_load((ROOT / "workflows" / "agentic-sdd-sequential" / "workflow.yml").read_text())
    reviews = [s["id"] for s in seq["steps"] if s["id"].endswith("independent-verifier") and "implement" in s["id"] or s["id"].startswith("rework")
               and s["id"].endswith("independent-verifier")]
    assert len(reviews) == 3  # the first review and at most two rework rounds, never a third
