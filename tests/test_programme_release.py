"""A programme's release waits for its children (PRR-1 to PRR-8, docs/design/programme-release.md).

Each test is named after the acceptance criterion it proves. The project is the self-test's sample, whose profile is
Regulated, with a parent and two children added. A file plays GitHub for the other repository, `acme/billing`, as in
tests/test_programme_view.py. No test reaches GitHub.
Run: python -m pytest tests/test_programme_release.py -q
"""
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit import adapters, core, selftest  # noqa: E402
from agentic_kit.checks_gov import required_gates  # noqa: E402

core.load_plugins(CORE)

CHECK = "CK-PROGRAMME-RELEASE"
PARENT, FIRST, SECOND, FAR = "010-totals", "011-orders-total", "012-billing-total", "004-billing-total"
REPO = "acme/billing"
PIN = "3f18fec" + "0" * 33
RECORDS = f"{core.KIT_DIR}/decisions"
STAND_IN = f"{core.KIT_DIR}/_adapter/reviews.json"


def spec_md(name, **front):
    head = {"spec": name, "tier_declared": "high", "owner_role": "backend", **front}
    return f"---\n{yaml.safe_dump(head, sort_keys=False)}---\n# {name}\n\n- **FR-001**: System MUST work.\n"


def record(root, spec, gate, decision="approve"):
    selftest._dump(root, f"{RECORDS}/{spec}/{gate}.yml", {"schema": "agentic-decision/1", "spec": spec, "gate": gate, "decision": decision})


def parent(root, *children, programme=None):
    rows = list(children)
    prog = programme if programme is not None else {
        "children": rows, "contract": "contract-demo-openapi",
        "rollout": [str(row.get("spec")) for row in rows if isinstance(row, dict)]}
    selftest._write(root, f"specs/{PARENT}/spec.md", spec_md(PARENT, programme=prog))


def passed(root, spec, but=None):
    """Every gate the spec needs approved, apart from those `but` names: gate -> decision, or None for no record."""
    for gate in required_gates(selftest.context(root), spec):
        decision = (but or {}).get(gate, "approve")
        if decision is not None:
            record(root, spec, gate, decision)


def run(root, check=CHECK):
    return core.run_check(check, selftest.context(root))


def msgs(result):
    return [f.message for f in result.findings]


def far_files(profile="standard", records=(("G7", "approve"),)):
    files = {f"{core.KIT_DIR}/kit.yml": yaml.safe_dump({"schema": "agentic-kit/1", "profile": profile}),
             f"specs/{FAR}/spec.md": spec_md(FAR)}
    for gate, decision in records:
        files[f"{RECORDS}/{FAR}/{gate}.yml"] = yaml.safe_dump({"spec": FAR, "gate": gate, "decision": decision})
    return files


def other_repository(root, files, name=REPO):
    path = root / STAND_IN
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("repositories", {})[name] = {"default": PIN, "commits": {PIN: files}}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def far(**more):
    return {"spec": FAR, "repo": REPO, "ref": PIN[:7], **more}


class Asked:
    """Stands where the enforcement adapter stands, and writes down what it is asked."""

    def __init__(self, monkeypatch, inner=None):
        self.calls, self.inner = [], inner
        monkeypatch.setattr(adapters, "enforcement", lambda ctx: self)

    def __getattr__(self, name):
        def call(*args):
            self.calls.append((name, *args))
            if self.inner is None:
                raise AssertionError(f"the adapter was asked: {name}{args}")
            return getattr(self.inner, name)(*args)
        return call


@pytest.fixture()
def sample(tmp_path):
    """The sample with a parent and two children in this repository. Nothing is recorded for the three."""
    selftest.build_sample(tmp_path)
    for name in (FIRST, SECOND):
        selftest._write(tmp_path, f"specs/{name}/spec.md", spec_md(name, parent=PARENT))
    parent(tmp_path, {"spec": FIRST}, {"spec": SECOND})
    return tmp_path


# ── children in this repository ─────────────────────────────────────────────────

def test_AC_001_the_release_passes_where_every_child_has_passed_and_nothing_is_held_before_it(sample):
    assert run(sample).ok, "no record for the parent: nothing is looked at"
    record(sample, PARENT, "G5")   # a gate before the release
    passed(sample, FIRST, but={"G1": None})
    r = run(sample)
    assert r.ok and r.findings == [], "a child with no record does not hold anything before the release"
    assert run(sample, "CK-PROGRAMME").ok, "the sample's parent and children are a well-formed programme"

    passed(sample, FIRST)
    passed(sample, SECOND)
    record(sample, PARENT, "G7")
    r = run(sample)
    assert r.ok, msgs(r)


