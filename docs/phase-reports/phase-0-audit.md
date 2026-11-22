# Phase 0 — Upstream and community audit

- **Phase and date:** Phase 0, 2026-11-21
- **Pinned upstream (proposed for D6):** github/spec-kit `v1.4.3`, commit `980b3d0`, dated 2026-11-19, MIT
- **Requirement IDs covered:** ADP-1, ADP-2; gap table covers all of `spec/10`–`16`
- **Assumptions:** the latest tag is the right one to pin; catalog entries at that tag are the candidate set
- **Unverified:** see section 8. No extension code was executed. Depth of source reading varies and is stated per candidate.

## 1. Bottom line
1. **Delivery shape: (b), no fork.** Upstream v1.4.3 has every extension point the kit needs: extensions, presets, workflows, installable custom workflow step types, bundles, hooks and catalogs. Nothing in the requirements needs a core change.
2. **Upstream gates are pause points, not approvals.** The built-in `gate` step accepts its verdict from a workflow input. Anyone, or any agent, with a shell can run `specify workflow resume <run_id> --input spec_verdict=approve`. There is no identity check. This confirms GOV-6 is a real gap and must be anchored outside the workflow engine.
3. **Upstream hooks, in the command templates, are instructions to the agent.** Command templates tell the agent to read `.specify/extensions.yml` and emit `EXECUTE_COMMAND:` for mandatory hooks. A hook runs only if the agent complies.
4. **The community catalog is wide but thin.** Of 59 candidate repos read, 36 contain no executable code (prompt files only), 31 have a single author, 31 have no tests, and 18 have one or two commits. Most "gates" in the catalog are prompts asking an agent to stop.
5. **Three candidates are serious prior art:** `spec-gates` (deterministic enforcement at agent, git and CI boundaries), `specassay` (durable IDs, trace manifest, CI gate) and `spec-kit-ado` (human approvals bound to separate approver identities and to a hash of the bytes signed). None covers the system map, data-change governance or shared-component rules.
6. **Recommendation on reuse:** no hard community dependency in slice 0.1. Adapt patterns with attribution, and offer `spec-gates` and `specassay` as optional integrations after a full source review in Phase 2. This is narrower than charter D7 implies; see section 7.

## 2. Upstream at v1.4.3
Evidence paths are relative to the upstream repo.

| Area | What exists | Evidence |
|---|---|---|
| Core commands | 9: constitution, specify, clarify, plan, checklist, tasks, analyze, implement, converge | `templates/commands/` |
| Converge | Assesses code against spec, plan and tasks; append-only to `tasks.md` | `templates/commands/converge.md`, `docs/reference/agentic-sdd.md` |
| Integrations | Over 40 agent integration packages, including Claude Code and Copilot | `src/specify_cli/integrations/` |
| Workflow engine | 14 step types: command, prompt, shell, github, init, slot, gate, if, switch, while, do-while, fan-out, fan-in, workflow | `docs/workflow-steps/types.md` |
| Parallel dispatch | `fan-out` with `max_concurrency`, `fan-in` to aggregate | `src/specify_cli/workflows/step/fan_out/__init__.py` |
| Custom steps | Installable Python step packages via `specify workflow step` | `docs/workflow-steps/developing.md` |
| Built-in workflow | `speckit`: specify → gate → plan → gate → tasks → implement (two gates) | `workflows/speckit/workflow.yml` |
| Hooks | before/after events per command; optional or mandatory | `docs/extensions/api.md` lines 638–790 |
| Bundles | Versioned sets of extensions, presets, workflows, steps | `bundles/assess/bundle.yml` |
| Presets | Official: `lean`, `constitution-sync` (plus scaffold and self-test) | `presets/` |
| IDs | `FR-###`, `SC-###` in specs; `[P]` parallel marker in tasks | `templates/spec-template.md`, `templates/tasks-template.md` |
| Guidance only | Monorepo, contract-driven development, existing projects, spec-of-specs, evolving specs | `docs/how-to/` |
| Other | MCP server, artifact introspection (`specify artifact`), agent runtime events | `src/specify_cli/mcp_server`, `artifacts`, `events` |
| Catalogs | Community: 203 extensions, 43 presets, 5 bundles, 4 workflows. Official: 5, 2, 2, 3 | `*/catalog*.json` |

