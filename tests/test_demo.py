"""The demo of one gate (DEMO-1 to DEMO-9, docs/design/demo.md). Each test is named after the acceptance criterion it proves.
Run: python -m pytest tests/test_demo.py -q"""
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit import core, demo  # noqa: E402
from agentic_kit.__main__ import _captured, build_parser, main  # noqa: E402

core.load_plugins(CORE)

FOLDER = re.compile(r"throwaway project: (\S+)")
STEPS = ["1. Where the change stands", "2. An agent says it approved", "3. A named person approves", "4. The spec changes after the approval"]


@pytest.fixture(scope="module")
def shown():
    """One run of the demo: its exit code and the lines it printed."""
    lines = []
    code = demo.run(_captured, out=lines.append)
    return code, lines


def between(lines, start, end=None):
    """The lines from the one that equals `start` up to the one that equals `end`."""
    first = lines.index(start)
    last = lines.index(end) if end else len(lines)
    return "\n".join(lines[first:last])


def board_rows(lines):
    """What the gate board said for G1, each time the demo showed it."""
    return [row.split("|")[2].strip() for row in lines if row.strip().startswith(f"| {demo.SPEC} |")]


def test_AC_001_nothing_is_written_where_the_demo_is_run_and_its_folder_is_gone(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["--root", str(tmp_path), "demo"]) == 0
    assert list(tmp_path.iterdir()) == []
    folder = Path(FOLDER.search(capsys.readouterr().out).group(1))
    assert tmp_path not in folder.parents and folder != tmp_path
    assert not folder.exists()


def test_AC_002_an_approval_by_the_agents_own_account_fails(shown):
    code, lines = shown
    step = between(lines, STEPS[1], STEPS[2])
    assert code == 0
    assert "FAIL     CK-APPROVER" in step
    assert "the agent's or CI's own identity" in step


def test_AC_003_an_approval_by_a_listed_person_passes_and_the_board_says_approved(shown):
    _, lines = shown
    step = between(lines, STEPS[2], STEPS[3])
    for check in ("CK-APPROVER", "CK-GATE-MIRROR", "CK-GATE-RECORD"):
        assert f"ok       {check}" in step
    assert "FAIL" not in step and "NOT RUN" not in step
    assert board_rows(lines)[1] == "approved"


def test_AC_004_a_change_to_the_approved_spec_opens_the_gate_again(shown):
    _, lines = shown
    step = between(lines, STEPS[3], "What you saw")
    assert "approve recorded for DIFFERENT evidence" in step
    assert board_rows(lines) == ["open", "approved", "open"]


def test_AC_005_the_start_and_the_end_say_that_the_stand_in_proves_nothing(shown):
    _, lines = shown
    start = between(lines, lines[0], STEPS[0])
    end = between(lines, "What you did not see")
    for block in (start, end):
        assert "proves nothing about who approved" in block
    assert "pull-request review on GitHub" in start


def test_AC_006_a_step_that_does_not_go_as_written_is_named_and_the_demo_ends_with_1():
    def kit_that_lets_the_agent_through(argv):
        code, text = _captured(argv)
        if argv[-2:] == ["check", "CK-APPROVER"]:
            return 0, "ok       CK-APPROVER\n\n1 passed, 0 failed, 0 not run\n"
        return code, text

    lines = []
    assert demo.run(kit_that_lets_the_agent_through, out=lines.append) == 1
    text = "\n".join(lines)
    assert "The demo did not go as written. 2. An agent says it approved:" in text
    assert "What you saw" not in text
    assert not Path(FOLDER.search(text).group(1)).exists()


def test_AC_007_keep_leaves_the_project_in_place():
    lines = []
    assert demo.run(_captured, keep=True, out=lines.append) == 0
    text = "\n".join(lines)
    folder = Path(FOLDER.search(text).group(1))
    try:
        assert f"The project is kept at {folder}" in text
        assert (folder / core.KIT_DIR / "kit.yml").is_file()
        assert (folder / demo.SPEC_FILE).is_file()
        assert (folder / core.KIT_DIR / "decisions" / demo.SPEC / "G1.yml").is_file()
    finally:
        demo._remove(folder)
    assert not folder.exists()


def test_AC_008_every_command_line_the_demo_prints_is_one_the_cli_accepts(shown):
    _, lines = shown
    printed = [line[len("$ agentic.py "):] for line in lines if line.startswith("$ agentic.py ")]
    assert len(printed) == 10
    parser = build_parser()
    for words in printed:
        parser.parse_args(shlex.split(words))  # a name the parser does not have ends the test with SystemExit


def test_AC_009_the_project_is_lite_with_the_file_adapter_and_the_core_extension_is_enough(tmp_path):
    demo.build_project(tmp_path)
    kit = yaml.safe_load((tmp_path / core.KIT_DIR / "kit.yml").read_text(encoding="utf-8"))
    assert kit["profile"] == "lite"
    assert kit["enforcement"]["adapter"] == "file"
    core_only = ("import sys; sys.path.insert(0, sys.argv[1]); from agentic_kit.__main__ import main; code = main(['demo']); "
                 "assert not [m for m in sys.modules if m.startswith('agentic_kit_')], 'another extension was loaded'; sys.exit(code)")
    done = subprocess.run([sys.executable, "-c", core_only, str(CORE)], capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0, done.stdout[-600:] + done.stderr[-600:]
    assert "What you saw" in done.stdout
