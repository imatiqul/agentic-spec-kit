"""What the first run on Windows showed (WIN-7 to WIN-12, docs/design/windows-first-run.md).

Each test is named after the acceptance criterion it proves. Line ends are written as bytes, and git is told to
convert them the way Git for Windows does when it is installed, so the tests are the same on every system.
AC-001 is the walk in tests/test_install_walk.py, on a machine without the Claude Code program. AC-007 is a document.
Run: python -m pytest tests/test_windows_first_run.py -q
"""
import errno
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "extensions" / "agentic" / "scripts"
sys.path.insert(0, str(CORE))

from agentic_kit import core, demo  # noqa: E402
from agentic_kit.__main__ import _captured, reader_went_away  # noqa: E402

core.load_plugins(CORE)

from agentic_kit_team import golden  # noqa: E402

SPEC, GATE, CHANGE = demo.SPEC, demo.GATE, demo.CHANGE
BRIEF = f"specs/{SPEC}/briefs/{GATE}.md"
FIXTURE = ROOT / "fixtures" / "multi-app"


def kit(root, *words):
    return _captured(["--root", str(root), *words])


def git(root, *args):
    done = subprocess.run(["git", "-C", str(root), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True)
    assert done.returncode == 0, done.stderr.decode(errors="replace")
    return done.stdout


def crlf(path):
    """Give a file the line ends it has in a working copy on Windows."""
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def line_of(root):
    text = kit(root, "gate", "--spec", SPEC, "--gate", GATE)[1]
    return next(row.strip() for row in text.splitlines() if row.strip().startswith(f"gate {GATE} approve sha256:"))


def project(root, windows: bool):
    """The demo's project with its brief, committed. With `windows`, git converts line ends and the files on disk have CRLF."""
    demo.build_project(root)
    git(root, "init", "-q")
    git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    git(root, "config", "core.autocrlf", "true" if windows else "false")
    assert kit(root, "brief", "--spec", SPEC, "--gate", GATE, "--write")[0] == 0
    if windows:
        crlf(root / demo.SPEC_FILE)   # as an editor there saves it
        crlf(root / BRIEF)            # as a checkout there writes it
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "the spec and the reviewer's page")
    return git(root, "rev-parse", "HEAD").decode().strip()


def test_AC_002_a_gate_holds_where_git_keeps_lf_in_the_commit_and_crlf_on_disk(tmp_path):
    root, twin = tmp_path / "windows", tmp_path / "elsewhere"
    root.mkdir()
    twin.mkdir()
    commit = project(root, windows=True)
    project(twin, windows=False)
    for rel in (demo.SPEC_FILE, BRIEF):   # the two byte strings of one file, which is what Windows has
        assert b"\r\n" in (root / rel).read_bytes()
        assert b"\r" not in git(root, "show", f"{commit}:{rel}")
    line = line_of(root)
    assert line == line_of(twin), "one line for the same evidence, whatever the line ends on disk"
    demo._reviews(root, [demo._review(2, demo.PERSON, commit, line)])
    code, text = kit(root, "record", "--spec", SPEC, "--gate", GATE, "--change", CHANGE)
    assert code == 0, text
    code, text = kit(root, "check", *demo.APPROVAL_CHECKS)
    assert code == 0, text
    assert "Not committed" not in kit(root, "gate", "--spec", SPEC, "--gate", GATE)[1]


def test_AC_003_text_hashes_the_same_with_either_line_end_and_a_binary_file_does_not(tmp_path):
    lf, cr = tmp_path / "lf", tmp_path / "crlf"
    for folder, end in ((lf, b"\n"), (cr, b"\r\n")):
        folder.mkdir()
        (folder / "spec.md").write_bytes(b"# A spec" + end + b"- **FR-001**: it greets" + end)
        (folder / "scan.bin").write_bytes(b"\0\1\2" + end + b"\3" + end)
    one = [core.evidence_hash(core.Source(folder), "001-a", "G1", ["spec.md"]) for folder in (lf, cr)]
    assert one[0] == one[1]
    two = [core.evidence_hash(core.Source(folder), "001-a", "G1", ["scan.bin"]) for folder in (lf, cr)]
    assert two[0] != two[1], "git does not convert a file with a NUL byte, so its bytes are what was approved"
    assert core.Source(cr).read("spec.md") == core.Source(lf).read("spec.md")
    assert core.unix_line_ends(b"a\rb") == b"a\rb", "a lone CR is left as it is"


def test_AC_004_a_hash_over_files_with_no_crlf_is_what_the_formula_always_gave(tmp_path):
    files = {"specs/001-a/spec.md": b"# A spec\n- **FR-001**: it greets\n", "specs/001-a/plan.md": "# Plan\nGr\u00fc\u00dfe\n".encode("utf-8")}
    for rel, body in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(body)
    by_hand = hashlib.sha256()
    by_hand.update(b"agentic-evidence/1\n001-a\nG3\n")
    for rel in sorted(files):
        by_hand.update(rel.encode() + b"\0" + hashlib.sha256(files[rel]).hexdigest().encode() + b"\n")
    assert core.evidence_hash(core.Source(tmp_path), "001-a", "G3", list(files)) == "sha256:" + by_hand.hexdigest()


def test_AC_005_a_golden_task_completes_in_parallel_mode_where_git_converts_line_ends(tmp_path, monkeypatch):
    settings = tmp_path / "gitconfig"   # what Git for Windows sets for every repository of the machine
    settings.write_bytes(b"[core]\n\tautocrlf = true\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(settings))
    task = golden.run_task(FIXTURE, "shared-lib-field", "parallel", golden.Scripted(), tmp_path / "run")
    assert task["completed"] and not task["failing_checks"], task
    root = tmp_path / "run" / "shared-lib-field-parallel"
    assert git(root, "config", "core.autocrlf").strip() == b"true", "this git does not read GIT_CONFIG_GLOBAL, so nothing was tried"
    on_disk = [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    assert any(b"\r\n" in path.read_bytes() for path in on_disk), "no file on disk has CRLF, so nothing was tried"


def test_AC_006_on_windows_a_failed_write_that_left_nothing_to_flush_still_counts_as_a_reader_gone():
    class NothingLeft:  # standard output after a large write went straight to a pipe nobody reads
        def __init__(self):
            self.pending = False

        def write(self, text):
            self.pending = True

        def flush(self):
            if self.pending:
                raise OSError(errno.EINVAL, "Invalid argument")

    class Intact:
        def __init__(self):
            self.written = []

        def write(self, text):
            self.written.append(text)

        def flush(self):
            pass

    invalid = OSError(errno.EINVAL, "Invalid argument")
    assert reader_went_away(invalid, stream=NothingLeft(), windows=True)
    assert not reader_went_away(invalid, stream=NothingLeft(), windows=False), "elsewhere a closed pipe is a broken pipe"
    intact = Intact()
    assert not reader_went_away(invalid, stream=intact, windows=True), "standard output still takes a line: another error"
    assert intact.written == ["\n"]
    named, untouched = OSError(errno.EINVAL, "Invalid argument", "C:\\a|b.yml"), Intact()
    assert not reader_went_away(named, stream=untouched, windows=True) and untouched.written == [], "an invalid file name"
    refused, untouched = OSError(errno.EINVAL, "The parameter is incorrect"), Intact()
    refused.winerror = 87
    assert not reader_went_away(refused, stream=untouched, windows=True) and untouched.written == [], "Windows refused a call"
