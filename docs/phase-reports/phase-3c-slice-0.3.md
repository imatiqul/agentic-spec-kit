# Phase 3c — Slice 0.3: the agent team

- **Phase and date:** Phase 3c, 2026-11-21
- **Pinned upstream:** github/spec-kit `v1.4.3`; installed and run against that version
- **Requirement IDs implemented:** AGT-1 to AGT-13, ADP-10 to ADP-13, TRC-6 (all 18 tagged `[0.3]`)
- **Review status:** not reviewed by the owner. On 2026-11-21 the owner asked for the rest of the kit to be built without a stop after each phase. Every decision that would normally have gone to the owner is listed in section 6 so it can be reversed.
- **Assumptions:**
  1. No coding agent is available where this was built, so no model was run. The team's machinery is tested by calling the kit exactly as an agent would.
  2. The file formats for Claude Code subagents and GitHub Copilot custom agents are taken from the vendors' references as read on 2026-11-21.
  3. The person at each gate in the golden tasks is simulated through the file adapter, which exists for tests only.
- **Unverified:** see section 5

## 1. What was built

| Unit | Path |
|---|---|
| Team extension: 3 commands, 1 runtime event | `extensions/agentic-team/` |
| 16 agent specs | `extensions/agentic-team/agents/` |
| Renderers for Claude Code, Copilot and sequential mode | `.../agentic_kit_team/agents.py` |
| Work items, path locks, isolated working copies, rework limit, runs and budgets, the path guard | `.../agentic_kit_team/work.py` |
| 9 checks | `.../agentic_kit_team/checks_team.py` |
| Golden tasks and seeded defects | `.../agentic_kit_team/golden.py` |
| Two workflows | `workflows/agentic-sdd-team/`, `workflows/agentic-sdd-sequential/` |
| Guide: what each runtime enforces (ADP-13) | `docs/adapters/agent-runtime.md` |
| Tests | `tests/test_team.py` (54 tests) |

About 2,100 lines of code. The kit now has 55 checks, the number the Phase 2 design planned for slices 0.1 to 0.3.

### Checks added

| Check | Fails when |
|---|---|
| `CK-AGENT-SPEC` | An agent spec is invalid, has an empty `never` list, a reviewer can edit, the minimum team is incomplete, or a rendered runtime file differs from a fresh render |
| `CK-WORKITEM` | A work item is invalid, makes an illegal move, was handed off without evidence, or was closed by an agent that is not a reviewer |
| `CK-PATH-LOCK` | Two items in progress could edit the same file, or the same migration folder, contract or shared component |
| `CK-PATH-DIFF` | An item recorded a change outside its paths, a commit naming an item changed other files, or a file changed that no work item declares |
| `CK-REWORK-LIMIT` | An item went past two rework rounds, or left an escalation without a decision by a person in `roles.yml` |
| `CK-BUDGET` | A run has no budget, ran past it without stopping, or stopped without a report |
| `CK-AUTHOR-NEQ-VERIFIER` | The same agent authored and reviewed or verified |
| `CK-CRED` | The agent's credential has admin or maintain permission, can push to an unprotected default branch, holds a publishing or workflow scope, or is listed as a person |
| `CK-GOLDEN` | Golden-task results are missing where required, stale against the agent specs, lack a mode, or show a defect that was not caught |

### How the team is held to its limits

1. **One definition, three runtimes.** `team render` writes a Claude Code subagent, a Copilot custom agent and a section of the sequential prompt from each spec. Reviewing agents get no edit tool; the Orchestrator gets none either.
2. **State is in the repository.** One file per task with its history and handoff. An agent that starts cold reads `team brief` and continues.
3. **Path limits at three points.** Before the write, where the runtime has a pre-tool-use event; at handoff, where the kit compares the diff with the item's paths and refuses; and afterwards in CI.
4. **Locks.** An item cannot be claimed while another holds an overlapping path, or the same migration folder, contract or shared component.
5. **Two rework rounds, then a person.** The third return blocks the item and writes both positions for the accountable role. Work resumes only after a person in `roles.yml` records a decision.
6. **Budgets.** A run stops with a report when its steps or minutes are spent.
7. **Gates are unchanged.** Both workflows pause at G1 to G7 through the same `agentic-gate` step as slice 0.1.

## 2. Verification

| What | Result |
|---|---|
| Self-tests | 55 checks, each passing on the sample project and failing on its broken variant |
| Unit tests | 167 pass: 36 core, 15 system map, 62 change packs, 54 team |
| Golden tasks, scripted driver | 4 tasks and 3 seeded defects, in parallel and sequential mode: all pass. Each task is taken through every gate of its profile on a throwaway git copy of the fixture; at each gate nothing is approved until a simulated person reviews |
| Real install | Fresh Standard project on spec-kit 1.4.3 through `scripts/install.sh`: three extensions, both new workflows accepted by upstream's validator, 16 subagent files and 16 Copilot agent files rendered, `team check` passes except `CK-CRED`, which is "not run" without a live repository |
| Event wiring | Spec Kit wrote a `PreToolUse` hook into `.claude/settings.json` from the extension's `events` entry. Hand-written tool calls piped through upstream's own dispatcher were blocked with exit code 2 and a reason, or allowed, as designed |
| Guard cost | About 0.4 seconds per tool call through the dispatcher on this machine |

