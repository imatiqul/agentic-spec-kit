# The MCP server's first tool that writes: a question into a decision log

- **Phase and date:** Phase 12, after the live test on HealthQCopilot; 2026-11-28 (UTC)
- **Upstream and reference:** github/spec-kit `v1.4.3`; `docs/design/mcp-server.md` (MCP-1 to MCP-21); `docs/design/decision-log.md` (DEC-1 to DEC-18)
- **Requirement IDs covered:** MCW-1 to MCW-8, new with this document. They add one tool to the server, and change no check and no rule. The tool allowlist (AGT-20, `CK-TOOL-ALLOWLIST`) judges the launch that turns the tool on as it judges any other
- **Assumptions:**
  1. The Phase 12 report lists, as decision 5 that is the owner's to change: "The MCP server only reads. A tool that adds a question to a decision log would be the first that writes, and needs a spec of its own." On 2026-11-28 the owner said to build it. This is that spec.
  2. The tool adds a question the way a question left at a hand-off is added (DEC-18): as a proposal, through `decision_log.propose`. A proposal decides nothing. What counts is the approval of G5 with the log in its evidence, as `docs/design/decision-log.md` says.
  3. A coding agent that has the server can usually write files in the same checkout. The tool gives it a way that keeps the log's form and adds a line to the audit log; it gives it no power it did not have.
- **Unverified:** no MCP client such as Claude Code, GitHub Copilot or Cursor has called the tool. The tool hints and their defaults are taken from the official `mcp` package for Python, 2.3.0 (`mcp.types.ToolAnnotations`, read on 2026-11-28), and not from the specification's pages

## Why

An agent that meets a question the spec does not answer should leave it for a person, and not decide it in code. The kit has a place for such a question: the change's decision log, where a question an agent leaves becomes a proposal that a person decides. Through the MCP server an agent could read the log, and not add to it.

## Requirements

| ID | Requirement |
|---|---|
| MCW-1 | The server lists a tool that writes only where it is started with `--allow-write decision-log`. Started without it, it is what it was: the same tools, each with the hint that it reads only, the same instructions, and the same line on standard error. The option takes one word, `decision-log`. Any other word ends the server with 2 and one line on standard error, before anything is read or listed. |
| MCW-2 | With the option, `tools/list` names one more tool, `decision_add`, after the others. Its arguments: `spec`; `question`, from 1 to 500 characters; and `affects`, optional, up to 20 ids of requirements, tasks or criteria, each of them one name of up to 60 characters. It adds the question to the spec's decision log, `specs/<spec>/decision-log.yml`, as an entry in the state `proposed`, through the kit's own `decision_log.propose`. A log that does not exist yet is made. |
| MCW-3 | The entry names `agentic-mcp` under `proposed_by`, and the spec's audit log gets one entry, `decision-log.add`, whose actor has the type `agent` and the id `agentic-mcp`. The tool never writes an outcome, an owner or a day, and never changes an entry that is there. A question the log holds already, in the same words with case and spaces aside, is not added again, and nothing is written: the answer gives that entry as it is. |
| MCW-4 | The tool refuses, and writes nothing, for: a spec the project does not have; a question that is empty, longer than 500 characters or holds a control character; an id under `affects` that is not one name, or that names a requirement or a task the spec does not have (DEC-13); and any question while gate G5 of the spec is approved, because an entry added then opens G5 again, which is a person's call. Where the product extension is there, the question is screened as an incoming request is (`intake.screen`, with the project's own patterns), and a question in which the screen finds anything is refused, naming what it found. A log that is not a decision log is refused with the kit's own words. A refusal is a tool result marked as an error (MCP-18). |
| MCW-5 | The tool writes the log and the spec's audit log, in the working copy, and nothing else: no other file, no bytecode, no commit. A log or an audit log that a link leads out of the project is refused (MCP-18). The answer says that the entry is a proposal, that it decides nothing, that a person decides it with `agentic.py decision decide`, and that the change is in the working copy until someone commits it. It ends with the fixed line of MCP-19. |
| MCW-6 | Under each revision that has tool annotations (2025-03-26 and later), `decision_add` carries `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: true` and `openWorldHint: false`; the other tools keep `readOnlyHint: true`. With the option the instructions say that one tool writes and what it writes, and the line on standard error says so where it said "read-only". |
| MCW-7 | The README gives a second pair of entries, for `tools.yml` and for the client's configuration, with `--allow-write decision-log` in `args`. `CK-TOOL-ALLOWLIST` compares the two word for word, so a project turns the tool on in a reviewed change of `tools.yml`, as for any launch that is new. The setup command says so. |
| MCW-8 | `docs/design/mcp-server.md` (MCP-20 and "What it will not do"), the Phase 12 report (decision 5) and `docs/limits.md` say that the server writes where it is started with the option, and then only into a decision log. The limits say that the kit cannot tell which agent called the tool, that every entry it adds names `agentic-mcp`, and that the question is screened only where the product extension is there. |

