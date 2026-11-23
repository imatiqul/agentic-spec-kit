# Release notes

- **Phase and date:** closing documents, 2026-11-22
- **Requirement IDs covered:** all slices; see `docs/design/requirement-map.md` and each phase report
- **Assumptions:** none
- **Unverified:** see `docs/limits.md`, "Never run"

Nothing here has been released. These notes say what each slice contains, so a reader can tell what they are installing. Counts are from the code on 2026-11-22: 105 checks, each with a passing and a failing fixture.

## 0.1 Govern — `extensions/agentic`
Roles, gates G0 to G7, three profiles, risk tiers, waivers and the adoption baseline, the trace manifest, the hash-chained audit log, drift detection, and decisions mirrored from pull-request reviews and bound to a hash of the evidence. 18 checks.

Added to it in slice 0.4: the fast lane, the emergency lane, amendments that re-open only the gates they affect, the one-page reviewer brief (CK-LANE, CK-EMERGENCY-DEADLINE, CK-AMENDMENT, CK-BRIEF), the report views, and the auditor evidence pack (CK-AUDIT-PACK). 23 checks in all.

## 0.2 System — `extensions/agentic-system`
A system map of services, data stores, contracts, shared components and external systems, with discovery, impact analysis and reviewers derived from what a change touches. Change packs for data stores, contracts, shared components, external dependencies and the supply chain. 28 checks.

## 0.3 Team — `extensions/agentic-team`
Sixteen agents described once and rendered for Claude Code, GitHub Copilot and a sequential mode. Work items with a state machine, path locks, isolated working copies, a rework limit, run budgets, a path guard, and golden tasks with seeded defects. 9 checks.

Added to it in slice 0.4: context packs, the tool allowlist, run records, routing and spend, the golden baseline, planted-instruction tests and the instruction-file lint. 16 checks in all.

## 0.4 Depth — `extensions/agentic-quality`, and the additions above
Quality packs that switch on from a spec's tier and what it touches: threat model and security evidence, privacy impact, test depth, AI evaluation and safety, infrastructure and release readiness, decision records and the incident loop. 22 checks.

## 0.5 Truth — `extensions/agentic-product`
Intake records, requirement linting, a glossary, living capability specs fed by deltas and rebuilt by replay, duplicate detection decided by a Product Owner, outcomes, sealing, and lineage from a line of code. 13 checks.

## 0.6 Connected — `extensions/agentic-connect`
Requirements from Azure DevOps, Jira, ClickUp, GitHub Issues and Projects, and documents. One pipeline command, with files for GitHub Actions, Azure Pipelines and GitLab CI. Review mirroring. Notifications to Slack, Teams, email and the originating work item. 3 checks.

## Since the slices, from using the kit on the reference project
- The pinning check (CK-PIN) reads the containers a .NET Aspire application host starts, and treats a tag that ends in `-latest` as floating. Before, finding N8 of the reference (two floating tags in such a file) was one the kit could not see.
- Writing a reviewer brief that has not changed no longer adds a second `gate.ready` entry to the audit log.
- Discovery finds Dapr event topics in C#, with who publishes and who subscribes, reading calls that name their arguments across lines. The reference map had been drawn without two publishers, and a reviewer caught it; the drift check could not have.
- Impact analysis reaches the events a touched component publishes, and their subscribers. Before, a change to a publisher did not reach the services that act on its events.
- A Critical change plans its rollback rehearsal at G3 and shows it at G7. Before, the check asked for the rehearsal's evidence as soon as a plan existed, which no plan could have.
- A Critical change's test strategy answers for each external system it may rely on: a resilience test, or a stated reason why the change does not rely on it. Systems the spec lists under `depends_on` are included and cannot be reasoned away; a placeholder no longer passes.
- The independent verifier may be given the code it verifies in a project that says what a spec touches by component. The artifact is the paths the spec's task list names and the files of the components it says it touches; the verifier may also read the files of what the spec says it depends on. Before, only paths written in the spec's front matter counted, so a spec that names components could not list a single source file.
- `why <file>:<line>` goes back to the principle and forward to what the change reaches: the task's criteria (read from the task list), the requirements, the principles the spec is held to, the component the file belongs to, what the spec touches and depends on, and the data stores, contracts, shared components and applications it reaches. A commit that names a work item settles which spec is shown.
- `team init` changes only its own block of `kit.yml`. Before, it rewrote the file and the comments in it were lost.
- The check for figures with no recorded source (CK-METRIC-PROVENANCE) reads code and data files a project lists, and there treats a number given to a name such as `accuracy` or `aiAccuracyRate` as a figure. Before, it read percentages in prose only, so it could not see finding H4 of the reference: accuracy figures written into an endpoint.
- A work item that comes back for rework in a shared working copy is no longer blamed for what others wrote in the meantime. Taking the rework up records what is there at that moment; the hand-off then lists only what the author changed after it. Before, the hand-off of a returned item was refused as soon as any other item had been handed off or a reviewer had written a report.
- What a reviewing agent writes for a gate (`specs/<spec>/reviews/G5-security.md`) is part of that gate's evidence, so a decision is bound to the findings as well. Before, a security review sat beside the evidence, and a gate could be approved on a hash that did not include it.
- A YAML file is parsed once in a process and every caller gets its own copy. Before, a check parsed a file each time it asked for it: on the reference, with 25 specs, the duplicate check parsed the system map about 1,300 times and took 78 seconds. It takes 2 now, the checks on a branch of the reference take 17 seconds, and the kit's own tests take about three minutes where they took nearly eight.
- The duplicate check lists the words two requirements share in the same order in every run. Before, words of equal weight came out in whatever order the run gave them, so two runs on the same files could print different messages.

## Installing
`scripts/install.sh <project> <lite|standard|regulated>` installs `agentic` and `agentic-team` for every profile, and the other four for Standard and Regulated. Lite is unchanged by slices 0.2 to 0.6.

## Known gaps
`docs/limits.md`.
