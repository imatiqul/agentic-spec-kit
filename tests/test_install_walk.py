"""The install, done as a newcomer does it, with the real Spec Kit (WIN-1 to WIN-3, docs/design/windows-job.md).

`specify init`, the kit's install script, `init`, `team init`, one person in roles.yml, `doctor`, `check`, `selftest`,
and one spec taken to an open gate: sections "Before you start" and 1 to 3 of docs/install.md. On Windows the install
script is install.ps1, run through PowerShell; elsewhere it is install.sh, run through bash; where the other shell is
there too, that script is tried as well.

Skipped where `specify` is not installed. No network is reached: `gh` is given no sign-in, so the one check that
asks GitHub something says it could not run. Run: python -m pytest tests/test_install_walk.py -q

Spec Kit is told not to look for the coding agent's program (WIN-7, docs/design/windows-first-run.md). Without that,
`specify init --integration claude` ends with "Agent Detection Error" on a machine that has no Claude Code, and the
first run on Windows stopped there. What is walked is the kit's install, not whether Claude Code is installed.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
KIT = ".specify/extensions/agentic/scripts/agentic.py"
SPEC = "001-greeting"
SPEC_MD = f"""---
spec: {SPEC}
tier_declared: low
owner_role: product-owner
paths: ["src/greeting/*"]
---
# Feature Specification: A greeting that uses the person's name

## Requirements
- **FR-001**: The command MUST print a greeting that contains the name it was given.
"""

pytestmark = pytest.mark.skipif(shutil.which("specify") is None,
                                reason="Spec Kit's `specify` program is not installed, so the install cannot be walked")


def bash_program():
    """bash, and on Windows the one that comes with Git. `bash` on the path there can be the launcher of the Linux
    subsystem, which is another machine with another file system. The run of 2026-11-26 passed with what this returned there; its log does not say which file that was."""
    if os.name == "nt" and shutil.which("git"):
        for folder in Path(shutil.which("git")).resolve().parents[:3]:
            if (folder / "bin" / "bash.exe").is_file():
                return str(folder / "bin" / "bash.exe")
    return shutil.which("bash")


def installers():
    """The install scripts this system can run, its own first: (name, the command up to the project's path, what follows it)."""
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    bash = bash_program()
    found = []
    if powershell:
        found.append(("install.ps1", [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                      str(ROOT / "scripts" / "install.ps1"), "-Project"], ["-Profile", "lite"]))
    if bash:
        found.append(("install.sh", [bash, (ROOT / "scripts" / "install.sh").as_posix()], ["lite"]))
    if os.name != "nt":
        found.reverse()
    return found


def run(command, cwd, env=None):
    return subprocess.run([str(word) for word in command], cwd=str(cwd), env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def said(done):
    return f"exit {done.returncode}\n{done.stdout[-1500:]}\n{done.stderr[-1500:]}"


@pytest.fixture(scope="module", params=installers(), ids=lambda found: found[0])
def project(request, tmp_path_factory):
    """A new Spec Kit project with the kit's Lite profile installed by one of the install scripts."""
    _, before, after = request.param
    base = tmp_path_factory.mktemp("walk")
    done = run(["specify", "init", "shop", "--integration", "claude", "--non-interactive", "--ignore-agent-tools"], base)
    assert done.returncode == 0, said(done)
    root = base / "shop"
    assert (root / ".specify").is_dir(), "specify init made no .specify folder"
    done = run([*before, root, *after], base)
    assert done.returncode == 0, said(done)
    return root


@pytest.fixture(scope="module")
def kit(project, tmp_path_factory):
    """Runs one command of the installed kit in the project. `gh` finds no sign-in, so nothing goes to GitHub."""
    env = {**os.environ, "GH_CONFIG_DIR": str(tmp_path_factory.mktemp("no-gh-sign-in")), "GH_TOKEN": "", "GITHUB_TOKEN": ""}

    def call(*words):
        return run([sys.executable, KIT, *words], project, env)
    return call


def test_the_install_puts_the_kits_commands_where_the_coding_agent_reads_them(project):
    skills = project / ".claude" / "skills"
    for name in ("speckit-agentic-guide", "speckit-agentic-check", "speckit-agentic-gate", "speckit-agentic-team-orchestrate"):
        assert (skills / name / "SKILL.md").is_file(), name
    assert (project / KIT).is_file()
    assert (project / ".specify" / "presets" / "agentic-lite").is_dir()


def test_init_and_team_init_write_the_settings_and_six_agents_for_three_runtimes(project, kit):
    done = kit("init", "--profile", "lite", "--repository", "owner/name")
    assert done.returncode == 0, said(done)
    for rel in (".specify/agentic/kit.yml", ".specify/agentic/roles.yml", ".github/workflows/agentic-checks.yml"):
        assert (project / rel).is_file(), rel
    done = kit("team", "init", "--runtimes", "claude,copilot,sequential")
    assert done.returncode == 0, said(done)
    assert len(list((project / ".specify/agentic/agents").glob("*.yml"))) == 6
    assert len(list((project / ".claude/agents").glob("*.md"))) == 6
    assert len(list((project / ".github/agents").glob("*.agent.md"))) == 6
    assert (project / ".specify/agentic/agents/rendered/sequential.md").is_file()


def test_doctor_names_the_missing_people_and_check_passes_once_one_is_listed(project, kit):
    done = kit("doctor")
    assert done.returncode == 1 and "FAIL     CK-ROLES" in done.stdout, said(done)
    roles = project / ".specify/agentic/roles.yml"
    text = roles.read_text(encoding="utf-8")
    assert text.count("people: []") == 1
    roles.write_text(text.replace("people: []", "people:\n  - id: newcomer\n    roles: [product-owner, solutions-architect, qa]"),
                     encoding="utf-8", newline="\n")
    (project / ".github" / "CODEOWNERS").write_text("/.specify/ @newcomer\n", encoding="utf-8", newline="\n")
    done = kit("check")
    assert "0 failed" in done.stdout and "FAIL" not in done.stdout, said(done)
    assert "NOT RUN  CK-CRED" in done.stdout, said(done)   # it asks GitHub about the token in use, and there is no sign-in
    assert done.returncode == 0, said(done)                # in Lite, a check that could not run is a warning


def test_the_self_test_passes_inside_the_project(kit):
    done = kit("selftest")
    assert done.returncode == 0 and "all self-tests behaved as expected" in done.stdout, said(done)


def test_one_spec_reaches_an_open_gate_with_its_line_to_paste(project, kit):
    spec = project / "specs" / SPEC / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(SPEC_MD, encoding="utf-8", newline="\n")
    done = kit("report", "gates")
    assert done.returncode == 0 and f"| {SPEC} | open | later | later | product-owner |" in done.stdout, said(done)
    done = kit("gate", "--spec", SPEC, "--gate", "G1")
    assert done.returncode == 0 and "gate G1 approve sha256:" in done.stdout, said(done)