## Acceptance criteria

- **AC-001** (verifies MCW-1): Given the server started without the option, Then the tools, their hints, the instructions and the line on standard error are what they were. Given `--allow-write` with another word, Then the server ends with 2, says why in one line on standard error, and writes nothing to standard output.
- **AC-002** (verifies MCW-2, MCW-3): Given the option, Then `decision_add` is listed last. Called with a question and `affects: [FR-001]`, Then the log holds one more entry, in the state `proposed`, with `proposed_by: agentic-mcp`, that `affects` and no outcome, owner or day; the audit log holds one more entry, `decision-log.add`, by an agent named `agentic-mcp`; and `CK-DECISION-LOG` passes. Called again with the same question, with other case and spaces, Then the answer gives the same entry and says that nothing was added, and the two files are byte for byte what they were. Given a spec with no log, Then the log is made.
- **AC-003** (verifies MCW-4): Given each of: a spec the project does not have, `..` as the spec, a question of 501 characters, a question with a control character, `affects: [FR-999]`, `affects: [../x]`, a question that holds an e-mail address, and a spec whose G5 is approved, Then the tool refuses, the answer says what was wrong, and the project is byte for byte what it was.
- **AC-004** (verifies MCW-5): Given a call that adds an entry, Then the project differs from before in the log and the audit log alone, and the answer says "proposal", "decides nothing", `agentic.py decision decide` and "working copy". Given a log that a link leads out of the project, Then the tool refuses and the file it leads to is unchanged.
- **AC-005** (verifies MCW-6): Under 2025-03-26 and later, Then `decision_add` has the four hints of MCW-6 and every other tool `readOnlyHint: true`; under 2024-11-05 no tool has annotations. Then the instructions name `decision_add`, and the line on standard error says that one tool writes.
- **AC-006** (verifies MCW-7): Then the README's second pair of entries have the same `command` and `args`, `args` holds `--allow-write decision-log`, a project with both passes `CK-TOOL-ALLOWLIST`, and the server started with those `args` lists `decision_add`. Then the setup command names the option.
- **AC-007** (verifies MCW-8): Then the three documents say what MCW-8 says.
- **AC-008** (verifies MCW-2, MCW-6): Where the official `mcp` package for Python is installed, Then its client lists `decision_add` with the hint that it does not only read, and calling it adds a proposal.

## What this does not do

- Decide, supersede or change an entry. A person does that with `agentic.py decision`, and G5's approval counts it.
- Tell which agent called. Every entry it adds names the server, `agentic-mcp`.
- Commit. The log changes in the working copy, where the person or the agent commits it with the rest of the change.
- Write anything but a decision log. A second tool that writes needs a spec of its own.

## Sources

1. `docs/phase-reports/phase-12-features.md` of this repository, "Decisions that are the owner's to change", decision 5.
2. The official `mcp` package for Python, version 2.3.0: `mcp.types.ToolAnnotations` and its comments, which give each hint with its default (`readOnlyHint` false, `destructiveHint` true, `idempotentHint` false, `openWorldHint` true). Read on 2026-11-28 in the package installed for the kit's test AC-019.