def test_AC_002_a_child_with_a_rejected_or_missing_gate_holds_the_release_and_is_named(sample):
    passed(sample, FIRST, but={"G5": "reject", "G6": None, "G7": None})
    passed(sample, SECOND, but={"G7": "approve-with-conditions"})
    record(sample, PARENT, "G7", "approve-with-conditions")
    r = run(sample)
    assert not r.ok and len(r.findings) == 1, msgs(r)
    assert msgs(r) == [f"the release of {PARENT} (G7) is approved while its child {FIRST} has not passed its gates: "
                       "G5 reject, G6 not recorded, G7 not recorded"]
    assert r.findings[0].path == f"{RECORDS}/{PARENT}/G7.yml", "the finding points at the release that came too early"
    assert SECOND not in " ".join(msgs(r)), "approve-with-conditions passes a gate"

    passed(sample, FIRST)
    parent(sample, {"spec": FIRST}, {"spec": SECOND}, {"spec": "013-nowhere"})
    assert msgs(run(sample)) == [f"the release of {PARENT} (G7) is approved while its child 013-nowhere has not passed: "
                                 "the folder specs/013-nowhere/ does not exist"]
    parent(sample, {"spec": FIRST}, {"spec": SECOND})
    record(sample, PARENT, "G7", "reject")
    assert run(sample).ok, "a rejected release is no release"


# ── a child in another repository ───────────────────────────────────────────────

def test_AC_003_a_child_in_another_repository_has_passed_where_its_last_gate_is_approved_at_the_pin(sample):
    passed(sample, FIRST)
    parent(sample, {"spec": FIRST}, far())
    record(sample, PARENT, "G7")
    other_repository(sample, far_files("standard", [("G5", "approve"), ("G7", "approve")]))
    r = run(sample)
    assert r.ok, msgs(r)

    other_repository(sample, far_files("standard", [("G5", "approve"), ("G6", "approve")]))
    assert msgs(run(sample)) == [f"the release of {PARENT} (G7) is approved while its child {FAR} in {REPO}, pinned to {PIN[:7]}, "
                                 "has not been shown to pass: that commit holds no decision record for G7, "
                                 "the last gate its standard profile asks for"]
    other_repository(sample, far_files("standard", [("G7", "reject")]))
    assert msgs(run(sample))[0].endswith("the decision recorded there for G7 is reject")

    other_repository(sample, far_files("lite", [("G5", "approve")]))
    r = run(sample)
    assert r.ok, msgs(r)
    other_repository(sample, far_files("lite", [("G5", "approve-with-conditions")]))
    assert run(sample).ok

    files = far_files("regulated", [])
    files[f"{RECORDS}/{FAR}/G7.yml"] = yaml.safe_dump({"spec": "other-spec", "gate": "G7", "decision": "approve"})
    other_repository(sample, files)
    assert msgs(run(sample))[0].endswith(f"the record of G7 there does not name {FAR} and G7")
    other_repository(sample, {**far_files(), f"{core.KIT_DIR}/kit.yml": "profile: strict\n"})
    assert "that commit holds no .specify/agentic/kit.yml that names a profile the kit knows" in msgs(run(sample))[0]


