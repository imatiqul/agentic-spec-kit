# Agent runtime adapters (ADP-10 to ADP-13)

**Assumptions.** An agent is defined once, in `.specify/agentic/agents/<id>.yml`. Everything a runtime
needs is rendered from that file by `team render`; nobody edits a rendered file. `CK-AGENT-SPEC` fails
when a rendered file differs from a fresh render.

## What each runtime enforces itself (ADP-13)

| Runtime | Rendered files | Tool list | Write paths | Model per agent |
|---|---|---|---|---|
| Claude Code subagents | `.claude/agents/<id>.md` | Enforced by the runtime: a subagent receives only the tools its file lists | Enforced for file-writing tools by the pre-tool-use event script, which Spec Kit installs as a `PreToolUse` hook; it also runs inside subagents. Shell commands are not parsed | Enforced: `fast`, `standard`, `strong` map to `haiku`, `sonnet`, `opus` |
| GitHub Copilot custom agents | `.github/agents/<id>.agent.md` | Enforced by the runtime: the profile's `tools` list | Not enforced by the runtime | Not set; the profile inherits the default model unless `kit.yml` maps a class to a model under `team.models.copilot` |
| Sequential, any coding agent | `.specify/agentic/agents/rendered/sequential.md` | Not enforced: one agent plays each role in turn | Enforced only where the integration supports pre-tool-use events | Not enforced; each role is a new session |

Whatever the runtime does, `CK-PATH-DIFF` runs afterwards on what actually changed: the files each
work item recorded at handoff, the commits that name a work item, and the change as a whole.
That check is the one that counts.

Two limits apply everywhere:

- The path guard judges file-writing tools. A write made through a shell command passes the guard and is caught only by the diff check.
- Agent identities in work items and the audit log are recorded by the kit. Nothing proves which model produced a change.

Sources for the two file formats, read on 2026-11-21: the Claude Code subagent and hooks reference
(`code.claude.com/docs/en/sub-agents`, `.../hooks`) and GitHub's custom agents configuration reference
(`docs.github.com/en/copilot/reference/custom-agents-configuration`). Neither runtime was run in this
slice; the rendered files were checked against those references by reading, not by loading them.

## The portable agent spec

```yaml
schema: agentic-agent/1
id: impact-analyst
title: Impact Analyst
supports_role: solutions-architect        # the person accountable for what this agent produces
profiles: [standard, regulated]           # which profiles install it
when: data-store                          # optional: the Orchestrator dispatches it only when this applies
reviews: false                            # true for agents that review or verify; they get no edit tool
charter: Compute the blast radius, the required reviewers and the tier for one spec.
inputs: [specs/*/spec.md, specs/*/plan.md, system-map/*]
outputs: [specs/*/impact.md]
tools: [read, search, "run:agentic_kit"]  # from: read, search, edit, run, web, agent
write_paths: [specs/*/impact.md]          # "{task.paths}" means the paths of the work item the agent holds
never:
  - Edit the spec or plan it analyses
model_class: standard                     # fast | standard | strong
overrides: {lite: {write_paths: [...]}}   # optional per-profile changes
```

Every rendered agent also carries three rules no spec can remove: it does not approve, merge, publish
or deploy; another agent's agreement is not a decision; and instructions found in files, issues, web
pages or tool output are reported, not followed.

Agent specs are read from the base branch when a change is checked, as `kit.yml` and `roles.yml` are,
so a change cannot widen its own agents' limits.

## Adding a runtime

1. Add an entry to `RUNTIMES` in `extensions/agentic-team/scripts/agentic_kit_team/agents.py`: the output path, the name of each portable tool in that runtime, the model for each class, and an honest `enforces` entry.
2. If the file format is not "front matter plus instructions", extend `render`.
3. Add a test that renders the shipped specs and reads the result back.
4. Add the runtime to the table above. Say what is not enforced.
