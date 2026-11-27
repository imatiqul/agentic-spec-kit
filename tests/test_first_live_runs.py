"""Tests for docs/design/first-live-runs.md (LIV-1 to LIV-11): what the kit's first runs on GitHub showed.

GitHub's answers in this file have the shape of what a real repository answered on 2026-11-27, with invented names.
No test here asks GitHub anything. Run: python -m pytest tests/test_first_live_runs.py -q
"""
import io
import re
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentic_kit import adapters, core, selftest  # noqa: E402
from agentic_kit.__main__ import main  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")

from agentic_kit_connect import notify  # noqa: E402
from agentic_kit_connect import sample as csample  # noqa: E402

import test_install_walk as walk  # noqa: E402  (the install scripts this system can run, and how to run them)

REPO = "acme/shop"
RULES = f"repos/{REPO}/rules/branches/main"
PROTECTION = f"repos/{REPO}/branches/main/protection"
ENTRY = f"repos/{REPO}/branches/main"
RULESET_AT = f"repos/{REPO}/rulesets/12"
#: What GitHub says to a pipeline's own token where a request needs an administrator, or a user.
REFUSED = "gh: Resource not accessible by integration (HTTP 403)"
NOT_PROTECTED = "gh: Branch not protected (HTTP 404)"

REVIEWS, OWNERS, REQUIRED, ADMINS = ("pull request reviews required", "code owner review required",
                                     "agentic-checks is a required status check", "administrators are not exempt")


def rule(kind, ruleset=12, **parameters):
    row = {"type": kind, "ruleset_source_type": "Repository", "ruleset_source": REPO, "ruleset_id": ruleset}
    return {**row, "parameters": parameters} if parameters else row


OTHER_RULES = [rule("deletion", 11), rule("non_fast_forward", 11), rule("required_signatures")]
REVIEW_RULE = rule("pull_request", allowed_merge_methods=["merge", "rebase"], dismiss_stale_reviews_on_push=True, require_code_owner_review=True,
                   require_last_push_approval=True, required_approving_review_count=1, required_review_thread_resolution=True)
CHECKS_RULE = rule("required_status_checks", strict_required_status_checks_policy=False,
                   required_status_checks=[{"context": "agentic-checks", "integration_id": 15368}])