def test_AC_004_what_cannot_be_read_holds_the_release_and_the_adapter_is_asked_three_things_at_most(sample, monkeypatch):
    passed(sample, FIRST)
    record(sample, PARENT, "G7")
    parent(sample, {"spec": FIRST}, far())
    r = run(sample)   # the stand-in file holds no repository acme/billing
    assert not r.ok and msgs(r)[0].startswith(f"the release of {PARENT} (G7) is approved while its child {FAR} in {REPO}, "
                                              f"pinned to {PIN[:7]}, could not be read (")
    assert "holds no repository acme/billing" in msgs(r)[0] and msgs(r)[0].endswith("so the release cannot be shown to wait for it")
    other_repository(sample, far_files())
    parent(sample, {"spec": FIRST}, far(ref="9a5a465"))
    assert "holds no commit 9a5a465 of acme/billing" in msgs(run(sample))[0]

    asked = Asked(monkeypatch)   # from here on, a question to the adapter fails the test
    parent(sample, {"spec": FIRST}, far(ref="main"), far(repo="billing"), far(spec="../../etc"), "a plain word")
    r = run(sample)
    assert asked.calls == [] and r.not_run is None
    assert msgs(r) == [
        f"the release of {PARENT} (G7) is approved while its child {FAR} in {REPO} is not pinned to a commit id, so it was not read",
        f"the release of {PARENT} (G7) is approved while the repository of its child {FAR}, `billing`, is not named as owner/name, "
        "so it was not read",
        f"the release of {PARENT} (G7) is approved while its child `../../etc` is not the plain name of a spec's folder, "
        "so it was not looked up",
        f"the release of {PARENT} (G7) is approved while an entry under children names no spec, so it cannot be shown to have passed"]

    asked = Asked(monkeypatch, inner=adapters.FileAdapter(core.Source(sample)))
    parent(sample, {"spec": FIRST}, far())
    assert run(sample).ok
    assert asked.calls == [("commit_at", REPO, PIN[:7]),
                           ("file_at", REPO, PIN, f"{core.KIT_DIR}/kit.yml"),
                           ("file_at", REPO, PIN, f"{RECORDS}/{FAR}/G7.yml")]


# ── the self-test, the documents and the programme check ────────────────────────

def test_AC_005_the_self_test_passes_on_the_sample_and_fails_on_the_fixture(tmp_path):
    what, mutate, passing, failing = selftest.all_fixtures()[CHECK]
    good, broken = tmp_path / "good", tmp_path / "broken"
    selftest.build_sample(good)
    assert core.run_check(CHECK, selftest.context(good, **passing)).ok
    selftest.build_sample(broken)
    mutate(broken)
    found = core.run_check(CHECK, selftest.context(broken, **failing))
    assert not found.ok and found.not_run is None
    assert found.findings[0].message.startswith(f"the release of {selftest.SPEC} (G7) is approved while its child 002-other has not passed")
    assert "release" in what and passing == {} and failing == {}
    assert core.run_check("CK-SELFTEST", selftest.context(good)).ok
    assert core.REGISTRY[CHECK].profiles == ("standard", "regulated") == core.REGISTRY["CK-PROGRAMME"].profiles


def test_AC_006_the_documents_say_the_release_waits(tmp_path):
    view = (ROOT / "docs" / "design" / "programme-view.md").read_text(encoding="utf-8")
    report = (ROOT / "docs" / "phase-reports" / "phase-12-features.md").read_text(encoding="utf-8")
    limits = (ROOT / "docs" / "limits.md").read_text(encoding="utf-8")
    assert CHECK in view and re.search(r"the view itself (still )?adds no rule", view)
    assert re.search(r"6\. \*\*A parent's release waits for its children\.\*\*", report) and CHECK in report
    assert CHECK in limits and re.search(r"private repository", limits) and re.search(r"release (then )?stays held", limits)


def test_AC_007_the_programme_check_fails_where_it_stopped_and_the_release_is_not_passed_over_it(sample):
    record(sample, PARENT, "G7")
    cases = [({"children": "a word"}, "the children of the programme are not a list"),
             ({"children": ["a word"], "contract": "contract-demo-openapi", "rollout": []},
              "an entry under children is not a mapping with the key spec"),
             ({"children": [{"spec": FIRST}], "contract": ["a", "list"], "rollout": 5}, "the shared contract is not the name of a node"),
             ({"children": [{"spec": FIRST}], "contract": "contract-demo-openapi", "rollout": 5}, "the rollout order is not a list")]
    for prog, said in cases:
        parent(sample, programme=prog)
        r = run(sample, "CK-PROGRAMME")
        assert r.not_run is None and any(said in m for m in msgs(r)), (prog, msgs(r))
        assert not run(sample).ok, prog
    selftest._write(sample, f"specs/{PARENT}/spec.md", spec_md(PARENT, programme="yes"))
    r = run(sample, "CK-PROGRAMME")
    assert msgs(r) == ["the programme entry is not a mapping, so it names no children, shared contract or rollout order"]
    assert msgs(run(sample)) == [f"the release of {PARENT} (G7) is approved while its programme entry names no children "
                                 "that can be read, so it cannot be shown to wait for them"]
