# agentic-team (slice 0.3 — the agent team)

Sixteen agents defined once and rendered for Claude Code, GitHub Copilot, or one agent playing each role in turn.
Work is tracked in the repository, not in any agent's memory. Gates stay with people.
Requires `agentic`. Works on every profile; Lite installs the minimum team (Orchestrator, Spec Author, implementers, Independent Verifier).

```bash
A="python .specify/extensions/agentic/scripts/agentic.py"
specify extension add --dev path/to/agentic-spec-kit/extensions/agentic-team
$A team init --runtimes claude,copilot,sequential   # agent specs into .specify/agentic/agents/, runtime files rendered
$A team list                                        # the agents, and what each runtime enforces
$A work create --spec <spec>                        # one work item per open task
$A work list --spec <spec> --ready                  # what can start now; items in a group may run together
$A work claim --spec <spec> --item T001 --agent backend-implementer --worktree
$A work handoff --spec <spec> --item T001 --agent backend-implementer --done "..." --evidence <file>
$A work review --spec <spec> --item T001 --by independent-verifier --accept     # or --return "<finding>"
$A work integrate --spec <spec> --item T001
$A team check
```

Workflows: `agentic-sdd-team` (the Orchestrator dispatches each stage's agents) and `agentic-sdd-sequential`
(one role per step, each step a new session). Both pause at G1 to G7 through the `agentic-gate` step.

## What the kit holds agents to

| Rule | How |
|---|---|
| An agent changes only the files of the work item it holds | The path guard blocks the write where the runtime has pre-tool-use events; `work handoff` refuses; `CK-PATH-DIFF` checks afterwards |
| No two agents edit the same file, migration folder, contract or shared component | `work claim` refuses; `CK-PATH-LOCK` |
| The author never reviews its own work | `work review` refuses; `CK-AUTHOR-NEQ-VERIFIER` |
| At most two rework rounds | The third return blocks the item and writes an escalation with both positions for the accountable person; `CK-REWORK-LIMIT` |
| Every run has a budget | `orchestrate step` stops the run with a report when steps or minutes run out; `CK-BUDGET` |
| Agent steps are on the record | Each step and state change is an entry in the hash-chained audit log: which agent, on whose behalf, inputs and outputs |
| The agent's credential cannot approve, merge past protection, publish or deploy | `CK-CRED`, also run by `doctor` |
| Runtime files match the specs | `CK-AGENT-SPEC` |

## Golden tasks

`$A golden run --fixture fixtures/multi-app` takes four tasks through every gate and plants three defects, in parallel
and sequential mode, on throwaway copies of the fixture. The default driver is a scripted stand-in: it proves the
machinery end to end and nothing about a model's judgement. `--agent-command "<command>"` runs a real coding agent
for each implementation and review step instead; that path has not been run with a model.

## Limits

- No coding agent was run in this slice. The rendered agent files, both workflows and the event wiring were installed on Spec Kit 1.4.3, and the event script was driven with hand-written tool calls.
- The path guard does not parse shell commands.
- Agent identities are recorded, not proven.
- `CK-CRED` sees the credential the kit runs with, not every credential on the machine.
