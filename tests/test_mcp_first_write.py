"""The MCP server's first tool that writes (MCW-1 to MCW-8, docs/design/mcp-first-write.md).

Each test is named after the acceptance criterion it proves. The server is started as a client starts it and spoken to
line by line, with the helpers of tests/test_mcp.py. The project is the self-test's sample with one more spec, 021-notes,
which has no decision log and whose gates are not decided; the sample's own spec has G5 approved.
Run: python -m pytest tests/test_mcp_first_write.py -q
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import test_mcp as tm
from agentic_kit import core, decision_log, selftest
from agentic_kit_mcp import protocol, tools

WRITE = ["--allow-write", "decision-log"]
NOTES = "021-notes"
LOG, AUDIT = decision_log.log_path(NOTES), f"{core.KIT_DIR}/audit/{NOTES}.jsonl"
ASKED = "Is an empty note kept, or is it dropped?"
SPEC_MD = f"""---
spec: {NOTES}
tier_declared: high
owner_role: backend
---
# Feature Specification: Notes

## Requirements
- **FR-001**: System MUST keep a note a person writes.
"""
TASKS_MD = "# Tasks\n\n- [ ] T001 Store the notes\n"


def project(root):
    """The sample, with the spec 021-notes, committed."""
    root.mkdir(parents=True, exist_ok=True)
    selftest.build_sample(root)
    selftest._write(root, f"specs/{NOTES}/spec.md", SPEC_MD)
    selftest._write(root, f"specs/{NOTES}/tasks.md", TASKS_MD)
    return tm.committed(root)


def writing(root):
    return tm.server(command=[sys.executable, tm.SERVER, "--root", root, *WRITE])


def answer(text):
    return json.loads(text)


def audit(root):
    path = root / AUDIT
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


# ── the option ──────────────────────────────────────────────────────────────────

def test_AC_001_without_the_option_the_server_is_what_it_was_and_another_word_ends_it(tmp_path):
    root = project(tmp_path / "project")
    with tm.server(root) as client:
        first = client.open()
        listed = client.ask("tools/list")["result"]["tools"]
        code, rest = client.close()
        said = client.said()
    assert [tool["name"] for tool in listed] == tm.expected_tools() and "decision_add" not in [tool["name"] for tool in listed]
    assert all(tool["annotations"]["readOnlyHint"] is True and set(tool["annotations"]) == {"title", "readOnlyHint", "openWorldHint"}
               for tool in listed)
    assert first["instructions"] == tools.INSTRUCTIONS and code == 0 and rest == []
    assert said.splitlines()[-1].endswith(f"{len(tm.expected_tools())} tools, read-only")

    for words in (["--allow-write", "everything"], ["--allow-write", "decision-log", "--allow-write", "specs"]):
        done = subprocess.run([sys.executable, str(tm.SERVER), "--root", str(root), *words], input=b"", capture_output=True, env=tm.PLAIN, timeout=60)
        said = done.stderr.decode("utf-8").splitlines()
        assert done.returncode == 2 and done.stdout == b"", words
        assert len(said) == 1 and said[0].startswith("agentic_mcp: --allow-write takes decision-log, and '") and said[0].endswith("' is not that")


# ── adding a question ───────────────────────────────────────────────────────────

def test_AC_002_with_the_option_decision_add_adds_a_proposal_once(tmp_path):
    root = project(tmp_path / "project")
    assert not (root / LOG).exists() and audit(root) == []
    with writing(root) as client:
        client.open()
        names = [tool["name"] for tool in client.ask("tools/list")["result"]["tools"]]
        assert names == tm.expected_tools() + ["decision_add"]
        text, failed = client.call("decision_add", spec=NOTES, question=ASKED, affects=["FR-001"])
        assert not failed, text
        made = answer(text)
        log_after, audit_after = (root / LOG).read_bytes(), audit(root)
        again, failed = client.call("decision_add", spec=NOTES, question="  is an EMPTY note kept,   or is it dropped?  ", affects=["FR-001"])
        assert not failed, again
    assert made["added"] is True and made["path"] == LOG and made["spec"] == NOTES
    entry = made["entry"]
    assert (entry["id"], entry["title"], entry["state"], entry["proposed_by"], entry["affects"]) == ("D-001", ASKED, "proposed", tools.WRITER, ["FR-001"])
    assert entry["outcome"] is None and entry["owner"] is None and entry["decided_on"] is None
    on_disk = yaml.safe_load((root / LOG).read_text(encoding="utf-8"))
    assert on_disk["schema"] == decision_log.SCHEMA and on_disk["entries"] == [
        {"id": "D-001", "title": ASKED, "state": "proposed", "proposed_by": "agentic-mcp", "affects": ["FR-001"]}]
    [added] = audit_after
    assert added["action"] == "decision-log.add" and added["actor"] == {"type": "agent", "id": "agentic-mcp"} and added["entry"] == "D-001"
    assert core.run_check("CK-DECISION-LOG", selftest.context(root)).ok
    assert core.run_check("CK-AUDIT-CHAIN", selftest.context(root)).ok

    held = answer(again)
    assert held["added"] is False and held["entry"]["id"] == "D-001" and "Nothing was written" in held["note"]
    assert (root / LOG).read_bytes() == log_after and audit(root) == audit_after, "the same question twice changes nothing"


def test_AC_003_what_the_tool_refuses_leaves_the_project_as_it_was(tmp_path):
    root = project(tmp_path / "project")
    before = tm.snapshot(root)
    looks_like_an_id = "-".join(["000", "00", "0000"])   # the form of a national id, built here
    asked = [
        ({"spec": "999-none", "question": ASKED}, "the project has no spec 999-none"),
        ({"spec": "..", "question": ASKED}, "`spec` is refused: it holds `..`"),
        ({"spec": NOTES, "question": "x" * 501}, "must have at most 500 characters"),
        ({"spec": NOTES, "question": "Is it kept?\nOr is it dropped?"}, "it holds a control character"),
        ({"spec": NOTES, "question": "   "}, "it holds nothing but spaces"),
        ({"spec": NOTES, "question": ASKED, "affects": ["FR-999"]}, "the entry affects FR-999, and the spec has no such requirement"),
        ({"spec": NOTES, "question": ASKED, "affects": ["T009"]}, "the entry affects T009, and the task list has no such task"),
        ({"spec": NOTES, "question": ASKED, "affects": ["../x"]}, "`affects` is refused: it holds `..`"),
        ({"spec": NOTES, "question": f"Is {looks_like_an_id} the right number to keep?"}, "it holds what looks like national-id"),
        ({"spec": selftest.SPEC, "question": ASKED}, f"G5 of {selftest.SPEC} is approved, and an entry added now would open it again"),
    ]
    with writing(root) as client:
        client.open()
        for arguments, said in asked:
            text, failed = client.call("decision_add", **arguments)
            assert failed and said in text, (arguments, text)
    assert tm.snapshot(root) == before, "a refusal writes nothing"

    (root / f"specs/{NOTES}/decision-log.yml").write_text("schema: something-else\nentries: []\n", encoding="utf-8", newline="\n")
    with writing(root) as client:
        client.open()
        text, failed = client.call("decision_add", spec=NOTES, question=ASKED)
    assert failed and "is not a decision log" in text, text


def test_AC_004_a_call_that_adds_changes_the_two_logs_alone_and_a_link_out_is_refused(tmp_path):
    root = project(tmp_path / "project")
    before = tm.snapshot(root)
    with writing(root) as client:
        client.open()
        text, failed = client.call("decision_add", spec=NOTES, question=ASKED)
    after = tm.snapshot(root)
    assert not failed
    assert sorted(set(after) ^ set(before)) == [AUDIT, LOG] and all(after[name] == before[name] for name in before), \
        "nothing but the log and the audit log; no bytecode file, no commit"
    note = answer(text)["note"]
    for words in ("proposal", "decides nothing", "`agentic.py decision decide`", "working copy"):
        assert words in note, words

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "log.yml").write_text(f"schema: {decision_log.SCHEMA}\nentries: []\n", encoding="utf-8", newline="\n")
    other = root / "specs" / "022-linked"
    selftest._write(root, "specs/022-linked/spec.md", SPEC_MD.replace(NOTES, "022-linked"))
    try:
        os.symlink(outside / "log.yml", other / "decision-log.yml")
    except (OSError, NotImplementedError) as wrong:
        pytest.skip(f"this system would not make a link ({wrong}), so the half about links was not tried; the half before it passed")
    with writing(root) as client:
        client.open()
        text, failed = client.call("decision_add", spec="022-linked", question=ASKED)
    assert failed and "a link leads it out of the project" in text, text
    assert (outside / "log.yml").read_text(encoding="utf-8") == f"schema: {decision_log.SCHEMA}\nentries: []\n"


# ── what the client is told ─────────────────────────────────────────────────────

def test_AC_005_the_hints_the_instructions_and_the_line_on_standard_error_say_that_one_tool_writes(tmp_path):
    root = project(tmp_path / "project")
    with writing(root) as client:
        newest = client.ask("tools/list", meta=tm.ENVELOPE)["result"]["tools"]
        found = {}
        for revision in ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"):
            with writing(root) as other:
                first = other.open(revision)
                found[revision] = (first, other.ask("tools/list")["result"]["tools"])
        client.close()
        said = client.said()
    for revision, listed in [("2026-07-28", newest)] + [(rev, row[1]) for rev, row in found.items() if rev != "2024-11-05"]:
        hints = {tool["name"]: tool["annotations"] for tool in listed}
        assert hints.pop("decision_add") == {"title": "Add a question to a decision log", "readOnlyHint": False, "openWorldHint": False,
                                             "destructiveHint": False, "idempotentHint": True}, revision
        assert all(hint["readOnlyHint"] is True and "destructiveHint" not in hint for hint in hints.values()), revision
    assert all("annotations" not in tool for tool in found["2024-11-05"][1])
    assert all(first["instructions"] == tools.WRITING and "decision_add" in first["instructions"] for first, _ in found.values())
    assert said.splitlines()[0].endswith(f"{len(tm.expected_tools()) + 1} tools, one of which writes: decision_add, "
                                                  "into the decision log of a spec")


def test_AC_006_the_readmes_second_pair_of_entries_turns_the_tool_on_and_passes_the_allowlist(tmp_path):
    readme = (tm.EXTENSION / "README.md").read_text(encoding="utf-8")
    listed = [yaml.safe_load(block) for block in re.findall(r"```yaml\n(.*?)```", readme, re.S)]
    configured = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", readme, re.S)]
    assert len(listed) == len(configured) == 2, "the first pair reads only, the second turns the tool on"
    entry, (name, started) = listed[1]["mcp_servers"][0], next(iter(configured[1]["mcpServers"].items()))
    assert entry["name"] == name == "agentic-spec-kit"
    assert (entry["command"], entry["args"]) == (started["command"], started["args"]) == ("python", [tm.INSTALLED, "--root", ".", *WRITE])

    root = tm.new_sample(tmp_path / "project")
    client_file, allowlist = root / ".mcp.json", root / core.KIT_DIR / "tools.yml"
    servers = json.loads(client_file.read_text(encoding="utf-8"))
    servers["mcpServers"][name] = started
    client_file.write_text(json.dumps(servers, indent=2) + "\n", encoding="utf-8", newline="\n")
    held = yaml.safe_load(allowlist.read_text(encoding="utf-8"))
    held["mcp_servers"].append({**entry, "args": [tm.INSTALLED, "--root", "."], "reviewed_by": "pat", "reason": "Agents ask where a gate stands"})
    allowlist.write_text(yaml.safe_dump(held, sort_keys=False), encoding="utf-8", newline="\n")
    assert not core.run_check("CK-TOOL-ALLOWLIST", selftest.context(root)).ok, "the read-only entry does not let the option through"
    held["mcp_servers"][-1] = {**entry, "reviewed_by": "pat", "reason": "Agents leave the questions they meet in the decision log"}
    allowlist.write_text(yaml.safe_dump(held, sort_keys=False), encoding="utf-8", newline="\n")
    assert core.run_check("CK-TOOL-ALLOWLIST", selftest.context(root)).ok

    shop = tm.installed(tmp_path / "shop", "agentic", "agentic-mcp")
    with tm.server(command=[sys.executable, *started["args"]], cwd=shop) as client:
        client.open()
        assert [tool["name"] for tool in client.ask("tools/list")["result"]["tools"]][-1] == "decision_add"
    setup = (tm.EXTENSION / "commands" / "setup.md").read_text(encoding="utf-8")
    assert "--allow-write decision-log" in setup and "decision_add" in setup


def test_AC_007_the_documents_say_where_the_server_writes():
    design = (tm.ROOT / "docs" / "design" / "mcp-server.md").read_text(encoding="utf-8")
    report = (tm.ROOT / "docs" / "phase-reports" / "phase-12-features.md").read_text(encoding="utf-8")
    limits = (tm.ROOT / "docs" / "limits.md").read_text(encoding="utf-8")
    assert "--allow-write decision-log" in design and "mcp-first-write.md" in design
    assert re.search(r"5\. \*\*The MCP server reads only, unless it is started to write into a decision log\.\*\*", report)
    assert "decision_add" in report
    for words in ("decision_add", "cannot tell which agent", "`agentic-mcp`", "product extension"):
        assert words in limits, words


def test_AC_008_the_official_client_lists_the_tool_as_one_that_writes_and_adds_a_proposal(tmp_path):
    if importlib.util.find_spec("mcp") is None:
        pytest.skip("the official `mcp` package for Python is not installed here. `pip install mcp` in a virtual environment of your own runs this test")
    import asyncio

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    root = project(tmp_path / "project")
    started = StdioServerParameters(command=sys.executable, args=[str(tm.SERVER), "--root", str(root), *WRITE])

    def wire(model):  # the message as it went over the line, whatever the client's own names for its fields
        return json.loads(model.model_dump_json(by_alias=True, exclude_none=True))

    async def run():
        async with stdio_client(started) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return wire(await session.list_tools()), wire(await session.call_tool("decision_add", {"spec": NOTES, "question": ASKED}))

    listed, called = asyncio.run(run())
    tool = next(tool for tool in listed["tools"] if tool["name"] == "decision_add")
    assert {key: tool["annotations"][key] for key in ("readOnlyHint", "destructiveHint", "idempotentHint")} == \
        {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True}
    assert not called.get("isError")
    text = called["content"][0]["text"]
    assert text.endswith(tools.NOTICE) and json.loads(text[: -len(tools.NOTICE)])["entry"]["state"] == "proposed"
    assert [entry["title"] for entry in decision_log.entries(selftest.context(root), NOTES)] == [ASKED]
