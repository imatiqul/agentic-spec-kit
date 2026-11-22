# Agent team design

- **Phase and date:** Phase 2 (design), 2026-11-21
- **Requirement IDs covered:** AGT-1 to AGT-13, ADP-10 to ADP-13, QLT-1, TRC-6
- **Assumptions:** the Claude Code integration supports subagents and the runtime events upstream documents; the Copilot custom-agent file format will be confirmed against current documentation in Phase 3c
- **Unverified:** no agent has been run; the Copilot rendering is a design intent only

## Final roster by profile
The 14 agents in `spec/15-agent-team.md` stay. What changes by profile is which are installed.

| Agent | Supports role | Lite | Standard | Regulated |
|---|---|---|---|---|
| Orchestrator | Engineering Manager | ✓ | ✓ | ✓ |
| Spec Author | Product Owner | ✓ | ✓ | ✓ |
| Implementer (backend, frontend, AI variants) | Backend, Frontend, AI Engineer | ✓ | ✓ | ✓ |
| Independent Verifier | QA | ✓ | ✓ | ✓ |
| Architect | Solutions Architect | | ✓ | ✓ |
| Impact Analyst | Solutions Architect | | ✓ | ✓ |
| Test Agent | QA | | ✓ | ✓ |
| Cartographer | Platform | | ✓ | ✓ |
| Scribe | Engineering Manager | | ✓ | ✓ |
| Data Agent | Data Owner | | when a data store is touched | ✓ |
| Contract Agent | Platform | | when a contract or shared component is touched | ✓ |
| Security & Compliance Reviewer | Security & Compliance | | by tier | ✓ |
| Release Agent | DevOps/SRE | | ✓ | ✓ |
| Drift Sentinel | DevOps/SRE | | ✓ | ✓ |

In Lite the Orchestrator also does the Scribe's work, and the Spec Author also drafts the plan.

## Who works at each gate
| Stage | Authoring agents | Reviewing agents | Human gate |
|---|---|---|---|
| Spec | Spec Author | Independent Verifier (spec against constitution) | G1 |
| Clarify | Spec Author | — | G2 |
| Plan | Architect, Impact Analyst, Data Agent, Contract Agent | Security & Compliance Reviewer, Independent Verifier | G3 |
| Tasks | Architect | Independent Verifier (tasks against plan) | G4 |
| Implement | Test Agent first, then Implementers in parallel | Security & Compliance Reviewer | G5 |
| Verify | — | Independent Verifier, Drift Sentinel | G6 |
| Release | Release Agent | — | G7 |

The Scribe records each step in the audit log and assembles each evidence bundle. The Orchestrator dispatches and stops at each gate.

## Coordination protocol
1. The Orchestrator reads `tasks.md` and the dependency markers and creates one work item per task.
2. It groups ready items whose `paths` do not overlap and dispatches each group through upstream's `fan-out` step, one working copy per item.
3. An agent sets its item to in-progress, does the work inside its `paths`, writes the handoff block and sets in-review.
4. The reviewer or verifier either accepts (done) or returns it (rework) with findings. `rework_rounds` increments.
5. After two rework rounds the Orchestrator writes an escalation with both positions and stops for the accountable human.
6. When a gate's work items are all done, the Scribe builds the evidence bundle, the Orchestrator runs the checks, and the `agentic-gate` step pauses.

State is only in `.specify/agentic/work/` and the audit log. An agent that starts cold can pick up from those files alone.

## Isolation
| Rule | How it is applied | Limit |
|---|---|---|
| Author is never reviewer or verifier | `CK-AUTHOR-NEQ-VERIFIER` on recorded agent ids | Ids are recorded by the kit, not proven by the runtime |
| Verifier sees only the artifact, spec, constitution and map | Fresh session started with an input manifest; `CK-VERIFY-INPUTS` checks the manifest | The kit cannot inspect a model's context |
| Different model for verification | `model_class` in the agent spec, mapped per runtime | Best effort; not all runtimes expose model choice |
| Tool and path limits | Runtime adapter renders allow-lists; a pre-tool-use event script denies writes outside `write_paths` where the integration supports events; `CK-PATH-DIFF` always runs afterwards | Native denial only where events exist |
| No approval-capable credentials | `CK-CRED` inspects the token in use | Cannot rule out other credentials on the machine |
| Untrusted input | Every agent spec carries the rule; the Orchestrator logs reported instructions | Tested adversarially only in slice 0.4 |

## Runtime adapters
| Runtime | Rendered from the agent spec | Tools enforced | Paths enforced |
|---|---|---|---|
| Claude Code | One subagent file per agent, with its tool list | Natively | By event script, then diff check |
| Copilot | One custom agent file per agent | To be confirmed in Phase 3c | Diff check |
| Sequential | One prompt section per role, run in order by `agentic-sdd-sequential`; a new session for the verifier | No | Diff check |

Rendered files are generated and checked for drift by `CK-AGENT-SPEC`. People edit the agent spec, never the rendered file.

## Golden tasks (AGT-13)
Run on `fixtures/multi-app/` in both modes:
1. Add a field to the shared library's public type. Expected: consumer matrix runs, both service owners added as reviewers.
2. Add a column to the shared database. Expected: data-change plan required, shared-store flag raised.
3. Change the external API stub's contract. Expected: breaking change detected.

Seeded defects the reviewing agents must catch: an undeclared table touch, a breaking contract change described as additive, and a query missing its tenant filter.

## What reuses upstream and what is new
- **Reused:** `fan-out` and `fan-in` for dispatch, `command` and `prompt` steps to invoke agents, workflow `resume`, runtime events for the agent boundary, the `[P]` marker as the starting point for parallelism.
- **Adapted (with attribution):** scripted worktree creation from the community `worktrees` extension.
- **New:** agent spec and renderers, work items and their state machine, path locks, rework limit, the gate step.
