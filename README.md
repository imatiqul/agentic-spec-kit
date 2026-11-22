# agentic-spec-kit

> **Status: pre-alpha, private.** Phases 0 and 1 are complete; no toolkit code exists
> yet. This repository must stay private until the reference findings are fixed or
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
| `examples/healthq/` | Reference example: draft system map and the script that reproduces the Phase 1 findings. No source code from the reference repo is copied here. |
| `NOTICE.md` | Upstream and community attribution. |

## Progress

| Phase | Output | State |
|---|---|---|
| 0 | Upstream and community audit | Approved 2026-11-21 |
| 1 | Findings verification and system map | Awaiting approval |
| 2 | Design of all four slices | Not started |
| 3a–3c | Build slices 0.1, 0.2, 0.3 | Not started |
| 4–7 | Reference constitution, specs, plans, C4 walkthrough | Not started |
| 8–10 | Guide, slice 0.4, final verification | Not started |

## Release slices

| Slice | Name | Contains |
|---|---|---|
| 0.1 | Govern | Roles, gates, enforcement, risk tiers, profiles, waivers, traceability, audit log |
| 0.2 | System | System map, impact analysis, change packs |
| 0.3 | Team | Agent team, coordination, sequential fallback |
| 0.4 | Depth | Change lanes, quality packs, agent operations, integrations |

## Working rules for this repository
- No commits to `main` after the initial commit; work on feature branches and open draft pull requests.
- No real personal or health data, and no secrets.
- Upstream is pinned at spec-kit `v1.4.3`.

## Licence
MIT. See `LICENSE` and `NOTICE.md`.