### Findings that shape the design
- **F1 Gate verdict is caller-supplied.** `src/specify_cli/workflows/step/gate/__init__.py` reads the choice from `context.inputs[verdict_input]`; `docs/workflow-steps/types.md` lines 471–510 document `resume --input spec_verdict=approve`. No approver identity, no link to a commit.
- **F2 Mandatory hooks depend on agent compliance.** `templates/commands/*.md` contain 23 `EXECUTE_COMMAND` instructions; the agent reads the hook list and is told to act on it.
- **F3 No roles, tiers, waivers, audit log, system map or dependency model** anywhere in upstream. Checklists carry a convention that implementation "must not silently self-approve" (`docs/reference/agentic-sdd.md` line 91), which is not enforced.
- **F4 Upstream's own practice keeps agents out of release.** `docs/guides/agentic-sdlc.md` section 6 is titled "Deployment: publish without an agent". The kit's non-goal on deployment matches upstream.
- **F5 Traceability is partial.** Requirement and task IDs exist, but no check links requirement → test → change, and `/speckit.analyze` is a read-only model review.

## 3. Community candidates
Facts were collected by script from shallow clones (`audit/facts.json`). "Code" is lines of Python, shell, PowerShell, JS/TS outside test folders; "tests" is an approximate file count by path. "Read" states how deep I went: **M** manifest and README, **C** also command or rule files, **S** also source.

### Serious candidates
| Candidate | Last commit | Commits | Code / tests | Read | What it does | Can a human gate be bypassed? | Verdict |
|---|---|---|---|---|---|---|---|
| spec-gates (`gates`) | 2026-11-20 | 173 | 19,021 / 19 | C | One policy file enforced at three boundaries: Claude Code hooks, git hooks, CI; optional branch protection | Protected changes need `Approved-By` commit trailers, which its own docs call "an auditable declaration, not a credential"; it relies on CODEOWNERS plus branch protection for real approval | Optional integration; adapt policy-boundary pattern. README says verified against Spec Kit v0.12.4, so compatibility with v1.4.3 is unproven |
| specassay (`specassay-check`) | 2026-10-11 | 302 | 5,376 / 35 | M | Durable IDs, `@covers` marks, named tests, deterministic CI gate, `trace-manifest.json` | Not a human gate; a trace gate | Optional integration or adapt ID convention for TRC-1 to TRC-4 |
| spec-kit-ado (`ado`) | 2026-11-16 | 146 | 14,025 / 94 | C | Human-gated lifecycle on Azure DevOps: trust keys read only from the target branch, approvers as separate identities, sign-off comments bound to a content hash, refusal without a terminal, `doctor` fails if the agent's token is an approver | Designed against it; I did not test it | Adapt design with attribution for GOV-6 to GOV-8. Azure DevOps only, so not a dependency for the GitHub adapter |
| verify-tasks | 2026-09-15 | 24 | 1,551 / 63 | M | Detects tasks ticked done with no implementation, in layered checks | n/a | Optional integration for QLT-1 |
| v-model | 2026-05-21 | 294 | 15,787 / 285 | M | Paired dev and test specs, trace matrix scripts, eval workflow in CI | Human decides by design | Study trace scripts; too broad to depend on (111 commands) |
| schedule | 2026-09-06 | 34 | 12,280 / 48 | M | Turns `tasks.md` into conflict-free parallel rounds with a constraint solver, then dispatches subagents | n/a | Optional for AGT-4; heavy dependency (solver, private Python env) |
| worktrees | 2026-05-06 | 24 | 259 / 2 | M | Scripted git worktree creation per feature | n/a | Adapt or depend for AGT-4 |
| blueprint-index | 2026-08-24 | 69 | 4,340 / 8 | M | Living architecture map of specs and code sections with a CI drift gate | n/a | Study for MAP-6. Its README describes no owners, data stores or consumer edges |
| brownkit | 2026-09-03 | 63 | 2,250 / 11 | M | Evidence → discovery → capabilities → risk pipeline for existing codebases | n/a | Evaluate in Phase 2 for MAP-15 |
| threatspec | 2026-11-20 | 10 | 2,220 / 13 | M | Threat model → security requirements → tasks and tests | n/a | Candidate for QLT-3 in slice 0.4 |
| knowledge | 2026-10-27 | 137 | 7,048 / 1 | M | Injects decisions and contracts from other repos into the workflow | n/a | Study for MAP-7 federation |
| multi-repo-sync | 2026-07-08 | 6 | 1,539 / 2 | M | Creates matching feature branches across sub-repos and submodules | n/a | Possible helper for MAP-14 |

