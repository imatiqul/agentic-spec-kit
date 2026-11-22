# agentic-spec-kit

> **Status: pre-alpha, public.** All six slices (0.1 to 0.6) are built: 105 checks, each with a passing and a failing fixture.
> Nothing has been run against a live GitHub repository, a real coding agent, or a live tracker or chat service yet. The
> reference example has an approved constitution (Phase 4, now version 2) and twenty-five specs (Phase 5): sixteen approved at gates G1 and G2, in conversation and not yet by a pull-request review, and nine drafts that wait at those gates. Six of the specs have a draft plan (Phase 6). Do not rely on any of this for real work.
> `docs/limits.md` lists what the kit does not do.
>
> The owner decided on 2026-11-22 to keep this repository public. Charter decision D2 says so, as updated on his approval.

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
| `docs/design/` | Phase 2 design: architecture, schemas, check catalogue, agent team, source review, requirement map. Also the comparison with other spec-driven tools, and `requirement-map-as-built.md`: every requirement and the checks that enforce it today. |
| `docs/adapters/` | How each adapter works and how to add one: engines, contract formats, agent runtimes, domain packs, trackers, pipelines. |
| `extensions/agentic/` | Slice 0.1: the check CLI, commands, templates and the CI workflow. Slice 0.4: the fast and emergency lanes, amendments, the reviewer's one page, report views and the auditor evidence pack. |
| `extensions/agentic-system/` | Slice 0.2: system map, discovery, impact analysis, and change packs for data stores, contracts, shared components, external services and the supply chain. |
| `extensions/agentic-team/` | Slice 0.3: sixteen agents rendered per runtime, work items, path locks, rework limit, run budgets, golden tasks. Slice 0.4: a context pack per task, an allowlist of tool servers, a record of every step (model, inputs, tools, cost), a routing policy with spend limits, a golden baseline, planted-instruction tests and a lint of instruction files. |
| `extensions/agentic-quality/` | Slice 0.4: quality packs for security, privacy, test depth, AI systems, release and feedback. |
| `extensions/agentic-product/` | Slice 0.5: intake records, requirement linting, living capability specs fed by deltas, duplicate detection decided by a person, outcomes, lineage. |
| `extensions/agentic-connect/` | Slice 0.6: requirements from Azure DevOps, Jira, ClickUp, GitHub and documents; pipelines for GitHub Actions, Azure Pipelines and GitLab CI; notifications to Slack, Teams, email and the work item. |
| `fixtures/multi-app/` | Two services, a shared library, a shared database and an external API, for cross-application tests. |
| `extensions/agentic-hipaa/` | HIPAA domain pack (an engineering aid, not legal advice). |
| `presets/`, `steps/`, `workflows/`, `bundles/` | Profile presets, the `agentic-gate` step, the lifecycle workflow, bundle manifests. |
| `scripts/` | Install scripts for bash and PowerShell. |
| `tests/` | Unit tests. Self-tests live in the CLI: `agentic.py selftest`. |
| `docs/install.md`, `docs/admin-setup.md` | How to install, and what an administrator must configure. |
| `docs/guide/roles.md` | What each role approves, what they look at, and where. |
| `docs/limits.md` | What the kit does not enforce, cannot see, and has never been run against. Read this before relying on anything. |
| `docs/release-notes.md` | What each slice contains. Nothing has been released. |
| `examples/healthq/` | Reference example: the Phase 1 findings script and draft map, the approved constitution (`phase-4/`), and `project/`: the reference as a project the kit checks, with its system map and specs. `overlay.py` lays it over a clone of the healthcare repo, and `export.py` writes it as it goes into that repo. No source code from that repo is copied here. |
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
| 3d | Build slices 0.5 and 0.6, and part of 0.4 | Built, 2026-11-22. Its decisions 1 to 20 approved by the owner, 2026-11-22 ("Needs you: approve"). See `docs/phase-reports/phase-3d-truth-connect-depth.md` |
| 3e | Build the rest of slice 0.4; role guide, limits, release notes | Built, 2026-11-22. Its decisions 21 to 35 approved by the owner, 2026-11-22 ("Needs you: approve"). See `docs/phase-reports/phase-3e-slice-0.4.md` |
| 4 | Reference constitution | Approved by the owner at gate G0, 2026-11-22 ("Needs you: approve"), as drafted. `examples/healthq/phase-4/`; `docs/phase-reports/phase-4-constitution.md` |
| 5 | Reference specs, in four batches by tier | Batch 1 (Critical: C1 to C6, N1, N2) approved by the owner at G1 and G2, 2026-11-22 ("G1: yes", "G2: approve"), with four clinical conditions for G3. See `docs/phase-reports/phase-5-batch-1-critical.md`. Batch 2 (High: H1 to H6, N3, N4) approved the same day ("Batch 2, waiting on you: go ahead"); see `docs/phase-reports/phase-5-batch-2-high.md`. Batch 1 is merged into the healthcare repo's `main` (pull request #72). Batches 3 and 4 (Medium and Low: M1 to M5, N6 to N10) are drafted and wait at G1 and G2; see `docs/phase-reports/phase-5-batch-3-4-medium-low.md` |
| 6 | Plans and tasks for C1 and C3 to C6, a data-change plan for H5, a breakdown of C2 | Drafted, 2026-11-22; they wait at G3 and G4. The kit's gate check fails on them, as it should: no pull-request review has approved a gate. Planning corrected one Phase 1 finding and the map, and found nine things in the code that Phase 1 had not. See `docs/phase-reports/phase-6-plans.md` |
| 7 | C4 walkthrough | Not started |
| 8–10 | The halves that need the reference: acceptance of the reference example, slice 0.4 applied to the showcase findings, a sample evidence pack for the C4 change | Not started; they need Phases 5 to 7 |

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
- Agents never merge, mark a pull request ready, or approve. Since 2026-11-22 an agent may commit and push a change the owner has approved (charter D4); before that the owner committed each phase's work to `main` himself. Nothing has gone through a pull request yet, because no live GitHub test has been run.
- No real personal or health data, and no secrets.
- Upstream is pinned at spec-kit `v1.4.3`.

## Licence
MIT. See `LICENSE` and `NOTICE.md`.
