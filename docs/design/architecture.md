# Architecture

- **Phase and date:** Phase 2 (design), 2026-11-21
- **Pinned upstream:** github/spec-kit `v1.4.3` (commit `980b3d0`, 2026-11-19)
- **Requirement IDs covered:** all 132; see `requirement-map.md`
- **Assumptions:** listed in section 10
- **Unverified:** nothing here has been built or run. Upstream APIs were read at the pinned tag; community designs were read, not executed.

Companion files: `schemas.md` (data shapes), `checks.md` (check catalogue), `agents.md` (agent team), `source-review.md` (design references), `requirement-map.md` (generated coverage table).

## 1. What ships

Everything installs on unmodified upstream with the normal `specify` commands (charter D12).

| Unit | Upstream kind | Id | Slice | Contains |
|---|---|---|---|---|
| Core extension | extension | `agentic` | 0.1 | Commands, templates, the check CLI, the GitHub enforcement adapter |
| System extension | extension | `agentic-system` | 0.2 | System map, discovery, impact, change packs and their adapters |
| Team extension | extension | `agentic-team` | 0.3 | Agent specs, work items, locks, orchestration, runtime adapters |
| Profiles | preset ×3 | `agentic-lite`, `agentic-standard`, `agentic-regulated` | 0.1 | Template and command overrides per profile |
| Gate step | workflow step | `agentic-gate` | 0.1 | Custom step that reads approval from the enforcement channel |
| Lifecycle | workflow ×2 | `agentic-sdd`, `agentic-sdd-sequential` | 0.1 / 0.3 | G0–G7 as a workflow; the sequential variant for one agent |
| Domain pack | extension | `agentic-hipaa` | 0.1 | Mandatory sections, control mapping, classification vocabulary |
| Bundles | bundle ×3 | one per profile | 0.1 | Installs the right set in one command |
| CI | workflow file | `agentic-checks.yml` | 0.1 | Runs every check on pull requests and on the default branch |

Three extensions instead of one so that each slice is usable alone (charter slices) and Lite never installs code it does not use (D10).

## 2. Repository layout

```
agentic-spec-kit/
  extensions/
    agentic/            extension.yml, commands/, templates/, scripts/agentic_kit/ (Python), ci/
    agentic-system/     commands/, templates/, scripts/agentic_kit_system/, adapters/
    agentic-team/       agents/, commands/, scripts/agentic_kit_team/, adapters/
    agentic-hipaa/      pack.yml, templates/, controls.yml
  presets/              agentic-lite/, agentic-standard/, agentic-regulated/
  workflows/            agentic-sdd/, agentic-sdd-sequential/
  steps/                agentic-gate/ (step.yml, __init__.py)
  bundles/              lite/, standard/, regulated/
  fixtures/             pass/ and fail/ per check; multi-app/ (charter D8)
  tests/                unit tests for the CLI; self-test runner
  examples/healthq/     reference example
  docs/                 prompts/, design/, phase-reports/, admin-setup.md, adapters/
```

In a project that adopts the kit, state lives under `.specify/agentic/`:

```
.specify/agentic/
  kit.yml               profile, domain packs, enforcement adapter, thresholds
  roles.yml             role → people
  constitution.map.yml  principle → check or judging gate
  waivers/              one file per waiver; baseline.yml for adopted suppressions
  decisions/<spec>/     one mirrored decision record per gate
  audit/<spec>.jsonl    hash-chained log per spec; audit/kit.jsonl for kit-level events
  work/<spec>/          work items (slice 0.3)
system-map/             nodes.yml, edges.yml, index.yml (slice 0.2)
specs/<spec>/           upstream artifacts plus impact.md, data-change-plan.md, trace-manifest.json
```

## 3. The check CLI

One Python package per extension, run as `python -m agentic_kit <check> [--json]`. Python because upstream already requires it. The only third-party dependency is PyYAML.

- Every check is a pure function of files in the repo plus, for approval checks, one adapter call.
- Every check has an ID (`CK-…`), names the requirements it enforces, and exits non-zero on failure with a one-line reason per finding.
- Every check reads `kit.yml` first and skips itself when the profile does not require it, saying so in its output.
- The same entry point runs at three boundaries, a pattern taken from `spec-gates`: on the developer's or agent's machine, as an agent runtime event where the integration supports it, and in CI. CI is the one that counts.
- A check never trusts its own previous output. Reports are regenerated and compared, never read back as evidence.

## 4. Gates and the trust model

### Gate sequence
| Gate | Decides | Artifacts in the evidence bundle | Default approvers (Standard) |
|---|---|---|---|
| G0 | Constitution or amendment | constitution, `constitution.map.yml` | Product Owner, Solutions Architect, Security & Compliance |
| G1 | Spec | `spec.md`, declared tier and touches | Product Owner |
| G2 | Clarifications resolved | `spec.md` diff, clarification log | Product Owner, Solutions Architect |
| G3 | Plan | `plan.md`, `impact.md`, data-change and rollout sections | Solutions Architect, owner of each touched node |
| G4 | Tasks and analysis | `tasks.md`, analysis report, trace manifest | Engineering Manager, QA |
| G5 | Implementation | code diff, test results, trace manifest, waiver list | Code owners, QA, Security & Compliance by tier |
| G6 | Verification | verifier report, converge result, drift report | QA |
| G7 | Release | rollout and rollback plan, open waivers, readiness | DevOps/SRE, Product Owner |

