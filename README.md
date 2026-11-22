# agentic-spec-kit

> **Status: pre-alpha, private.** Slices 0.1, 0.2, 0.3, 0.5 and 0.6 are built; slice 0.4 is built in part.
> Nothing has been run against a live GitHub repository, a real coding agent, or a live tracker or chat service yet. This repository must stay private until the reference findings are fixed or
> the owner decides otherwise (charter D2).

An Agentic Specification-Driven Development toolkit that builds on
[github/spec-kit](https://github.com/github/spec-kit). Agents draft, build and
verify. Named humans approve at every gate. Nothing advances on an agent's say-so.

A change is treated as a change to a system: every spec knows which data stores,
shared components, contracts and other applications it touches, who owns them, and
who must approve.

## Where things are

| Path | What it is |
|---|---|
| `docs/prompts/` | The specification of the kit and the plan for building it. Start with `docs/prompts/README.md`. |
| `docs/prompts/00-charter.md` | Mission, non-goals, owner decisions and the decision log. |
| `docs/prompts/spec/` | Requirements by concept, each with an ID and a release slice. |
| `docs/prompts/30-phases.md` | Order of work and stop points. |
| `docs/phase-reports/` | Evidence from each completed phase. |
| `docs/design/` | Phase 2 design: architecture, schemas, check catalogue, agent team, source review, requirement map. Also the comparison with other spec-driven tools. |
| `docs/adapters/` | How each adapter works and how to add one: engines, contract formats, agent runtimes, domain packs, trackers, pipelines. |
| `extensions/agentic/` | Slice 0.1: the check CLI, commands, templates and the CI workflow. |
| `extensions/agentic-system/` | Slice 0.2: system map, discovery, impact analysis, and change packs for data stores, contracts, shared components, external services and the supply chain. |
| `extensions/agentic-team/` | Slice 0.3: sixteen agents rendered per runtime, work items, path locks, rework limit, run budgets, golden tasks. Slice 0.4: a context pack per task and an allowlist of tool servers. |
| `extensions/agentic-quality/` | Slice 0.4: quality packs for security, privacy, test depth, AI systems, release and feedback. |
| `extensions/agentic-product/` | Slice 0.5: intake records, requirement linting, living capability specs fed by deltas, duplicate detection decided by a person, outcomes, lineage. |
| `extensions/agentic-connect/` | Slice 0.6: requirements from Azure DevOps, Jira, ClickUp, GitHub and documents; pipelines for GitHub Actions, Azure Pipelines and GitLab CI; notifications to Slack, Teams, email and the work item. |
| `fixtures/multi-app/` | Two services, a shared library, a shared database and an external API, for cross-application tests. |
| `extensions/agentic-hipaa/` | HIPAA domain pack (an engineering aid, not legal advice). |
| `presets/`, `steps/`, `workflows/`, `bundles/` | Profile presets, the `agentic-gate` step, the lifecycle workflow, bundle manifests. |
| `scripts/` | Install scripts for bash and PowerShell. |
| `tests/` | Unit tests. Self-tests live in the CLI: `agentic.py selftest`. |
| `docs/install.md`, `docs/admin-setup.md` | How to install, and what an administrator must configure. |
| `examples/healthq/` | Reference example: draft system map and the script that reproduces the Phase 1 findings. No source code from the reference repo is copied here. |
| `NOTICE.md` | Upstream and community attribution. |

## Progress

| Phase | Output | State |
|---|---|---|
| 0 | Upstream and community audit | Approved 2026-11-21 |
| 1 | Findings verification and system map | Complete; proceeded on the owner's go-ahead, 2026-11-21 |
| 2 | Design of all four slices | Approved by the owner, 2026-11-21 |
| 3a | Build slice 0.1 | Approved by the owner, 2026-11-21; live GitHub test skipped |
| 3b | Build slice 0.2 | Approved by the owner, 2026-11-21 (both parts) |
| 3c | Build slice 0.3 | Built, 2026-11-21. Not reviewed by the owner: on that date the owner asked for the rest of the kit to be built without a stop after each phase |
| 3d | Build slices 0.5 and 0.6, and part of 0.4 | Built, 2026-11-22. Not reviewed by the owner. See `docs/phase-reports/phase-3d-truth-connect-depth.md` |
| 4–7 | Reference constitution, specs, plans, C4 walkthrough | Not started |
| 8–10 | Guide, the rest of slice 0.4, final verification | Not started |

## Try it
```bash
pip install pyyaml pytest
python extensions/agentic/scripts/agentic.py selftest     # every check fails on its broken fixture
python -m pytest tests -q
```
See `docs/install.md` to install it into a Spec Kit project.

## Release slices

| Slice | Name | Contains |
|---|---|---|
| 0.1 | Govern | Roles, gates, enforcement, risk tiers, profiles, waivers, traceability, audit log |
| 0.2 | System | System map, impact analysis, change packs |
| 0.3 | Team | Agent team, coordination, sequential fallback |
| 0.4 | Depth | Change lanes, quality packs, agent operations, integrations |
| 0.5 | Truth | Intake, requirement quality, living capability specs, duplicates, outcomes, lineage |
| 0.6 | Connected | Tracker sources, pipelines, notifications |

Slices 0.5 and 0.6 were added at the owner's request on 2026-11-21 and are not yet in the charter. `docs/design/competitive-gap-analysis.md` says why they exist and what is still missing.

## Working rules for this repository
- No commits to `main` after the initial commit; work on feature branches and open draft pull requests.
- No real personal or health data, and no secrets.
- Upstream is pinned at spec-kit `v1.4.3`.

## Licence
MIT. See `LICENSE` and `NOTICE.md`.