RULESET = {"id": 12, "name": "Main", "target": "branch", "enforcement": "active", "current_user_can_bypass": "always",
           "bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]}
NO_PROTECTION = {"name": "main", "protected": True,
                 "protection": {"enabled": False, "required_status_checks": {"enforcement_level": "off", "contexts": [], "checks": []}}}
HAS_PROTECTION = {**NO_PROTECTION, "protection": {**NO_PROTECTION["protection"], "enabled": True}}
READ_ONLY = {"admin": False, "maintain": False, "push": False, "triage": False, "pull": True}


def github(answers):
    """The adapter, given GitHub's answers by path. A text is an error with those words. A path that is not listed is
    refused, as GitHub refuses a pipeline's own token what needs an administrator or a user."""
    def ask(path):
        answer = answers.get(path, REFUSED)
        if isinstance(answer, str):
            raise core.KitError(f"gh api {path} failed: {answer}")
        return answer
    return adapters.GitHubAdapter(REPO, "main", runner=ask)


def report(answers):
    return {row["item"]: row for row in github(answers).setup_report()}


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


def edit(root, rel, old, new):
    path = root / rel
    body = path.read_text(encoding="utf-8")
    assert old in body, f"{old!r} not in {rel}"
    path.write_text(body.replace(old, new), encoding="utf-8", newline="\n")


def cli(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--root", str(root), *args])
    return code, out.getvalue() + err.getvalue()


# ── LIV-1 to LIV-3: the rules of the default branch ─────────────────────────────

def test_AC_001_the_rules_of_the_branch_answer_what_only_an_administrator_could_read_before():
    seen = report({RULES: [*OTHER_RULES, REVIEW_RULE], ENTRY: NO_PROTECTION, RULESET_AT: RULESET})
    assert (seen[REVIEWS]["status"], seen[REVIEWS]["detail"]) == ("pass", "required approvals: 1")
    assert seen[OWNERS]["status"] == "pass"
    assert seen[REQUIRED]["status"] == "fail", "no rule requires a status check, and the branch has no protection"
    seen = report({RULES: [REVIEW_RULE, CHECKS_RULE], ENTRY: NO_PROTECTION, RULESET_AT: RULESET})
    assert seen[REQUIRED]["status"] == "pass" and "agentic-checks" in seen[REQUIRED]["detail"]


def test_AC_002_where_no_rule_asks_for_a_review_protection_decides_and_what_cannot_be_read_is_said_so():
    assert report({RULES: OTHER_RULES, PROTECTION: NOT_PROTECTED})[REVIEWS]["status"] == "fail"
    assert report({RULES: OTHER_RULES, ENTRY: NO_PROTECTION})[REVIEWS]["status"] == "fail", "refused, and the branch says protection is off"
    hidden = report({RULES: OTHER_RULES, ENTRY: HAS_PROTECTION})
    assert {row["status"] for row in hidden.values()} == {"not-checkable"} and "could not be read" in hidden[REVIEWS]["detail"]
    classic = {"required_pull_request_reviews": {"required_approving_review_count": 2, "require_code_owner_reviews": True},
               "required_status_checks": {"contexts": [], "checks": [{"context": "agentic-checks", "app_id": 15368}]}, "enforce_admins": {"enabled": True}}
    seen = report({RULES: OTHER_RULES, PROTECTION: classic})
    assert {row["status"] for row in seen.values()} == {"pass"} and seen[REVIEWS]["detail"] == "required approvals: 2"
    # a review that only protection asks for, behind rules that ask for something else, still counts
    assert report({RULES: [CHECKS_RULE], PROTECTION: classic})[REVIEWS]["status"] == "pass"
    # the rules cannot be read: protection alone decides, as before this change
    before = report({RULES: "gh: Not Found (HTTP 404)", PROTECTION: {"required_pull_request_reviews": {"required_approving_review_count": 0}}})
    assert [before[item]["status"] for item in (REVIEWS, OWNERS, REQUIRED, ADMINS)] == ["fail"] * 4
    # neither can be read
    rows = github({RULES: "gh: Not Found (HTTP 404)"}).setup_report()
    assert [(row["item"], row["status"]) for row in rows] == [("branch protection", "not-checkable")] and "403" in rows[0]["detail"]


def test_AC_003_who_may_bypass_the_ruleset_that_asks_for_the_review_decides_whether_administrators_are_exempt(sample, monkeypatch):
    asked = {RULES: [REVIEW_RULE], ENTRY: NO_PROTECTION}
    row = report({**asked, RULESET_AT: RULESET})[ADMINS]
    assert row["status"] == "fail" and "Main" in row["detail"] and "RepositoryRole" in row["detail"]
    assert report({**asked, RULESET_AT: {**RULESET, "bypass_actors": []}})[ADMINS]["status"] == "pass"
    silent = {key: value for key, value in RULESET.items() if key != "bypass_actors"}
    assert report({**asked, RULESET_AT: silent})[ADMINS]["status"] == "not-checkable"
    assert report(asked)[ADMINS]["status"] == "not-checkable", "the ruleset itself is refused"
    of_an_organization = {**REVIEW_RULE, "ruleset_source_type": "Organization"}
    assert report({RULES: [of_an_organization], ENTRY: NO_PROTECTION})[ADMINS]["status"] == "not-checkable"
    # protection that asks for the review and enforces it for administrators passes, whoever may bypass a ruleset
    classic = {"required_pull_request_reviews": {"required_approving_review_count": 1}, "enforce_admins": {"enabled": True}}
    assert report({**asked, RULESET_AT: RULESET, PROTECTION: classic})[ADMINS]["status"] == "pass"
    # and the check that reads the report says it, in a profile that enforces
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: github({**asked, RULESET_AT: RULESET}))
    said = msgs(run(sample, "CK-ENFORCE-SETUP"))
    assert "administrators are not exempt: ruleset Main may be bypassed by: RepositoryRole" in said
    assert "pull request reviews required" not in said


# ── LIV-4: a credential that has no user ────────────────────────────────────────

def test_AC_004_a_pipelines_own_token_has_no_user_and_the_credential_check_runs_all_the_same(sample, monkeypatch):
    answers = {f"repos/{REPO}": {"permissions": READ_ONLY}, RULES: [REVIEW_RULE], ENTRY: NO_PROTECTION, RULESET_AT: {**RULESET, "bypass_actors": []}}
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert github(answers).agent_credential() == {"identity": "github-actions[bot]", "account_type": "Bot", "permissions": READ_ONLY, "scopes": []}
    assert github(answers).agent_identity() == "github-actions[bot]"
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: github(answers))
    result = run(sample, "CK-CRED")
    assert result.ok and not result.not_run, msgs(result)
    # a token of the same kind that may push, where no review is asked for, is found out like any other credential
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: github({**answers, f"repos/{REPO}": {"permissions": {**READ_ONLY, "push": True}}, RULES: OTHER_RULES}))
    assert "github-actions[bot] can push, and the default branch does not require pull request reviews" in msgs(run(sample, "CK-CRED"))

    monkeypatch.delenv("GITHUB_ACTIONS")   # the same refusal outside GitHub Actions: an installation's token that nobody can name
    assert github(answers).agent_credential()["identity"] == "" and github(answers).agent_identity() is None
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: github(answers))
    assert not run(sample, "CK-CRED").not_run

    wrong = {**answers, "user": "gh: Bad credentials (HTTP 401)"}   # any other failure is still a check that could not run
    assert github(wrong).agent_identity() is None
    monkeypatch.setattr(adapters, "enforcement", lambda ctx: github(wrong))
    assert run(sample, "CK-CRED").not_run
    known = {**answers, "user": {"login": "kit-agent", "type": "User"}}   # and a credential with a user is read as before
    assert github(known).agent_credential()["identity"] == "kit-agent"


