# Phases — order of work

This file says when and in what order. It adds no requirements; it cites IDs from
`spec/`. `00-charter.md` and `01-working-rules.md` are always loaded.

| Phase | Output | Stop |
|---|---|---|
| 0 | Upstream and community audit | End |
| 1 | Findings verification and discovered system map | End |
| 2 | Design of all four slices | End |
| 3a | Build slice 0.1 | End |
| 3b | Build slice 0.2 | End |
| 3c | Build slice 0.3 | End |
| 4 | Reference constitution | End (this is gate G0) |
| 5 | Reference spec backlog | After each tier batch |
| 6 | Plans, tasks, impact reports, data-change plans | End |
| 7 | C4 walkthrough | At every gate |
| 8 | Role guide and verification of 0.1–0.3 | End |
| 9 | Build slice 0.4 and apply it to the reference | After each group |
| 10 | Final verification and release notes | End |

Hard order: no toolkit code before Phase 2 is approved; no specs before Phase 1 is
approved; no slice 0.4 code before Phase 8 is approved.

---

## Phase 0 — Audit
Loads: `spec/16-adapters.md` (ADP-1, ADP-2); skim the other spec files for the
capability list.
1. Read the pinned spec-kit release: core commands, integrations, extensions,
   presets, bundles, workflows, workflow steps, hooks, catalogs.
2. Survey the official and community catalogs. Evaluate at least these candidates,
   confirm each still exists, and add any missed:
   - Orchestration: MAQA, Fleet Orchestrator, Conduct, Agent Assign, Multi-Model
     Review, Spec Kit Schedule, Worktrees, Worktree Isolation
   - Cross-repo and cross-spec: Multi-Repo Branch Sync, Shared Knowledge, Spec
     Orchestrator, Epic, Explicit Task Dependencies preset
   - Contracts and data: API Evolve, Data Model Diagram, Azure Cosmos DB
   - Architecture and impact: Architecture Guard, Blueprint Index, Repository Index,
     Ripple, What-if Analysis, Architect Impact Previewer
   - Brownfield: Brownfield Bootstrap, BrownKit, Time Machine, Spec Kit Discovery
   - Gates, verification, traceability, drift: Plan Review Gate, CI Guard, Quality
     Gates, Verify, Verify Tasks, Spec Trace, V-Model, Spec Sync, Reconcile
   - Security: ThreatSpec, AttackTree, Security Review, Red Team, Architecture
     Governance preset
   - Agent operations: MemoryLint, Optimize, Agent Parity Governance preset, Golden
     Demo
   - Trackers and accessibility: GitHub Issues and Azure DevOps integrations, A11Y
     Governance preset
   For each: what its code does (not its description), licence, last release,
   maintenance signals, whether a human gate can be bypassed, and a verdict: depend
   on, adapt with attribution, or build.
3. Gap table keyed by requirement ID: requirement | upstream today | community
   component | reuse, extend or build | delivery vehicle | reason.
4. Recommend one delivery shape with trade-offs: fork, extension + preset + bundle,
   or hybrid.
Output: audit report, gap table, recommendation.

## Phase 1 — Verify and map
Loads: `reference/20-healthq.md`, `spec/12-system-map-and-impact.md` (MAP-1 to
MAP-5, MAP-15).
1. Check every finding against the repo at a recorded commit SHA. Status:
   confirmed, corrected, stale or false. Corrected findings carry the corrected
   statement forward. False and stale findings are dropped with a note.
2. Derive Low findings, at most 10.
3. Discover the system map; mark every node and edge derived or assumed.
Output: verification report, draft system map.

## Phase 2 — Design
Loads: all of `spec/`.
Design all four slices before building any: schemas (roles, gates, decisions,
waivers, profile, IDs, system map, work items, agent spec, audit log), check list
with the requirement each enforces, adapter interfaces, command list, final agent
roster, and which community components are used where.
Output: architecture document, schemas, a requirement-to-component table. Flag any
requirement that cannot be enforced and say what it degrades to.

## Phase 3a / 3b / 3c — Build slices 0.1, 0.2, 0.3
Loads: the spec files containing that slice's tagged requirements, plus
`spec/16-adapters.md`.
Build every requirement tagged with the slice. Build the fixture (charter D8) in 3b.
Each check ships with passing and failing fixtures (TRC-17).
Output per slice: code, self-test results, docs, install path, and the slice's
acceptance checklist from `90-acceptance.md` filled in with evidence.

## Phase 4 — Constitution (G0)
Loads: `reference/20-healthq.md`, `spec/10-governance.md` (GOV-11).
Draft the reference constitution. Every principle is machine-checked or marked
human-judged.

## Phase 5 — Spec backlog (G1, G2)
Loads: `reference/20-healthq.md`, `spec/12-system-map-and-impact.md`.
One spec per confirmed or corrected finding. Submit in four batches: Critical,
High, Medium, Low.

## Phase 6 — Plans and tasks (G3, G4)
Loads: `reference/20-healthq.md`, `spec/12`, `spec/13`.
For C1–C6: plan, task list, impact report. H5: data-change plan. C2: impact report
and programme-spec breakdown only.

## Phase 7 — C4 walkthrough
Loads: `reference/20-healthq.md` (walkthrough scope), `spec/15-agent-team.md`.
Run C4 through G1–G7 with the agent team, stopping at each gate.
- G5: implement on a feature branch, build and run tests, open a draft PR.
- G6: independent verification attached to the PR.
- G7: evidence bundle prepared; decision pending.
Output: every gate decision, the run log (which agent did what, each handoff, each
rework round), and the trace from changed lines to principles and to affected nodes.

## Phase 8 — Guide and verification of 0.1–0.3
Loads: `90-acceptance.md`.
Write the per-role, per-profile day-to-day guide. Generate the traceability matrix.
Run the acceptance checklists for slices 0.1–0.3 and report gaps.

## Phase 9 — Build slice 0.4 and apply it
Loads: the spec files containing `[0.4]` requirements, `reference/20-healthq.md`
(showcases table).
Build in this order, stopping after each group:
1. Lanes and amendments (GOV-12, GOV-17 to GOV-20)
2. Security and privacy (QLT-3 to QLT-6)
3. Test depth (QLT-7 to QLT-11)
4. AI systems (QLT-13 to QLT-19)
5. Infrastructure, release and operability (CHG-16, CHG-17, CHG-19 to CHG-21, QLT-20)
6. Feedback loops and debt (QLT-21, QLT-22, MAP-16, TRC-12)
7. Agent operations (AGT-14 to AGT-18, TRC-13)
8. Integrations and reporting (TRC-15, TRC-16, ADP-16)
After each group, apply it to the showcase findings it covers.

## Phase 10 — Final
Loads: `90-acceptance.md`.
Run every acceptance checklist. Produce a sample auditor evidence pack for the C4
change, release notes per slice, and a list of everything the kit does not enforce.
