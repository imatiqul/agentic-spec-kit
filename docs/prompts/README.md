# agentic-spec-kit prompt set (v5)

This replaces the single v4 prompt. Each file owns one concern and changes for one
reason. Nothing is stated twice; files point to each other by requirement ID.

## Files and what each one owns

| File | Concern | Answers | Changes when |
|---|---|---|---|
| `00-charter.md` | Purpose and owner decisions | Why, for whom, what is out of scope, what I decided | I change my mind |
| `01-working-rules.md` | Behaviour of the agent running the work | How to act, when to stop, what never to do | Trust or safety boundaries change |
| `spec/10-governance.md` | Who decides | Roles, gates, tiers, profiles, lanes, waivers, amendments | The decision model changes |
| `spec/11-traceability-and-audit.md` | What is recorded | IDs, links, audit log, drift, metrics, reports | Evidence needs change |
| `spec/12-system-map-and-impact.md` | What exists and what a change reaches | Map, discovery, impact analysis, cross-spec control | The dependency model changes |
| `spec/13-change-packs.md` | Rules for changing a kind of thing | Data stores, contracts, shared components, external apps, supply chain, infrastructure, release | A kind of change needs new rules |
| `spec/14-quality-packs.md` | How deep the checking goes | Security, privacy, test depth, AI governance, operability, feedback loops | Quality bar changes |
| `spec/15-agent-team.md` | Who does the work | Roster, coordination, isolation, agent operations | The team design changes |
| `spec/16-adapters.md` | Vendor- and technology-specific bindings | GitHub, database engines, agent runtimes, HIPAA, trackers | A platform is added or changes |
| `reference/20-healthq.md` | The system used as proof | Stack, constitution topics, findings, showcases | The healthcare repo changes |
| `30-phases.md` | Order of work | What to do in each phase, what to load, where to stop | The plan changes |
| `90-acceptance.md` | How we know it is done | Acceptance per release slice and overall | The bar for done changes |

## Separation rules (keep these true when editing)
1. **Policy, mechanism, binding.** `spec/10`–`15` state rules and the checks that
   enforce them in neutral terms. Product and vendor names appear only in
   `spec/16-adapters.md`.
2. **Kit versus example.** `spec/` never mentions the healthcare system.
   `reference/` never adds a kit requirement; it only says which requirements the
   example exercises.
3. **What versus when.** `spec/` has no phases or ordering. `30-phases.md` has no
   requirements of its own; it cites IDs.
4. **Concept versus release slice.** Files are organised by concept. Each
   requirement carries a slice tag `[0.1]`–`[0.4]` saying when it ships.
5. **Human versus agent.** Decisions that are mine live in `00-charter.md`. An
   agent may propose a change to them but never edits that file.
6. **Dependency direction.** phases → spec → charter. reference → spec. Nothing
   in `spec/` depends on phases or reference.

## How to run
Give the agent this, one phase at a time:

> Read `docs/prompts/00-charter.md` and `docs/prompts/01-working-rules.md` in full. Then run
> Phase N from `docs/prompts/30-phases.md`, loading only the files that phase lists.
> Stop where the phase says stop.

## What changed from v4 besides the split
- Adoption profiles and waivers moved into slice 0.1. Every check reads the profile,
  and the example needs waivers from the start, so retrofitting them later would
  mean rewriting checks.
- The GitHub trust anchor, PostgreSQL, HIPAA and the agent runtimes moved out of the
  core rules into adapters, each with a stated limit of what it can enforce.
- Healthcare-specific wording (clinical sign-off, PHI) was removed from kit
  requirements and replaced with neutral terms (domain sign-off, classified data).
- The escaped-defects metric is now tied to the incident loop that feeds it, instead
  of being described in two places with different status.
- A minimum viable agent team (four agents) is defined, so slice 0.3 does not
  depend on all fourteen.
- Requirement IDs were added so phases, acceptance and the example can cite a rule
  instead of restating it.