Lite keeps G1, G3 and G5 with one approver each.

### Two pull requests per spec
- **Spec PR** carries `specs/<spec>/` and passes G1–G4. Merging it is what makes the spec approved.
- **Implementation PR** carries code and passes G5–G6. It may not open for review until the spec PR is merged.
- G0 is a pull request against the constitution. G7 is a review on a release pull request or tag; the kit prepares the bundle and stops.

This follows upstream's own shape (spec and plan reviewed before tasks) and gives every gate a commit to bind to.

### What counts as an approval
Adapted from `spec-kit-ado` (see `source-review.md`). A gate is approved only when the enforcement adapter returns a review that passes every one of these:

1. The reviewer is listed in `roles.yml` **as read from the base branch**, never from the pull request's own copy, and holds a role the gate requires.
2. The reviewer is a human account, is not the agent's token identity, and is not the CI identity.
3. The reviewer did not author the commits that changed the gate's artifacts. Where they did, the decision is recorded as `single_approver_exception: true` (charter D3) and the profile decides whether that is allowed.
4. The review state is approved and has not been dismissed.
5. The review is on the commit whose evidence bundle hashes to the value the reviewer stated. The kit prints the line to paste, for example `gate G3 approve sha256:9c1e…`. In Lite the hash line is optional and any approving review on the head commit by a role holder counts.

The `agentic-gate` step computes the bundle hash, asks the adapter, and returns `PAUSED` until a valid review exists. It has no verdict input, so the upstream weakness found in Phase 0 (F1) does not apply to it.

After approval the Scribe agent writes the mirrored decision record. `CK-GATE-MIRROR` in CI compares every record with the adapter and fails on any mismatch.

### What an administrator must configure
`python -m agentic_kit doctor` reports each item as pass, fail or not-checkable:
- Branch protection on the default branch requiring pull requests, at least one approval, and the `agentic-checks` status check.
- CODEOWNERS covering `.specify/agentic/roles.yml`, `kit.yml`, `constitution.map.yml`, `waivers/` and the constitution.
- The token the agent uses is not an approver, cannot bypass branch protection, and cannot approve reviews.

Without these, GOV-6, GOV-7, GOV-16, MAP-12 and CHG-12 are convention, and the kit says so in every gate brief.

## 5. Traceability

IDs are minted where intent is written and never renumbered, a rule taken from `specassay`.

| Thing | ID form | Minted in | Carried by |
|---|---|---|---|
| Principle | `P-3` | constitution | spec front matter `principles:` |
| Requirement | `FR-004` (upstream form) | `spec.md` | acceptance criteria |
| Acceptance criterion | `AC-012` with `verifies: FR-004` | `spec.md` | tasks (`Carries:`), tests |
| Task | `T017` (upstream form) | `tasks.md` | commits |
| Test | name or annotation containing the AC id | test code | trace manifest |
| Change | pull request number | enforcement channel | decision record |
| Evidence | `EV-<gate>-<n>` | decision record | audit log |
| System-map node | node id | `system-map/` | spec `touches:` |

Across specs an ID is written `<spec>:<id>`. `CK-TRACE` builds `trace-manifest.json` and fails on a missing or orphaned link in either direction. An acceptance criterion is in one of four states: proven (a named test exists and passed in this run), tracked debt (an open task carries it), waived, or gap. Only gap fails.

## 6. Audit log
- One JSON Lines file per spec, so parallel specs do not conflict on merge.
- Each entry carries the hash of the previous entry. `CK-AUDIT-CHAIN` verifies each file.
- The head hash of the spec's log is copied into every gate decision record, which is in turn bound to a human review. That is what makes a wholesale rewrite detectable.
- The log records kit command runs, agent runs and gate decisions. It does not record what an agent does outside kit commands (TRC-7).

## 7. System map and impact (slice 0.2)
- `system-map/nodes.yml` and `edges.yml` hold the map; `index.yml` maps path globs to nodes and is what makes `CK-TOUCH` possible.
- Discovery adapters emit candidate nodes and edges with the file that proves each. A human confirms the map at a gate; afterwards discovery runs in CI and `CK-MAP-DRIFT` reports differences.
- `impact` walks edges from the nodes a spec touches and writes `impact.md`: affected nodes by distance, their owners, the resulting tier, and the required approvers per gate. `agentic-gate` reads the approver list from there.
- Change packs are triggered by the type of node touched: a data-store node requires `data-change-plan.md`, a contract node triggers the contract checks, a shared library or package triggers the consumer matrix.

## 8. Adapters
Each adapter is a Python module implementing one small interface and shipping its own fixtures. Vendor names appear only here and in `spec/16-adapters.md`.

