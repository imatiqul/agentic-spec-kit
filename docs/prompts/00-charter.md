# Charter

## Mission
Create `agentic-spec-kit`: an open-source, MIT-licensed Agentic Specification-Driven
Development toolkit that builds on github/spec-kit. A team of specialised agents
drafts, builds and verifies; named humans review and approve at every gate. Nothing
advances past a gate on an agent's say-so.

The kit treats a change as a change to a system, not to one repo: every spec knows
which data stores, shared components, contracts and other applications it touches,
who owns them, and who must approve.

Prove it on a real system, described in `reference/20-healthq.md`.

## Non-goals
- Not a fork of spec-kit unless the audit proves a core change is unavoidable.
- Not a compliance certification, legal advice, or a substitute for an auditor.
- Not a deployment tool. The kit prepares release evidence; it does not release.
- Not autonomous delivery. No configuration of the kit lets an agent approve.
- Not a rebuild of community extensions that already do the job well.

## Release slices
| Slice | Name | Contains |
|---|---|---|
| 0.1 | Govern | Roles, gates, enforcement, risk tiers, profiles, waivers, traceability, audit log, self-tests |
| 0.2 | System | System map, impact analysis, change packs, supply chain |
| 0.3 | Team | Agent team, coordination, sequential fallback |
| 0.4 | Depth | Change lanes, amendments, quality packs, agent operations, integrations, auditor pack |

Each slice must be usable on its own. Each requirement in `spec/` carries its slice.

## Decisions I have made (change these before running if wrong)
- D1 Repos: toolkit in a new repo `imatiqul/agentic-spec-kit`. The reference example
  lives in `examples/healthq/` inside it and points at the healthcare repo by commit
  SHA; it does not copy source code.
- D2 Disclosure: the toolkit repo stays PRIVATE until findings C1–C6 are fixed in
  the healthcare repo or I explicitly accept publishing them.
- D3 People: I am the only human and hold every role. Record approvals under my
  GitHub identity with the role I am acting in. Where separation of duties would
  need a second person, record "single-approver exception"; never imply two people.
- D4 Pushes: feature branches and draft PRs are allowed in both repos. Never push
  to main, merge, mark a PR ready for review, or approve.
- D5 Agent runtimes: Claude Code subagents first, GitHub Copilot custom agents
  second, and a sequential single-agent mode that every workflow must also support.
- D6 Upstream: pinned to github/spec-kit `v1.4.3`, commit `980b3d0`, dated
  2026-11-19. Record tag and date in every artifact that depends on it.
- D7 Reuse first: learn from community extensions and optionally integrate them;
  build only what is missing. No hard community dependency in slice 0.1. Design
  references: `spec-kit-ado` (approver identities and hash-bound sign-off),
  `spec-gates` (enforcement at agent, git and CI boundaries), `specassay` (durable
  IDs and trace gate). Community extensions are unaudited, so read the source of
  anything proposed as a dependency or optional integration.
- D8 Cross-application proof: the healthcare repo is one repo, so cross-repo and
  shared-component features are proven on a synthetic fixture, `fixtures/multi-app/`
  (two services, one shared library, one shared database, one external API stub).
- D9 Order: slices ship in order. Slice 0.4 is designed early but built only after
  the end-to-end walkthrough passes on 0.1–0.3. If the walkthrough exposes a core
  problem, fix the core first.
- D10 Proportionality: three adoption profiles (Lite, Standard, Regulated). The
  reference example uses Regulated. No later slice may make Lite heavier.
- D11 First adapters: GitHub for enforcement, PostgreSQL plus one non-relational
  store the reference system uses, HIPAA as the first domain pack. An Azure DevOps
  approval design already exists in the community (`spec-kit-ado`) and informs the
  adapter interface.
- D12 Delivery shape: extension + presets + workflow + custom gate step + bundles on
  unmodified upstream. No fork.

## Decision log
| Date | Phase | Decision | Source |
|---|---|---|---|
| 2026-11-21 | 0 | Approved delivery shape (D12), pin v1.4.3 (D6), reuse stance (D7), full source review of the three design references in Phase 2, read-only clone of the healthcare repo at head of `main` | Owner approval in chat ("yes, go ahead"); charter updated by the agent on that approval |

## Glossary
- **Gate**: a point where work stops until a human records a decision.
- **Role**: a human accountability. **Agent**: a model-driven worker supporting a role.
- **System map**: the versioned record of what exists and what depends on what.
- **Node / edge**: a thing in the map / a dependency between two things.
- **Touches**: nodes a spec changes. **Depends on**: nodes or specs it relies on.
- **Risk tier**: Critical, High, Medium or Low; sets reviewers, test depth, evidence.
- **Profile**: how much of the kit a team adopts (Lite, Standard, Regulated).
- **Lane**: the route one change takes through the gates (standard, fast, emergency).
- **Pack**: a set of rules for one kind of change or one quality dimension.
- **Adapter**: the binding of a neutral rule to one platform or technology.
- **Waiver**: a recorded, owned, expiring exception to a rule.
- **Evidence bundle**: the files a human needs to decide at a gate.