### Slice 0.3 acceptance checklist (`90-acceptance.md`)

| Criterion | Status | Evidence |
|---|---|---|
| The minimum team of four completes a fixture task end to end, stopping at every gate | Met with stand-ins, not with models | Golden task `minimum-team`: Lite profile, six agent specs installed (the four roles, with three implementer variants), stops at G1, G3, G5 |
| The same task completes in sequential mode with the same gates and evidence | Met with stand-ins | Every golden task passes in both modes with the same gates; `tests/test_team.py::test_golden_tasks_complete_in_both_modes_stopping_at_every_gate` |
| Seeded defects are caught by the reviewer or verifier | Two of three by kit checks; the third only by a scripted rule | Undeclared table touch: `CK-TOUCH`. Breaking contract change: `CK-CONTRACT-BREAK`. Missing tenant filter: a pattern in the stand-in reviewer. No kit check can catch that one; it needs a model's judgement |
| An agent editing outside its declared paths is detected | Met | Guard, handoff refusal and `CK-PATH-DIFF`, each tested |
| A third rework round does not happen; the disagreement is escalated | Met | `test_a_third_rework_round_does_not_happen_the_disagreement_is_escalated` |
| No agent credential can approve, merge, publish or deploy; shown, not asserted | Not met | `CK-CRED` is built and tested on recorded responses. Showing it needs a live repository and token |

## 3. Changes to earlier slices

1. Core: the file and GitHub adapters gained `agent_credential()`. `doctor` now also runs `CK-CRED` when the team extension is installed.
2. Core: domain packs are read from the base branch (approved 2026-11-21), through new `Context.pack()` and `Context.packs()`.
3. `spec/10-governance.md`: GOV-21 widened to cover unmet standing rules (approved 2026-11-21). The project copy is updated.
4. Install scripts add the team extension and the two workflows.

## 4. Deviations from the Phase 2 design

1. **Parallel dispatch does not use upstream's `fan-out` step.** The Orchestrator dispatches through the runtime's own subagents. A task graph unlocks new items as others finish, and one fan-out pass cannot express that without a loop around it.
2. **The working-copy script is not adapted from the community `worktrees` extension.** It is a few lines of `git worktree` written here. No code was copied.
3. **The sequential workflow unrolls the rework limit.** It contains the first review and exactly two rework passes, so a third round cannot be expressed.
4. **Copilot path limits are not claimed.** Upstream maps `pre_tool_use` for Copilot, but how a Copilot hook blocks a call was not verified, so the adapter says "diff check only".

## 5. Unverified

- No coding agent ran. Not the subagent files, not the Copilot agent files, not either workflow end to end, not the `--agent-command` golden driver with a model.
- The golden tasks prove the machinery. They prove nothing about whether a model follows its charter, catches a defect, or stops at a gate.
- `CK-CRED` has not run against GitHub.
- Windows: `work claim --worktree` and the event script (`py` variant) were not run on Windows.
- Everything unverified in slices 0.1 and 0.2 still applies: no live GitHub, no CI run.

## 6. Decisions made without the owner, and how to reverse each

| Decision | Reverse by |
|---|---|
| An item holds its path lock until it is done, including while in review | Remove `in-review` from `LOCKING` in `work.py` |
| Agent specs are read from the base branch when a change is checked | `ag.load(ctx, trusted=False)` in the checks |
| A handoff needs at least one evidence file | Relax `work.handoff` |
| In an isolated working copy the kit commits the agent's work at handoff, with `Work-Item` and `Agent` trailers | Remove the commit in `work.handoff`; `CK-PATH-DIFF` then relies on recorded files only |
| `work integrate` merges an item's branch into the spec branch locally, and refuses on `main`, `master` or the configured default branch | Remove the command; integrate by hand |
| Budget defaults: 200 steps, 240 minutes per run | `team.budget` in `kit.yml` |
| Model classes: reviewers and the Architect `strong`, implementers `standard`, Scribe and Drift Sentinel `fast` | Each agent spec's `model_class` |
| The guard blocks file-writing tools on decision records, the audit log, `roles.yml`, `kit.yml`, agent specs, work items, runs and `CODEOWNERS` for every agent | `PROTECTED` in `work.py` |

## 7. What waits for the owner

1. Run a real agent through one golden task (`golden run --agent-command`), on Claude Code first. This is the first point at which the team is tested with a model.
2. The live GitHub test, which now also covers `CK-CRED`.
3. Review the 16 agent specs: they are the team's job descriptions.