### Prompt-only or stale candidates (not suitable as dependencies)
| Candidate | Last commit | Commits | Code | Note |
|---|---|---|---|---|
| Fleet Orchestrator | 2026-03-31 | 10 | 0 | "Human gate after every phase" is an instruction to the orchestrating agent to ask the user. Read: C |
| MAQA (+6 tracker add-ons) | 2026-09-06 | 11 | 0 | Coordinator, feature and QA prompts with GitHub Issues as state. Add-ons are single-commit. Read: C |
| Plan Review Gate | 2026-03-30 | 10 | 0 | Checks that spec and plan exist on the default branch; does not check that anyone reviewed them; has a `--skip-review` override. Read: C |
| API Evolve | 2026-05-07 | 1 | 0 | Breaking-change "detection" is done by the model reading contract files; no diff tool. Read: M |
| Spec Trace | 2026-05-12 | 1 | 0 | Trace matrix produced by prompt. Read: M |
| Spec Orchestrator | 2026-04-24 | 1 | 0 | Cross-feature conflict report by prompt; no licence file in repo |
| CI Guard, Brownfield Bootstrap, Staff Review, Worktree Isolation, GitHub Issues 1 | Apr 2026 | 1–2 | 0 | Single-commit prompt packs |
| Epic | 2026-10-09 | 13 | 0 | Requires Spec Kit `<1.2.0`; incompatible with v1.4.3 |
| Agent Assign, Conduct, Multi-Model Review, Ripple, Time Machine, Discovery, Reconcile, Spec Sync, Red Team, Optimize, Golden Demo, Data Model Diagram, Explicit Task Dependencies | various | 2–38 | 0–711 | Useful ideas, small or prompt-led; I saw no enforcement in any of them |
| Architect Impact Previewer, Repository Index | Mar–Apr 2026 | 1–3 | 0–140 | No licence file in repo despite MIT in the catalog |
| What-if Analysis | — | — | — | Repository could not be cloned (not reachable without credentials); excluded |

Not evaluated beyond facts, because they belong to slice 0.4 and can wait for Phase 9: Architecture Guard, Security Review, AttackTree, MemoryLint, Azure Cosmos DB, the two Azure DevOps integrations, and the four governance presets (A11Y, Architecture, iSAQB Architecture, Agent Parity).

## 4. Gap table
Vehicle key: **E** extension, **P** preset, **W** workflow, **S** custom workflow step, **B** bundle, **CI** check script shipped by the extension.

| Requirements | Upstream today | Community | Verdict | Vehicle | Reason |
|---|---|---|---|---|---|
| GOV-1 to GOV-3 roles | None | `ado` role map (Azure DevOps only) | Build | E | No portable role model exists |
| GOV-4, GOV-5 gates | `gate` step; two gates in `speckit` workflow | Fleet (prompt), `ado` (12 gates) | Build on upstream | W + S | Reuse the engine; define G0–G7 as a workflow |
| GOV-6 to GOV-8 enforcement | None (F1) | Plan Review Gate (bypassable), `ado` (strong, other platform) | Build; adapt `ado` pattern | S + CI | Needs a GitHub-anchored approver check |
| GOV-9, GOV-10 tiers | None | None | Build | E + CI | — |
| GOV-11 enforceable constitution | Prose constitution | `spec-gates` policy file | Build mapping; optional `spec-gates` | E + CI | Principle-to-check mapping is missing everywhere |
| GOV-13, GOV-14 profiles | `lean` preset | — | Build | P ×3 | Presets are the upstream mechanism for this |
| GOV-15, GOV-16 waivers | None | `spec-gates` records weakenings with commit trailers | Build; study | E + CI | — |
| TRC-1 to TRC-4 traceability | `FR`, `SC`, task IDs | `specassay`, `v-model`, Spec Trace (prompt) | Adapt `specassay` convention | E + CI | Extend to principle, gate and evidence links |
| TRC-5 to TRC-7 audit log | Workflow run state only | None found | Build | E | — |
| TRC-8, TRC-10 drift | `converge` before merge | Spec Sync, Reconcile, Blueprint Index | Reuse `converge`; build post-merge check | CI | — |
| TRC-11, TRC-14 metrics | None | None | Build | E | Derived from audit log |
| TRC-17 self-tests | `selftest` extension, `self-test` preset | — | Follow upstream pattern | E | — |
| QLT-1, QLT-2 verification | `analyze`, `converge` | Verify, Verify Tasks, Review, Multi-Model Review | Build isolation wrapper; optional Verify Tasks | W + E | Isolation of inputs is the missing part |
| MAP-1 to MAP-7 system map | None | Blueprint Index (no owners or data stores in its README), Knowledge | Build | E + CI | Confirmed gap |
| MAP-8 to MAP-12 impact | None | Ripple, Architect Preview (prompt) | Build | E + CI | Must be deterministic to drive reviewers |
| MAP-13, MAP-14 cross-spec, programme | `spec-of-specs` how-to | Spec Orchestrator (prompt), Epic (incompatible) | Build on upstream roadmap convention | E | — |
| MAP-15 brownfield | `existing-projects` how-to | BrownKit, others | Evaluate BrownKit; build map discovery | E | — |
| CHG-1 to CHG-5 data stores | None | None (Cosmos DB is code guidance; Data Model Diagram draws ER diagrams) | Build | E + CI | Confirmed gap |
| CHG-6 to CHG-9 contracts | Contract how-to | API Evolve (prompt) | Build with established open-source diff tools | E + CI | Detection must not be a model's opinion |
| CHG-10 to CHG-15, CHG-18 | None | None | Build | E + CI | — |
| AGT-1, AGT-2 agent definitions | Over 40 integrations | Agent Assign, MAQA, Fleet | Build portable spec | E | — |
| AGT-3 repo state | Workflow run state | MAQA uses GitHub Issues | Build | E | — |
| AGT-4 isolation of work | `[P]` marker | Worktrees, Schedule | Adapt Worktrees; Schedule optional | E | — |
| AGT-5 to AGT-8 orchestration | `fan-out`, `fan-in`, `gate`, `resume` | Conduct, Fleet | Use upstream engine | W | — |
| AGT-9 to AGT-12 privilege | None | `spec-gates` agent-boundary hooks | Adapt or integrate | E | — |
| AGT-13 golden tasks | `selftest` | `v-model` eval workflow | Build | CI | — |
| Slice 0.4 (QLT-3 to QLT-22, AGT-14 to AGT-18, CHG-16 to CHG-21, GOV-12, GOV-17 to GOV-20, TRC-12 to TRC-16, ADP-16) | None | ThreatSpec, Security Review, MemoryLint, A11Y preset, tracker integrations | Decide in Phase 9 | — | Not needed before the walkthrough |

