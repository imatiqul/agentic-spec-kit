"""Tests for docs/design/first-gate-on-github.md (FGR-1 to FGR-15): what the first gate on GitHub showed.

No test reaches GitHub. Its answers are written by hand, in the shape the reference repository gave on 2026-11-27,
and the reviews come from the file adapter's stand-in.
Run: python -m pytest tests/test_first_gate_on_github.py -q
"""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentic_kit import adapters, core, delivery, demo, selftest  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

from agentic_kit_connect import sample as csample  # noqa: E402

import test_changeset as tcs  # noqa: E402  (the demo's project as a git repository, and its helpers)
import test_first_live_runs as tl  # noqa: E402  (GitHub's answers about the rules of a branch, written by hand)
import test_product as tp  # noqa: E402  (a spec drafted into the sample)

SPEC = selftest.SPEC
SAMPLE_CONNECT = csample.NOTIFY_FLOW


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def flat(rel):
    """The file's text with every run of white space made one space, so that a sentence may wrap; in a workflow file,
    across the lines of a comment too."""
    return " ".join(" ".join(line.strip().lstrip("#") for line in read(rel).splitlines()).split())


@pytest.fixture()
def sample(tmp_path):
    root = tmp_path / "sample"
    root.mkdir()
    selftest.build_sample(root)
    return root


def run(root, cid):
    return core.run_check(cid, selftest.context(root))


def msgs(result):
    return " | ".join(finding.message for finding in result.findings)


def demo_project(root):
    """The demo's Lite project as a git repository on `main`, its spec and brief committed: the commit, and the line for G1."""
    demo.build_project(root)
    demo._git(root, "init", "-q")
    demo._git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    assert tcs.kit(root, "brief", "--spec", tcs.SPEC, "--gate", tcs.GATE, "--write")[0] == 0
    first = demo._commit(root, "the spec and the reviewer's page")
    return first, tcs.line_of(root)


# ── FGR-1, FGR-2: where the record goes ─────────────────────────────────────────

def test_AC_001_the_documents_say_that_a_push_onto_the_reviewed_pull_request_dismisses_the_review():
    for rel in ("docs/install.md", "extensions/agentic/commands/gate.md", "docs/limits.md", "extensions/agentic-connect/ci/github-actions.yml"):
        text = flat(rel)
        assert "dismiss" in text and "after the merge, on a branch of its own" in text, rel
    for rel in ("docs/install.md", "docs/limits.md"):
        assert "first-gate-on-github.md" in read(rel) and "open question 1" in flat(rel), rel


def test_AC_002_record_says_when_a_push_onto_the_open_pull_request_would_dismiss_the_review_it_cites(tmp_path):
    record = f"{core.KIT_DIR}/decisions/{tcs.SPEC}/{tcs.GATE}.yml"
    note = f"note: {tcs.CHANGE} is open"

    said = tmp_path / "said"
    said.mkdir()
    first, line = demo_project(said)
    demo._reviews(said, [demo._review(2, demo.PERSON, first, line)])
    tcs.stand_in(said, lambda held: held.update(dismiss_stale_reviews_on_push=True))
    code, text = tcs.kit(said, "record", "--spec", tcs.SPEC, "--gate", tcs.GATE, "--change", tcs.CHANGE)
    assert code == 0 and (said / record).is_file(), text
    assert note in text and "would dismiss review 2, which it cites" in text and "after the merge, on a branch of its own" in text

    merged = tmp_path / "merged"
    merged.mkdir()
    first, line = demo_project(merged)
    demo._reviews(merged, [demo._review(2, demo.PERSON, first, line)])
    tcs.stand_in(merged, lambda held: (held.update(dismiss_stale_reviews_on_push=True),
                                       held["changes"][tcs.CHANGE].update(state="merged", merge_commit=first)))
    code, text = tcs.kit(merged, "record", "--spec", tcs.SPEC, "--gate", tcs.GATE, "--change", tcs.CHANGE)
    assert code == 0 and (merged / record).is_file() and "note:" not in text, text

    silent = tmp_path / "silent"
    silent.mkdir()
    first, line = demo_project(silent)
    demo._reviews(silent, [demo._review(2, demo.PERSON, first, line)])
    code, text = tcs.kit(silent, "record", "--spec", tcs.SPEC, "--gate", tcs.GATE, "--change", tcs.CHANGE)
    assert code == 0 and (silent / record).is_file() and note not in text, text

    # what the GitHub adapter makes of the rules of the branch
    assert tl.github({tl.RULES: [tl.REVIEW_RULE], tl.ENTRY: tl.NO_PROTECTION}).stale_approvals_dismissed() is True
    quiet = tl.rule("pull_request", required_approving_review_count=1)
    assert tl.github({tl.RULES: [quiet], tl.PROTECTION: tl.NOT_PROTECTED}).stale_approvals_dismissed() is False
    classic = {"required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": True}}
    assert tl.github({tl.RULES: [], tl.PROTECTION: classic}).stale_approvals_dismissed() is True
    assert tl.github({}).stale_approvals_dismissed() is None, "neither the rules nor the protection can be read"