# ── LIV-5: a comment is not a value ─────────────────────────────────────────────

def test_AC_005_a_yaml_comment_after_a_reference_to_the_secret_store_is_not_read_as_a_value(sample):
    line = "JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}"
    edit(sample, csample.NOTIFY_FLOW, line, line + "   # read by the job that tells people")
    assert run(sample, "CK-PIPELINE-SECRETS").ok
    edit(sample, csample.NOTIFY_FLOW, line + "   # read by the job that tells people", "JIRA_TOKEN: hunter2 # read by the job that tells people")
    assert "JIRA_TOKEN is given a literal value" in msgs(run(sample, "CK-PIPELINE-SECRETS"))
    edit(sample, csample.NOTIFY_FLOW, "JIRA_TOKEN: hunter2 # read by the job that tells people", 'JIRA_TOKEN: "hunter # 2"')
    assert "JIRA_TOKEN is given a literal value" in msgs(run(sample, "CK-PIPELINE-SECRETS"))
    edit(sample, csample.NOTIFY_FLOW, 'JIRA_TOKEN: "hunter # 2"', "JIRA_TOKEN:   # set by the pipeline")
    assert run(sample, "CK-PIPELINE-SECRETS").ok, "a line with no value holds no secret"


# ── LIV-6: the event says what it counts ────────────────────────────────────────

def test_AC_006_the_event_counts_what_failed_and_what_could_not_run_and_says_when_it_names_only_some(sample):
    ctx = selftest.context(sample)
    failed = [SimpleNamespace(check=f"CK-F{n:02d}", findings=["a finding"], not_run=False) for n in range(21)]
    could_not = [SimpleNamespace(check=f"CK-N{n}", findings=[], not_run=True) for n in range(2)]

    def text(results):
        (event,) = [e for e in notify.detect(ctx, results, "abc123") if e.type == "check-failed"]
        return notify.title(event)

    both = text(failed + could_not)
    assert both.startswith("23 check(s) failed or could not run: CK-F00, CK-F01, ") and both.endswith("CK-F11 and 11 more")
    assert both.count("CK-") == 12
    assert text(failed[:1]) == "1 check(s) failed: CK-F00"
    assert text(could_not) == "2 check(s) could not run: CK-N0 (not run), CK-N1 (not run)"
    assert notify.title(notify.Event("check-failed", "k", facts={"ids": ["CK-TRACE"], "count": 1})) == "1 check(s) failed: CK-TRACE"


