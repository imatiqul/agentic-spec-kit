"""The command lines written in the skills, the command files and the guides, compared with the kit's own parser.

Names only: a command, an action or a view given by position, a flag, and a value that must come from a list.
Nothing is run, so this says nothing about what a command does. Run: python -m pytest tests -q
"""
import argparse
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extensions" / "agentic" / "scripts"))

from agentic_kit import core, reports  # noqa: E402
from agentic_kit.__main__ import build_parser  # noqa: E402

core.load_plugins(ROOT / "extensions" / "agentic" / "scripts")  # the other extensions add their commands and views

PARSER = build_parser()
VIEWS = set(reports.views()) | {"all", "list"}
SKILLS_AND_COMMANDS = sorted(ROOT.glob("extensions/*/commands/*.md")) + sorted(ROOT.glob(".claude/skills/*/SKILL.md"))
GUIDES = [ROOT / "README.md", ROOT / "docs" / "install.md", ROOT / "docs" / "admin-setup.md", *sorted(ROOT.glob("docs/guide/*.md")),
          *sorted(ROOT.glob("docs/adapters/*.md")), *sorted(ROOT.glob("extensions/*/README.md"))]

CALL = re.compile(r"(?:python3?\s+)?(?:[\w./-]*/)?agentic\.py[ \t]+([^`\n]*)")
SHORTHAND = re.compile(r"`A[ \t]+([^`\n]+)`")  # a file that writes `A check` says first that `A` means `python .../agentic.py`


def command_lines(text):
    """Each place the text calls the kit: its line number, and the words after the program's name.

    A place that names the program with no command after it, as in `agentic.py <command>`, is not one."""
    for found in sorted([*CALL.finditer(text), *SHORTHAND.finditer(text)], key=lambda m: m.start()):
        rest = re.split(r"\s(?:\||&&|;|>)\s|\s+#", found.group(1))[0].strip()  # up to a pipe, a second command or a comment
        try:
            words = shlex.split(rest)
        except ValueError:
            words = rest.split()
        words = [w for w in (word.strip("[](),.") for word in words) if w]
        if words[:1] == ["--root"]:
            words = words[2:]
        if words and re.fullmatch(r"[a-z][a-z-]*", words[0]):
            yield text.count("\n", 0, found.start()) + 1, words


def written_out(word):
    """A value as it would be typed, and not a placeholder such as <spec> or a choice such as lite|standard."""
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", word))


def wrong_names(words):
    """What a command line names that the parser does not have."""
    wrong, here, path, by_position = [], PARSER, [], []
    flags = dict(PARSER._option_string_actions)
    at = 0
    while at < len(words):
        word = words[at]
        at += 1
        if word.startswith("--"):
            name, has_value, value = word.partition("=")
            flag = flags.get(name)
            if flag is None:
                wrong.append(f"`{' '.join(path)}` has no flag {name}")
                continue
            if flag.nargs != 0 and not has_value:  # the flag takes a value: it is the next word
                value = words[at] if at < len(words) else ""
                at += 1
            if flag.choices and written_out(value) and value not in flag.choices:
                wrong.append(f"{name} does not take `{value}`")
            continue
        commands = next((a.choices for a in here._actions if isinstance(a, argparse._SubParsersAction)), None)
        if commands is not None:
            if word not in commands:
                wrong.append(f"there is no command `{' '.join([*path, word])}`")
                break
            here = commands[word]
            path.append(word)
            flags.update(here._option_string_actions)
            by_position = [a for a in here._get_positional_actions() if not isinstance(a, argparse._SubParsersAction)]
            continue
        if by_position:
            takes = by_position[0]
            if takes.nargs not in ("*", "+"):
                by_position.pop(0)
            allowed = takes.choices or (VIEWS if path == ["report"] and takes.dest == "view" else None)
            if allowed and written_out(word) and word not in allowed:
                wrong.append(f"`{' '.join(path)}` does not take `{word}`")
    return wrong


def compared(files):
    lines = [(f.relative_to(ROOT).as_posix(), number, words) for f in files for number, words in command_lines(f.read_text(encoding="utf-8"))]
    return lines, [f"{rel}:{number}: {problem}, in: {' '.join(words)}" for rel, number, words in lines for problem in wrong_names(words)]


def test_the_skills_and_the_command_files_name_only_what_the_cli_has():
    lines, problems = compared(SKILLS_AND_COMMANDS)
    assert len(lines) > 50, "the comparison read far fewer command lines than the files hold"
    assert {rel for rel, _, _ in lines} >= {f".claude/skills/agentic-spec-kit-{name}/SKILL.md" for name in ("try", "install", "review")}
    assert not problems, "\n".join(problems)


def test_the_guides_name_only_what_the_cli_has():
    lines, problems = compared(GUIDES)
    assert len(lines) > 50, "the comparison read far fewer command lines than the files hold"
    assert not problems, "\n".join(problems)


def test_the_comparison_sees_a_wrong_command_action_view_flag_and_value():
    right = "\n".join([
        "Run `A report gates`, then `A brief --spec <spec> --gate <gate> --write`.",
        "python .specify/extensions/agentic/scripts/agentic.py team init --runtimes claude,copilot   # name yours",
        "python extensions/agentic/scripts/agentic.py --root fixtures/multi-app gate --spec 001-money-format --gate G1 | head",
        "The launcher is `agentic.py <command>`; `agentic.py` alone prints nothing useful.",
    ])
    assert [words for _, words in command_lines(right)] == [
        ["report", "gates"], ["brief", "--spec", "<spec>", "--gate", "<gate>", "--write"],
        ["team", "init", "--runtimes", "claude,copilot"], ["gate", "--spec", "001-money-format", "--gate", "G1"]]
    assert [problem for _, words in command_lines(right) for problem in wrong_names(words)] == []

    def said(line):
        return [problem for _, words in command_lines(line) for problem in wrong_names(words)]

    assert said("`A reprot gates`") == ["there is no command `reprot`"]
    assert said("`A report gatez`") == ["`report` does not take `gatez`"]
    assert said("`A work reviews --spec <spec> --item <task>`") == ["`work` does not take `reviews`"]
    assert said("`A brief --sepc <spec> --gate G1`") == ["`brief` has no flag --sepc"]
    assert said("`A brief --spec <spec> --gate G9`") == ["--gate does not take `G9`"]