# ── FGR-3, FGR-7: what GitHub does with the connect workflow ────────────────────

def test_AC_003_the_documents_say_what_github_did_with_the_connect_workflow():
    for rel in ("extensions/agentic-connect/README.md", "docs/limits.md"):
        text = flat(rel)
        for words in ("whose actor is the workflow's own bot", "cache write", "before the pull request is merged", "who may bypass a ruleset"):
            assert words in text, (rel, words)
    assert "whose actor is the workflow's own bot" in flat("extensions/agentic-connect/ci/github-actions.yml")


# ── FGR-4: the kit's own pipeline ───────────────────────────────────────────────

def test_AC_004_a_pull_requests_runs_are_grouped_by_its_number():
    flow = yaml.safe_load(read(".github/workflows/tests.yml"))
    assert flow["concurrency"]["group"] == "tests-${{ github.event.pull_request.number || github.ref }}"


# ── FGR-5, FGR-13 to FGR-15: the setup of the enforcement channel ───────────────

def test_AC_005_a_failed_item_of_the_setup_says_not_met(sample, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    answers = {tl.RULES: [tl.REVIEW_RULE], tl.ENTRY: tl.NO_PROTECTION, tl.RULESET_AT: {**tl.RULESET, "bypass_actors": []}}
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: tl.github(answers))
    said = [f.message for f in run(sample, "CK-ENFORCE-SETUP").findings]
    assert "not met: agentic-checks is a required status check" in said, said
    assert not any(m.startswith(("pull request reviews required", "agentic-checks is")) for m in said)
    tp.kit(sample, profile="lite")
    lite = run(sample, "CK-ENFORCE-SETUP")
    assert any(n.startswith("not enforced: agentic-checks is a required status check") for n in lite.notes), lite.notes
    assert not any("not met:" in n for n in lite.notes) and not any("not met:" in f.message for f in lite.findings)


def two_rules(first, second):
    return {tl.RULES: [first, second], tl.ENTRY: tl.NO_PROTECTION,
            tl.RULESET_AT: {**tl.RULESET, "bypass_actors": []}, f"repos/{tl.REPO}/rulesets/13": {**tl.RULESET, "id": 13, "name": "Release"}}


def test_AC_012_every_rule_that_asks_for_a_pull_request_counts():
    lax = tl.rule("pull_request", 12, required_approving_review_count=0, require_code_owner_review=False)
    strict = tl.rule("pull_request", 13, required_approving_review_count=2, require_code_owner_review=True)
    for answers in (two_rules(lax, strict), two_rules(strict, lax)):
        seen = tl.report(answers)
        assert (seen[tl.REVIEWS]["status"], seen[tl.REVIEWS]["detail"]) == ("pass", "required approvals: 2")
        assert seen[tl.OWNERS]["status"] == "pass"