# ── LIV-7: the same releases in both workflows ──────────────────────────────────

def test_AC_007_agentic_checks_pins_the_releases_of_githubs_actions_that_the_connect_workflow_pins():
    def pins(rel):
        found = re.findall(r"uses:\s*(actions/[\w-]+)@([0-9a-f]{40})\b", (ROOT / rel).read_text(encoding="utf-8"))
        return {action: {commit for name, commit in found if name == action} for action, _ in found}

    checks, connect = pins("extensions/agentic/ci/agentic-checks.yml"), pins("extensions/agentic-connect/ci/github-actions.yml")
    assert set(checks) == {"actions/checkout", "actions/setup-python"}
    for action, commits in checks.items():
        assert commits == connect[action], action


# ── LIV-8: the ledger is there when notify ends ─────────────────────────────────

def test_AC_008_notify_leaves_its_ledger_in_place_also_when_nothing_was_sent(sample, tmp_path):
    settings = sample / csample.CONNECT
    cfg = yaml.safe_load(settings.read_text(encoding="utf-8"))
    cfg["notify"]["channels"], cfg["notify"]["routes"] = [], []
    settings.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8", newline="\n")
    ledger = tmp_path / "state" / "sent.txt"
    code, out = cli(sample, "connect", "notify", "--ledger", str(ledger))
    assert code in (0, 1), out
    assert ledger.is_file() and ledger.read_text(encoding="utf-8") == ""
    ledger.write_text("sent before\n", encoding="utf-8", newline="\n")
    cli(sample, "connect", "notify", "--ledger", str(ledger))
    assert ledger.read_text(encoding="utf-8") == "sent before\n"


# ── LIV-9, LIV-10: what the install scripts leave and say ───────────────────────

@pytest.mark.skipif(shutil.which("specify") is None, reason="Spec Kit's `specify` program is not installed, so the install scripts cannot run")
@pytest.mark.parametrize("found", walk.installers(), ids=lambda found: found[0])
def test_AC_009_the_install_ignores_compiled_python_and_says_when_spec_kit_was_never_set_up(found, tmp_path):
    _, before, after = found
    bare = tmp_path / "bare"   # a folder with .specify/ that Spec Kit never set up, as a repository has that holds only the kit's files
    (bare / ".specify" / "memory").mkdir(parents=True)
    done = walk.run([*before, bare, *after], tmp_path)
    assert done.returncode == 0, walk.said(done)
    ignore = bare / ".specify" / "extensions" / ".gitignore"
    assert "__pycache__/" in ignore.read_text(encoding="utf-8").splitlines()
    assert "Spec Kit was never set up in this project" in done.stdout and "CK-UPSTREAM-PIN" in done.stdout, walk.said(done)

    done = walk.run(["specify", "init", "shop", "--integration", "claude", "--non-interactive", "--ignore-agent-tools"], tmp_path)
    assert done.returncode == 0, walk.said(done)
    mine = tmp_path / "shop" / ".specify" / "extensions" / ".gitignore"   # a project Spec Kit set up, with an ignore file of its owner's
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("mine\n", encoding="utf-8", newline="\n")
    done = walk.run([*before, tmp_path / "shop", *after], tmp_path)
    assert done.returncode == 0, walk.said(done)
    assert mine.read_text(encoding="utf-8") == "mine\n"
    assert "never set up" not in done.stdout, walk.said(done)


# ── LIV-11: the documents ───────────────────────────────────────────────────────

def test_AC_010_the_documents_say_what_to_look_at_before_a_commit_and_which_token_reads_a_project():
    install = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    for name in ("workflow-registry.json", ".step-install.lock", ".workflow-install.lock", ".specify/extensions/.gitignore"):
        assert name in install, name
    trackers = (ROOT / "docs" / "adapters" / "trackers.md").read_text(encoding="utf-8")
    assert "read:project" in trackers and "fine-grained" in trackers
    limits = (ROOT / "docs" / "limits.md").read_text(encoding="utf-8")
    assert "rules/branches" in limits and "github-actions[bot]" in limits
