"""The features of Phase 12 on one project, with every extension loaded.

Each feature has its own spec and its own tests, and each was built on its own. These tests are for the places
where they meet: the page of a change takes sections from three other features through `core.CHANGESET_HOOKS`
(CHS-2 in docs/design/changeset.md, DEC-17 in decision-log.md, CNV-13 in conversation.md, PRG-1 in
programme-view.md), and a kept page must not reach a gate or a check (CHS-9). The project is the self-test's
sample: a Regulated project with a decision log, a recorded conversation and one work item.
Run: python -m pytest tests/test_phase12_together.py -q
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit import changeset, core, selftest  # noqa: E402
from agentic_kit.__main__ import _captured  # noqa: E402

core.load_plugins(CORE)

SPEC = "001-demo"
DECISIONS, CONVERSATION = "Decisions made in this change", "The conversation behind it"


def kit(root, *words):
    return _captured(["--root", str(root), *words])


@pytest.fixture()
def sample(tmp_path):
    selftest.build_sample(tmp_path)
    return tmp_path


def results(root):
    """Every check's result on the project, by the check's id."""
    code, text = kit(root, "check", "--today", selftest.TODAY, "--json")
    return code, {row["check"]: {key: value for key, value in row.items() if key != "check"} for row in json.loads(text)["results"]}


def evidence(root):
    """The line a reviewer pastes for each gate of the spec: it holds the hash of that gate's evidence."""
    lines = {}
    for gate in core.GATES[1:]:
        text = kit(root, "gate", "--spec", SPEC, "--gate", gate)[1]
        lines[gate] = [row.strip() for row in text.splitlines() if "sha256:" in row]
    return lines


def test_the_page_of_one_change_holds_the_sections_of_the_other_features_after_its_own(sample):
    code, text = kit(sample, "changeset", "--spec", SPEC)
    assert code == 0, text
    headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
    assert headings[:7] == list(changeset.HEADINGS)
    assert headings[7:] == [DECISIONS, CONVERSATION], "the decision log is part of the core and comes first; the spec is no parent and no child"
    decided = text.split(f"## {DECISIONS}\n", 1)[1].split("\n## ", 1)[0]
    assert "`D-002` decided by alice" in decided and "`D-001` superseded by D-002" in decided
    said = text.split(f"## {CONVERSATION}\n", 1)[1]
    assert "**Confirmed by alice**" in said and "the kit cannot tell who wrote that line" in said and "2 comment(s) when fetched" in said
    code, doc = kit(sample, "changeset", "--spec", SPEC, "--json")
    assert code == 0 and [part["heading"] for part in json.loads(doc)["sections"]] == headings
    code, view = kit(sample, "report", "changesets")
    assert code == 0 and f"| {SPEC} | Demo |" in view


def test_a_kept_page_changes_the_result_of_no_check_and_the_evidence_of_no_gate(sample):
    code, before = results(sample)
    lines = evidence(sample)
    assert code == 0 and len(before) == len(core.REGISTRY) - 1 and all(row["ok"] for row in before.values())
    assert "decision-log.yml" in kit(sample, "gate", "--spec", SPEC, "--gate", "G5")[1], "the log is evidence of G5"
    code, said = kit(sample, "changeset", "--spec", SPEC, "--write")
    assert code == 0 and (sample / "specs" / SPEC / "changeset.md").is_file(), said
    code, after = results(sample)
    assert code == 0 and after == before, [check for check in after if after[check] != before.get(check)]
    assert evidence(sample) == lines, "the page is evidence of no gate, so no hash moved"
    for gate in core.GATES[1:]:
        assert "changeset.md" not in kit(sample, "gate", "--spec", SPEC, "--gate", gate)[1]