def test_AC_013_one_ruleset_that_nobody_may_bypass_is_enough():
    def at(rid, actors, name):
        body = {**tl.RULESET, "id": rid, "name": name}
        if actors is None:
            body.pop("bypass_actors")
        else:
            body["bypass_actors"] = actors
        return body

    admins = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
    deploy = [{"actor_id": 9, "actor_type": "DeployKey", "bypass_mode": "always"}]
    asks = [tl.rule("pull_request", 12, required_approving_review_count=1), tl.rule("pull_request", 13, required_approving_review_count=1)]
    base = {tl.RULES: asks, tl.ENTRY: tl.NO_PROTECTION}

    def admins_row(first, second):
        return tl.report({**base, f"repos/{tl.REPO}/rulesets/12": first, f"repos/{tl.REPO}/rulesets/13": second})[tl.ADMINS]

    assert admins_row(at(12, admins, "Main"), at(13, [], "Release"))["status"] == "pass"
    both = admins_row(at(12, admins, "Main"), at(13, deploy, "Release"))
    assert both["status"] == "fail" and "ruleset Main may be bypassed by: RepositoryRole" in both["detail"]
    assert "ruleset Release may be bypassed by: DeployKey" in both["detail"]
    assert admins_row(at(12, admins, "Main"), at(13, None, "Release"))["status"] == "not-checkable"
    # a ruleset whose rule asks for no approval enforces no review, whoever may bypass it
    none_asked = [tl.rule("pull_request", 12, required_approving_review_count=1), tl.rule("pull_request", 13, required_approving_review_count=0)]
    row = tl.report({tl.RULES: none_asked, tl.ENTRY: tl.NO_PROTECTION, f"repos/{tl.REPO}/rulesets/12": at(12, admins, "Main"),
                     f"repos/{tl.REPO}/rulesets/13": at(13, [], "Loose")})[tl.ADMINS]
    assert row["status"] == "fail" and "Loose" not in row["detail"]


def test_AC_014_rules_that_github_refuses_leave_what_protection_does_not_meet_not_checkable():
    classic = {"required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": False}}
    refused = tl.report({tl.RULES: tl.REFUSED, tl.PROTECTION: classic})
    assert refused[tl.OWNERS]["status"] == "not-checkable" and "the rules of the branch could not be read" in refused[tl.OWNERS]["detail"]
    assert refused[tl.REVIEWS]["status"] == "pass", "what protection meets is met, whatever the rules say"
    assert tl.report({tl.RULES: [], tl.PROTECTION: classic})[tl.OWNERS]["status"] == "fail"
    assert tl.report({tl.RULES: "gh: Not Found (HTTP 404)", tl.PROTECTION: classic})[tl.OWNERS]["status"] == "fail", "404: protection alone decides (LIV-1)"


# ── FGR-6: the line goes into the text of the review ────────────────────────────

def test_AC_006_gate_and_the_brief_say_that_an_approval_without_the_line_records_nothing(sample):
    code, text = tcs.kit(sample, "gate", "--spec", SPEC, "--gate", "G6")
    assert code == 0 and "An approval without it records nothing." in text, text
    assert tcs.kit(sample, "brief", "--spec", SPEC, "--gate", "G6", "--write")[0] == 0
    lines = (sample / f"specs/{SPEC}/briefs/G6.md").read_text(encoding="utf-8").rstrip("\n").splitlines()
    assert "records nothing" in lines[-1] and "on a line of its own" in lines[-1] and lines[-2] == "", "one line, as before"


# ── FGR-8: a score is relative ──────────────────────────────────────────────────

def test_AC_007_the_duplicate_check_says_that_its_scores_are_relative(tmp_path):
    selftest.build_sample(tmp_path)
    tp.draft(tmp_path, sid="002-hello", title="Hello", requirement="System MUST greet each user by their name.", delta=False)
    found = run(tmp_path, "CK-DUPLICATE")
    assert not found.ok and sum("weighted by every requirement, spec and intake record" in n for n in found.notes) == 1, found.notes
    tp.kit(tmp_path, intake={"dedupe": {"threshold": 0.95}})
    none = run(tmp_path, "CK-DUPLICATE")
    assert none.ok and not any("weighted by" in n for n in none.notes)


# ── FGR-9: the documents say where the fixes ran ────────────────────────────────

