#!/usr/bin/env python3
"""Launcher: python .specify/extensions/agentic-mcp/scripts/agentic_mcp.py --root <project>

An MCP server for the kit, on standard input and output (MCP-1 to MCP-21, docs/design/mcp-server.md). It reads only.
Started with `--allow-write decision-log`, it also lists one tool that adds a question to a spec's decision log
(MCW-1 to MCW-8, docs/design/mcp-first-write.md). An MCP client starts it; a person adds it to the client's
configuration and to `.specify/agentic/tools.yml`, and the option with it.
"""
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent.parent / "agentic" / "scripts"  # <extensions>/agentic/scripts, in this repository and when installed
WRITABLE = ("decision-log",)  # what `--allow-write` may name (MCW-1)


def prepare() -> None:
    """Before anything of the kit is imported: no bytecode files, and the kit beside this script on the import path.

    The kit may lie inside the project that is read (`.specify/extensions/`). Importing it must leave no file there (MCP-20)."""
    sys.dont_write_bytecode = True
    for folder in (HERE, CORE):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))


def log(line: str) -> None:
    try:
        print(line, file=sys.stderr, flush=True)
    except (OSError, ValueError, AttributeError):  # nobody reads standard error: nothing to do about it
        pass


def take_streams():
    """The line to the client, kept apart from everything else that writes or reads (MCP-4).

    The server keeps handles of its own on the two streams the client gave it. Then descriptor 1 is made to lead
    where standard error leads, and descriptor 0 to the null device. So a `print` in the kit, and a program the kit
    starts, write to standard error, and no such program can read a message meant for the server. Where the
    descriptors cannot be changed, Python's own `sys.stdout` still goes to standard error."""
    try:
        sys.stdout.flush()
    except (OSError, ValueError, AttributeError):
        pass
    try:
        to_client, from_client = os.fdopen(os.dup(1), "wb"), os.fdopen(os.dup(0), "rb")
    except (OSError, ValueError):
        to_client, from_client = sys.__stdout__.buffer, sys.__stdin__.buffer
    else:
        try:
            null = os.open(os.devnull, os.O_RDONLY)
            try:
                os.dup2(null, 0)
            finally:
                os.close(null)
            os.dup2(2, 1)
        except (OSError, ValueError):
            pass
    sys.stdout = sys.stderr
    return to_client, from_client


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="agentic_mcp", description="An MCP server for agentic-spec-kit, on standard input and output. It reads "
                                                                     "only, unless --allow-write says otherwise. An MCP client starts it; it is not "
                                                                     "for a person to type into.")
    parser.add_argument("--root", default=".", help="the project to read (default: the folder the server is started in)")
    parser.add_argument("--allow-write", action="append", default=[], metavar="WHAT",
                        help="decision-log: also list decision_add, which adds a question to a spec's decision log as a proposal. "
                             "Left out, no tool writes")
    args = parser.parse_args(argv)
    to_client, from_client = take_streams()

    def stop(why: str) -> int:
        log(f"agentic_mcp: {why}")
        return 2

    wrong = [word for word in args.allow_write if word not in WRITABLE]
    if wrong:  # before anything is read or listed (MCW-1)
        return stop(f"--allow-write takes {' or '.join(WRITABLE)}, and {wrong[0]!r} is not that")
    root = Path(args.root)
    if not root.is_dir():
        return stop(f"{args.root} is not a folder. --root names the project to read")
    prepare()
    try:
        from agentic_kit import core
    except ImportError as wrong:
        return stop(f"the kit could not be loaded ({wrong}). The agentic extension has to lie beside this one, and Python needs PyYAML")
    try:
        loaded = core.load_plugins(CORE)
        from agentic_kit_mcp import __version__, protocol, tools
        listed = tools.build(root.resolve(), loaded, log, writes=tuple(dict.fromkeys(args.allow_write)))
    except Exception as wrong:  # noqa: BLE001 - whatever stops the kit from loading: said in one line, and the server does not start
        return stop(f"the kit could not be loaded ({type(wrong).__name__}: {wrong})")
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"  # git run for a tool leaves the index as it is, and its lock to the person at work (MCP-20)

    def send(line: bytes) -> None:
        try:
            to_client.write(line)
            to_client.flush()
        except (OSError, ValueError) as wrong:  # a closed pipe; on Windows it can come as an invalid argument
            raise protocol.Gone() from wrong

    server = protocol.Server(listed, name="agentic-spec-kit", version=__version__, instructions=tools.instructions(listed), send=send,
                             finish=tools.finish, log=log)
    writing = [tool.name for tool in listed if tool.writes]
    told = f"one of which writes: {writing[0]}, into the decision log of a spec" if writing else "read-only"
    log(f"agentic-spec-kit MCP server {__version__}: reading {root.resolve()}, {len(listed)} tools, {told}")
    try:
        server.serve(iter(from_client.readline, b""))
    except protocol.Gone:  # the client stopped reading: there is nobody left to answer
        pass
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
