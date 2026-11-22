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

## Installing
`scripts/install.sh <project> <lite|standard|regulated>` installs `agentic` and `agentic-team` for every profile, and the other four for Standard and Regulated. Lite is unchanged by slices 0.2 to 0.6.

## Known gaps
`docs/limits.md`.