def test_AC_008_no_document_says_that_the_fixes_have_not_run_on_github():
    gone = ["None of the changes has run on GitHub", "- Not run: any of these changes on GitHub.\n",
            "- Not run: any of this on GitHub. The review's threads", "No gate has been approved there yet",
            "As of 2026-11-26 this workflow has not run on GitHub", "It has not run on GitHub, and the next section"]
    texts = {rel.relative_to(ROOT).as_posix(): rel.read_text(encoding="utf-8")
             for rel in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md"), *(ROOT / "extensions").rglob("README.md")]}
    for rel, text in texts.items():
        for words in gone:
            assert words not in text, (rel, words)
    limits = flat("docs/limits.md")
    assert "pull request 6" in limits and "771 unit tests passed and 3 were skipped" in limits


# ── FGR-10: a commit that GitHub does not hold ──────────────────────────────────

def test_AC_009_a_commit_github_does_not_hold_is_skipped_and_named_and_the_others_are_read(tmp_path, monkeypatch):
    known, unknown = "a" * 40, "b" * 40
    merged = {"number": 87, "state": "closed", "merged_at": "2026-11-27T02:31:03Z", "merge_commit_sha": "c" * 40,
              "head": {"ref": "sdd/020-clarify"}, "base": {"ref": "main"}, "html_url": "https://github.com/o/r/pull/87"}

    def answer(path, only=None):
        if path.endswith(f"/{only or unknown}/pulls"):
            raise core.KitError(f"gh api {path} failed: gh: No commit found for SHA: {only or unknown} (HTTP 422)")
        return [merged]

    adapter = adapters.GitHubAdapter("o/r", runner=answer)
    assert [p["change"] for p in adapter.pulls([known, unknown])] == ["pull/87"] and adapter.unknown == [unknown]

    def gone(path):
        raise core.KitError(f"gh api {path} failed: gh: Not Found (HTTP 404)")

    with pytest.raises(core.KitError, match="Not Found"):
        adapters.GitHubAdapter("o/r", runner=gone).pulls([known])

    root = tmp_path / "project"
    root.mkdir()
    first, _ = demo_project(root)
    second = tcs.commit(root, "the spec, once more", {f"specs/{tcs.SPEC}/notes.md": "A note.\n"})
    kit_yml = root / core.KIT_DIR / "kit.yml"
    data = yaml.safe_load(kit_yml.read_text(encoding="utf-8"))
    data["enforcement"] = {"adapter": "github", "repository": "o/r", "default_branch": "main"}
    kit_yml.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8", newline="\n")
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: adapters.GitHubAdapter("o/r", runner=lambda path: answer(path, second)))
    ledger = delivery.ledger(tcs.ctx(root), tcs.SPEC)
    assert ledger["unknown"] == [second] and [p["change"] for p in ledger["pulls"]] == ["pull/87"], ledger
    told = tcs.section(tcs.page(root), "Delivery")
    assert f"GitHub does not hold 1 of the 2 commit(s), so their pull requests were not asked for: `{second[:12]}`" in told, told
    assert "Pull request `pull/87`: merged" in told and "No pull request holds any of these commits" not in told


# ── FGR-11: the MCP server and `gh`'s credential ────────────────────────────────

def test_AC_010_the_mcp_readme_says_how_gh_keeps_its_credential():
    text = flat("extensions/agentic-mcp/README.md")
    assert "small environment" in text and "gh auth login" in text and "`checks_run`" in text


# ── FGR-12: a # right after = ───────────────────────────────────────────────────

def test_AC_011_a_hash_right_after_equals_belongs_to_the_value(sample):
    flow = sample / SAMPLE_CONNECT

    def with_step(line):
        base = flow.read_text(encoding="utf-8").split("\n      - run: |\n")[0].rstrip("\n")
        flow.write_text(f"{base}\n      - run: |\n          {line}\n", encoding="utf-8", newline="\n")
        return run(sample, "CK-PIPELINE-SECRETS")

    assert "JIRA_TOKEN is given a literal value" in msgs(with_step("JIRA_TOKEN=#hunter2 python notify.py"))
    assert with_step("JIRA_TOKEN= # set by the job").ok
    assert with_step("JIRA_TOKEN=${{ secrets.JIRA_TOKEN }} # the store").ok
    assert with_step("echo ready").ok, "the sample as it was, with one harmless step"