## 5. Delivery shape
| Option | For | Against |
|---|---|---|
| (a) Fork | Could harden the built-in gate | Permanent merge burden against a fast-moving upstream (tag dated two days ago); nothing requires it |
| **(b) Extension + preset + workflow + custom step + bundle** | All needed extension points exist; installs with the normal `specify` commands; upstream upgrades stay cheap | Enforcement cannot live in the workflow engine alone, so the kit must ship CI checks and document repository settings |
| (c) Hybrid | — | No core change identified to justify it |

**Recommended: (b).** Concretely: one extension (commands, schemas, check scripts), three presets (Lite, Standard, Regulated), one workflow for G0–G7, one custom step type that reads the approval from the enforcement channel instead of a workflow input, and one bundle per profile. If Phase 2 finds a case that truly needs a core change, raise it upstream as an issue rather than fork.

## 6. Risks found
- **R1 Upstream moves quickly.** v1.4.3 was tagged on 2026-11-19; several community extensions pin older ranges. Pin the tag and run the kit's self-tests against new tags before moving.
- **R2 Community dependencies are fragile.** Single maintainers, missing licence files, version pins that exclude current upstream. A hard dependency could break the kit's install.
- **R3 Catalog descriptions overstate.** Several entries describe gates and detection that are prompts. Every reuse decision needs source reading (ADP-2), which this phase did only in part.
- **R4 The trust anchor I planned is the one others already use.** `spec-gates` reaches the same conclusion as GOV-6: commit-level approval marks are declarations, and real approval needs CODEOWNERS plus branch protection. That supports the GitHub adapter design (ADP-3) and means the kit's value is in tying that review to gates, roles and evidence, not in inventing a new approval channel.
- **R5 Custom step packages run Python.** The kit's step is executable code installed into a user's project, so it needs its own review and tests, and the README must say so.

## 7. Decisions I need from you
1. Approve delivery shape (b).
2. Approve pinning `v1.4.3` for D6.
3. Reuse stance: **no hard community dependencies in slice 0.1; adapt with attribution; optional integrations only** (my recommendation), or allow hard dependencies on `spec-gates` and/or `specassay`.
4. Whether the three serious candidates get a full source review in Phase 2 (about a day of reading), or only those you choose.

### Proposed charter changes (I have not edited the charter)
- **D6:** record `v1.4.3`, commit `980b3d0`, 2026-11-19.
- **D7:** change "integrate community extensions under one system map and one gate model" to "learn from and optionally integrate", and name `spec-kit-ado`, `spec-gates` and `specassay` as design references.
- **D11:** note that an Azure DevOps approval design already exists in the community and should inform the adapter interface (ADP-4).

## 8. What I did not verify
- I executed no extension, script or workflow. All statements about behaviour come from reading files.
- Source-level reading was limited to the upstream gate step and the files marked **C**. Candidates marked **M** were judged from README, manifest and repo facts.
- Whether `spec-gates` and `specassay` work on Spec Kit v1.4.3.
- Whether upstream's CLI hook executor enforces mandatory hooks in any path other than the command templates I read.
- The "tests" column is a path-based count, not a test run.
- Shallow clones (depth 200) cap commit counts at 200 for larger repos; two repos show more because of merge history.
- What-if Analysis could not be read at all.
- The roughly 150 community extensions and 38 presets outside the candidate list were not examined.

## 9. What Phase 1 needs from you
- Approval of this phase.
- Confirmation that I may clone `imatiqul/azure-ai-cloud-healthcare` read-only and which commit to verify against (default: current head of the default branch).