| Interface | Methods | First implementations |
|---|---|---|
| Enforcement | `agent_identity()`, `approvals(change)`, `change_authors(change)`, `setup_report()` | GitHub |
| Suppression detector | `find(repo) → [suppression]` | CI escapes, test skips, lint disables, advisory suppressions for .NET and Node |
| Discovery | `discover(repo) → nodes, edges, evidence` | .NET solutions, Node workspaces, ORM contexts and migrations, module federation, infrastructure as code, CI |
| Data engine | `classify(migration)`, `apply(container)`, `model_drift()` | PostgreSQL; Qdrant proposed as the non-relational one |
| Contract | `diff(old, new) → [change, breaking?]` | OpenAPI, GraphQL |
| Agent runtime | `render(agent_spec) → files`, `enforces → {tools, paths}` | Claude Code, Copilot, sequential |
| Domain pack | `sections()`, `controls()`, `classification()` | HIPAA |
| Tracker (0.4) | `sync(spec)` | GitHub Issues and Projects, Azure DevOps |

The enforcement interface was shaped so that an Azure DevOps adapter could follow the comment-based design `spec-kit-ado` already uses (charter D11).

## 9. Commands
Namespaced `speckit.agentic.*`. Each wraps a CLI call so the same logic runs with or without an agent.

| Command | Purpose | Slice |
|---|---|---|
| `init` | Write `kit.yml`, `roles.yml`, CI file; run doctor | 0.1 |
| `doctor` | Report enforcement setup and what is not enforced | 0.1 |
| `adopt` | Brownfield: inventory suppressions, propose baseline waivers, draft map and findings | 0.1 / 0.2 |
| `gate` | Show gate status, evidence hash, the line to paste | 0.1 |
| `waive` | Create or renew a waiver | 0.1 |
| `trace` | Build the trace manifest and matrix | 0.1 |
| `check` | Run all checks for the active profile | 0.1 |
| `verify` | Run the independent verifier with an input manifest | 0.1 |
| `map` | Discover, validate and diff the system map | 0.2 |
| `impact` | Write the impact report for a spec | 0.2 |
| `data-plan` | Scaffold and check a data-change plan | 0.2 |
| `orchestrate` | Run the agent team for a spec | 0.3 |

## 10. What cannot be enforced, and what it degrades to
| Requirement | Limit | Degrades to |
|---|---|---|
| GOV-6, GOV-7 | Needs branch protection and CODEOWNERS | Convention, stated in doctor output and every gate brief |
| GOV-7 with one human (D3) | Identity binding protects only while the agent cannot use the approver's credentials | Single-approver exception recorded on every decision; doctor verifies the agent's token is not the approver |
| GOV-11 | The kit can check that a principle names a check, not that the check is sufficient | Human judgement at G0 |
| GOV-15 | Only known suppression patterns are detected | Pattern list is configurable; unknown patterns are a documented gap |
| TRC-5 | Someone with push rights can rewrite the log | Chain heads bound to human reviews |
| TRC-8 | Semantic drift cannot be decided deterministically | Deterministic for traces and touched files; an advisory agent finding for meaning |
| QLT-1 | The kit cannot prove what a model saw | Checks the verifier's declared input manifest; states the limit (QLT-2) |
| MAP-5 | Discovery is heuristic | Unproven facts are marked assumed and must be confirmed by a human |
| CHG-4 | Needs a container runtime in CI | Check reports not-run, which fails at Standard and above |
| AGT-10 | Path limits are native only where the runtime has pre-tool events | Post-run diff check everywhere |
| AGT-11 | Cannot prove no other credential exists on a machine | Checks the token in use; documents the residual risk |

## 11. Spec changes (approved by the owner on 2026-11-21 and applied to `spec/`)
1. **GOV-21 [0.1] Adoption baseline.** When the kit is first applied to an existing codebase, existing suppressions may be recorded as one baseline, grouped by rule, each group with an owner, reason and expiry, approved once at a gate. New suppressions need individual waivers. The count in each group may only go down. Reason: the reference repo has about 236 existing suppressions (Phase 1).
2. **TRC-18 [0.1] Evidence hash.** A gate decision names the hash of its evidence bundle. Reason: without it an approval is not bound to what was reviewed. This is already implied by GOV-5 "tied to a commit" but is stronger and is the core of the trust model.
3. **ADP-6 wording.** Name Qdrant as the non-relational store, since the reference system uses it for retrieval and it exercises the re-embedding rule in CHG-5.

## 12. Assumptions and open questions
- **A1** A project has one enforcement adapter. Mixed hosting is out of scope.
- **A2** Spec artifacts live in the same repo as the code they describe, as upstream assumes. Programme specs point to child specs in other repos by pinned reference.
- **A3** PyYAML is acceptable as the only runtime dependency.
- **Q1** Two pull requests per spec (section 4) or one. Two is cleaner for gates; one is less ceremony. I recommend two for Standard and Regulated and one for Lite.
- **Q2** Whether Lite should require the hash line. I recommend not.
- **Q3** Whether the three extensions should be one. I recommend three.
- **Q4** System-map owners and tiers for the reference example, deferred from Phase 1. They are needed before Phase 5, not before Phase 3.
