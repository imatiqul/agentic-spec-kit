"""A pull request opened by a workflow (BOT-1 to BOT-5, docs/design/pull-request-by-workflow.md).

Each test is named after the acceptance criterion it proves. Nothing here reaches GitHub: where the workflow's command
runs, a small program stands in for `gh`. AC-005 needs GitHub and is not here.
Run: python -m pytest tests/test_open_pr_workflow.py -q
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit.__main__ import _captured  # noqa: E402

SHIPPED = ROOT / "extensions" / "agentic" / "ci" / "agentic-open-pull-request.yml"
INSTALLED = ".github/workflows/agentic-open-pull-request.yml"


def workflow():
    doc = yaml.safe_load(SHIPPED.read_text(encoding="utf-8"))
    return doc, doc.get("on", doc.get(True))  # YAML 1.1 reads the key `on` as true


def test_AC_001_the_workflow_starts_by_hand_names_no_secret_and_may_only_write_pull_requests():
    doc, starts = workflow()
    assert list(starts) == ["workflow_dispatch"]
    assert set(starts["workflow_dispatch"]["inputs"]) == {"branch", "title"}
    assert all(spec["required"] for spec in starts["workflow_dispatch"]["inputs"].values())
    assert doc["permissions"] == {"contents": "read"}
    (job,) = doc["jobs"].values()
    assert job["permissions"] == {"contents": "read", "pull-requests": "write"}
    assert "secrets." not in SHIPPED.read_text(encoding="utf-8")
    assert not any("uses" in step for step in job["steps"]), "no action from outside is run"


def test_AC_002_nothing_a_person_types_is_pasted_into_a_command():
    doc, _ = workflow()
    (job,) = doc["jobs"].values()
    for step in job["steps"]:
        assert "${{" not in step.get("run", ""), "an expression inside a command would be run as part of it"
    assert {"HEAD_BRANCH", "TITLE"} <= set(job["env"])
    assert re.fullmatch(r"\$\{\{ inputs\.branch \}\}", job["env"]["HEAD_BRANCH"]) and re.fullmatch(r"\$\{\{ inputs\.title \}\}", job["env"]["TITLE"])


def test_AC_003_init_writes_the_workflow_only_when_asked(tmp_path):
    for name, extra in (("plain", []), ("asked", ["--open-pr-workflow"])):
        root = tmp_path / name
        (root / ".specify").mkdir(parents=True)
        (root / ".specify" / "init-options.json").write_text('{"speckit_version": "1.4.3"}', encoding="utf-8", newline="\n")
        code, text = _captured(["--root", str(root), "init", "--profile", "lite", "--repository", "o/r", *extra])
        assert code == 0, text
        assert (root / ".github/workflows/agentic-checks.yml").exists()
        assert (root / INSTALLED).exists() == bool(extra)
    assert (tmp_path / "asked" / INSTALLED).read_bytes() == SHIPPED.read_bytes()


@pytest.mark.skipif(os.name == "nt" or shutil.which("bash") is None, reason="the workflow's command is a bash script for a Linux runner")
def test_AC_004_the_command_refuses_the_default_branch_and_ends_well_when_one_is_already_open(tmp_path):
    doc, _ = workflow()
    (job,) = doc["jobs"].values()
    script = job["steps"][0]["run"]
    calls = tmp_path / "calls.txt"
    stand_in = tmp_path / "bin" / "gh"   # plays `gh`: writes down what it was asked, and answers from GH_ANSWER
    stand_in.parent.mkdir()
    stand_in.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$CALLS"\nprintf "%s" "$GH_ANSWER"\n', encoding="utf-8", newline="\n")
    stand_in.chmod(0o755)

    def run(branch, answer=""):
        calls.write_text("", encoding="utf-8")
        env = {**os.environ, "PATH": f"{stand_in.parent}{os.pathsep}{os.environ['PATH']}", "CALLS": str(calls), "GH_ANSWER": answer,
               "HEAD_BRANCH": branch, "BASE_BRANCH": "main", "TITLE": "A title; $(echo not run)", "OWNER": "o", "ASKED_BY": "pat",
               "GITHUB_REPOSITORY": "o/r"}
        done = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, cwd=str(tmp_path))
        return done, calls.read_text(encoding="utf-8")

    done, asked = run("main")
    assert done.returncode == 2 and "other than main" in done.stderr and asked == ""
    done, asked = run("feature/x", answer="https://example.invalid/o/r/pull/7")
    assert done.returncode == 0 and "already open: https://example.invalid/o/r/pull/7" in done.stdout
    assert asked.count("\n") == 1 and "head=o:feature/x" in asked, "it only looked; it opened nothing"
    done, asked = run("feature/x")
    assert done.returncode == 0, done.stderr
    lines = asked.splitlines()
    assert len(lines) == 2 and "repos/o/r/pulls" in lines[1] and "head=feature/x" in lines[1] and "base=main" in lines[1]
    assert "title=A title; $(echo not run)" in lines[1], "the title is passed as one argument, and nothing in it is run"
